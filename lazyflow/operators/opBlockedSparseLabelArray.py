#Python
import threading
import logging
import copy
import time
from functools import partial
logger = logging.getLogger(__name__)

#SciPy
import numpy

#third-party
import blist

#lazyflow
from lazyflow.utility import Tracer
from lazyflow.rtype import SubRegion
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice
from lazyflow.operators.opSparseLabelArray import OpSparseLabelArray

class OpBlockedSparseLabelArray(Operator):
    """
    This operator is designed to provide sparse access to label data.
    
    Inputs:
        Input - Must be connected to a slot whose axistags are correct for the data being stored.
                The partner will NOT be used for obtaining label data.  It will just be used to get the axistags.
                Client code uses setitem syntax with this input to insert new labels into the array.
                e.g. op.Input[0:1,10:20,20:30,30:40,0:1] = mydata[0:1,0:10,0:10,0:10,0:1]
        shape - The shape of the overall data array
        eraser - The value that represents the eraser label.  If this label is seen in data that 
                    comes in via setInSlot(), then the labels at these points will be deleted (reset to zero).
        deleteLabel - A "special" input that is monitored for TRANSITIONS.  
                        When it transitions from -1 to some label value N, label value N is deleted from the array.  
                        All other labels > N are decremented afterwards, so the stored labels are always in a continuous sequence.
                        For example, if the array already has values for labels 1, 2, and 3, setting deleteLabel to 2 
                        will cause all 2s to be deleted, and then the 3s are converted to 2s.  
                        The end result is a stored array that contains label values for 1 and 2.
        blockShape - The shape of the internal blocks used to store (sparsely) the label values in the array
    
    Outputs:
        Output - The stored values.  Any data that has not been marked with a label yet will be given as zeros.
        nonzeroValues - The list of label values (e.g. [1,2,3])
        nonzeroCoordinates - NOT SUPPORTED
        nonzeroBlocks - A list of slicings that will yield non-zero data if queried on the Output slot
        maxLabel - The maximum label value currently stored anywhere in the array.
    """
    name = "Blocked Sparse Label Array"
    description = "simple cache for sparse label arrays"

    inputSlots = [InputSlot("Input"),
                    InputSlot("shape"),
                    InputSlot("eraser"),
                    InputSlot("deleteLabel", optional = True),
                    InputSlot("blockShape")]

    outputSlots = [OutputSlot("Output"),
                    OutputSlot("nonzeroValues"),
                    OutputSlot("nonzeroCoordinates"),
                    OutputSlot("nonzeroBlocks"),
                    OutputSlot("maxLabel")]

    loggerName = __name__ + ".OpBlockedSparseLabelArray"
    logger = logging.getLogger(loggerName)
    traceLogger = logging.getLogger("TRACE." + loggerName)

    def __init__(self, *args, **kwargs):
        with Tracer(self.traceLogger):
            super(OpBlockedSparseLabelArray, self).__init__( *args, **kwargs )
            self.lock = threading.Lock()

            self._sparseNZ = None
            self._labelers = {}
            self._oldMaxLabels = {}
            self._cacheShape = None
            self._cacheEraser = None
            self._maxLabel = 0
            self._maxLabelHistogram = numpy.zeros((1024,), numpy.uint32) # keeps track of how many sub- OpSparseLabelArrays vote for a vertain maxLabel
            self.deleteLabel.setValue(-1)

    def setupOutputs(self):
        with Tracer(self.traceLogger):
            if self.inputs["shape"].ready():
                self._cacheShape = self.inputs["shape"].value

                # FIXME: This is a super-special case because we are changing an INPUT shape from within setupOutputs!
                if self.inputs["Input"].meta.shape != self._cacheShape:
                    self.inputs["Input"].meta.shape = self._cacheShape
                    # If we're wrapped, then we have to propagate this shape change BACKWARDS.
                    if self.inputs['Input'].partner is not None:
                        self.inputs['Input'].partner.meta.shape = self._cacheShape
                    #self.inputs["Input"]._changed()

                self.outputs["Output"].meta.dtype = numpy.uint8
                self.outputs["Output"].meta.shape = self._cacheShape
                self.outputs["Output"].meta.axistags = self.Input.meta.axistags

                # Copy axis tags from input if possible
                inputAxisTags = self.inputs["Input"].meta.axistags
                if inputAxisTags is not None:
                    self.outputs["Output"].meta.axistags = copy.copy(inputAxisTags)

                self.outputs["nonzeroValues"].meta.dtype = object
                self.outputs["nonzeroValues"].meta.shape = (1,)

                self.outputs["nonzeroCoordinates"].meta.dtype = object
                self.outputs["nonzeroCoordinates"].meta.shape = (1,)

                self.outputs["nonzeroBlocks"].meta.dtype = object
                self.outputs["nonzeroBlocks"].meta.shape = (1,)

                self.outputs["maxLabel"].setValue(self._maxLabel)

                #Filled on request
                self._sparseNZ =  blist.sorteddict()

            if self.inputs["eraser"].ready():
                self._cacheEraser = self.inputs["eraser"].value
                for l in self._labelers.values():
                    l.inputs['eraser'].setValue(self._cacheEraser)

            if self.inputs["blockShape"].ready():
                self._origBlockShape = self.inputs["blockShape"].value

                if type(self._origBlockShape) != tuple:
                    self._blockShape = (self._origBlockShape,)*len(self._cacheShape)
                else:
                    self._blockShape = self._origBlockShape

                self._blockShape = numpy.minimum(self._blockShape, self._cacheShape)

                self._dirtyShape = numpy.ceil(1.0 * numpy.array(self._cacheShape) / numpy.array(self._blockShape))

                self.logger.debug( "Reconfigured Sparse labels with {}, {}, {}, {}".format( self._cacheShape, self._blockShape, self._dirtyShape, self._origBlockShape ) )
                #FIXME: we don't really need this blockState thing
                self._blockState = numpy.ones(self._dirtyShape, numpy.uint8)

                _blockNumbers = numpy.dstack(numpy.nonzero(self._blockState.ravel()))
                _blockNumbers.shape = self._dirtyShape

                _blockIndices = numpy.dstack(numpy.nonzero(self._blockState))
                _blockIndices.shape = self._blockState.shape + (_blockIndices.shape[-1],)


                self._blockNumbers = _blockNumbers
                #self._blockIndices = _blockIndices

                # allocate queryArray object
                self._flatBlockIndices =  _blockIndices[:]
                self._flatBlockIndices = self._flatBlockIndices.reshape(self._flatBlockIndices.size/self._flatBlockIndices.shape[-1],self._flatBlockIndices.shape[-1],)


            if self.inputs["deleteLabel"].ready():
                for l in self._labelers.values():
                    l.inputs["deleteLabel"].setValue(self.inputs['deleteLabel'].value)
                    
                    # Our internal labelers will mark their outputs as dirty,
                    # But we aren't hooked up to forward those dirty notifications to our outputs.
                    # Instead, we'll just mark our whole output dirty right now.
                    self.Output.setDirty(slice(None))

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        self.lock.acquire()
        assert(self.inputs["eraser"].ready() == True and self.inputs["shape"].ready() == True and self.inputs["blockShape"].ready()==True), \
        "OpBlockedSparseLabelArray:  One of the neccessary input slots is not ready: shape: %r, eraser: %r" % \
        (self.inputs["eraser"].ready(), self.inputs["shape"].ready())
        if slot.name == "Output":
                #result[:] = self._denseArray[key]
                #find the block key
            start, stop = sliceToRoi(key, self._cacheShape)
            blockStart = (1.0 * start / self._blockShape).floor()
            blockStop = (1.0 * stop / self._blockShape).ceil()
            blockKey = roiToSlice(blockStart,blockStop)
            innerBlocks = self._blockNumbers[blockKey]
            for b_ind in innerBlocks.ravel():
                #which part of the original key does this block fill?
                offset = self._blockShape*self._flatBlockIndices[b_ind]
                bigstart = numpy.maximum(offset, start)
                bigstop = numpy.minimum(offset + self._blockShape, stop)

                smallstart = bigstart-offset
                smallstop = bigstop - offset

                bigkey = roiToSlice(bigstart-start, bigstop-start)
                smallkey = roiToSlice(smallstart, smallstop)
                if not b_ind in self._labelers or not self._labelers[b_ind].Output.ready():
                    result[bigkey]=0
                else:
                    try:
                        labeler = self._labelers[b_ind]
                        denseArray = labeler._denseArray[smallkey]
                        result[bigkey]= denseArray
                    except:
                        print "Exception in OpBlockedSparseLabelArray.execute, probably due to simultaneous calls to setInSlot() and execute()"
                        print "labeler =", labeler
                        print "denseArray =", denseArray
                        print "result =", result
                        raise

        elif slot.name == "nonzeroValues":
            nzvalues = set()
            for l in self._labelers.values():
                nzvalues |= set(l._sparseNZ.values())
            result[0] = numpy.array(list(nzvalues))

        elif slot.name == "nonzeroCoordinates":
            print "not supported yet"
            #result[0] = numpy.array(self._sparseNZ.keys())
        elif slot.name == "nonzeroBlocks":
            #we only return all non-zero blocks, no keys
            slicelist = []
            for b_ind in self._labelers.keys():
                offset = self._blockShape*self._flatBlockIndices[b_ind]
                bigstart = offset
                bigstop = numpy.minimum(offset + self._blockShape, self._cacheShape)
                bigkey = roiToSlice(bigstart, bigstop)
                slicelist.append(bigkey)

            result[0] = slicelist
        elif slot.name == "maxLabel":
            result[0] = self._maxLabel

        self.lock.release()
        return result

    def setInSlot(self, slot, subindex, roi, value):
        key = roi.toSlice()
        with Tracer(self.traceLogger):
            time1 = time.time()
            start, stop = sliceToRoi(key, self._cacheShape)

            blockStart = (1.0 * start / self._blockShape).floor()
            blockStop = (1.0 * stop / self._blockShape).ceil()
            blockStop = numpy.where(stop == self._cacheShape, self._dirtyShape, blockStop)
            blockKey = roiToSlice(blockStart,blockStop)
            innerBlocks = self._blockNumbers[blockKey]
            for b_ind in innerBlocks.ravel():

                offset = self._blockShape*self._flatBlockIndices[b_ind]
                bigstart = numpy.maximum(offset, start)
                bigstop = numpy.minimum(offset + self._blockShape, stop)
                smallstart = bigstart-offset
                smallstop = bigstop - offset
                bigkey = roiToSlice(bigstart-start, bigstop-start)
                smallkey = roiToSlice(smallstart, smallstop)
                smallvalues = value[tuple(bigkey)]
                if (smallvalues != 0 ).any():
                    if not b_ind in self._labelers:
                        self._labelers[b_ind]=OpSparseLabelArray(self)
                        # Don't connect deletelabel; it is set manually (here and also above)
                        self._labelers[b_ind].inputs["deleteLabel"].setValue(self.inputs["deleteLabel"].value)
                        self._labelers[b_ind].inputs["shape"].setValue(self._blockShape)
                        self._labelers[b_ind].inputs["eraser"].setValue(self.inputs["eraser"].value)

                        # remember old max labele, i.e. 0 since we just created
                        self._oldMaxLabels[b_ind] = 0
                        # add the 0 to the histogram
                        self._maxLabelHistogram[0] += 1
                        
                        def max_label_changed(b_ind, slot, *args):
                            self.lock.acquire()

                            newmax = slot.value

                            # make sure histogram is large enough
                            if newmax > self._maxLabelHistogram.shape[0] -1:
                                self._maxLabelHistogram.resize((newmax+1,))

                            # update histogram
                            oldmax = self._oldMaxLabels[b_ind]
                            self._maxLabelHistogram[oldmax] -= 1
                            self._maxLabelHistogram[newmax] += 1
                            self._oldMaxLabels[b_ind] = newmax
                            
                            # check wether self._maxlabel needs to be updated (up and down)
                            maxdirty = False
                            if newmax > self._maxLabel:
                                assert self._maxLabelHistogram[newmax] == 1
                                self._maxLabel = newmax
                            elif self._maxLabelHistogram[oldmax] == 0:
                                self._maxLabel = numpy.max(numpy.nonzero(self._maxLabelHistogram)[0])

                            self.lock.release()
                            
                            self.maxLabel.setValue(self._maxLabel)


                            
                        self._labelers[b_ind].inputs["maxLabel"].notifyDirty(partial(max_label_changed, b_ind))
                        
                    self._labelers[b_ind].inputs["Input"][smallkey] = smallvalues
            
            time2 = time.time()
            logger.debug("OpBlockedSparseLabelArray: setInSlot writing took %fs" % (time2-time1,))
            # Set our max label output dirty

            self.Output.setDirty(key)

            time3 = time.time()
            logger.debug("OpBlockedSparseLabelArray: setInSlot setDirty took %fs" % (time3-time2,))
            logger.debug("OpBlockedSparseLabelArray: setInSlot total took %fs" % (time3-time1,))

    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        if slot == self.inputs["Input"]:
            self.Output.setDirty(key)