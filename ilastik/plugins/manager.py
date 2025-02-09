###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################
import os
import sys
from collections import namedtuple

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

from yapsy.PluginManager import PluginManager

from ilastik.config import cfg

from .types import ObjectFeaturesPlugin, TrackingExportFormatPlugin

# these directories are searched for plugins
plugin_paths = cfg.ilastik.plugin_directories
plugin_paths = list(os.path.expanduser(d) for d in plugin_paths.split(",") if len(d) > 0)
plugin_paths.append(os.path.join(os.path.split(os.path.split(__file__)[0])[0], "plugins_default"))

# Add directories from registered entrypoints
for ep in entry_points(group="ilastik.objectfeatures"):
    plugin_paths.append(os.path.split(ep.load().__file__)[0])

# Helper class used to pass the necessary context information to the export plugin
PluginExportContext = namedtuple(
    "PluginExportContext", ["objectFeaturesSlot", "labelImageSlot", "rawImageSlot", "additionalPluginArgumentsSlot"]
)

###############
# the manager #
###############

pluginManager = PluginManager()
pluginManager.setPluginPlaces(plugin_paths)

pluginManager.setCategoriesFilter(
    {"ObjectFeatures": ObjectFeaturesPlugin, "TrackingExportFormats": TrackingExportFormatPlugin}
)

pluginManager.collectPlugins()
for pluginInfo in pluginManager.getAllPlugins():
    pluginManager.activatePluginByName(pluginInfo.name)
