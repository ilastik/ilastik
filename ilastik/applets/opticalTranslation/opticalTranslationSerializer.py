from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot

class OpticalTranslationSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
#        slots = [SerialSlot(operator.MinSize, autodepends=True),
#                 SerialSlot(operator.MaxSize, autodepends=True),
#                 SerialSlot(operator.HighThreshold, autodepends=True),
#                 SerialSlot(operator.LowThreshold, autodepends=True),
#                 SerialDictSlot(operator.SmootherSigma, autodepends=True),
#                 SerialSlot(operator.Channel, autodepends=True),
#                ]
#        
        super(self.__class__, self).__init__(projectFileGroupName, slots=slots)
