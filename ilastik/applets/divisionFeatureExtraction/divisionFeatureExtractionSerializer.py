from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot,\
    deleteIfPresent, getOrCreateGroup
from ilastik.applets.objectExtraction.objectExtractionSerializer import ObjectExtractionSerializer,\
    SerialLabelImageSlot

import numpy as np
import collections

class SerialExtendedFeaturesSlot(SerialSlot):

    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        for i, op in enumerate(innerops):
            opgroup = getOrCreateGroup(group, str(i))
            for t in op._opDivFeats._cache.keys():
                t_gr = opgroup.create_group(str(t))
                for ch in range(len(op._opDivFeats._cache[t])):
                    ch_gr = t_gr.create_group(str(ch))
                    feats = op._opDivFeats._cache[t][ch]
                    for key, val in feats.iteritems():
                        # workaround for Coord<ValueList> which is stored as list of numpy arrays of different sizes:
                        # create numpy array with shape (n_objects*max_length, 3)
                        # if an object has less pixels than max_length, fill the first spare coordinate row with -1,
                        # the rest with 0
                        is_list_of_iterable = False
                        storage_val = val
                        attribute_dict = {}
                        if type(val) is list:
                            if isinstance(val[0], collections.Iterable):
                                is_list_of_iterable = True
                                max_len = 0
                                for el in val[1:]:
                                    curr_len = len(el)
                                    if curr_len > max_len:
                                        max_len = curr_len
                                storage_val = np.zeros((len(val)*max_len, 3))
                                attribute_dict['stride'] = max_len
                                attribute_dict['was_list'] = True
                                attribute_dict['n_objects'] = len(val)
                                for idx, el in enumerate(val):
                                    curr_len = len(el)
                                    storage_val[idx*max_len:idx*max_len+curr_len,...] = np.array(el)
                                    if curr_len < max_len:
                                        storage_val[idx*max_len+curr_len,...] = np.array([-1.0,-1.0,-1.0])
                            else:
                                pass
                        else:
                            pass
                        ds = ch_gr.create_dataset(name=key, data=np.array(storage_val,dtype=np.float), compression=1)
                        for k, v in attribute_dict.iteritems():
                            ds.attrs[k] = v
                        
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
                        # need special treatment for Coord<ValueList> (compare serialize())
                        attribute_dict = gr[t][ch][key].attrs
                        if 'was_list' in attribute_dict:
                            stride = attribute_dict['stride']
                            n_obj = attribute_dict['n_objects']
                            list_feat = [[0]]
                            for idx in xrange(stride, stride*n_obj, stride):
                                max_valid = np.where(gr[t][ch][key][idx:idx+stride,0] == -1)
                                curr_stride = stride
                                if max_valid[0].shape[0] > 0:
                                    curr_stride = max_valid[0][0]
                                list_feat.append(np.array(gr[t][ch][key][idx:idx+curr_stride,...]))
                            feat[key] = list_feat
                        else:
                            feat[key] = gr[t][ch][key].value
                    cache[int(t)].append(feat)
            op._opDivFeats._cache = cache
        self.dirty = False

class DivisionFeatureExtractionSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):        
        slots = [
            SerialLabelImageSlot(operator.LabelImage, name="LabelImage"),
            SerialExtendedFeaturesSlot(operator.RegionFeatures, name="samples"),
        ]

        super(DivisionFeatureExtractionSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
        
