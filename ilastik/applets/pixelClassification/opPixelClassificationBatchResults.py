from lazyflow.graph import InputSlot
from ilastik.applets.batchIo.opBatchIo import OpBatchIo


class OpPixelClassificationBatchResults( OpBatchIo ):
    # Add these additional input slots, to be used by the GUI.
    PmapColors = InputSlot()
    LabelNames = InputSlot()
    ConstraintDataset = InputSlot()
    
    def __init__(self,*args,**kwargs):
        super(OpPixelClassificationBatchResults, self).__init__(*args, **kwargs)
        self.ConstraintDataset.notifyReady(self.checkDataConstraint)
        self.RawImage.notifyReady(self.checkDataConstraint)
        
    def checkDataConstraint(self,evt):
        '''check if the batch input data corresponds to the training input data'''
        if not self.ConstraintDataset.ready() or not self.RawImage.ready():
            return
        
        cdm = self.ConstraintDataset.meta
        rim = self.RawImage.meta
        assert len(cdm.shape) == len(rim.shape),\
            "Batch input must have the same dimension as training input."
        assert cdm.shape[cdm.axistags.index("c")] == rim.shape[rim.axistags.index("c")],\
            "Batch input must have the same number of channels as training input."
    
