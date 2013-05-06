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

    @staticmethod
    def combine_dicts(ds):
        return dict(sum((d.items() for d in ds), []))

    @staticmethod
    def combine_dicts_with_numpy(ds):
        #stack arrays which correspond to the same keys
        keys = ds[0].keys()
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
        return dict((prefix + k + suffix, v) for k, v in d.items())

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


###############
# the manager #
###############

pluginManager = PluginManager()
pluginManager.setPluginPlaces(plugin_paths)

pluginManager.setCategoriesFilter({
   "ObjectFeatures" : ObjectFeaturesPlugin,
   })

pluginManager.collectPlugins()
for pluginInfo in pluginManager.getAllPlugins():
    pluginManager.activatePluginByName(pluginInfo.name)
