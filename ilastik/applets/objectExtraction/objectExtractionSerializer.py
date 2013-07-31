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

                        # to do:
                        # create subfolder for each object
                        is_list_of_iterable = False
                        if featname == 'Coord<ValueList>':
                            if featname not in plugin_group:
                                dg = plugin_group.create_group(featname)
                            else:
                                dg = plugin_group[featname]
                                if not type(dg) is  h5py.Group:
                                    raise Exception, "%s already exists and is not of type Group!" % featname
                            for idx, values in enumerate(featval):
                                if idx == 0 and len(featval) > 1:
                                    dim = featval[1][0].shape[1]
                                    ds = dg.create_dataset(name=str(idx), data=numpy.zeros((1,dim), dtype=numpy.float32))
                                else:
                                    ds = dg.create_dataset(name=str(idx), data=numpy.array(values[0], dtype=numpy.float32))

                        else:
                            ds = plugin_group.create_dataset(name=featname, data=featval)


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

                        # now: features for Coord<ValueList> reside in own subfolder
                        if featname == 'Coord<ValueList>':
                            list_feat = [[]]
                            for obj_id in sorted([int(x) for x in featval.keys()]):
                                values = featval[str(obj_id)]
                                list_feat.append(numpy.array([numpy.array(values.value, dtype=object)], dtype=object))
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
