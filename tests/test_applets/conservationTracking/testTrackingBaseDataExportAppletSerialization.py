from typing import Mapping, Any

import h5py

import pytest
from ilastik.applets.tracking.base.trackingBaseDataExportApplet import TrackingBaseDataExportApplet
from lazyflow.graph import Graph
from lazyflow.operator import Operator


@pytest.fixture
def project_path(tmp_path):
    op = Operator(graph=Graph())
    dataExportApplet = TrackingBaseDataExportApplet(op, "Tracking Result Export")
    dataExportSerializer = dataExportApplet.dataSerializers[0]

    opTrackingBaseDataExport = dataExportApplet.topLevelOperator
    opTrackingBaseDataExport.SelectedPlugin.setValue("Fiji-MaMuT")
    opTrackingBaseDataExport.SelectedExportSource.setValue("Plugin")
    opTrackingBaseDataExport.AdditionalPluginArguments.setValue({"bdvFilePath": "/tmp/bdv.xml"})

    path = tmp_path / "test_tracking_project.ilp"

    with h5py.File(path) as project:
        dataExportSerializer.serializeToHdf5(project, path)

    return path


def test_applet_serialization(project_path):
    with h5py.File(project_path) as project:
        assert project["Tracking Result Export/SelectedPlugin"].value.decode() == "Fiji-MaMuT"
        assert project["Tracking Result Export/SelectedExportSource"].value.decode() == "Plugin"
        assert (
            project["Tracking Result Export/AdditionalPluginArguments/bdvFilePath"].value.decode() == "/tmp/bdv.xml"
        )


def test_applet_deserialization(project_path):
    op = Operator(graph=Graph())
    dataExportApplet = TrackingBaseDataExportApplet(op, "Tracking Result Export")
    dataExportSerializer = dataExportApplet.dataSerializers[0]

    with h5py.File(project_path) as project:
        dataExportSerializer.deserializeFromHdf5(project, project_path)

    assert dataExportSerializer.topLevelOperator.SelectedPlugin.value == "Fiji-MaMuT"
    assert dataExportSerializer.topLevelOperator.SelectedExportSource.value == "Plugin"
    assert dataExportSerializer.topLevelOperator.AdditionalPluginArguments.value["bdvFilePath"] == "/tmp/bdv.xml"
