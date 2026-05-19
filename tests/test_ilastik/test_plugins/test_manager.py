from unittest.mock import Mock

import pytest

from ilastik.plugins.manager import PluginManager, PluginNotFound, plugin_manager
from ilastik.plugins.types import ObjectFeaturesPlugin, TrackingExportFormatPlugin

A = object()
B = object()


def test_manager_instantiates_plugins():
    oc_mock = Mock(return_value=A)
    tr_mock = Mock(return_value=B)
    manager = PluginManager({"OC1": oc_mock}, {"TR1": tr_mock, "TR2": Mock()})

    oc_mock.assert_not_called()
    oc_plugin = manager.get_object_feature_plugin_by_name("OC1")
    assert oc_plugin == A
    oc_mock.assert_called_once()

    tr_mock.assert_not_called()
    tr_plugin = manager.get_tracking_export_plugin_by_name("TR1")
    assert tr_plugin == B
    tr_mock.assert_called_once()

    oc_plugins = manager.get_object_feature_plugins()
    assert len(oc_plugins) == 1
    assert oc_mock.call_count == 2

    tr_plugins = manager.get_tracking_export_plugins()
    assert len(tr_plugins) == 2
    assert tr_mock.call_count == 2


def test_manager_raises_when_plugin_not_found():
    manager = PluginManager({}, {})

    assert manager.get_object_feature_plugins() == []
    with pytest.raises(PluginNotFound):
        manager.get_object_feature_plugin_by_name("DoesNotExist")

    assert manager.get_tracking_export_plugins() == []
    with pytest.raises(PluginNotFound):
        manager.get_tracking_export_plugin_by_name("DoesNotExist")


def test_default_object_feature_plugins_found():
    oc_plugins = plugin_manager.get_object_feature_plugins()

    assert all(isinstance(p, ObjectFeaturesPlugin) for p in oc_plugins)

    expected_plugin_names = [
        "TestFeatures",
        "Standard Object Features",
        "2D Convex Hull Features",
        "3D Convex Hull Features",
        "2D Skeleton Features",
        "Spherical Texture",
    ]
    plugin_names = [p.plugin_info.name for p in oc_plugins]

    missing = []
    for plugin_name in expected_plugin_names:
        if not plugin_name in plugin_names:
            missing.append(plugin_name)

    assert not missing


def test_default_tracking_export_plugins_found():
    tr_plugins = plugin_manager.get_tracking_export_plugins()

    assert all(isinstance(p, TrackingExportFormatPlugin) for p in tr_plugins)

    expected_plugin_names = [
        "Contours",
        "Contours-With-Head",
        "CSV-Table",
        "CellTrackingChallenge",
        "H5-Event-Sequence",
        "JSON",
        "Fiji-MaMuT",
        "Multi-Worm-Tracker",
    ]
    plugin_names = [p.plugin_info.name for p in tr_plugins]

    missing = []
    for plugin_name in expected_plugin_names:
        if not plugin_name in plugin_names:
            missing.append(plugin_name)

    assert not missing
