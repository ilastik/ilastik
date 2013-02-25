from ilastik.applets.base.appletSerializer import AppletSerializer,\
    deleteIfPresent, getOrCreateGroup, SerialSlot

import numpy


class SerialLabelImageSlot(SerialSlot):

    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        for i, op in enumerate(mainOperator.innerOperators):
            oplabel = op._opLabelImage
            assert False, "FIXME: OpLabelImage implementation has changed, no longer has _processedTimeSteps member"
            ts = oplabel._processedTimeSteps
            if len(ts) > 0:
                subgroup = getOrCreateGroup(group, str(i))
                subgroup.create_dataset(name='timesteps', data=list(ts))

                if oplabel.compressed:
                    src = oplabel._mem_h5
                    subgroup.copy(src['/LabelImage'], subgroup, name='data')
                else:
                    src = oplabel._labeled_image
                    subgroup.create_dataset(name='data', data=src)
        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        opgroup = group[self.name]
        for inner in opgroup.keys():
            mygroup = opgroup[inner]
            oplabel = innerops[int(inner)]._opLabelImage
            ts = set(numpy.array(mygroup['timesteps'][:]).flat)
            assert False, "FIXME: OpLabelImage implementation has changed, no longer has _processedTimeSteps member"
            oplabel._processedTimeSteps = ts
            oplabel._fixed = False

            if oplabel.compressed:
                dest = oplabel._mem_h5
                del dest['LabelImage']
                dest.copy(mygroup['data'], dest, name='LabelImage')
            else:
                oplabel._labeled_image[:] = mygroup['data'][:]

        self.dirty = False


class SerialObjectFeaturesSlot(SerialSlot):

    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        for i, op in enumerate(innerops):
            opgroup = getOrCreateGroup(group, str(i))
            for t in op._opRegFeats._cache.keys():
                t_gr = opgroup.create_group(str(t))
                for ch in range(len(op._opRegFeats._cache[t])):
                    ch_gr = t_gr.create_group(str(ch))
                    feats = op._opRegFeats._cache[t][ch]
                    for key, val in feats.iteritems():
                        ch_gr.create_dataset(name=key, data=val)
        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        opgroup = group[self.name]
        for inner in opgroup.keys():
            gr = opgroup[inner]
            op = innerops[int(inner)]
            cache = {}
            for t in gr.keys():
                cache[int(t)] = []
                for ch in sorted(gr[t].keys()):
                    feat = dict()
                    for key in gr[t][ch].keys():
                        feat[key] = gr[t][ch][key].value
                    cache[int(t)].append(feat)
            op._opRegFeats._cache = cache
        self.dirty = False


class ObjectExtractionSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [
            SerialLabelImageSlot(operator.LabelImage, name="LabelImage"),
            SerialObjectFeaturesSlot(operator.RegionFeatures, name="samples"),
        ]

        super(ObjectExtractionSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
