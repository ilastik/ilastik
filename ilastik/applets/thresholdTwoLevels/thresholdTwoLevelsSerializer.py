from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot, SerialHdf5BlockSlot

class ThresholdTwoLevelsSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialSlot(operator.CurOperator, autodepends=True),
                 SerialSlot(operator.MinSize, autodepends=True),
                 SerialSlot(operator.MaxSize, autodepends=True),
                 SerialSlot(operator.HighThreshold, autodepends=True),
                 SerialSlot(operator.LowThreshold, autodepends=True),
                 SerialSlot(operator.SingleThreshold, autodepends=True),
                 SerialDictSlot(operator.SmootherSigma, autodepends=True),
                 SerialSlot(operator.Channel, autodepends=True),
                 SerialHdf5BlockSlot(operator.InputHdf5,
                                     operator.OutputHdf5,
                                     operator.CleanBlocks,
                                     name="CachedThresholdOutput")
                ]
        
        super(self.__class__, self).__init__(projectFileGroupName, slots=slots)
