#Python
from functools import partial
import math
import logging
import glob
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

    inputSlots = [InputSlot("filepath", stype = "string"),
                  InputSlot("dummy", stype = "list"),
                  InputSlot("input")]
    outputSlots = [OutputSlot("WritePNGStack")]

    def setupOutputs(self):
        assert self.inputs['input'].meta.getAxisKeys() == ['t', 'x', 'y', 'z', 'c']
        assert self.inputs['input'].meta.shape is not None
        self.outputs["WritePNGStack"].meta.shape = self.inputs['input'].meta.shape
        self.outputs["WritePNGStack"].meta.dtype = object

    def execute(self, slot, subindex, roi, result):
        image = self.inputs["input"][roi.toSlice()].wait()

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
                        vigra.impex.writeImage(image[:,:,i,j,k],
                                               filepath+"-xt-y_%04d_z_%04d_c_%04d." % (i,j,k)+filetype)
        if "yz" in dummy:
            for i in range(image.shape[0]):
                for j in range(image.shape[1]):
                    for k in range(image.shape[4]):
                        vigra.impex.writeImage(image[i,j,:,:,k],
                                               filepath+"-yz-t_%04d_x_%04d_c_%04d." % (i,j,k)+filetype)
        if "yt" in dummy:
            for i in range(image.shape[1]):
                for j in range(image.shape[3]):
                    for k in range(image.shape[4]):
                        vigra.impex.writeImage(image[:,i,:,j,k],
                                               filepath+"-yt-x_%04d_z_%04d_c_%04d." % (i,j,k)+filetype)
        if "zt" in dummy:
            for i in range(image.shape[1]):
                for j in range(image.shape[2]):
                    for k in range(image.shape[4]):
                        vigra.impex.writeImage(image[:,i,j,:,k],
                                               filepath+"-zt-x_%04d_y_%04d_c_%04d." % (i,j,k)+filetype)

    def propagateDirty(self, slot, subindex, roi):
        self.WritePNGStack.setDirty(slice(None))


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
