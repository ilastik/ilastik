from ilastik.applets.base.appletSerializer import AppletSerializer

class ObjectExtractionSerializer(AppletSerializer):
    """
    """
    SerializerVersion = 0.1
    
    def __init__(self, mainOperator, projectFileGroupName):
        super( ObjectExtractionSerializer, self ).__init__( projectFileGroupName, self.SerializerVersion )
        self.mainOperator = mainOperator
        self._dirty = False
    
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        print "tracking: serializeToHdf5", topGroup, hdf5File, projectFilePath
        self._dirty = False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        print "objectExtraction: deserializeFromHdf5", topGroup, groupVersion, hdf5File, projectFilePath

        self._dirty = False

    def isDirty(self):
        return self._dirty

    def handleDirty(self, slot, roi):
        self._dirty = True

    def unload(self):
        pass

