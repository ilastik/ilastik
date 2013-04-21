#Python
import logging
import sys

#SciPy
import numpy

#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility import Tracer
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.roi import sliceToRoi
from lazyflow.operators.arrayCacheMemoryMgr import ArrayCacheMemoryMgr, MemInfoNode
from lazyflow.operators.opCache import OpCache

class OpSlicedBlockedArrayCache(OpCache):
    name = "OpSlicedBlockedArrayCache"
    description = ""

    #Inputs
    Input = InputSlot()
    innerBlockShape = InputSlot()
    outerBlockShape = InputSlot()
    fixAtCurrent = InputSlot(value = False)
   
    #Outputs
    Output = OutputSlot()
    InnerOutputs = OutputSlot(level=1)

    loggerName = __name__ + ".OpSlicedBlockedArrayCache"
    logger = logging.getLogger(loggerName)
    traceLogger = logging.getLogger("TRACE." + loggerName)

    def __init__(self, *args, **kwargs):
        with Tracer(self.traceLogger):
            super(OpSlicedBlockedArrayCache, self).__init__(*args, **kwargs)
            self._innerOps = []
            self._somethingIsDirty = False

    def generateReport(self, report):
        report.name = self.name
        report.fractionOfUsedMemoryDirty = self.fractionOfUsedMemoryDirty()
        report.usedMemory = self.usedMemory()
        report.lastAccessTime = self.lastAccessTime()
        report.dtype = self.Output.meta.dtype
        report.type = type(self)
        report.id = id(self)
        sh = self.Output.meta.shape
        report.roi = ([0]*len(sh), sh)
        
        for i, iOp in enumerate(self._innerOps):
            n = MemInfoNode()
            report.children.append(n)
            iOp.generateReport(n)
            
    def usedMemory(self):
        tot = 0.0
        for iOp in self._innerOps:
            tot += iOp.usedMemory()
        return tot
    
    def setupOutputs(self):
        self.shape = self.inputs["Input"].meta.shape
        self._outerShapes = self.inputs["outerBlockShape"].value
        self._innerShapes = self.inputs["innerBlockShape"].value

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

        # We also provide direct access to each of our inner cache outputs.        
        self.InnerOutputs.resize( len(self._innerOps) )
        for i, slot in enumerate(self.InnerOutputs):
            slot.connect(self._innerOps[i].Output)
        
    def execute(self, slot, subindex, roi, result):
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
                self.Output.setDirty( slice(None) )
            elif slot == self.fixAtCurrent:
                # Special case: If *nothing* has become dirty since we became 'fixed',
                #  then there's no reason to send out a big dirty notification.
                if self._somethingIsDirty:
                    self.Output.setDirty( slice(None) )
                    self._somethingIsDirty = False
            else:
                assert False, "Unknown dirty input slot"
        elif slot != self.fixAtCurrent:
            self._somethingIsDirty = True
