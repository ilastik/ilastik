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
#          http://ilastik.org/license.html
###############################################################################
from collections import namedtuple
from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Type

from .types import ObjectFeaturesPlugin, TrackingExportFormatPlugin, PluginNotFound


@dataclass
class PluginManager:
    _object_feature_plugins: dict[str, Type[ObjectFeaturesPlugin]]
    _tracking_export_plugins: dict[str, Type[TrackingExportFormatPlugin]]

    def get_object_feature_plugins(self) -> list[ObjectFeaturesPlugin]:
        return [plugin() for plugin in self._object_feature_plugins.values()]

    def get_object_feature_plugin_by_name(self, name: str) -> ObjectFeaturesPlugin:
        if name not in self._object_feature_plugins:
            raise PluginNotFound(
                f"Could not find object feature plugin by {name=}. Available plugins: {', '.join(self._object_feature_plugins.keys())}"
            )
        return self._object_feature_plugins[name]()

    def get_tracking_export_plugins(self) -> list[TrackingExportFormatPlugin]:
        return [plugin() for plugin in self._tracking_export_plugins.values()]

    def get_tracking_export_plugin_by_name(self, name: str) -> TrackingExportFormatPlugin:
        if name not in self._tracking_export_plugins:
            raise PluginNotFound(
                f"Could not find tacking export plugin by {name=}. Available plugins: {', '.join(self._tracking_export_plugins.keys())}"
            )
        return self._tracking_export_plugins[name]()


object_classification_plugins: dict[str, Type[ObjectFeaturesPlugin]] = {}
for ep in entry_points(group="ilastik.objectfeature_plugins.default"):
    plugin_cls = ep.load()
    assert issubclass(plugin_cls, ObjectFeaturesPlugin)
    object_classification_plugins[plugin_cls.plugin_info.name] = plugin_cls

# third-party plugins
for ep in entry_points(group="ilastik.objectfeature_plugins"):
    plugin_cls = ep.load()
    assert issubclass(plugin_cls, ObjectFeaturesPlugin), f"Could not load plugin {ep.name} of type {plugin_cls}"
    object_classification_plugins[plugin_cls.plugin_info.name] = plugin_cls

tracking_plugins: dict[str, Type[TrackingExportFormatPlugin]] = {}
for ep in entry_points(group="ilastik.tracking_export_plugins.default"):
    plugin_cls = ep.load()
    assert issubclass(plugin_cls, TrackingExportFormatPlugin)
    tracking_plugins[plugin_cls.plugin_info.name] = plugin_cls

# third-party plugins
for ep in entry_points(group="ilastik.tracking_export_plugins"):
    plugin_cls = ep.load()
    assert issubclass(plugin_cls, TrackingExportFormatPlugin)
    tracking_plugins[plugin_cls.plugin_info.name] = plugin_cls

# Helper class used to pass the necessary context information to the export plugin
PluginExportContext = namedtuple(
    "PluginExportContext", ["objectFeaturesSlot", "labelImageSlot", "rawImageSlot", "additionalPluginArgumentsSlot"]
)

plugin_manager = PluginManager(object_classification_plugins, tracking_plugins)
