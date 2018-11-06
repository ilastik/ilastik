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
from ilastik.config import cfg

from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager

import os
from collections import namedtuple
from functools import partial
import numpy

# these directories are searched for plugins
plugin_paths = cfg.get('ilastik', 'plugin_directories')
plugin_paths = list(os.path.expanduser(d) for d in plugin_paths.split(',')
                    if len(d) > 0)
plugin_paths.append(os.path.join(os.path.split(__file__)[0], "plugins_default"))

##########################
# different plugin types #
##########################

class ObjectFeaturesPlugin(IPlugin):
    """Plugins of this class calculate object features."""

    name = "Base object features plugin"

    # TODO for now, only one margin will be set in the dialog. however, it
    # should be repeated for each feature, because in the future it
    # might be different, or each feature might take other parameters.

    def __init__(self, *args, **kwargs):
        super(ObjectFeaturesPlugin, self).__init__(*args, **kwargs)
        self._selectedFeatures = []

    def availableFeatures(self, image, labels):
        """Reports which features this plugin can compute on a
        particular image and label image.

        :param image: numpy.ndarray
        :param labels: numpy.ndarray, dtype=int
        :returns: a nested dictionary, where dict[feature_name] is a
            dictionary of parameters.

        """
        return []

    def compute_global(self, image, labels, features, axes):

        """calculate the requested features.

        :param image: np.ndarray
        :param labels: np.ndarray, dtype=int
        :param features: which features to compute
        :param axes: axis tags

        :returns: a dictionary with one entry per feature.
            dict[feature_name] is a numpy.ndarray with ndim=2 and
            shape[0] == number of objects

        """
        return dict()

    def compute_local(self, image, binary_bbox, features, axes):
        """Calculate features on a single object.

        :param image: np.ndarray - image[expanded bounding box]
        :param binary_bbox: binarize(labels[expanded bounding box])
        :param features: which features to compute
        :param axes: axis tags

        :returns: a dictionary with one entry per feature.
            dict[feature_name] is a numpy.ndarray with ndim=1

        """
        return dict()

    def fill_properties(self, feature_dict):
        """
        For every feature in the feature dictionary, fill in its properties,
        such as 'detailtext', which will be displayed in help, or 'displaytext'
        which will be displayed instead of the feature name
        Args:
            feature_dict: dictionary of features

        Returns:
            same dictionary, with additional fields filled for each feature

        """
        return feature_dict

    @staticmethod
    def combine_dicts(ds):
        return dict(sum((list(d.items()) for d in ds), []))

    @staticmethod
    def combine_dicts_with_numpy(ds):
        #stack arrays which correspond to the same keys
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
            prefix = ''
        if suffix is None:
            suffix = ''
        return dict((prefix + k + suffix, v) for k, v in list(d.items()))

    def do_channels(self, fn, image, axes, **kwargs):
        """Helper for features that only take one channel.

        :param fn: function that computes features

        """
        results = []
        slc = [slice(None)] * 4
        for channel in range(image.shape[axes.c]):
            slc[axes.c] = channel
            #a dictionary for the channel
            result = fn(image[slc], axes=axes, **kwargs)
            results.append(result)
        
        return self.combine_dicts_with_numpy(results)

class TrackingExportFormatPlugin(IPlugin):
    """Plugins of this class can export a tracking solution."""

    name = "Base Tracking export format plugin"
    exportsToFile = True # depending on this setting, the user can choose a file or a folder where to export 

    def __init__(self, *args, **kwargs):
        super(TrackingExportFormatPlugin, self).__init__(*args, **kwargs)

    def checkFilesExist(self, filename):
        ''' Check whether the files we want to export (when appending the base filename) are already present '''
        return False

    def export(self, filename, hypothesesGraph, pluginExportContext):
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
        return False

    @classmethod
    def _getFeatureNameTranslation(cls, category, name):
        '''
        extract the long name of the given feature, or fall back to the plain name if no long name could be found

        :param category: The feature "group" or "plugin" (e.g. "Standard Object Features")
        :param name: The feature name string
        :returns: the long name of the feature
        '''
        all_props = None

        if category == 'Default features':
            plugin = pluginManager.getPluginByName("Standard Object Features", "ObjectFeatures")
        else:
            plugin = pluginManager.getPluginByName(category, "ObjectFeatures")
        if plugin:
            plugin_feature_names = {name: {}}
            all_props = plugin.plugin_object.fill_properties(plugin_feature_names)  # fill in display name and such

        if all_props:
            long_name = all_props[name]["displaytext"]
        else:
            long_name = name

        return long_name


# Helper class used to pass the necessary context information to the export plugin
PluginExportContext = namedtuple('PluginExportContext',
                                 [
                                     'objectFeaturesSlot',
                                     'labelImageSlot',
                                     'rawImageSlot',
                                     'additionalPluginArgumentsSlot'
                                 ])

###############
# the manager #
###############

pluginManager = PluginManager()
pluginManager.setPluginPlaces(plugin_paths)

pluginManager.setCategoriesFilter({
   "ObjectFeatures" : ObjectFeaturesPlugin,
   "TrackingExportFormats": TrackingExportFormatPlugin
   })

pluginManager.collectPlugins()
for pluginInfo in pluginManager.getAllPlugins():
    pluginManager.activatePluginByName(pluginInfo.name)
