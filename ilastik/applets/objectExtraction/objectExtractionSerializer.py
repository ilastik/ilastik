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
            src = op._opLabelImage._mem_h5
            ts = op._opLabelImage._processedTimeSteps
            if len(ts) > 0:
                subgroup = getOrCreateGroup(group, str(i))
                subgroup.copy(src['/LabelImage'], subgroup, name='data')
                subgroup.create_dataset(name='timesteps', data=list(ts))
        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        opgroup = group[self.name]
        for inner in opgroup.keys():
            mygroup = opgroup[inner]
            op = innerops[int(inner)]
            dest = op._opLabelImage._mem_h5
            del dest['LabelImage']
            dest.copy(mygroup['data'], dest, name='LabelImage')
            ts = set(numpy.array(mygroup['timesteps'][:]).flat)
            op._opLabelImage._processedTimeSteps = ts
            op._opLabelImage._fixed = False
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
