from ilastik.applets.base.appletSerializer import (
    AppletSerializer,
    SerialBlockSlot,
    SerialListSlot,
    SerialSlot,
    jsonSerializerRegistry,
)

from ..neuralNetwork.nnClassSerializer import BioimageIOModelSlot


class PixelClassificationEnhancerSerializer(AppletSerializer):
    def __init__(self, topLevelOperator, projectFileGroupName):
        self.VERSION = 1

        slots = [
            BioimageIOModelSlot(topLevelOperator.BIOModel),
            SerialListSlot(topLevelOperator.SelectedChannels),
        ]

        super().__init__(projectFileGroupName, slots)
