from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot, SerialHdf5BlockSlot

class ThresholdTwoLevelsSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialSlot(operator.CurOperator, selfdepends=True),
                 SerialSlot(operator.MinSize, selfdepends=True),
                 SerialSlot(operator.MaxSize, selfdepends=True),
                 SerialSlot(operator.HighThreshold, selfdepends=True),
                 SerialSlot(operator.LowThreshold, selfdepends=True),
                 SerialSlot(operator.SingleThreshold, selfdepends=True),
                 SerialDictSlot(operator.SmootherSigma, selfdepends=True),
                 SerialSlot(operator.Channel, selfdepends=True),
                 SerialHdf5BlockSlot(operator.OutputHdf5,
                                     operator.InputHdf5,
                                     operator.CleanBlocks,
                                     name="CachedThresholdOutput")
                ]

        super(self.__class__, self).__init__(projectFileGroupName, slots=slots)
