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
        
        dataTrain = self.ConstraintDataset.meta
        dataBatch = self.RawImage.meta
        
        assert len(dataTrain.shape) == len(dataBatch.shape),\
            "Batch input must have the same dimension as training input."
        assert dataTrain.shape[dataTrain.axistags.index("c")] == dataBatch.shape[dataBatch.axistags.index("c")],\
            "Batch input must have the same number of channels as training input."
        assert dataTrain.getAxisKeys() == dataBatch.getAxisKeys(),\
            "Batch input axis must fit axis of training input."
