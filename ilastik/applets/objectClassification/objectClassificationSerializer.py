import warnings

from ilastik.applets.base.appletSerializer import \
  AppletSerializer, SerialSlot, SerialDictSlot, \
  SerialClassifierSlot, SerialListSlot


class ObjectClassificationSerializer(AppletSerializer):
    # FIXME: predictions can only be saved, not loaded, because it
    # would call setValue() on a connected slot

    def __init__(self, topGroupName, operator):
        warnings.warn("FIXME: Not serializing/deserializing object predictions")        
        serialSlots = [SerialListSlot(operator.LabelNames,
                                transform=str),
                       SerialListSlot(operator.LabelColors, transform=lambda x: tuple(x.flat)),
                       SerialListSlot(operator.PmapColors, transform=lambda x: tuple(x.flat)),
                       SerialDictSlot(operator.LabelInputs, transform=int),
                       SerialClassifierSlot(operator.Classifier,
                                            operator.classifier_cache,
                                            name="ClassifierForests",
                                            subname="Forest{:04d}"),
                       SerialDictSlot(operator.Probabilities,
                                      operator.InputProbabilities,
                                      transform=int),
                       ]

        super(ObjectClassificationSerializer, self ).__init__(topGroupName,
                                                              slots=serialSlots,
                                                              operator=operator)
