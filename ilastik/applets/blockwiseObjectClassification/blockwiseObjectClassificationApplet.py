from ilastik.applets.base.standardApplet import StandardApplet

from opBlockwiseObjectClassification import OpBlockwiseObjectClassification
from blockwiseObjectClassificationSerializer import BlockwiseObjectClassificationSerializer

class BlockwiseObjectClassificationApplet(StandardApplet):
    def __init__(self,
                 workflow=None,
                 name="Blockwise Object Classification",
                 projectFileGroupName="BlockwiseObjectClassification"):
        super(BlockwiseObjectClassificationApplet, self).__init__(name=name, workflow=workflow)

        self._serializableItems = \
        [ BlockwiseObjectClassificationSerializer(projectFileGroupName, self.topLevelOperator) ]

    @property
    def singleLaneOperatorClass(self):
        return OpBlockwiseObjectClassification

    @property
    def broadcastingSlots(self):
        return ['BlockShape', 'HaloPadding', 'Classifier']
    
    @property
    def singleLaneGuiClass(self):
        from blockwiseObjectClassificationGui import BlockwiseObjectClassificationGui
        return BlockwiseObjectClassificationGui

    @property
    def dataSerializers(self):
        return self._serializableItems
