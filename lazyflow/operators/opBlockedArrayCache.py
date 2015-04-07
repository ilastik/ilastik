###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
#Python
import sys
import time
import generic
import logging
logger = logging.getLogger(__name__)
from threading import Lock

#SciPy
import numpy

#lazyflow
from lazyflow.roi import roiToSlice
from lazyflow.utility import RamMeasurementContext
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
from lazyflow.request import RequestPool
from lazyflow.operators.opCache import ObservableCache
from lazyflow.operators.opArrayCache import OpArrayCache
from lazyflow.operators.opCache import MemInfoNode


class OpBlockedArrayCache(Operator, ObservableCache):
    name = "OpBlockedArrayCache"
    description = ""

    #Input
    Input = InputSlot(allow_mask=True)
    innerBlockShape = InputSlot()
    outerBlockShape = InputSlot()
    fixAtCurrent = InputSlot()
    forward_dirty = InputSlot(value = True)
   
    #Output
    Output = OutputSlot("Output", allow_mask=True)

    loggerName = __name__ + ".OpBlockedArrayCache"
    logger = logging.getLogger(loggerName)
    traceLogger = logging.getLogger("TRACE." + loggerName)

    def __init__(self, *args, **kwargs):
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

        # This member is used by tests that check RAM usage.
        self.setup_ram_context = RamMeasurementContext()
        
        # Now that we're initialized, it's safe to register with the memory manager
        self.registerWithMemoryManager()

    def setupOutputs(self):
        if len(self.innerBlockShape.value) != len(self.Input.meta.shape) or\
           len(self.outerBlockShape.value) != len(self.Input.meta.shape):
            self.Output.meta.NOTREADY = True
            return

        with self.setup_ram_context:
            self._fixed = self.inputs["fixAtCurrent"].value
            self._forward_dirty = self.forward_dirty.value
    
            inputSlot = self.inputs["Input"]
            shape = inputSlot.meta.shape
            if (    shape != self.Output.meta.shape
                 or self._outerBlockShape != self.outerBlockShape.value
                 or self._innerBlockShape != self.innerBlockShape.value ):
                self._configured = False
                
            if min(shape) == 0:
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
                    self._dirtyShape = numpy.ceil(1.0 * numpy.array(self.shape) /
                                                  numpy.array(self._blockShape)).astype(numpy.int)
                    assert numpy.array(self._dirtyShape).min() > 0, "ERROR in OpBlockedArrayCache: invalid dirtyShape = {dirtyShape}".format(dirtyShape=self._dirtyShape)
    
                    # Estimate ram usage            
                    ram_per_pixel = 0
                    if self.Output.meta.dtype == object or self.Output.meta.dtype == numpy.object_:
                        ram_per_pixel = sys.getsizeof(None)
                    elif numpy.issubdtype(self.Output.meta.dtype, numpy.dtype):
                        ram_per_pixel = self.Output.meta.dtype().nbytes
    
                    tagged_shape = self.Output.meta.getTaggedShape()
                    if 'c' in tagged_shape:
                        ram_per_pixel *= float(tagged_shape['c'])
        
                    if self.Output.meta.ram_usage_per_requested_pixel is not None:
                        ram_per_pixel = max( ram_per_pixel, self.Output.meta.ram_usage_per_requested_pixel )
        
                    self.Output.meta.ram_usage_per_requested_pixel = ram_per_pixel
        
                for op in self._cache_list.values():
                    op.cleanUp()
                for op in self._opSub_list.values():
                    op.cleanUp()
    
                self._opSub_list = {}
                self._cache_list = {}
    
                self._configured = True
    
                if notifyOutputDirty:
                    self.Output.setDirty(slice(None))

    def _get_block_multi_index(self, block_flat_index):
        """
        Convert a given block number (i.e. a raveled block index) into a multi_index.
        """
        multi_index = numpy.unravel_index( (block_flat_index,), self._dirtyShape )
        multi_index = numpy.array(multi_index)[:,0]
        return multi_index

    def _get_block_numbers(self, start_block_multi_index, stop_block_multi_index):
        """
        For the given start/stop roi of blocks (i.e. in block coordinate space, not image space),
        Return an array (shape = stop - start) of the raveled block numbers.

        As a better explanation, consider the following equivalent function.  
        (This version can't be used because all_block_numbers uses lots of RAM if self._dirtyShape is large.)
        
        def _get_block_numbers(start, stop):
            num_blocks = numpy.prod(self._dirtyShape)
            all_block_numbers = numpy.arange( num_blocks )
            all_block_numbers = numpy.reshape(all_block_numbers, self._dirtyShape)
            block_numbers = all_block_numbers[roiToSlice(start, stop)]
            return block_numbers
            
        Below, we achieve the same result without allocating a huge array of all possible block numbers.
        """        
        shape = numpy.array(stop_block_multi_index, dtype=numpy.int) -\
            numpy.array(start_block_multi_index, dtype=numpy.int)
        block_indices = numpy.indices( shape )
        
        # Create an array of multi_indexes
        block_indices = numpy.rollaxis( block_indices, 0, block_indices.ndim )
        block_indices += start_block_multi_index

        # Reshape into a 2D array so we can pass to numpy.ravel_multi_index
        num_indexes = numpy.prod(block_indices.shape[:-1])
        axiscount = block_indices.shape[-1]
        block_indices = numpy.reshape( block_indices, (num_indexes, axiscount) )
        
        # Convert multi_indexes to block numbers via ravel_multi_index
        raveled_indices = numpy.ravel_multi_index(block_indices.transpose(), self._dirtyShape)
        
        # Reshape to fit original roi start/stop
        raveled_indices_block = numpy.reshape(raveled_indices, shape)
        return raveled_indices_block

    def generateReport(self, report):
        report.name = self.name
        report.fractionOfUsedMemoryDirty = self.fractionOfUsedMemoryDirty()
        report.usedMemory = self.usedMemory()
        report.type = type(self)
        report.id = id(self)

        for block_index in self._cache_list.keys():
            start = self._blockShape*self._get_block_multi_index(block_index)
            stop = map(lambda z: z[0]+z[1], zip(start, self._blockShape))
            stop = numpy.minimum(stop, self.Output.meta.shape)
            
            n = MemInfoNode()
            n.roi = (start, stop)
            report.children.append(n)
            try:
                block = self._cache_list[block_index]
            except KeyError:
                # probably cleaned up 
                pass
            else:
                block.generateReport(n)
            
    def usedMemory(self):
        tot = 0.0
        for block in self._cache_list.values():
            tot += block.usedMemory()
        return tot

    def fractionOfUsedMemoryDirty(self):
        tot = 0.0
        dirty = 0.0
        for block in self._cache_list.values():
            mem = block.usedMemory()
            tot += mem
            dirty += block.fractionOfUsedMemoryDirty()*mem
        if dirty > 0:
            return tot/float(dirty)
        else:
            return 0.0
        

    def execute(self, slot, subindex, roi, result):
        assert (roi.start >= 0).all(), \
            "Requested roi is out-of-bounds: [{}, {}]".format( roi.start, roi.stop )
        assert (roi.stop <= self.Input.meta.shape).all(), \
            "Requested roi is out-of-bounds: [{}, {}] (exceeds shape {})"\
            .format( roi.start, roi.stop, self.Input.meta.shape )
            
        if not self._configured:
            # this happens when the operator is not yet fully configured due to fixAtCurrent == True
            result[:] = 0
            return
        
        t = time.time()

        start, stop = roi.start, roi.stop

        blockStart = (start / self._blockShape)
        blockStop = (stop * 1.0 / self._blockShape).ceil()
        innerBlocks = self._get_block_numbers(blockStart, blockStop)

        pool = RequestPool()
        for block_index in innerBlocks.flat:
            #which part of the original key does this block fill?
            block_multi_index = self._get_block_multi_index(block_index)
            offset = self._blockShape*block_multi_index
            bigstart = numpy.maximum(offset, start)
            bigstop = numpy.minimum(offset + self._blockShape, stop)


            smallstart = bigstart-offset
            smallstop = bigstop - offset

            bigkey = roiToSlice(bigstart-start, bigstop-start)

            with self._lock:    
                if not self._fixed:
                    if not self._cache_list.has_key(block_index):

                        self._opSub_list[block_index] = generic.OpSubRegion(parent=self)
                        self._opSub_list[block_index].inputs["Input"].connect(self.inputs["Input"])
                        tstart = self._blockShape*block_multi_index
                        tstop = numpy.minimum((block_multi_index+numpy.ones(block_multi_index.shape, numpy.uint8))*self._blockShape, self.shape)
    
                        self._opSub_list[block_index].Roi.setValue( (tuple(tstart), tuple(tstop)) )
    
                        self._cache_list[block_index] = OpArrayCache(parent=self)
                        self._cache_list[block_index].inputs["Input"].connect(self._opSub_list[block_index].outputs["Output"])
                        self._cache_list[block_index].inputs["fixAtCurrent"].connect( self.fixAtCurrent )
                        self._cache_list[block_index].inputs["blockShape"].setValue(self.inputs["innerBlockShape"].value)
                        # we dont register a callback for dirtyness, since we already forward the signal
                        
                        # Forward value changed notifications to our own output.
                        self._cache_list[block_index].Output.notifyValueChanged( self.Output._sig_value_changed )

            if self._cache_list.has_key(block_index):
                op = self._cache_list[block_index]
                #req = self._cache_list[block_index].outputs["Output"][smallkey].writeInto(result[bigkey])

                smallroi = SubRegion(op.outputs["Output"], start = smallstart , stop= smallstop)
                req = op.Output(smallroi.start, smallroi.stop)
                req.writeInto(result[bigkey])
                pool.add( req )
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
                    self._fixed_dirty_blocks.add(block_index)

        pool.wait()
            
        self.logger.debug("read %r took %f msec." % (roi.pprint(), 1000.0*(time.time()-t)))


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
                    # check whether the dirty region encompasses the whole cache
                    if (blockStart == 0).all() and (blockStop == self._dirtyShape).all():
                        self._fixed_all_dirty = True

                    # shortcut, if everything is dirty already, dont loop over the blocks
                    if self._fixed_all_dirty is False:
                        innerBlocks = self._get_block_numbers(blockStart, blockStop)
                        for block_index in innerBlocks.flat:
                            self._fixed_dirty_blocks.add(block_index)            

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
                        for block_index in self._fixed_dirty_blocks:
                            offset = self._blockShape*self._get_block_multi_index(block_index)
                            bigstart = offset
                            bigstop = numpy.minimum(offset + self._blockShape, self.Output.meta.shape)
                            
                            dirtystart = numpy.minimum(bigstart, dirtystart)
                            dirtystop = numpy.maximum(bigstop, dirtystop)
                        
                        self._fixed_dirty_blocks = set()
                    # reset all dirty state to false
                    self._fixed_all_dirty = False 

                if dirtystart is not None:
                    self.Output.setDirty(dirtystart, dirtystop)
