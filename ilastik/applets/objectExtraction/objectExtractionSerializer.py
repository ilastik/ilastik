from ilastik.applets.base.appletSerializer import AppletSerializer,\
    deleteIfPresent, getOrCreateGroup

class ObjectExtractionSerializer(AppletSerializer):
    def __init__(self, mainOperator, projectFileGroupName):
        super(ObjectExtractionSerializer, self).__init__(projectFileGroupName)
        self.mainOperator = mainOperator

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        print "object extraction: serializeToHdf5", topGroup, hdf5File, projectFilePath
        print "object extraction: saving label image"
        deleteIfPresent(topGroup, "LabelImage")
        group = getOrCreateGroup(topGroup, "LabelImage")
        for i, op in enumerate(self.mainOperator.innerOperators):
            src = op._opLabelImage._mem_h5
            group.copy(src['/LabelImage'], group, name=str(i))

        print "object extraction: saving region features"
        deleteIfPresent(topGroup, "samples")
        samples_gr = getOrCreateGroup(topGroup, "samples")
        for i, op in enumerate(self.mainOperator.innerOperators):
            opgroup = getOrCreateGroup(samples_gr, str(i))
            for t in op._opRegFeats._cache.keys():
                t_gr = opgroup.create_group(str(t))
                for ch in range(len(op._opRegFeats._cache[t])):
                    ch_gr = t_gr.create_group(str(ch))
                    feats = op._opRegFeats._cache[t][ch]
                    for key, val in feats.iteritems():
                        ch_gr.create_dataset(name=key, data=val)


    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        print "objectExtraction: deserializeFromHdf5", topGroup, groupVersion, hdf5File, projectFilePath

        print "objectExtraction: loading label image"

        if 'LabelImage' in topGroup.keys():
            opgroup = topGroup['LabelImage']
            self.mainOperator.LabelImage.resize(len(opgroup))
            for inner in opgroup.keys():
                op = self.mainOperator.innerOperators[int(inner)]
                dest = op._opLabelImage._mem_h5
                del dest['LabelImage']
                dest.copy(opgroup[inner], dest, name='LabelImage')
                op._opLabelImage._fixed = False
                op._opLabelImage._processedTimeSteps = range(opgroup[inner].shape[0])

        print "objectExtraction: loading region features"
        if "samples" in topGroup.keys():
            opgroup = topGroup['samples']
            for inner in opgroup.keys():
                gr = opgroup[inner]
                op = self.mainOperator.innerOperators[int(inner)]
                cache = {}
                for t in gr.keys():
                    cache[int(t)] = []
                    for ch in sorted(gr[t].keys()):
                        feat = dict()
                        for key in gr[t][ch].keys():
                            feat[key] = gr[t][ch][key].value
                        cache[int(t)].append(feat)
                op._opRegFeats._cache = cache

    def isDirty(self):
        return True

    def unload(self):
        print "ObjExtraction.unload not implemented"
