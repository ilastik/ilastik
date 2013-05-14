import logging
import warnings
from functools import partial

import numpy

from lazyflow.rtype import SubRegion
from lazyflow.roi import getIntersectingBlocks, TinyVector, getBlockBounds, roiToSlice
from lazyflow.request import Request, RequestLock, RequestPool

from ilastik.applets.base.appletSerializer import AppletSerializer,\
    deleteIfPresent, getOrCreateGroup, SerialSlot, SerialHdf5BlockSlot, SerialDictSlot

from ilastik.utility.timer import timeLogged

import collections

logger = logging.getLogger(__name__)

class SerialObjectFeaturesSlot(SerialSlot):

    def __init__(self, slot, inslot, blockslot, name=None,
                 subname=None, default=None, depends=None,
                 selfdepends=True):
        super(SerialObjectFeaturesSlot, self).__init__(
            slot, inslot, name, subname, default, depends, selfdepends
        )

        self.blockslot = blockslot
        self._bind(slot)

    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()

        for i in range(len(mainOperator)):
            subgroup = getOrCreateGroup(group, str(i))

            cleanBlockRois = self.blockslot[i].value
            for roi in cleanBlockRois:
                region_features_arr = self.slot[i]( *roi ).wait()
                assert region_features_arr.shape == (1,)
                region_features = region_features_arr[0]
                roi_grp = subgroup.create_group(name=str(roi))
                logger.debug('Saving region features into group: "{}"'.format( roi_grp.name ))
                for key, val in region_features.iteritems():
                    plugin_group = getOrCreateGroup(roi_grp, key)
                    for featname, featval in val.iteritems():
                        # workaround for Coord<ValueList> which is stored as list of numpy arrays of different sizes:
                        # create numpy array with shape (n_objects*max_length, 3)
                        # if an object has less pixels than max_length, fill the first spare coordinate row with -1,
                        # the rest with 0
                        is_list_of_iterable = False
                        storage_val = featval
                        attribute_dict = {}
                        if featname == 'Coord<ValueList>':
                            if isinstance(featval[0], collections.Iterable):
                                is_list_of_iterable = True
                                max_len = 0
                                for tmp_el in featval[1:]:
                                    el = tmp_el[0]
                                    curr_len = el.shape[0]
                                    if curr_len > max_len:
                                        max_len = curr_len
                                storage_val = numpy.zeros((len(featval)*max_len, 3),dtype=numpy.float)
                                attribute_dict['stride'] = max_len
                                attribute_dict['was_list'] = True
                                attribute_dict['n_objects'] = len(featval)
                                for idx, tmp_el in enumerate(featval):
                                    if idx == 0:
                                        el = numpy.array([], dtype=numpy.float).reshape((0,3))
                                    else:
                                        el = tmp_el[0]
                                    curr_len = el.shape[0]
                                    storage_val[idx*max_len:idx*max_len+curr_len,...] = numpy.array(el)
                                    if curr_len < max_len:
                                        storage_val[idx*max_len+curr_len,...] = numpy.array([-1.0,-1.0,-1.0])
                            else:
                                pass
                        else:
                            pass
                        ds = plugin_group.create_dataset(name=featname, data=storage_val)
                        for k, v in attribute_dict.iteritems():
                            ds.attrs[k] = v

        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        opgroup = group[self.name]
        for i, (_, subgroup) in enumerate( sorted(opgroup.items() ) ):
            for roiString, roi_grp in subgroup.iteritems():
                logger.debug('Loading region features from dataset: "{}"'.format( roi_grp.name ))
                roi = eval(roiString)

                region_features = {}
                for key, val in roi_grp.iteritems():
                    region_features[key] = {}
                    for featname, featval in val.iteritems():
                        # for special feature Coord<ValueList>:
                        # copy meaningful coordinates into python list
                        # for each region omit everything after [-1 -1 -1]
                        if featname == 'Coord<ValueList>':
                            stride = featval.attrs['stride']
                            n_obj = featval.attrs['n_objects']
                            list_feat = [[]]
                            for idx in xrange(stride, stride*n_obj, stride):
                                max_valid = numpy.where(featval[idx:idx+stride,0] == -1)
                                curr_stride = stride
                                if max_valid[0].shape[0] > 0:
                                    curr_stride = max_valid[0][0]
                                list_feat.append(numpy.array([numpy.array(featval[idx:idx+curr_stride,...], dtype=object)], dtype=object))
                            region_features[key][featname] = numpy.array(list_feat, dtype=object)
                        else:
                            region_features[key][featname] = featval[...]

                slicing = roiToSlice( *roi )
                self.inslot[i][slicing] = numpy.array([region_features])

        self.dirty = False


class ObjectExtractionSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [
            SerialHdf5BlockSlot(operator.LabelOutputHdf5,
                                operator.LabelInputHdf5,
                                operator.CleanLabelBlocks,
                                name="LabelImage"),
            SerialDictSlot(operator.Features, transform=str),
            SerialObjectFeaturesSlot(operator.BlockwiseRegionFeatures,
                                     operator.RegionFeaturesCacheInput,
                                     operator.RegionFeaturesCleanBlocks,
                                     name="RegionFeatures"),
        ]

        super(ObjectExtractionSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
