from ilastik.applets.base.appletSerializer import AppletSerializer,\
    SerialDictSlot, SerialSlot

class TrackingSerializer(AppletSerializer):
    
    def __init__(self, mainOperator, projectFileGroupName):
        slots = [SerialDictSlot(mainOperator.Parameters, selfdepends=True),
                 SerialSlot(mainOperator.Output, selfdepends=True)]
        try:
            print 'I have a MergerOutput slot'
            slots.append(SerialSlot(mainOperator.MergerOutput, selfdepends=True))
        except:
            print 'I have no MergerOutput slot'
            pass
            
        super( TrackingSerializer, self ).__init__( projectFileGroupName, slots=slots )
        