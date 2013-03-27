from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot,\
    deleteIfPresent, getOrCreateGroup
import numpy


class SerialTranslationVectorsSlot(SerialSlot):

    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        for i, op in enumerate(mainOperator.innerOperators):            
            ts = op._processedTimeSteps
            if len(ts) > 0:
                subgroup = getOrCreateGroup(group, str(i))
                subgroup.create_dataset(name='timesteps', data=list(ts))
                
                src = op._mem_h5
                subgroup.copy(src['/TranslationVectors'], subgroup, name='data')                
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
            ts = set(numpy.array(mygroup['timesteps'][:]).flat)
            op._processedTimeSteps = ts
            
            dest = op._mem_h5
            del dest['TranslationVectors']
            dest.copy(mygroup['data'], dest, name='TranslationVectors')            
        self.dirty = False

class OpticalTranslationSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialDictSlot(operator.Parameters, autodepends=True),
                 SerialTranslationVectorsSlot(operator.TranslationVectors, autodepends=True),                 
                ]

        super(OpticalTranslationSerializer, self).__init__(projectFileGroupName, slots=slots)

