from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot

class OpticalTranslationSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialDictSlot(operator.Parameters, autodepends=True),
                 SerialSlot(operator.TranslationVectors, autodepends=True),                 
                ]

        super(OpticalTranslationSerializer, self).__init__(projectFileGroupName, slots=slots)
