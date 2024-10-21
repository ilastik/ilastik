###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################
import logging
from typing import Optional

from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction, OpObjectExtractionFromLabels
from lazyflow.roi import roiToSlice
import numpy
import numpy.typing as npt

from ilastik.applets.base.appletSerializer import (
    AppletSerializer,
    SerialBlockSlot,
    SerialObjectFeatureNamesSlot,
    SerialRelabeledDataSlot,
    SerialSlot,
    deleteIfPresent,
)
from ilastik.plugins.manager import pluginManager
from ilastik.utility.commandLineProcessing import convertStringToList
from lazyflow.slot import InputSlot, OutputSlot


logger = logging.getLogger(__name__)


class UnsatisfyableObjectFeaturesError(BaseException):
    pass


class SerialObjectFeaturesSlot(SerialSlot):
    def __init__(
        self,
        slot: OutputSlot,
        inslot: InputSlot,
        blockslot: OutputSlot,
        name: Optional[str] = None,
        subname=None,
        default=None,
        depends=None,
        selfdepends=True,
    ):
        super(SerialObjectFeaturesSlot, self).__init__(slot, inslot, name, subname, default, depends, selfdepends)

        self.blockslot = blockslot
        self._bind(slot)

    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = group.require_group(self.name)
        mainOperator = self.slot.operator

        for i in range(len(mainOperator)):
            subgroup = group.require_group(f"{i:04d}")

            cleanBlockRois = self.blockslot[i].value
            for roi in cleanBlockRois:
                region_features_arr = self.slot[i](*roi).wait()
                assert region_features_arr.shape == (1,)
                region_features = region_features_arr[0]
                roi_string = str([[r.start for r in roi], [r.stop for r in roi]])
                roi_grp = subgroup.create_group(name=str(roi_string))
                logger.debug('Saving region features into group: "{}"'.format(roi_grp.name))
                for key, val in region_features.items():
                    plugin_group = roi_grp.require_group(key)
                    for featname, featval in val.items():
                        plugin_group.create_dataset(name=featname, data=featval)

        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        opgroup = group[self.name]
        # Note: We sort by NUMERICAL VALUE here.
        for i, (group_name, subgroup) in enumerate(sorted(list(opgroup.items()), key=lambda k_v: int(k_v[0]))):
            assert int(group_name) == i, "subgroup extraction order should be numerical order!"
            for roiString, roi_grp in subgroup.items():
                logger.debug('Loading region features from dataset: "{}"'.format(roi_grp.name))
                roi = convertStringToList(roiString)
                roi = tuple(map(tuple, roi))
                assert len(roi) == 2
                assert len(roi[0]) == len(roi[1])

                region_features = {}
                for key, val in roi_grp.items():
                    region_features[key] = {}
                    for featname, featval in val.items():
                        region_features[key][featname] = featval[...]

                slicing = roiToSlice(*roi)
                self.inslot[i][slicing] = numpy.array([region_features])

        self.dirty = False


class ObjectExtractionSerializer(AppletSerializer):
    def __init__(self, operator: OpObjectExtraction, projectFileGroupName: str):
        slots = [
            SerialBlockSlot(
                operator.LabelImage,
                operator.LabelImageCacheInput,
                operator.CleanLabelBlocks,
                name="LabelImage_v2",
                subname="labelimage{:03d}",
                selfdepends=False,
                shrink_to_bb=False,
                compression_level=1,
            ),
            SerialObjectFeatureNamesSlot(operator.Features),
            SerialObjectFeaturesSlot(
                operator.BlockwiseRegionFeatures,
                operator.RegionFeaturesCacheInput,
                operator.RegionFeaturesCleanBlocks,
                name="RegionFeatures",
            ),
        ]

        super(ObjectExtractionSerializer, self).__init__(projectFileGroupName, slots=slots)

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath, headless=False):
        """Post-process slot deserialization"""
        # make sure all deserialized, selected features can be computed
        selected_features_slot = self.serialSlots[1].slot
        if not selected_features_slot.ready():
            return
        # {"feature_plugin": {"feature_name": {feature_details ...}}}
        selected_features_dict = selected_features_slot.value
        missing_features = []
        for plugin_name in selected_features_dict.keys():
            plugin_inner = pluginManager.getPluginByName(plugin_name, "ObjectFeatures")
            if not plugin_inner:
                missing_features.append(plugin_name)

        if missing_features:
            raise UnsatisfyableObjectFeaturesError(
                f"Could not find feature plugins {missing_features} that were used when creating this project. "
                "Install missing feature plugins to load this project file."
            )


class ObjectExtractionFromLabelsSerializer(AppletSerializer):

    @staticmethod
    def transform_to_h5(slot_val) -> npt.NDArray[numpy.uint32]:
        assert len(slot_val) == 1, f"Expected single length array entry for mapping dictionary, got {len(slot_val)=}."
        assert isinstance(slot_val[0], dict), f"Expected dict, got {type(slot_val[0])=}."
        return numpy.array(slot_val[0].items())

    @staticmethod
    def transform_from_h5(val: npt.NDArray[numpy.uint32]) -> npt.NDArray:
        return numpy.array([dict(val)])

    def __init__(self, operator: OpObjectExtractionFromLabels, projectFileGroupName: str):
        slots = [
            SerialRelabeledDataSlot(
                slot=operator.RelabelCacheOutput,
                inslot=operator.RelabelCacheInput,
                blockslot=operator.CleanLabelBlocks,
                name="RelabelData",
                subname="ImageLane{:03d}",
                selfdepends=False,
            ),
            SerialObjectFeatureNamesSlot(operator.Features),
            SerialObjectFeaturesSlot(
                operator.BlockwiseRegionFeatures,
                operator.RegionFeaturesCacheInput,
                operator.RegionFeaturesCleanBlocks,
                name="RegionFeatures",
            ),
        ]

        super().__init__(projectFileGroupName, slots=slots)
