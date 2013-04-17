from ilastik.applets.base.appletSerializer import \
    AppletSerializer, SerialSlot, SerialListSlot

class VigraWatershedViewerSerializer(AppletSerializer):
    """
    Serializes the user's watershed settings to an ilastik v0.6 project file.
    """
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialListSlot(operator.InputChannelIndexes, selfdepends=True),
                 SerialSlot(operator.WatershedPadding, selfdepends=True),
                 SerialSlot(operator.FreezeCache, selfdepends=True),
                 SerialSlot(operator.CacheBlockShape, selfdepends=True),
                 SerialSlot(operator.SeedThresholdValue, selfdepends=True),
                 SerialSlot(operator.MinSeedSize, selfdepends=True) ]
        
        super(VigraWatershedViewerSerializer, self).__init__(projectFileGroupName,
                                                             slots=slots)
