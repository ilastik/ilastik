from ilastik.applets.base.appletSerializer import \
  AppletSerializer, SerialSlot, SerialDictSlot


class Groups(object):
    Labels = "Labels"


class ObjectClassificationSerializer(AppletSerializer):
    def __init__(self, topGroupName, operator):
        serialSlots = [SerialDictSlot(operator.LabelInputs, transform=int)]
        super(ObjectClassificationSerializer, self ).__init__(topGroupName,
                                                              slots=serialSlots,
                                                              operator=operator)
