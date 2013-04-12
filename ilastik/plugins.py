from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager

import os
from collections import namedtuple

from functools import partial

# these directories are searched for plugins
# TODO: perhaps these should be set in the config file.
plugins_paths = ("~/.ilastik/plugins",
                 os.path.join(os.path.split(__file__)[0], "default_plugins"),
                 )

##########################
# different plugin types #
##########################

class ObjectFeaturesPlugin(IPlugin):
    """Plugins of this class calculate object features"""
    name = "Base object features plugin"

    def availableFeatures(self, image, labels):
        """returns a list of feature names supported by this plugin."""
        return []

    def compute_global(self, image, labels, features, axes):
        """calculate the requested features.

        Params:
        ------
        image: np.ndarray
        labels: np.ndarray of ints
        features: list of feature names.
        axes:

        Returns: a dictionary with one entry per feature.
        key: feature name
        value: numpy.ndarray with ndim=2 and shape[0] == number of objects

        """
        return dict()

    def compute_local(self, image, label_bboxes, axes, mins, maxs):
        """calculate requested features on a single object.

        Params:
        ------
        image: np.ndarray
        label_bboxes: labels for object, object+context, context
        features: np.ndarray of ints
        axes:
        mins:
        maxs:

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

    def do_channels(self, image, labels, features, axes, fn, **kwargs):
        """helper for features that only take one channel."""
        results = []
        slc = [slice(None)] * 4
        for channel in range(image.shape[axes.c]):
            slc[axes.c] = channel
            result = fn(image[slc], labels, features, axes, **kwargs)
            results.append(self.update_keys(result, suffix='_channel_{}'.format(channel)))
        return self.combine_dicts(results)

    def do_local(self, image, label_bboxes, features, axes, mins, maxs, fn, **kwargs):
        """helper that deals with individual objects"""
        results = []
        for label, suffix in zip(label_bboxes, ['', '_incl', '_excl']):
            result = fn(image, label, features, axes, mins=mins, maxs=maxs, **kwargs)
            results.append(self.update_keys(result, suffix=suffix))
        return self.combine_dicts(results)

    def do_local_channels(self, image, label_bboxes, features, axes, mins, maxs, fn, **kwargs):
        """combines both do_channels() and do_local()"""
        newfn = partial(self.do_channels, fn=fn)
        self.do_local(image, label_bboxes, features, axes, mins, maxs, newfn, **kwargs)


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
