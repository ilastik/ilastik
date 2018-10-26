###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
from builtins import range
import logging
import warnings
from functools import partial

import numpy

from lazyflow.rtype import SubRegion
from lazyflow.roi import getIntersectingBlocks, TinyVector, getBlockBounds, roiToSlice
from lazyflow.request import Request, RequestLock, RequestPool

from ilastik.applets.base.appletSerializer import AppletSerializer,\
    deleteIfPresent, getOrCreateGroup, SerialSlot, SerialBlockSlot, \
    SerialDictSlot, SerialObjectFeatureNamesSlot
from ilastik.utility.commandLineProcessing import convertStringToList

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
            subgroup = getOrCreateGroup(group, "{:04}".format(i))

            cleanBlockRois = self.blockslot[i].value
            for roi in cleanBlockRois:
                region_features_arr = self.slot[i]( *roi ).wait()
                assert region_features_arr.shape == (1,)
                region_features = region_features_arr[0]
                roi_string = str([[r.start for r in roi], [r.stop for r in roi]])
                roi_grp = subgroup.create_group(name=str(roi_string))
                logger.debug('Saving region features into group: "{}"'.format( roi_grp.name ))
                for key, val in region_features.items():
                    plugin_group = getOrCreateGroup(roi_grp, key)
                    for featname, featval in val.items():
                        plugin_group.create_dataset(name=featname, data=featval)

        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        opgroup = group[self.name]
        # Note: We sort by NUMERICAL VALUE here.
        for i, (group_name, subgroup) in enumerate( sorted(list(opgroup.items()), key=lambda k_v: int(k_v[0]) ) ):
            assert int(group_name) == i, "subgroup extraction order should be numerical order!"
            for roiString, roi_grp in subgroup.items():
                logger.debug('Loading region features from dataset: "{}"'.format( roi_grp.name ))
                roi = convertStringToList(roiString)
                roi = tuple(map(tuple, roi))
                assert len(roi) == 2
                assert len(roi[0]) == len(roi[1])

                region_features = {}
                for key, val in roi_grp.items():
                    region_features[key] = {}
                    for featname, featval in val.items():
                        region_features[key][featname] = featval[...]

                slicing = roiToSlice( *roi )
                self.inslot[i][slicing] = numpy.array([region_features])

        self.dirty = False


class ObjectExtractionSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [
            SerialBlockSlot(operator.LabelImage,
                            operator.LabelImageCacheInput,
                            operator.CleanLabelBlocks,
                            name='LabelImage_v2',
                            subname='labelimage{:03d}',
                            selfdepends=False,
                            shrink_to_bb=False,
                            compression_level=1),
            SerialObjectFeatureNamesSlot(operator.Features),
            SerialObjectFeaturesSlot(operator.BlockwiseRegionFeatures,
                                     operator.RegionFeaturesCacheInput,
                                     operator.RegionFeaturesCleanBlocks,
                                     name="RegionFeatures"),
        ]

        super(ObjectExtractionSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
