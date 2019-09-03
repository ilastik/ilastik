from typing import Any, Mapping

import h5py

import pytest
from ilastik.applets.tracking.base.trackingBaseDataExportApplet import TrackingBaseDataExportApplet
from lazyflow.graph import Graph
from lazyflow.operator import Operator


@pytest.fixture
def project_path(tmp_path):
    return str(tmp_path / "test_tracking_project.ilp")


@pytest.fixture
def data_export_applet():
    op = Operator(graph=Graph())
    dataExportApplet = TrackingBaseDataExportApplet(op, "Tracking Result Export")

    opTrackingBaseDataExport = dataExportApplet.topLevelOperator
    opTrackingBaseDataExport.SelectedPlugin.setValue("Fiji-MaMuT")
    opTrackingBaseDataExport.SelectedExportSource.setValue("Plugin")
    opTrackingBaseDataExport.AdditionalPluginArguments.setValue({"bdvFilePath": "/tmp/bdv.xml"})

    return dataExportApplet


def test_applet_serialization(project_path, data_export_applet):
    with h5py.File(project_path) as project_file:
        data_export_applet.dataSerializers[0].serializeToHdf5(project_file, project_path)

    with h5py.File(project_path) as project_file:
        assert project_file["Tracking Result Export/SelectedPlugin"].value.decode() == "Fiji-MaMuT"
        assert project_file["Tracking Result Export/SelectedExportSource"].value.decode() == "Plugin"
        assert (
            project_file["Tracking Result Export/AdditionalPluginArguments/bdvFilePath"].value.decode()
            == "/tmp/bdv.xml"
        )


def test_applet_deserialization(project_path, data_export_applet):
    with h5py.File(project_path) as project_file:
        data_export_applet.dataSerializers[0].serializeToHdf5(project_file, project_path)

    op = Operator(graph=Graph())
    data_export_applet = TrackingBaseDataExportApplet(op, "Tracking Result Export")

    with h5py.File(project_path) as project_file:
        data_export_applet.dataSerializers[0].deserializeFromHdf5(project_file, project_path)

    opTrackingBaseDataExport = data_export_applet.dataSerializers[0].topLevelOperator
    assert opTrackingBaseDataExport.SelectedPlugin.value == "Fiji-MaMuT"
    assert opTrackingBaseDataExport.SelectedExportSource.value == "Plugin"
    assert opTrackingBaseDataExport.AdditionalPluginArguments.value["bdvFilePath"] == "/tmp/bdv.xml"
