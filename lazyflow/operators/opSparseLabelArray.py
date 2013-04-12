#Python
import threading
from functools import partial

#SciPy
import numpy

#third-party
import blist

#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice

class OpSparseLabelArray(Operator):
    name = "Sparse Label Array"
    description = "simple cache for sparse label arrays"

    inputSlots = [InputSlot("Input", optional = True),
                    InputSlot("shape"),
                    InputSlot("eraser"),
                    InputSlot("deleteLabel", optional = True)]

    outputSlots = [OutputSlot("Output"),
                    OutputSlot("nonzeroValues"),
                    OutputSlot("nonzeroCoordinates"),
                    OutputSlot("maxLabel")]

    def __init__(self, *args, **kwargs):
        super(OpSparseLabelArray, self).__init__( *args, **kwargs )
        self.lock = threading.Lock()
        self._denseArray = None
        self._sparseNZ = None
        self._oldShape = (0,)
        self._maxLabel = 0            

    def setupOutputs(self):
        if (self._oldShape != self.inputs["shape"].value).any():
            shape = self.inputs["shape"].value
            self._oldShape = shape
            self.outputs["Output"].meta.dtype = numpy.uint8
            self.outputs["Output"].meta.shape = shape
            
            # FIXME: Don't give arbitrary axistags.  Specify them correctly if you need them.
            #self.outputs["Output"].meta.axistags = vigra.defaultAxistags(len(shape))

            self.inputs["Input"].meta.shape = shape


            self.outputs["nonzeroValues"].meta.dtype = object
            self.outputs["nonzeroValues"].meta.shape = (1,)

            self.outputs["nonzeroCoordinates"].meta.dtype = object
            self.outputs["nonzeroCoordinates"].meta.shape = (1,)

            self._denseArray = numpy.zeros(shape, numpy.uint8)
            self._sparseNZ =  blist.sorteddict()

        if self.inputs["deleteLabel"].ready() and self.inputs["deleteLabel"].value != -1:
            labelNr = self.inputs["deleteLabel"].value

            neutralElement = 0
            self.inputs["deleteLabel"].setValue(-1) #reset state of inputslot
            self.lock.acquire()

            # Find the entries to remove
            updateNZ = numpy.nonzero(numpy.where(self._denseArray == labelNr,1,0))
            if len(updateNZ)>0:
                # Convert to 1-D indexes for the raveled version
                updateNZRavel = numpy.ravel_multi_index(updateNZ, self._denseArray.shape)                                        
                # Zero out the entries we don't want any more
                self._denseArray.ravel()[updateNZRavel] = neutralElement
                # Remove the zeros from the sparse list
                for index in updateNZRavel:
                    self._sparseNZ.pop(index)
            # Labels are continuous values: Shift all higher label values down by 1.
            self._denseArray[:] = numpy.where(self._denseArray > labelNr, self._denseArray - 1, self._denseArray)
            self._maxLabel = self._denseArray.max()
            self.lock.release()
            self.outputs["nonzeroValues"].setDirty(slice(None))
            self.outputs["nonzeroCoordinates"].setDirty(slice(None))
            self.outputs["Output"].setDirty(slice(None))
            self.outputs["maxLabel"].setValue(self._maxLabel)

    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start,roi.stop)

        self.lock.acquire()
        assert(self.inputs["eraser"].ready() == True and self.inputs["shape"].ready() == True), "OpDenseSparseArray:  One of the neccessary input slots is not ready: shape: %r, eraser: %r" % (self.inputs["eraser"].ready(), self.inputs["shape"].ready())
        if slot.name == "Output":
            result[:] = self._denseArray[key]
        elif slot.name == "nonzeroValues":
            result[0] = numpy.array(self._sparseNZ.values())
        elif slot.name == "nonzeroCoordinates":
            result[0] = numpy.array(self._sparseNZ.keys())
        elif slot.name == "maxLabel":
            result[0] = self._maxLabel
        self.lock.release()
        return result

    def setInSlot(self, slot, subindex, roi, value):
        key = roi.toSlice()
        assert value.dtype == self._denseArray.dtype, "Labels must be {}".format(self._denseArray.dtype)
        assert isinstance(value, numpy.ndarray)            
        if type(value) != numpy.ndarray:
            # vigra.VigraArray doesn't handle advanced indexing correctly,
            #   so convert to numpy.ndarray first
            value = value.view(numpy.ndarray)
        
        shape = self.inputs["shape"].value
        eraseLabel = self.inputs["eraser"].value
        neutralElement = 0

        self.lock.acquire()
        #fix slicing of single dimensions:
        start, stop = sliceToRoi(key, shape, extendSingleton = False)
        start = start.floor()
        stop = stop.floor()

        tempKey = roiToSlice(start-start, stop-start) #, hardBind = True)

        stop += numpy.where(stop-start == 0,1,0)

        key = roiToSlice(start,stop)

        updateShape = tuple(stop-start)

        update = self._denseArray[key].copy()

        update[tempKey] = value

        startRavel = numpy.ravel_multi_index(numpy.array(start, numpy.int32),shape)

        #insert values into dict
        updateNZ = numpy.nonzero(numpy.where(update != neutralElement,1,0))
        updateNZRavelSmall = numpy.ravel_multi_index(updateNZ, updateShape)

        if isinstance(value, numpy.ndarray):
            valuesNZ = value.ravel()[updateNZRavelSmall]
        else:
            valuesNZ = value

        updateNZRavel = numpy.ravel_multi_index(updateNZ, shape)
        updateNZRavel += startRavel

        self._denseArray.ravel()[updateNZRavel] = valuesNZ

        valuesNZ = self._denseArray.ravel()[updateNZRavel]

        self._denseArray.ravel()[updateNZRavel] =  valuesNZ

        td = blist.sorteddict(zip(updateNZRavel.tolist(),valuesNZ.tolist()))

        self._sparseNZ.update(td)

        #remove values to be deleted
        updateNZ = numpy.nonzero(numpy.where(update == eraseLabel,1,0))
        if len(updateNZ)>0:
            updateNZRavel = numpy.ravel_multi_index(updateNZ, shape)
            updateNZRavel += startRavel
            self._denseArray.ravel()[updateNZRavel] = neutralElement
            for index in updateNZRavel:
                self._sparseNZ.pop(index)

        # Update our maxlabel
        self._maxLabel = self._denseArray.max()

        self.lock.release()

        # Set our max label dirty if necessary
        self.outputs["maxLabel"].setValue(self._maxLabel)
        self.outputs["Output"].setDirty(key)
    
    def propagateDirty(self, dirtySlot, subindex, roi):
        if dirtySlot == self.Input:
            self.Output.setDirty(roi)
        else:
            # All other inputs are single-value inputs that will trigger
            #  a new call to setupOutputs, which already sets the outputs dirty.
            # (See above.) 
            pass