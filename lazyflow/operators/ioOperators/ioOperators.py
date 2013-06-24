#Python
from functools import partial
import os
import math
import logging
import glob
from itertools import product, chain
from collections import deque
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

#SciPy
import vigra,numpy,h5py

#lazyflow
from lazyflow.graph import OrderedSignal, Operator, OutputSlot, InputSlot
from lazyflow.roi import roiToSlice

class OpStackLoader(Operator):
    """Imports an image stack.

    Note: This operator does NOT cache the images, so direct access
          via the execute() function is very inefficient, especially
          through the Z-axis. Typically, you'll want to connect this
          operator to a cache whose block size is large in the X-Y
          plane.

    :param globstring: A glob string as defined by the glob module. We
        also support the following special extension to globstring
        syntax: A single string can hold a *list* of globstrings. Each
        separate globstring in the list is separated by two forward
        slashes (//). For, example,

            '/a/b/c.txt///d/e/f.txt//../g/i/h.txt'

        is parsed as

            ['/a/b/c.txt', '/d/e/f.txt', '../g/i/h.txt']

    """
    name = "Image Stack Reader"
    category = "Input"

    inputSlots = [InputSlot("globstring", stype = "string")]
    outputSlots = [OutputSlot("stack")]

    class FileOpenError( Exception ):
        def __init__(self, filename):
            self.filename = filename
            self.msg = "Unable to open file: {}".format(filename)
            super(OpStackLoader.FileOpenError, self).__init__( self.msg )

    def setupOutputs(self):
        self.fileNameList = []
        globStrings = self.inputs["globstring"].value

        # Parse list into separate globstrings and combine them
        for globString in sorted(globStrings.split("//")):
            self.fileNameList += sorted(glob.glob(globString))

        if len(self.fileNameList) != 0:
            try:
                self.info = vigra.impex.ImageInfo(self.fileNameList[0])
            except RuntimeError:
                raise OpStackLoader.FileOpenError(self.fileNameList[0])

            oslot = self.outputs["stack"]
            
            #input-file should have type xyc
            #build 4D shape out of 2DShape and Filelist: xyzc
            oslot.meta.shape = (self.info.getShape()[0],
                                self.info.getShape()[1],
                                len(self.fileNameList),
                                self.info.getShape()[2])
            oslot.meta.dtype = self.info.getDtype()
            zAxisInfo = vigra.AxisInfo(key='z', typeFlags=vigra.AxisType.Space)
            axistags = self.info.getAxisTags()
            
            #Can't insert in axistags because axistags
            #of oslot and self.info are still connected!
            #Manipulating them by insert would change them
            #in self.info and shape and axistags will be mismatched.
            
            oslot.meta.axistags = vigra.AxisTags(axistags[0], axistags[1], zAxisInfo, axistags[2])
            
        else:
            oslot = self.outputs["stack"]
            oslot.meta.shape = None
            oslot.meta.dtype = None
            oslot.meta.axistags = None

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.globstring
        # Any change to the globstring means our entire output is dirty.
        self.stack.setDirty(slice(None))

    def execute(self, slot, subindex, roi, result):
        i=0
        key = roi.toSlice()
        traceLogger.debug("OpStackLoader: Execute for: " + str(roi))
        for fileName in self.fileNameList[key[2]]:
            traceLogger.debug( "Reading image: {}".format(fileName) )
            if self.info.getShape() != vigra.impex.ImageInfo(fileName).getShape():
                raise RuntimeError('not all files have the same shape')
            # roi is in xyzc order.
            # Copy each z-slice one at a time.
            result[...,i,:] = vigra.impex.readImage(fileName)[key[0],key[1],key[3]]
            i = i+1

class OpStackWriter(Operator):
    name = "Stack File Writer"
    category = "Output"

    inputSlots = [InputSlot("Filepath", stype = "string", value = ''),
                  InputSlot("Filename", stype = "string"),
                  InputSlot("Filetype", stype = "string", value = 'png'),
                  InputSlot("ImageAxesNames", stype = "list", value = 'xy'),
                  InputSlot("Image")]
    outputSlots = [OutputSlot("WriteImage"),
                  OutputSlot("FilePattern", stype = "string")
                  ]

    def __init__(self, *args, **kwargs):
        super(OpStackWriter, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()

    def setupOutputs(self):
        assert self.Image.meta.shape is not None
        self.WriteImage.meta.shape = (1,)
        self.WriteImage.meta.dtype = object
        self.FilePattern.meta.shape = (1,)
        self.FilePattern.meta.dtype = object
        self.setupIndices()

    def setupIndices(self):
        self.imageAxesFilteredNames = [axis for axis in
                                       self.ImageAxesNames.value if axis in
                                       self.Image.meta.getAxisKeys()]
        self.imageAxes = [self.Image.meta.axistags.index(axis) for axis in
                          self.imageAxesFilteredNames]
        self.orderedImageAxes = sorted(self.imageAxes)
        self.transposing = [self.imageAxes.index(x) for x in
                            self.orderedImageAxes]

        self.iterationIndices = [i for i in range(len(self.Image.meta.shape)) if i not in
                            self.imageAxes]

        self.axisKeys = self.Image.meta.getAxisKeys()
        

    def execute(self, slot, subindex, roi, result):
        if slot == self.FilePattern:
            filePattern = "%s-%s" % (self.Filename.value
                                      ,''.join(self.imageAxesFilteredNames))
            for iterationIndex in self.iterationIndices:
                filePattern = filePattern + "-" + str(self.axisKeys[iterationIndex]) +  "_%04d"
            filePattern = filePattern + "." + self.Filetype.value
            result[0] = filePattern

        if slot == self.WriteImage:
            filepath = self.Filepath.value
            filename = self.Filename.value
            #s = ...
            #image = self.Image[:].wait() #WIP, don't wait for everything at the same time
            imageShape = self.Image.meta.shape 
            slicings = self.computeRequestSlicings()
            numSlicings = numpy.prod(self.iteratingShape, dtype = numpy.int)
            axisKeys = self.Image.meta.getAxisKeys()
            iterationAxisDescriptors = [axisKeys[i] for i in self.iterationIndices]
            newImageShape = tuple([imageShape[key] for key in
                                   self.orderedImageAxes])
            #newImageAxisKeys = ''.join([axisKeys[i] for i in newImageIndices])
            filepattern = self.FilePattern[:].wait()[0]
            
            self.progressSignal(0)
            activeRequests = deque()
            activeSlicings = deque()
            # Start by activating 10 requests 
            for i in range( min(10, numSlicings) ):
                s = next(slicings)
                activeSlicings.append(s)
                self.logger.debug( "Creating request for slicing {}".format(s) )
                activeRequests.append( self.Image[s] )
            
            counter = 0

            while len(activeRequests) > 0:
                # Wait for a request to finish
                req = activeRequests.popleft()
                slicing=activeSlicings.popleft()
                data = req.wait()
                iterationIndexDescriptors = tuple([slicing[i].start for i in
                                                   self.iterationIndices])
                patternEntries = iterationIndexDescriptors
                
                fullFilename = filepath + filepattern % (patternEntries)
                vigra.impex.writeImage(data.reshape(*newImageShape).transpose(self.transposing), fullFilename)
                
                req.clean() # Discard the data in the request and allow its children to be garbage collected.

                try:
                    s = next(slicings)
                    activeSlicings.append(s)
                    activeRequests.append( self.Image[s] )
                except StopIteration:
                    pass

                # Since requests finish in an arbitrary order (but we always block for them in the same order),
                # this progress feedback will not be smooth.  It's the best we can do for now.
                self.progressSignal( 100*counter/numSlicings )
                self.logger.debug( "request {} out of {} executed".format( counter, numSlicings ) )
                counter += 1


            # We're finished.
            result[0] = True

            self.progressSignal(100)

    def computeRequestSlicings(self):

        imageShape = self.Image.meta.shape
        self.iteratingShape = [imageShape[i] for i in self.iterationIndices]
        indexList = [xrange(index) for index in self.iteratingShape]
        fullSliceObject = [slice(None) for i in imageShape]
        def fillSlicing(tup):
            slicing = numpy.copy(fullSliceObject)
            slicing[self.iterationIndices] = [slice(i, i + 1) for i in tup]
            return tuple(slicing)

        #for combo in product(*indexList):
        #    slicing = numpy.copy(fullSliceObject)
        #    slicing[self.iterationIndices] = [slice(i, i + 1) for i in combo]
        #    slicings.append(tuple(slicing))
        return (fillSlicing(tup) for tup in product(*indexList))

    def propagateDirty(self, slot, subindex, roi):
        self.FilePattern.setDirty(slice(None))
        self.WriteImage.setDirty(slice(None))

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
        self.progressSignal = OrderedSignal()
        self.opStackLoader = OpStackLoader(graph=self.graph, parent=self)
        self.opStackLoader.globstring.connect( self.GlobString )

    def setupOutputs(self):
        self.WriteImage.meta.shape = (1,)
        self.WriteImage.meta.dtype = object

    def propagateDirty(self, slot, subindex, roi):
        # Any change to our inputs means we're dirty
        assert slot == self.GlobString or slot == self.hdf5Group or slot == self.hdf5Path
        self.WriteImage.setDirty(slice(None))

    def execute(self, slot, subindex, roi, result):
        # Copy the data image-by-image
        stackTags = self.opStackLoader.stack.meta.axistags
        zAxis = stackTags.index('z')
        dataShape=self.opStackLoader.stack.meta.shape
        numImages = self.opStackLoader.stack.meta.shape[zAxis]
        axistags = self.opStackLoader.stack.meta.axistags
        dtype = self.opStackLoader.stack.meta.dtype
        if type(dtype) is numpy.dtype:
            # Make sure we're dealing with a type (e.g. numpy.float64),
            #  not a numpy.dtype
            dtype = dtype.type
        
        index_ = axistags.index('c')
        if index_ >= len(dataShape):
            numChannels = 1
        else:
            numChannels = dataShape[ index_]
        
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
                                    #compression_opts=4,
                                    shape=dataShape,
                                    dtype=dtype,
                                    chunks=chunkShape)
        # Now copy each image
        self.progressSignal(0)
        
        for z in range(numImages):
            # Ask for an entire z-slice (exactly one whole image from the stack)
            slicing = [slice(None)] * len(stackTags)
            slicing[zAxis] = slice(z, z+1)
            data[tuple(slicing)] = self.opStackLoader.stack[slicing].wait()
            self.progressSignal( z*100 / numImages )

        # We're done
        result[...] = True

        self.progressSignal(100)

        return result

class OpH5WriterBigDataset(Operator):
    name = "H5 File Writer BigDataset"
    category = "Output"

    inputSlots = [InputSlot("hdf5File"), # Must be an already-open hdf5File (or group) for writing to
                  InputSlot("hdf5Path", stype = "string"),
                  InputSlot("Image")]

    outputSlots = [OutputSlot("WriteImage")]

    loggingName = __name__ + ".OpH5WriterBigDataset"
    logger = logging.getLogger(loggingName)
    traceLogger = logging.getLogger("TRACE." + loggingName)

    def __init__(self, *args, **kwargs):
        super(OpH5WriterBigDataset, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()

    def setupOutputs(self):
        self.outputs["WriteImage"].meta.shape = (1,)
        self.outputs["WriteImage"].meta.dtype = object

        self.f = self.inputs["hdf5File"].value
        hdf5Path = self.inputs["hdf5Path"].value
        
        # On windows, there may be backslashes.
        hdf5Path = hdf5Path.replace('\\', '/')

        hdf5GroupName, datasetName = os.path.split(hdf5Path)
        if hdf5GroupName == "":
            g = self.f
        else:
            if hdf5GroupName in self.f:
                g = self.f[hdf5GroupName]
            else:
                g = self.f.create_group(hdf5GroupName)

        dataShape=self.Image.meta.shape
        taggedShape = self.Image.meta.getTaggedShape()
        dtype = self.Image.meta.dtype
        if type(dtype) is numpy.dtype:
            # Make sure we're dealing with a type (e.g. numpy.float64),
            #  not a numpy.dtype
            dtype = dtype.type

        numChannels = 1
        if 'c' in taggedShape:
            numChannels = taggedShape['c']

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
            axisKey = self.Image.meta.axistags[i].key
            # Chunk shape can't be larger than the data shape
            chunkShape += ( min( chunkDims[axisKey], dataShape[i] ), )

        self.chunkShape = chunkShape
        if datasetName in g.keys():
            del g[datasetName]
        self.d=g.create_dataset(datasetName,
                                shape=dataShape,
                                dtype=dtype,
                                chunks=self.chunkShape,
                                compression='gzip', # <-- Would be nice to use lzf compression here, but that is h5py-specific.
                                compression_opts=1) # <-- Optimize for speed, not disk space.

        if self.Image.meta.drange is not None:
            self.d.attrs['drange'] = self.Image.meta.drange

    def execute(self, slot, subindex, rroi, result):
        self.progressSignal(0)
        
        slicings=self.computeRequestSlicings()
        numSlicings = len(slicings)

        self.logger.debug( "Dividing work into {} pieces".format( len(slicings) ) )

        # Throttle: Only allow 10 outstanding requests at a time.
        # Otherwise, the whole set of requests can be outstanding and use up ridiculous amounts of memory.        
        activeRequests = deque()
        activeSlicings = deque()
        # Start by activating 10 requests 
        for i in range( min(10, len(slicings)) ):
            s = slicings.pop()
            activeSlicings.append(s)
            self.logger.debug( "Creating request for slicing {}".format(s) )
            activeRequests.append( self.inputs["Image"][s] )
        
        counter = 0

        while len(activeRequests) > 0:
            # Wait for a request to finish
            req = activeRequests.popleft()
            s=activeSlicings.popleft()
            data = req.wait()
            if data.flags.c_contiguous:
                self.d.write_direct(data.view(numpy.ndarray), dest_sel=s)
            else:
                self.d[s] = data
            
            req.clean() # Discard the data in the request and allow its children to be garbage collected.

            if len(slicings) > 0:
                # Create a new active request
                s = slicings.pop()
                activeSlicings.append(s)
                activeRequests.append( self.inputs["Image"][s] )
            
            # Since requests finish in an arbitrary order (but we always block for them in the same order),
            # this progress feedback will not be smooth.  It's the best we can do for now.
            self.progressSignal( 100*counter/numSlicings )
            self.logger.debug( "request {} out of {} executed".format( counter, numSlicings ) )
            counter += 1

        # Save the axistags as a dataset attribute
        self.d.attrs['axistags'] = self.Image.meta.axistags.toJSON()

        # We're finished.
        result[0] = True

        self.progressSignal(100)

    def computeRequestSlicings(self):
        #TODO: reimplement the request better
        shape=numpy.asarray(self.inputs['Image'].meta.shape)

        chunkShape = numpy.asarray(self.chunkShape)

        # Choose a request shape that is a multiple of the chunk shape
        axistags = self.Image.meta.axistags
        multipliers = { 'x':5, 'y':5, 'z':5, 't':1, 'c':100 } # For most problems, there is little advantage to breaking up the channels.
        multiplier = [multipliers[tag.key] for tag in axistags ]
        shift = chunkShape * numpy.array(multiplier)
        shift=numpy.minimum(shift,shape)
        start=numpy.asarray([0]*len(shape))

        stop=shift
        reqList=[]

        #shape = shape - (numpy.mod(numpy.asarray(shape),
        #                  shift))

        for indices in product(*[range(0, stop, step)
                        for stop,step in zip(shape, shift)]):

            start=numpy.asarray(indices)
            stop=numpy.minimum(start+shift,shape)
            reqList.append(roiToSlice(start,stop))
        return reqList

    def propagateDirty(self, slot, subindex, roi):
        # The output from this operator isn't generally connected to other operators.
        # If someone is using it that way, we'll assume that the user wants to know that 
        #  the input image has become dirty and may need to be written to disk again.
        self.WriteImage.setDirty(slice(None))

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

