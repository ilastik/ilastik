import h5py

import pytest
from ilastik.applets.tracking.base.trackingBaseDataExportApplet import TrackingBaseDataExportApplet
from lazyflow.graph import Graph
from lazyflow.operator import Operator


@pytest.fixture
def project_file(tmp_path):
    return tmp_path / "test_tracking_project.ilp"


def test_applet_serialization(project_file):
    g = Graph()
    op = Operator(graph=g)
    dataExportApplet = TrackingBaseDataExportApplet(op, "Tracking Result Export")
    dataExportSerializer = dataExportApplet.dataSerializers[0]

    with h5py.File(project_file) as testProject:
        opTrackingBaseDataExport = dataExportApplet.topLevelOperator
        opTrackingBaseDataExport.SelectedPlugin.setValue("Fiji-MaMuT")
        opTrackingBaseDataExport.SelectedExportSource.setValue("Plugin")
        opTrackingBaseDataExport.AdditionalPluginArguments.setValue({"bdvFilePath": "/tmp/bdv.xml"})

        dataExportSerializer.serializeToHdf5(testProject, project_file)

    # check serialized values
    with h5py.File(project_file) as testProject:
        assert testProject["Tracking Result Export/SelectedPlugin"].value.decode() == "Fiji-MaMuT"
        assert testProject["Tracking Result Export/SelectedExportSource"].value.decode() == "Plugin"
        assert (
            testProject["Tracking Result Export/AdditionalPluginArguments/bdvFilePath"].value.decode() == "/tmp/bdv.xml"
        )


def test_applet_deserialization(project_file):
    g = Graph()
    op = Operator(graph=g)
    dataExportApplet = TrackingBaseDataExportApplet(op, "Tracking Result Export")
    dataExportSerializer = dataExportApplet.dataSerializers[0]

    with h5py.File(project_file) as testProject:
        # serialize TrackingBaseDataExportApplet's topLevelOperator
        opTrackingBaseDataExport = dataExportApplet.topLevelOperator
        opTrackingBaseDataExport.SelectedPlugin.setValue("Fiji-MaMuT")
        opTrackingBaseDataExport.SelectedExportSource.setValue("Plugin")
        opTrackingBaseDataExport.AdditionalPluginArguments.setValue({"bdvFilePath": "/tmp/bdv.xml"})
        dataExportSerializer.serializeToHdf5(testProject, project_file)

        # create new instance of TrackingBaseDataExportApplet and deserialize its topLevelOperator
        dataExportApplet = TrackingBaseDataExportApplet(op, "Tracking Result Export")
        dataExportSerializer = dataExportApplet.dataSerializers[0]
        dataExportSerializer.deserializeFromHdf5(testProject, project_file)
        # check deserialized values in applet's topLevelOperator
        assert dataExportSerializer.topLevelOperator.SelectedPlugin.value == "Fiji-MaMuT"
        assert dataExportSerializer.topLevelOperator.SelectedExportSource.value == "Plugin"
        assert dataExportSerializer.topLevelOperator.AdditionalPluginArguments.value["bdvFilePath"] == "/tmp/bdv.xml"
