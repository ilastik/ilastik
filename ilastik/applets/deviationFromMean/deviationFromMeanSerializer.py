from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot

class DeviationFromMeanSerializer(AppletSerializer):
    """
    Serializes the user's settings in the "Deviation From Mean" applet to an ilastik v0.6 project file.
    """
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialSlot(operator.ScalingFactor, autodepends=True),
                 SerialSlot(operator.Offset, autodepends=True)]
        
        super(DeviationFromMeanSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
