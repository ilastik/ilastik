from ilastik.applets.base.appletSerializer import \
    AppletSerializer, SerialSlot, SerialListSlot

class VigraWatershedViewerSerializer(AppletSerializer):
    """
    Serializes the user's watershed settings to an ilastik v0.6 project file.
    """
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialListSlot(operator.InputChannelIndexes, autodepends=True),
                 SerialSlot(operator.WatershedPadding, autodepends=True),
                 SerialSlot(operator.FreezeCache, autodepends=True),
                 SerialSlot(operator.CacheBlockShape, autodepends=True),
                 SerialSlot(operator.SeedThresholdValue, autodepends=True),
                 SerialSlot(operator.MinSeedSize, autodepends=True) ]
        
        super(VigraWatershedViewerSerializer, self).__init__(projectFileGroupName,
                                                             slots=slots)
