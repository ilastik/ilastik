from ilastik.applets.base.appletSerializer import AppletSerializer,\
    SerialDictSlot

class ManualTrackingSerializer(AppletSerializer):
    
    def __init__(self, topGroupName, operator):
#        serialSlots = [SerialDictSlot(operator.Labels, transform=int),
##                       SerialDictSlot(operator.Predictions, transform=int),
#                       ]
        serialSlots = []

        super(ManualTrackingSerializer, self ).__init__(topGroupName,
                                                              slots=serialSlots,
                                                              operator=operator)
