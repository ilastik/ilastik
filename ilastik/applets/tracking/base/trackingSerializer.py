from ilastik.applets.base.appletSerializer import AppletSerializer,\
    SerialDictSlot, SerialSlot

class TrackingSerializer(AppletSerializer):
    
    def __init__(self, mainOperator, projectFileGroupName):
        slots = [SerialDictSlot(mainOperator.Parameters, autodepends=True),
                 SerialSlot(mainOperator.Output, autodepends=True)]
        super( TrackingSerializer, self ).__init__( projectFileGroupName, slots=slots )
        