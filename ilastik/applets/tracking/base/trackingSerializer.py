from ilastik.applets.base.appletSerializer import AppletSerializer,\
    SerialDictSlot, SerialSlot

class TrackingSerializer(AppletSerializer):
    
    def __init__(self, mainOperator, projectFileGroupName):
        slots = [SerialDictSlot(mainOperator.Parameters, selfdepends=True),
                 SerialSlot(mainOperator.Output, selfdepends=True)]
        super( TrackingSerializer, self ).__init__( projectFileGroupName, slots=slots )
        