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
import time
import logging
import sys

#SciPy
import numpy

#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.roi import sliceToRoi
from lazyflow.operators.opCache import MemInfoNode
from lazyflow.operators.opCache import ObservableCache

class OpSlicedBlockedArrayCache(Operator, ObservableCache):
    name = "OpSlicedBlockedArrayCache"
    description = ""

    #Inputs
    Input = InputSlot(allow_mask=True)
    innerBlockShape = InputSlot()
    outerBlockShape = InputSlot()
    fixAtCurrent = InputSlot(value = False)
   
    #Outputs
    Output = OutputSlot(allow_mask=True)
    InnerOutputs = OutputSlot(level=1, allow_mask=True)

    loggerName = __name__ + ".OpSlicedBlockedArrayCache"
    logger = logging.getLogger(loggerName)
    traceLogger = logging.getLogger("TRACE." + loggerName)

    def __init__(self, *args, **kwargs):
        super(OpSlicedBlockedArrayCache, self).__init__(*args, **kwargs)
        self._innerOps = []

        # Now that we're initialized, it's safe to register with the memory manager
        self.registerWithMemoryManager()

    def generateReport(self, report):
        report.name = self.name
        report.fractionOfUsedMemoryDirty = self.fractionOfUsedMemoryDirty()
        report.usedMemory = self.usedMemory()
        report.dtype = self.Output.meta.dtype
        report.type = type(self)
        report.id = id(self)
        sh = self.Output.meta.shape
        if sh is not None:
            report.roi = ([0]*len(sh), sh)

        for iOp in self._innerOps:
            n = MemInfoNode()
            report.children.append(n)
            iOp.generateReport(n)

    def usedMemory(self):
        tot = 0.0
        for iOp in self._innerOps:
            tot += iOp.usedMemory()
        return tot

    def fractionOfUsedMemoryDirty(self):
        tot = 0.0
        dirty = 0.0
        for iOp in self._innerOps:
            mem = iOp.usedMemory()
            tot += mem
            dirty += iOp.fractionOfUsedMemoryDirty()*mem
        if dirty > 0:
            return tot/float(dirty)
        else:
            return 0.0

    def setupOutputs(self):
        self.shape = self.inputs["Input"].meta.shape
        self._outerShapes = self.inputs["outerBlockShape"].value
        self._innerShapes = self.inputs["innerBlockShape"].value

        for blockshape in self._innerShapes + self._outerShapes:
            if len(blockshape) != len(self.Input.meta.shape):
                self.Output.meta.NOTREADY = True
                return

        # FIXME: This is wrong: Shouldn't it actually compare the new inner block shape with the old one?
        if len(self._innerShapes) != len(self._innerOps):
            # Clean up previous inner operators
            for slot in self.InnerOutputs:
                slot.disconnect()
            for o in self._innerOps:
                o.cleanUp()

            self._innerOps = []

            for i,innershape in enumerate(self._innerShapes):
                op = OpBlockedArrayCache(parent=self)
                op.inputs["fixAtCurrent"].connect(self.inputs["fixAtCurrent"])
                self._innerOps.append(op)
                
                op.inputs["Input"].connect(self.inputs["Input"])
                
                # Forward "value changed" notifications to our own output
                op.Output.notifyValueChanged( self.Output._sig_value_changed )

        for i,innershape in enumerate(self._innerShapes):
            op = self._innerOps[i]
            op.inputs["innerBlockShape"].setValue(innershape)
            op.inputs["outerBlockShape"].setValue(self._outerShapes[i])

        self.Output.meta.assignFrom(self.Input.meta)
        
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

        # We also provide direct access to each of our inner cache outputs.        
        self.InnerOutputs.resize( len(self._innerOps) )
        for i, slot in enumerate(self.InnerOutputs):
            slot.connect(self._innerOps[i].Output)
        
    def execute(self, slot, subindex, roi, result):
        t = time.time()
        assert slot == self.Output
        
        key = roi.toSlice()
        start,stop=sliceToRoi(key,self.shape)
        roishape=numpy.array(stop)-numpy.array(start)

        max_dist_squared=sys.maxint
        index=0

        for i,blockshape in enumerate(self._innerShapes):
            blockshape = numpy.array(blockshape)

            diff = roishape - blockshape
            diffsquared = diff * diff
            distance_squared = numpy.sum(diffsquared)
            if distance_squared < max_dist_squared:
                index = i
                max_dist_squared = distance_squared

        op = self._innerOps[index]
        op.outputs["Output"][key].writeInto(result).wait()
        self.logger.debug("read %r took %f msec." % (roi.pprint(), 1000.0*(time.time()-t)))

    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        # We *could* simply forward dirty notifications from our inner operators
        # to our output (by subscribing to their notifyDirty signals),
        # but that would result in duplicates of many (not all!) dirty notifications
        # (since we have more than one inner cache, and each is receiving dirty notifications)
        # Instead, we simply mark *everything* dirty when we beome unfixed or if the block shape changes.
        fixed = self.fixAtCurrent.value
        if not fixed:
            if slot == self.Input:
                self.Output.setDirty( key )        
            elif slot == self.outerBlockShape or slot == self.innerBlockShape:
                #self.Output.setDirty( slice(None) )
                pass # Blockshape changes don't trigger dirty notifications
                     # It is considered an error to change the blockshape after the initial configuration.
            elif slot == self.fixAtCurrent:
                self.Output.setDirty( slice(None) )
            else:
                assert False, "Unknown dirty input slot"
