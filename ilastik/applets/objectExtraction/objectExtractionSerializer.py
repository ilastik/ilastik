from ilastik.applets.base.appletSerializer import AppletSerializer

class ObjectExtractionSerializer(AppletSerializer):
    """
    """
    SerializerVersion = 0.1
    
    def __init__(self, mainOperator, projectFileGroupName):
        super( ObjectExtractionSerializer, self ).__init__( projectFileGroupName, self.SerializerVersion )
        self.mainOperator = mainOperator

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        print "tracking: serializeToHdf5", topGroup, hdf5File, projectFilePath

        src = self.mainOperator.innerOperators[0]._mem_h5
        if "LabelImage" in topGroup.keys():
            del topGroup["LabelImage"]
        src.copy('/LabelImage', topGroup) 

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        print "objectExtraction: deserializeFromHdf5", topGroup, groupVersion, hdf5File, projectFilePath

        dest = self.mainOperator.innerOperators[0]._mem_h5        
        print dest
        print topGroup.keys()
        del dest['LabelImage']
        topGroup.copy('LabelImage', dest)

    def isDirty(self):
        return True

    def unload(self):
        print "ObjExtraction.unload not implemented" 

