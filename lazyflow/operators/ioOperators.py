import vigra,numpy,h5py,glob
from lazyflow.graph import Operator,OutputSlot,InputSlot
from lazyflow.roi import roiToSlice

class OpH5Writer(Operator):
    name = "H5 File Writer"
    category = "Output"
    
    inputSlots = [InputSlot("filename", stype = "filestring"), \
                  InputSlot("hdf5Path", stype = "string"), InputSlot("input"),\
                  InputSlot("blockShape"),InputSlot("dataType"),InputSlot("roi"),\
                  InputSlot("normalize")]
    
    outputSlots = [OutputSlot("WriteImage")]

    def setupOutputs(self):        
        self.outputs["WriteImage"]._shape = (1,)
        self.outputs["WriteImage"]._dtype = object

    
    def execute(self, slot, roi, result):
        
        inputRoi = self.inputs["roi"].value
        key = roiToSlice(inputRoi[0], inputRoi[1])
        filename = self.inputs["filename"].value
        hdf5Path = self.inputs["hdf5Path"].value
        imSlot = self.inputs["input"]
        image = numpy.ndarray(imSlot.shape, dtype=self.inputs["dataType"].value)[key]
        
        try:
          #create H5File and DataSet
          f = h5py.File(filename, 'w')
        except:
          return
        g = f
        
        #check for valid hdf5 path, if not valid, use default
        try:
            pathElements = hdf5Path.split("/")
            for s in pathElements[:-1]:
                g = g.create_group(s)
            d = g.create_dataset(pathElements[-1],data = image)
        except:
            print '*************String %s is not a valid hdf5 path, path set to default************' %(hdf5Path)
            hdf5Path = 'volume/data' 
            pathElements = hdf5Path.split("/")
            for s in pathElements[:-1]:
                g = g.create_group(s)
            d = g.create_dataset(pathElements[-1],data = image)
            
        #get, respectively set the blockshape as a tuple
        bs = self.inputs["blockShape"].value
        if type(bs) != tuple:
            assert(type(bs) == int)
            bs = (bs,)*len(image.shape)

        #calculate the number of blocks
        nBlockShape = numpy.array(bs)
        nshape = numpy.array(image.shape)
        blocks = numpy.ceil(nshape*1.0 / nBlockShape).astype(numpy.int32)
        blockIndices = numpy.nonzero(numpy.ones(blocks))
        
        #calculate normalization
        max0, min0 = numpy.max(self.inputs["input"].value), numpy.min(self.inputs["input"].value)
        max1, min1 = self.inputs["normalize"].value[1],self.inputs["normalize"].value[0] 
        
        #check normalization limits positive? ordered?
        assert type(max1) == int and type(min1) == int, 'Normalization constants are not integer!'
        
        if max1 < 0 or min1 < 0 or max1 < min1:
            max1,min1 = sorted([abs(max1),abs(min1)])
            print '*************WARNING: Normalization limits arent positvive or ordered**********'
        
        #normalization function
        def normalize(value):
            return 1.0*(value - min0)*(max1-min1)/(max0-min0)+min1
        
        #check combination normalization limits with datatype
        if abs(max1)-abs(min1) <= 255 and (self.inputs["dataType"].value == 'uint8' or self.inputs["dataType"].value == 'uint16'):
            print '*************WARNING: Normalization is not appropriate for dataType************'
        
        
        #define write function
        def writeResult(result,blockNr, roiSlice):
            d[roiSlice] = normalize(result[:])
            print "writing block %d at %r" % (blockNr, roiSlice)
        
        requests = []
        
        #iter trough blocks and generate requests
        for bnr in range(len(blockIndices[0])):
            indices = [blockIndices[0][bnr]*nBlockShape[0],]
            for i in range(1,len(nshape)):
                indices.append(blockIndices[i][bnr]*nBlockShape[i])
            nIndices = numpy.array(indices)
            start =  nIndices
            stop = numpy.minimum(nshape,start+nBlockShape)

            s = roiToSlice(start,stop)
            req = self.inputs["input"][s]
            req.notify(writeResult,blockNr = bnr, roiSlice=s)
            requests.append(req)
        #execute requests
        for req in requests:
          req.wait()
        
        f.close()
        
        result[0] = True

class OpStackLoader(Operator):
    name = "Image Stack Reader"
    category = "Input"
    
    inputSlots = [InputSlot("globstring", stype = "string")]
    outputSlots = [OutputSlot("stack")]
    
    def setupOutputs(self):
        globString = self.inputs["globstring"].value
        self.fileNameList = sorted(glob.glob(globString))
        

        if len(self.fileNameList) != 0:
            self.info = vigra.impex.ImageInfo(self.fileNameList[0])
            oslot = self.outputs["stack"]
            
            #build 4D shape out of 2DShape and Filelist
            oslot._shape = (self.info.getShape()[0],self.info.getShape()[1],len(self.fileNameList),self.info.getShape()[2])
            oslot._dtype = self.info.getDtype()
            zAxisInfo = vigra.AxisInfo(key='z',typeFlags = vigra.AxisType.Space)
            oslot._axistags = self.info.getAxisTags()
            oslot._axistags.insert(2,zAxisInfo)
        
        else:
            oslot = self.outputs["stack"]
            oslot._shape = None
            oslot._dtype = None
            oslot._axistags = None
            
    def execute(self, slot, roi, result):
        i=0
        key = roi.toSlice()
        for fileName in self.fileNameList[key[2]]:
            assert (self.info.getShape() == vigra.impex.ImageInfo(fileName).getShape()), 'not all files have the same shape'
            result[:,:,i,:] = vigra.impex.readImage(fileName)[key[0],key[1],key[3]]
            i = i+1


class OpStackWriter(Operator):
    name = "Stack File Writer"
    category = "Output"
    
    inputSlots = [InputSlot("filepath", stype = "string"), \
                  InputSlot("dummy", stype = "list"), \
                  InputSlot("input")]
    outputSlots = [OutputSlot("WritePNGStack")]
    
    def setupOutputs(self):
        assert self.inputs['input'].shape is not None
        self.outputs["WritePNGStack"]._shape = self.inputs['input'].shape
        self.outputs["WritePNGStack"]._dtype = object
    
    def execute(self,slot,roi,result):
        image = self.inputs["input"][roi.toSlice()].allocate().wait()

        filepath = self.inputs["filepath"].value
        filepath = filepath.split(".")
        filetype = filepath[-1]
        filepath = filepath[0:-1]
        filepath = "/".join(filepath)
        dummy = self.inputs["dummy"].value
        
        if "xy" in dummy:
            pass
        if "xz" in dummy:
            pass
        if "xt" in dummy:
            for i in range(image.shape[2]):
                for j in range(image.shape[3]):
                    for k in range(image.shape[4]):
                        vigra.impex.writeImage(image[:,:,i,j,k],filepath+"-xt-y_%04d_z_%04d_c_%04d." % (i,j,k)+filetype)
        if "yz" in dummy:
            for i in range(image.shape[0]):
                for j in range(image.shape[1]):
                    for k in range(image.shape[4]):
                        vigra.impex.writeImage(image[i,j,:,:,k],filepath+"-yz-t_%04d_x_%04d_c_%04d." % (i,j,k)+filetype)
        if "yt" in dummy:
            for i in range(image.shape[1]):
                for j in range(image.shape[3]):
                    for k in range(image.shape[4]):
                        vigra.impex.writeImage(image[:,i,:,j,k],filepath+"-yt-x_%04d_z_%04d_c_%04d." % (i,j,k)+filetype)
        if "zt" in dummy:
            for i in range(image.shape[1]):
                for j in range(image.shape[2]):
                    for k in range(image.shape[4]):
                        vigra.impex.writeImage(image[:,i,j,:,k],filepath+"-zt-x_%04d_y_%04d_c_%04d." % (i,j,k)+filetype)
