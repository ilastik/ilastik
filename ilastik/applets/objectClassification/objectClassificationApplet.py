from ilastik.applets.base.standardApplet import StandardApplet

from opObjectClassification import OpObjectClassification
from objectClassificationSerializer import ObjectClassificationSerializer

from guiMessage import OpGuiDialog, GuiDialog

class ObjectClassificationApplet(StandardApplet):
    def __init__(self,
                 name="Object Classification",
                 workflow=None,
                 projectFileGroupName="ObjectClassification"):
        self._topLevelOperator = OpObjectClassification(parent=workflow)
        super(ObjectClassificationApplet, self).__init__(name=name, workflow=workflow)

        self._serializableItems = [
            ObjectClassificationSerializer(projectFileGroupName,
                                           self.topLevelOperator)]


    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    def createSingleLaneGui(self, imageLaneIndex):
        from objectClassificationGui import ObjectClassificationGui
        singleImageOperator = self.topLevelOperator.getLane(imageLaneIndex)
        gui = ObjectClassificationGui(singleImageOperator,
                                       self.shellRequestSignal,
                                       self.guiControlSignal)
        
        # setup message chain
        self._trainDialog = OpGuiDialog(parent=self._topLevelOperator.parent) #FIXME parent hack
        self._trainDialog.dialog = GuiDialog(gui)
        self._trainDialog.inputslot.connect(self._topLevelOperator.opTrain.Warnings)
        
        '''
        unsure about OperatorWrapper and stuff like this
        self._predictDialog = OpGuiDialog(parent=self._topLevelOperator.parent) #FIXME parent hack
        self._predictDialog.dialog = GuiDialog(gui)
        self._predictDialog.inputslot.level = 1
        self._predictDialog.inputslot.connect(self._topLevelOperator.opPredict.Warnings)
        '''
        return gui
