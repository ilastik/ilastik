from ilastik.applets.base.standardApplet import StandardApplet

from opVigraWatershedViewer import OpVigraWatershedViewer
from vigraWatershedViewerSerializer import VigraWatershedViewerSerializer

class VigraWatershedViewerApplet( StandardApplet ):
    """
    Viewer for watershed results, with minimal configuration controls.
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(VigraWatershedViewerApplet, self).__init__(guiName, workflow)
        self._serializableItems = [ VigraWatershedViewerSerializer(self.topLevelOperator, projectFileGroupName) ]
        
    @property
    def singleLaneOperatorClass(self):
        return OpVigraWatershedViewer

    @property
    def broadcastingSlots(self):
        return ['InputChannelIndexes', 'WatershedPadding', 'FreezeCache', 'CacheBlockShape', 'SeedThresholdValue', 'MinSeedSize' ]
    
    @property
    def singleLaneGuiClass(self):
        from vigraWatershedViewerGui import VigraWatershedViewerGui
        return VigraWatershedViewerGui

    @property
    def dataSerializers(self):
        return self._serializableItems
