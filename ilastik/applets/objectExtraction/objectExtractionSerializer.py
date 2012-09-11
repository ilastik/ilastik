from ilastik.applets.base.appletSerializer import AppletSerializer

class ObjectExtractionSerializer(AppletSerializer):
    """
    """
    SerializerVersion = 0.1
    
    def __init__(self, mainOperator, projectFileGroupName):
        super( ObjectExtractionSerializer, self ).__init__( projectFileGroupName, self.SerializerVersion )
        self.mainOperator = mainOperator

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        op = self.mainOperator.innerOperators[0]
        print "object extraction: serializeToHdf5", topGroup, hdf5File, projectFilePath
        print "object extraction: saving label image"
        src = op._mem_h5
        self.deleteIfPresent( topGroup, "LabelImage")
        src.copy('/LabelImage', topGroup) 

        print "object extraction: saving region centers"
        self.deleteIfPresent( topGroup, "samples")
        samples_gr = self.getOrCreateGroup( topGroup, "samples" )
        for t in op._opRegCent._cache.keys():
            t_gr = samples_gr.create_group(str(t))
            t_gr.create_dataset(name="region_center", data=op._opRegCent._cache[t])

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        print "objectExtraction: deserializeFromHdf5", topGroup, groupVersion, hdf5File, projectFilePath

        print "objectExtraction: loading label image"
        dest = self.mainOperator.innerOperators[0]._mem_h5        

        del dest['LabelImage']
        topGroup.copy('LabelImage', dest)

        print "objectExtraction: loading region centers"
        if "samples" in topGroup.keys():
            cache = {}

            for t in topGroup["samples"].keys():
                cache[int(t)] = topGroup["samples"][t]['region_center'].value
            self.mainOperator.innerOperators[0]._opRegCent._cache = cache

    def isDirty(self):
        return True

    def unload(self):
        print "ObjExtraction.unload not implemented" 

