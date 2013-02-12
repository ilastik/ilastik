from ilastik.applets.base.appletSerializer import AppletSerializer,\
    deleteIfPresent, getOrCreateGroup

class ObjectExtractionSerializer(AppletSerializer):
    def __init__(self, mainOperator, projectFileGroupName):
        super( ObjectExtractionSerializer, self ).__init__( projectFileGroupName )
        self.mainOperator = mainOperator

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        op = self.mainOperator.innerOperators[0]
        print "object extraction: serializeToHdf5", topGroup, hdf5File, projectFilePath
        print "object extraction: saving label image"
        deleteIfPresent( topGroup, "LabelImage")
        op._opLabelImage._mem_h5.copy('/LabelImage', topGroup)

        print "object extraction: saving region features"
        deleteIfPresent( topGroup, "samples")
        samples_gr = getOrCreateGroup( topGroup, "samples" )
        for t in op._opRegFeats._cache.keys():
            t_gr = samples_gr.create_group(str(t))
            for ch in range(len(op._opRegFeats._cache[t])):
                ch_gr = t_gr.create_group(str(ch))
                feats = op._opRegFeats._cache[t][ch]
                for key, val in feats.iteritems():
                    ch_gr.create_dataset(name=key, data=val)


    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        print "objectExtraction: deserializeFromHdf5", topGroup, groupVersion, hdf5File, projectFilePath

        print "objectExtraction: loading label image"
        op = self.mainOperator.innerOperators[0]

        if 'LabelImage' in topGroup.keys():
            dest = op._opLabelImage._mem_h5
            del dest['LabelImage']
            topGroup.copy('LabelImage', dest)
            op._opLabelImage._fixed = False
            op._opLabelImage._processedTimeSteps = range(topGroup['LabelImage'].shape[0])

        print "objectExtraction: loading region features"
        if "samples" in topGroup.keys():
            cache = {}
            for t in topGroup["samples"].keys():
                cache[int(t)] = []
                for ch in sorted(topGroup["samples"][t].keys()):
                    feat = dict()
                    for key in topGroup["samples"][t][ch].keys():
                        feat[key] = topGroup["samples"][t][ch][key].value
                    cache[int(t)].append(feat)
            self.mainOperator.innerOperators[0]._opRegFeats._cache = cache

    def isDirty(self):
        return True

    def unload(self):
        print "ObjExtraction.unload not implemented"
