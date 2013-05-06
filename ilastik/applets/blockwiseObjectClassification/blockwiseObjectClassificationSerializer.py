from ilastik.applets.base.appletSerializer import AppletSerializer, SerialDictSlot

class BlockwiseObjectClassificationSerializer(AppletSerializer):
    def __init__(self, topGroupName, operator):
        serialSlots = [SerialDictSlot(operator.BlockShape3dDict, selfdepends=True),
                       SerialDictSlot(operator.HaloPadding3dDict, selfdepends=True)]

        super(BlockwiseObjectClassificationSerializer, self ).__init__(topGroupName,
                                                              slots=serialSlots,
                                                              operator=operator)
