from ilastik.applets.base.appletSerializer import \
    AppletSerializer, SerialSlot

class ThresholdMaskingSerializer(AppletSerializer):
    """
    Serializes the user's pixel feature selections to an ilastik v0.6 project file.
    """
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialSlot(operator.MinValue, autodepends=True),
                 SerialSlot(operator.MaxValue, autodepends=True)]
        
        super(ThresholdMaskingSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
