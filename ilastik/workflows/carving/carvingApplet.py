from ilastik.applets.labeling.labelingApplet import LabelingApplet
from ilastik.applets.labeling.labelingGui import LabelingGui

from ilastik.utility import OpMultiLaneWrapper
from opCarvingTopLevel import OpCarving
from carvingSerializer import CarvingSerializer
from carvingGui import CarvingGui

class CarvingApplet(LabelingApplet):
    
    workflowName = "Carving"
    workflowDescription = "this is obviously self-explanatory"
    
    def __init__(self, workflow, projectFileGroupName,  hintOverlayFile=None, pmapOverlayFile=None):
        if hintOverlayFile is not None:
            assert isinstance(hintOverlayFile, str)

        if not hasattr(self, '_topLevelOperator'):
            op_kwargs = { 'hintOverlayFile' : hintOverlayFile,
                          'pmapOverlayFile' : pmapOverlayFile }
            self._topLevelOperator = OpMultiLaneWrapper( OpCarving,
                                                         parent=workflow,
                                                         operator_kwargs=op_kwargs )

        super(CarvingApplet, self).__init__(workflow, projectFileGroupName)

    @property
    def dataSerializers(self):
        return [ CarvingSerializer(self.topLevelOperator, "carving") ]
    
    @property
    def topLevelOperator(self):
        """
        Override from base class.
        """
        return self._topLevelOperator
    
    @property
    def singleLaneGuiClass(self):
        return CarvingGui
