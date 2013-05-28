from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot

class PatchCreatorSerializer(AppletSerializer):
    """Serializes the user's settings in the "Steerable Pyramid"
    applet to an ilastik v0.6 project file.

    """
    def __init__(self, topLevelOperator, projectFileGroupName):
        slots = [SerialSlot(topLevelOperator.PatchWidth, selfdepends=True),
                 SerialSlot(topLevelOperator.PatchHeight, selfdepends=True),
                 SerialSlot(topLevelOperator.PatchOverlapVertical, selfdepends=True),
                 SerialSlot(topLevelOperator.PatchOverlapHorizontal, selfdepends=True),
                 SerialSlot(topLevelOperator.GridStartVertical, selfdepends=True),
                 SerialSlot(topLevelOperator.GridStartHorizontal, selfdepends=True),
                 SerialSlot(topLevelOperator.GridWidth, selfdepends=True),
                 SerialSlot(topLevelOperator.GridHeight, selfdepends=True)]

        super(PatchCreatorSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
        self.topLevelOperator = topLevelOperator
