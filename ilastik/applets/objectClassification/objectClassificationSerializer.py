from ilastik.applets.base.appletSerializer import \
  AppletSerializer, SerialSlot, SerialDictSlot, \
  SerialClassifierSlot


class ObjectClassificationSerializer(AppletSerializer):
    # FIXME: predictions can only be saved, not loaded, because it
    # would call setValue() on a connected slot

    def __init__(self, topGroupName, operator):
        serialSlots = [SerialDictSlot(operator.LabelInputs, transform=int),
                       SerialClassifierSlot(operator.Classifier,
                                            operator.classifier_cache,
                                            name="ClassifierForests",
                                            subname="Forest{:04d}"),
#                       SerialDictSlot(operator.Predictions, transform=int),
                       ]

        super(ObjectClassificationSerializer, self ).__init__(topGroupName,
                                                              slots=serialSlots,
                                                              operator=operator)
