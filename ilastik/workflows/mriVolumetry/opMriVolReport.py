from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque

import numpy as np
import vigra


class OpMriVolReport(Operator):
    name = "MRI Report"

    RawInput = InputSlot(optional=True)
    # Filtered Argmax Input
    Input = InputSlot()
    LabelNames = InputSlot(stype=Opaque)
    ActiveChannels = InputSlot(stype=Opaque)
    
    # Pseudo slot for dirty signal propagation to gui
    ReportStatus = OutputSlot(stype=Opaque)

    # Volume = OutputSlot(stype=Opaque)

    def __init__(self, *args, **kwargs):
        super(OpMriVolReport, self).__init__(*args, **kwargs)
        # print 'init'
        # self.ReportStatus.setDirty(slice(None))
        self.LabelNames.notifyReady( self._debugPrint )

    def execute(self, slot, subindex, roi, destination):
        print 'execute'
        pass

    def propagateDirty(self, inputSlot, subindex, roi):
        # print 'propogate dirty'
        # print inputSlot , 'propDirty report'
        if inputSlot in [self.Input, self.RawInput, self.LabelNames, 
                         self.ActiveChannels]:
            self.ReportStatus.setDirty([0])

    def setupOutputs(self):
        # print 'setup outputs'
        self.ReportStatus.meta.assignFrom(self.Input.meta)
        # self.Volume.meta.assignFrom(self.ActiveChannels.meta)

    def _debugPrint(self, *args, **kwargs):
        print 'debug'
        print self.LabelNames.value

    def computeVolume(self, *args, **kwargs):
        print self.Input.meta.getTaggedShape()
        data = self.Input[...].wait().squeeze()
        print data.shape

        labels = self.LabelNames.value
        active_channels = np.nonzero(self.ActiveChannels.value)[0]
        print 'AC' , active_channels
        counts = np.bincount(data.ravel())
        print counts
        for i in range(counts.size):
            if i in active_channels:
                print labels[i], counts[i+1] 
            
        

    
