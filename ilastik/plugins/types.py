###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2026, the ilastik developers
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
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping, NotRequired, Optional, Type, TypedDict

import numpy
import numpy.typing as npt
import vigra

FloatArray = npt.NDArray[numpy.floating[Any]]


PartialFeatureDict = Mapping[str, dict[str, str | bool | int]]


class FeatureDescription(TypedDict):
    displaytext: str
    detailtext: str
    tooltip: str
    advanced: bool
    # for grouping features in plugins, adds another level in the feature
    # selection tree.
    # Only special value is "location", and should be given whenever
    # absolute coordinates (image) are involved.
    group: NotRequired[str]
    # _currently_ if this parameter is given, features are computed via
    # compute_local, very likely to be changed.
    # margin value can be set in the ilastik UI
    margin: NotRequired[int]
    # features are assumed to be able to do 2D and 3D. If your feature
    # cannot do one of them, you can mark those accordingly by setting
    # one of those keys in the feature description
    no_3D: NotRequired[bool]
    no_2D: NotRequired[bool]
    # if raw data is accessed for your feature, the most of the
    channel_aware: NotRequired[bool]


@dataclass(frozen=True)
class PluginInfo:
    name: str
    author: str
    description: str
    version: str
    website: Optional[str] = ""


FeatureDict = dict[str, FeatureDescription]


class ObjectFeaturesPlugin(ABC):
    """Plugins of this class calculate object features."""

    plugin_info: PluginInfo

    # TODO for now, only one margin will be set in the dialog. however, it
    # should be repeated for each feature, because in the future it
    # might be different, or each feature might take other parameters.

    def __init__(self, *args, **kwargs):
        super(ObjectFeaturesPlugin, self).__init__(*args, **kwargs)
        self._selectedFeatures = []

    @abstractmethod
    def availableFeatures(self, image: vigra.VigraArray, labels: vigra.VigraArray) -> PartialFeatureDict:
        """Reports which features this plugin can compute on a
        particular image and label image.

        often plugins may return a slightly different feature set depending
        on the image being 2D or 3D.

        Args:
            image: tagged vigra array
            labels: tagged vigra array

        Returns:
            a nested dictionary, where dict[feature_name] is a
            dictionary of parameters.
        """

    @abstractmethod
    def fill_properties(self, features: PartialFeatureDict) -> FeatureDict:
        """Augment die feature dictionary with additional fields

        For every feature in the feature dictionary, fill in its properties,
        such as 'detailtext', which will be displayed in help, or 'displaytext'
        which will be displayed instead of the feature name

        Only necessary if these keys are not present to begin with.

        Args:
            features: dict with feature names as keys

        Returns:
            same dictionary, with additional fields filled for each feature

        """

    def compute_global(
        self, image: vigra.VigraArray, labels: vigra.VigraArray, features: PartialFeatureDict, axes: str
    ) -> dict[str, FloatArray]:
        """calculate the requested features.

        Object id 0 should be excluded from feature computation here.
        (ilastik expects it that way.)

        Args:
            image: VigraArray of the image with axistags, always xyzc, full image
            labels: VigraArray of the labels with axistags, always xyz, full label
                image with all objects having unique pixel values.
                ObjectID 0 is considered background, object ids are positive integers
            features: list of feature names; which features to compute
            axes: axis tags, DEPRECATED; use `.axistags` attribute of image/labels

        Returns
            dictionary with one entry per feature. dict[feature_name] is a
            numpy.ndarray with shape (n_objs, n_featvals), where featvals is
            the number of elements for a single object for the particular feature
        """
        return dict()

    def compute_local(
        self, image: vigra.VigraArray, binary_bbox: vigra.VigraArray, features: PartialFeatureDict, axes: str
    ) -> dict[str, FloatArray]:
        """Calculate features on a single object.

        Args:
            image: VigraArray of the image with axistags, always xyzc, for one object, includes margin around
            binary_bbox: VigraArray of the image with axistags, always xyz, for one object, includes margin around
            features: which features to compute
            axes: axis tags, DEPRECATED; use `.axistags` attribute of image/labels

        Returns:
            a dictionary with one entry per feature.
            dict[feature_name] is a numpy.ndarray with ndim=1
        """
        return dict()

    @staticmethod
    def combine_dicts(ds):
        return dict(sum((list(d.items()) for d in ds), []))

    @staticmethod
    def combine_dicts_with_numpy(ds):
        # stack arrays which correspond to the same keys
        keys = list(ds[0].keys())
        result = {}
        for key in keys:
            arrays = [d[key] for d in ds]
            array_combined = numpy.hstack(arrays)
            result[key] = array_combined
        return result

    @staticmethod
    def update_keys(d, prefix=None, suffix=None):
        if prefix is None:
            prefix = ""
        if suffix is None:
            suffix = ""
        return dict((prefix + k + suffix, v) for k, v in list(d.items()))

    def do_channels(self, fn, image, axes, **kwargs):
        """Helper for features that only take one channel.

        :param fn: function that computes features

        """
        results = []
        slc = [slice(None)] * 4
        for channel in range(image.shape[axes.c]):
            slc[axes.c] = channel
            # a dictionary for the channel
            result = fn(image[slc], axes=axes, **kwargs)
            results.append(result)

        return self.combine_dicts_with_numpy(results)


class TrackingExportFormatPlugin(ABC):
    """Plugins of this class can export a tracking solution."""

    plugin_info: PluginInfo
    exportsToFile = True  # depending on this setting, the user can choose a file or a folder where to export

    def __init__(self, *args, **kwargs):
        super(TrackingExportFormatPlugin, self).__init__(*args, **kwargs)

    @abstractmethod
    def checkFilesExist(self, filename: str) -> bool:
        """Check whether the files we want to export (when appending the base filename) are already present"""

    @abstractmethod
    def export(self, filename, hypothesesGraph, pluginExportContext) -> bool:
        """Export the tracking solution stored in the hypotheses graph's "value" and "divisionValue"
        attributes (or the "lineageId" and "trackId" attribs). See https://github.com/chaubold/hytra for more details.

        :param filename: string of the file where to save the result (or folder where to put the export files)
        :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
        :param pluginExportContext ilastik.plugins.PluginExportContext: instance of PluginExportContext containing
            data necessary for the export such as:

            - objectFeaturesSlot (lazyflow.graph.InputSlot): connected to the RegionFeaturesAll output of
                ilastik.applets.trackingFeatureExtraction.opTrackingFeatureExtraction.OpTrackingFeatureExtraction
            - labelImageSlot (lazyflow.graph.InputSlot): labeled image slot
            - rawImageSlot (lazyflow.graph.InputSlot): raw image slot
            - additionalPluginArgumentsSlot (lazyflow.graph.InputSlot): slot containing a dictionary
                with plugin specific arguments

        :returns: True on success, False otherwise
        """

    @classmethod
    def _getFeatureNameTranslation(cls, category, name):
        """
        extract the long name of the given feature, or fall back to the plain name if no long name could be found

        :param category: The feature "group" or "plugin" (e.g. "Standard Object Features")
        :param name: The feature name string
        :returns: the long name of the feature
        """
        from ilastik.plugins.manager import plugin_manager

        all_props = None

        if category == "Default features":
            plugin = plugin_manager.get_object_feature_plugin_by_name("Standard Object Features")
        else:
            plugin = plugin_manager.get_object_feature_plugin_by_name(category)

        plugin_feature_names = {name: {}}
        all_props = plugin.fill_properties(plugin_feature_names)  # fill in display name and such

        if all_props:
            long_name = all_props[name]["displaytext"]
        else:
            long_name = name

        return long_name
