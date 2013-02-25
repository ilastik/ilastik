from ilastik.applets.base.appletSerializer import AppletSerializer

class BlockwiseObjectClassificationSerializer(AppletSerializer):
    def __init__(self, topGroupName, operator):
        serialSlots = []

        super(BlockwiseObjectClassificationSerializer, self ).__init__(topGroupName,
                                                              slots=serialSlots,
                                                              operator=operator)
