import math
import vigra,numpy,h5py,glob
from lazyflow.graph import Operator,OutputSlot,InputSlot
from lazyflow.roi import roiToSlice

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

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
        def writeResult(result, blockNr, roiSlice):
            d[roiSlice] = normalize(result)
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
            print "Requesting bnr", bnr
            req.notify(writeResult, blockNr = bnr, roiSlice=s)
            print "Added callback"
            requests.append(req)
        #execute requests
        for req in requests:
            req.wait()

        f.close()

        result[0] = True
        
    def propagateDirty(self, slot, roi):
        # The output from this operator isn't generally connected to other operators.
        # If someone is using it that way, we'll assume that the user wants to know that 
        #  the input image has become dirty and may need to be written to disk again.
        self.WriteImage.setDirty(slice(None))

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

            #build 5D shape out of 2DShape and Filelist
            oslot._shape = (1, self.info.getShape()[0],self.info.getShape()[1],len(self.fileNameList),self.info.getShape()[2])
            oslot._dtype = self.info.getDtype()
            zAxisInfo = vigra.AxisInfo(key='z',typeFlags = vigra.AxisType.Space)
            tAxisInfo = vigra.AxisInfo(key='t',typeFlags = vigra.AxisType.Time)
            oslot._axistags = self.info.getAxisTags()
            oslot._axistags.insert(0,tAxisInfo)
            oslot._axistags.insert(3,zAxisInfo)

        else:
            oslot = self.outputs["stack"]
            oslot._shape = None
            oslot._dtype = None
            oslot._axistags = None

    def execute(self, slot, roi, result):
        i=0
        key = roi.toSlice()
        traceLogger.debug("OpStackLoader: Execute for: " + str(roi))
        for fileName in self.fileNameList[key[3]]:
            traceLogger.debug( "Reading image: {}".format(fileName) )
            assert (self.info.getShape() == vigra.impex.ImageInfo(fileName).getShape()), 'not all files have the same shape'
            result[...,i,:] = vigra.impex.readImage(fileName)[key[1],key[2],key[4]]
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

class OpStackToH5Writer(Operator):
    name = "OpStackToH5Writer"
    category = "IO"
    
    GlobString = InputSlot(stype='globstring')
    hdf5Group = InputSlot(stype='object')
    hdf5Path  = InputSlot(stype='string')
    
    # Requesting the output induces the copy from stack to h5 file.
    WriteImage = OutputSlot(stype='bool')

    def __init__(self, *args, **kwargs):
        super(OpStackToH5Writer, self).__init__(*args, **kwargs)
        self.opStackLoader = OpStackLoader(graph=self.graph, parent=self)
        
        self.opStackLoader.globstring.connect( self.GlobString )
    
    def setupOutputs(self):
        self.WriteImage.meta.shape = (1,)
        self.WriteImage.meta.dtype = object

    def execute(self, slot, roi, result):
        # Copy the data image-by-image
        stackTags = self.opStackLoader.stack.meta.axistags
        zAxis = stackTags.index('z')
        dataShape=self.opStackLoader.stack.meta.shape
        numImages = self.opStackLoader.stack.meta.shape[zAxis]
        
        axistags = self.opStackLoader.stack.axistags
        dtype = self.opStackLoader.stack.dtype
        if type(dtype) is numpy.dtype:
            # Make sure we're dealing with a type (e.g. numpy.float64),
            #  not a numpy.dtype
            dtype = dtype.type

        numChannels = dataShape[ axistags.index('c') ]

        # Set up our chunk shape: Aim for a cube that's roughly 300k in size
        dtypeBytes = dtype().nbytes
        cubeDim = math.pow( 300000 / (numChannels * dtypeBytes), (1/3.0) )
        cubeDim = int(cubeDim)

        chunkDims = {}
        chunkDims['t'] = 1
        chunkDims['x'] = cubeDim
        chunkDims['y'] = cubeDim
        chunkDims['z'] = cubeDim
        chunkDims['c'] = numChannels
        
        # h5py guide to chunking says chunks of 300k or less "work best"
        assert chunkDims['x'] * chunkDims['y'] * chunkDims['z'] * numChannels * dtypeBytes  <= 300000

        chunkShape = ()
        for i in range( len(dataShape) ):
            axisKey = axistags[i].key
            # Chunk shape can't be larger than the data shape
            chunkShape += ( min( chunkDims[axisKey], dataShape[i] ), )

        # Create the dataset
        internalPath = self.hdf5Path.value
        internalPath = internalPath.replace('\\', '/') # Windows fix 
        group = self.hdf5Group.value
        if internalPath in group:
            del group[internalPath]

        data = group.create_dataset(internalPath,
                                    #compression='gzip',
                                    #compression_opts=4
                                    shape=dataShape,
                                    dtype=dtype,
                                    chunks=chunkShape)
        # Now copy each image
        for z in range(numImages):
            # Ask for an entire z-slice (exactly one whole image from the stack)
            slicing = [slice(None)] * len(stackTags)
            slicing[zAxis] = slice(z, z+1)            
            data[tuple(slicing)] = self.opStackLoader.stack[slicing].wait()
            
        # We're done
        result[...] = True
        
if __name__ == '__main__':
    from lazyflow.graph import Graph
    import h5py
    import sys

    traceLogger.addHandler(logging.StreamHandler(sys.stdout))
    traceLogger.setLevel(logging.DEBUG)
    traceLogger.debug("HELLO")
    
    f = h5py.File('/tmp/flyem_sample_stack.h5')
    internalPath = 'volume/data'
        
    # OpStackToH5Writer
    graph = Graph()
    opStackToH5 = OpStackToH5Writer()
    opStackToH5.GlobString.setValue('/tmp/flyem_sample_stack/*.png')
    opStackToH5.hdf5Group.setValue(f)
    opStackToH5.hdf5Path.setValue(internalPath)
    
    success = opStackToH5.WriteImage.value
    assert success















































            

