from ilastik.applets.base.appletSerializer import \
  AppletSerializer, SerialSlot, SerialDictSlot, \
  SerialClassifierSlot


class Groups(object):
    Labels = "Labels"


class ObjectClassificationSerializer(AppletSerializer):
    def __init__(self, topGroupName, operator):
        serialSlots = [SerialDictSlot(operator.LabelInputs, transform=int),
                       SerialClassifierSlot(operator.Classifier,
                                            operator.classifier_cache,
                                            name="ClassifierForests",
                                            subname="Forest{:04d}"),
                       ]

        super(ObjectClassificationSerializer, self ).__init__(topGroupName,
                                                              slots=serialSlots,
                                                              operator=operator)
