from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager

import os
from collections import namedtuple

from functools import partial

# these directories are searched for plugins
# TODO: perhaps these should be set in the config file.
plugins_paths = ("~/.ilastik/plugins",
                 os.path.join(os.path.split(__file__)[0], "plugins_default"),
                 )

##########################
# different plugin types #
##########################

class ObjectFeaturesPlugin(IPlugin):
    """Plugins of this class calculate object features"""
    name = "Base object features plugin"

    # TODO for now, only one margin will be set in the dialog. however, it
    # should be repeated for each feature, because in the future it
    # might be different, or each feature might take other parameters.

    def __init__(self, *args, **kwargs):
        super(ObjectFeaturesPlugin, self).__init__(*args, **kwargs)
        self._selectedFeatures = []

    def availableFeatures(self, image, labels):
        """returns a list of (feature name, feature parameters)"""
        return []

    def compute_global(self, image, labels, features, axes):
        """calculate the requested features.

        Params:
        ------
        image: np.ndarray
        labels: np.ndarray of ints
        axes: axis tags

        Returns: a dictionary with one entry per feature.
        key: feature name
        value: numpy.ndarray with ndim=2 and shape[0] == number of objects

        """
        return dict()

    def compute_local(self, image, binary_img, features, extent, axes):
        """calculate requested features on a single object.

        Params:
        ------
        image: np.ndarray - image[expanded bounding box]
        binary_img: binarize(labels[expanded bounding box])
        extent: actual object extent in bounding box
        axes: axis tags

        extend currently used for the slice-wise distance transform in anna's features

        Returns: a dictionary with one entry per feature.
        key: feature name
        value: numpy.ndarray with ndim=1

        """
        return dict()

    @staticmethod
    def combine_dicts(ds):
        return dict(sum((d.items() for d in ds), []))

    @staticmethod
    def update_keys(d, prefix=None, suffix=None):
        if prefix is None:
            prefix = ''
        if suffix is None:
            suffix = ''
        return dict((prefix + k + suffix, v) for k, v in d.items())

    def do_channels(self, fn, image, axes, **kwargs):
        """helper for features that only take one channel."""
        results = []
        slc = [slice(None)] * 4
        for channel in range(image.shape[axes.c]):
            slc[axes.c] = channel
            result = fn(image[slc], axes=axes, **kwargs)
            results.append(self.update_keys(result, suffix='_channel_{}'.format(channel)))
        return self.combine_dicts(results)


###############
# the manager #
###############

pluginManager = PluginManager()
pluginManager.setPluginPlaces(plugins_paths)

pluginManager.setCategoriesFilter({
   "ObjectFeatures" : ObjectFeaturesPlugin,
   })

pluginManager.collectPlugins()
for pluginInfo in pluginManager.getAllPlugins():
    pluginManager.activatePluginByName(pluginInfo.name)
