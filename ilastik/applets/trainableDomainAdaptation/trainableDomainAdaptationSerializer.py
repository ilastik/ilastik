from ilastik.applets.base.appletSerializer import AppletSerializer, SerialListSlot

from ..neuralNetwork.nnClassSerializer import BioimageIOModelSlot


class TrainableDomainAdaptationSerializer(AppletSerializer):
    def __init__(self, topLevelOperator, projectFileGroupName):
        self.VERSION = 1

        slots = [
            BioimageIOModelSlot(topLevelOperator.BIOModel),
            SerialListSlot(topLevelOperator.SelectedChannels),
        ]

        super().__init__(projectFileGroupName, slots)
