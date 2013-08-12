from ilastik.applets.base.standardApplet import StandardApplet

from opFillMissingSlices import OpFillMissingSlices
from fillMissingSlicesSerializer import FillMissingSlicesSerializer

from lazyflow.operatorWrapper import OperatorWrapper

class FillMissingSlicesApplet( StandardApplet ):
    """
    TODO: write some documentation
    """
    def __init__( self, workflow, guiName, projectFileGroupName, detectionMethod):
        super(FillMissingSlicesApplet, self).__init__(guiName, workflow)
        self._operator = self.topLevelOperator
        self._operator.DetectionMethod.setValue(detectionMethod)
        self._serializableItems = [FillMissingSlicesSerializer("FillMissingSlices", self._operator)]
        
    
    @property
    def singleLaneOperatorClass(self):
        return OpFillMissingSlices

    @property
    def broadcastingSlots(self):
        return ["DetectionMethod", "OverloadDetector", "PatchSize", "HaloSize"]
    
    
    @property
    def singleLaneGuiClass(self):
        from fillMissingSlicesGui import FillMissingSlicesGui
        return FillMissingSlicesGui
    

    @property
    def dataSerializers(self):
        return self._serializableItems
