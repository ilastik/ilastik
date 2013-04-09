from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager

import os
from collections import namedtuple

# these directories are searched for plugins
# TODO: perhaps these should be set in the config file.
plugins_paths = ("~/.ilastik/plugins",
                 os.path.join(os.path.split(__file__)[0], "plugins"),
                 )

##########################
# different plugin types #
##########################

class ObjectFeaturesPlugin(IPlugin):
    """Plugins of this class calculate object features"""
    name = "Base object features plugin"

    def availableFeatures(self):
        """returns a list of feature names supported by this plugin."""
        return []

    def execute(self, image, labels, features):
        """calculate the requested features.

        Params:
        ------
        image: np.ndarray
        labels: np.ndarray of ints
        features: list of feature names.

        Returns: a dictionary with one entry per feature.
        key: feature name
        value: numpy.ndarray with ndim=2 and shape[0] == number of objects

        """
        return dict()

    def execute_local(self, image, features, axes, min_xyz, max_xyz,
                      rawbbox, passed, ccbboxexcl, ccbboxobject):
        """calculate requested features on a single object.

        Params:
        ------
        image: np.ndarray
        features: np.ndarray of ints
        axes:
        min_xyz:
        max_xyz:
        rawbox:
        passed:
        ccbbboxexcl:
        ccbboxobject:

        Returns: a dictionary with one entry per feature.
        key: feature name
        value: numpy.ndarray with ndim=1

        """
        return dict()

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
