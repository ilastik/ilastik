from ilastik.applets.base.standardApplet import StandardApplet
from opPatchCreator import OpPatchCreator
from patchCreatorSerializer import PatchCreatorSerializer
from lazyflow.graph import OperatorWrapper

class PatchCreatorApplet( StandardApplet ):
    def __init__( self, workflow, projectFileGroupName ):
        super(PatchCreatorApplet, self).__init__("Patch Creator", workflow)
        self._serializableItems = [PatchCreatorSerializer(self.topLevelOperator,
                                                          projectFileGroupName)]

    @property
    def singleLaneOperatorClass(self):
        return OpPatchCreator

    @property
    def broadcastingSlots(self):
        return ["PatchWidth", "PatchHeight",
                "PatchOverlapVertical", "PatchOverlapHorizontal",
                "GridStartVertical", "GridStartHorizontal",
                "GridWidth", "GridHeight"]

    @property
    def singleLaneGuiClass(self):
        from patchCreatorGui import PatchCreatorGui
        return PatchCreatorGui

    @property
    def dataSerializers(self):
        return self._serializableItems
