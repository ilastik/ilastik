from lazyflow.graph import InputSlot
from ilastik.applets.dataExport.opDataExport import OpDataExport
from ilastik.applets.base.applet import DatasetConstraintError

class OpPixelClassificationDataExport( OpDataExport ):
    # Add these additional input slots, to be used by the GUI.
    PmapColors = InputSlot()
    LabelNames = InputSlot()
    ConstraintDataset = InputSlot()
    
    def __init__(self,*args,**kwargs):
        super(OpPixelClassificationDataExport, self).__init__(*args, **kwargs)
        self.ConstraintDataset.notifyReady(self.checkDataConstraint)
        self.RawData.notifyReady(self.checkDataConstraint)
        
    def checkDataConstraint(self,evt):
        '''check if the data input data corresponds to the training input data'''
        if not self.ConstraintDataset.ready() or not self.RawData.ready():
            return
        
        dataTrain = self.ConstraintDataset.meta
        dataBatch = self.RawData.meta
        
        if len(dataTrain.shape) != len(dataBatch.shape):
            raise DatasetConstraintError("Batch Prediction Input","Batch input must have the same dimension as training input.")
        elif dataTrain.getTaggedShape()['c'] != dataBatch.getTaggedShape()['c']:
            raise DatasetConstraintError("Batch Prediction Input","Batch input must have the same number of channels as training input.")
        elif dataTrain.getAxisKeys() != dataBatch.getAxisKeys():
            raise DatasetConstraintError("Batch Prediction Input","Batch input axis must fit axis of training input.")
