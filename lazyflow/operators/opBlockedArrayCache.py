#Python
import generic
import logging
logger = logging.getLogger(__name__)
from threading import Lock

#SciPy
import numpy

#lazyflow
from lazyflow.roi import roiToSlice
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
from lazyflow.utility import Tracer
from lazyflow.operators.opArrayCache import OpArrayCache

class OpBlockedArrayCache(Operator):
    name = "OpBlockedArrayCache"
    description = ""

    inputSlots = [InputSlot("Input"),InputSlot("innerBlockShape"), InputSlot("outerBlockShape"), InputSlot("fixAtCurrent"), InputSlot("forward_dirty", value = True)]
    outputSlots = [OutputSlot("Output")]

    loggerName = __name__ + ".OpBlockedArrayCache"
    logger = logging.getLogger(loggerName)
    traceLogger = logging.getLogger("TRACE." + loggerName)

    def __init__(self, *args, **kwargs):
        with Tracer(self.traceLogger):
            super(OpBlockedArrayCache, self).__init__( *args, **kwargs )
            self._configured = False
            self._fixed = False
            self._fixed_dirty_blocks = set()
            self._lock = Lock()
            self._innerBlockShape = None
            self._outerBlockShape = None
            self._blockShape = None
            self._fixed_all_dirty = False  # this is a shortcut for storing wehter all subblocks are dirty
            self._forward_dirty = False
            self._opDummy = None
            self._opSub_list = {}
            self._cache_list = {}

    def setupOutputs(self):
        with Tracer(self.traceLogger):
            self._fixed = self.inputs["fixAtCurrent"].value
            self._forward_dirty = self.forward_dirty.value

            inputSlot = self.inputs["Input"]
            shape = inputSlot.meta.shape
            if (    shape != self.Output.meta.shape
                 or self._outerBlockShape != self.outerBlockShape.value
                 or self._innerBlockShape != self.innerBlockShape.value ):
                self._configured = False
                
            if min(shape) == 0:
                # FIXME: This is evil, but there's no convenient way around it.
                # We don't want our output to be flagged as 'ready'
                # The only way to do that is to temporarily connect it to an unready operator
#                opTmp = OpArrayPiper(parent=self, graph=self.graph)
#                opTmp.Output.connect( self.Output )
                self._configured = False
                return
            else:
                if self.Output.partner is not None:
                    self.Output.disconnect()
    
            if not self._configured:
                self.Output.meta.assignFrom(inputSlot.meta)
                with self._lock:
                    self._innerBlockShape = self.innerBlockShape.value
                    self._outerBlockShape = self.outerBlockShape.value
                    if len(self._fixed_dirty_blocks) > 0:
                        self._fixed_dirty_blocks = set()
                        notifyOutputDirty = True # Notify dirty output after we're fully configured
                    else:
                        notifyOutputDirty = False
    
                    self.shape = self.Input.meta.shape
                    self._blockShape = self.inputs["outerBlockShape"].value
                    self._blockShape = tuple(numpy.minimum(self._blockShape, self.shape))
                    assert numpy.array(self._blockShape).min() > 0, "ERROR in OpBlockedArrayCache: invalid blockShape = {blockShape}".format(blockShape=self._blockShape)
                    self._dirtyShape = numpy.ceil(1.0 * numpy.array(self.shape) / numpy.array(self._blockShape))
                    assert numpy.array(self._dirtyShape).min() > 0, "ERROR in OpBlockedArrayCache: invalid dirtyShape = {dirtyShape}".format(dirtyShape=self._dirtyShape)

                    self._blockState = numpy.ones(self._dirtyShape, numpy.uint8)

                _blockNumbers = numpy.dstack(numpy.nonzero(self._blockState.ravel()))
                _blockNumbers.shape = self._dirtyShape

                _blockIndices = numpy.dstack(numpy.nonzero(self._blockState))
                _blockIndices.shape = self._blockState.shape + (_blockIndices.shape[-1],)

                self._blockNumbers = _blockNumbers

                # allocate queryArray object
                self._flatBlockIndices =  _blockIndices[:]
                self._flatBlockIndices = self._flatBlockIndices.reshape(self._flatBlockIndices.size/self._flatBlockIndices.shape[-1],self._flatBlockIndices.shape[-1],)

                for op in self._cache_list.values():
                    op.cleanUp()
                for op in self._opSub_list.values():
                    op.cleanUp()

                self._opSub_list = {}
                self._cache_list = {}

                self._configured = True

                if notifyOutputDirty:
                    self.Output.setDirty(slice(None))

    def execute(self, slot, subindex, roi, result):
        if not self._configured:
            # this happends when the operator is not yet fully configured due to fixAtCurrent == True
            result[:] = 0
            return

        #find the block key
        key = roi.toSlice()
        start, stop = roi.start, roi.stop

        blockStart = (start / self._blockShape)
        blockStop = (stop * 1.0 / self._blockShape).ceil()
        #blockStop = numpy.where(stop == self.shape, self._dirtyShape, blockStop)
        blockKey = roiToSlice(blockStart,blockStop)
        innerBlocks = self._blockNumbers[blockKey]

        requests = []
        for b_ind in innerBlocks.flat:
            #which part of the original key does this block fill?
            offset = self._blockShape*self._flatBlockIndices[b_ind]
            bigstart = numpy.maximum(offset, start)
            bigstop = numpy.minimum(offset + self._blockShape, stop)


            smallstart = bigstart-offset
            smallstop = bigstop - offset

            diff = smallstop - smallstart
            smallkey = roiToSlice(smallstart, smallstop)

            bigkey = roiToSlice(bigstart-start, bigstop-start)

            with self._lock:    
                if not self._fixed:
                    if not self._cache_list.has_key(b_ind):

                        self._opSub_list[b_ind] = generic.OpSubRegion(parent=self)
                        self._opSub_list[b_ind].inputs["Input"].connect(self.inputs["Input"])
                        tstart = self._blockShape*self._flatBlockIndices[b_ind]
                        tstop = numpy.minimum((self._flatBlockIndices[b_ind]+numpy.ones(self._flatBlockIndices[b_ind].shape, numpy.uint8))*self._blockShape, self.shape)
    
                        self._opSub_list[b_ind].inputs["Start"].setValue(tuple(tstart))
                        self._opSub_list[b_ind].inputs["Stop"].setValue(tuple(tstop))
    
                        self._cache_list[b_ind] = OpArrayCache(parent=self)
                        self._cache_list[b_ind].inputs["Input"].connect(self._opSub_list[b_ind].outputs["Output"])
                        self._cache_list[b_ind].inputs["fixAtCurrent"].connect( self.fixAtCurrent )
                        self._cache_list[b_ind].inputs["blockShape"].setValue(self.inputs["innerBlockShape"].value)
                        # we dont register a callback for dirtyness, since we already forward the signal
                        
                        # Forward value changed notifications to our own output.
                        self._cache_list[b_ind].Output.notifyValueChanged( self.Output._sig_value_changed )

            if self._cache_list.has_key(b_ind):
                op = self._cache_list[b_ind]
                #req = self._cache_list[b_ind].outputs["Output"][smallkey].writeInto(result[bigkey])

                smallroi = SubRegion(op.outputs["Output"], start = smallstart , stop= smallstop)
                req = op.Output(smallroi.start, smallroi.stop)
                req.writeInto(result[bigkey])
                req.wait()
                #op.execute(op.outputs["Output"], (), smallroi, result[bigkey])

                ####op.getOutSlot(op.outputs["Output"],smallkey,result[bigkey])
                #requests.append(req)
            else:
                #When this block has never been in the cache and the current
                #value is fixed (fixAtCurrent=True), return 0  values
                #This prevents random noise appearing in such cases.
                result[bigkey] = 0
                with self._lock:
                    # Since a downstream operator has expressed an interest in this block,
                    #  mark it to be signaled as dirty when we become unfixed.
                    # Otherwise, downstream operators won't know when there's valid data in this block.
                    self._fixed_dirty_blocks.add(b_ind)

        for r in requests:
            r.wait()


    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        if slot == self.inputs["Input"] and self._forward_dirty:
            if not self._fixed:
                self.outputs["Output"].setDirty(key)                    
            elif self._blockShape is not None:
                # Find the block key
                roi = SubRegion(slot, pslice=key)
                start, stop = roi.start, roi.stop
        
                blockStart = (start / self._blockShape)
                blockStop = (stop * 1.0 / self._blockShape).ceil()
                
                with self._lock:
                    # check wether the dirty region encompasses the whole cache
                    if (blockStart == 0).all() and (blockStop == self._blockNumbers.shape).all():
                        self._fixed_all_dirty = True

                    # shortcut, if everything is dirty already, dont loop over the blocks
                    if self._fixed_all_dirty is False:
                        blockKey = roiToSlice(blockStart,blockStop)
                        innerBlocks = self._blockNumbers[blockKey]
                        for b_ind in innerBlocks.flat:
                            self._fixed_dirty_blocks.add(b_ind)            

        if slot == self.fixAtCurrent:
            self._fixed = self.fixAtCurrent.value
            if not self._fixed:
                # We've become unfixed.
                # Take the superset of all the blocks that became dirty in the meantime and notify our output
                dirtystart, dirtystop = (None,None)
                with self._lock:
                    if self._fixed_all_dirty is True:
                        dirtystop = self.Output.meta.shape
                        dirtystart = [0] * len(self.Output.meta.shape)
                    elif len(self._fixed_dirty_blocks) > 0:
                        dirtystart = self.Output.meta.shape
                        dirtystop = [0] * len(self.Output.meta.shape)
                        for b_ind in self._fixed_dirty_blocks:
                            offset = self._blockShape*self._flatBlockIndices[b_ind]
                            bigstart = offset
                            bigstop = numpy.minimum(offset + self._blockShape, self.Output.meta.shape)
                            
                            dirtystart = numpy.minimum(bigstart, dirtystart)
                            dirtystop = numpy.maximum(bigstop, dirtystop)
                        
                        self._fixed_dirty_blocks = set()
                    # reset all dirty state to false
                    self._fixed_all_dirty = False 

                if dirtystart is not None:
                    self.Output.setDirty(dirtystart, dirtystop)
