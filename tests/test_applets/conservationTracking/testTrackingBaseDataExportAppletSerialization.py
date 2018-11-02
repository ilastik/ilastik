import os

import h5py
from lazyflow.graph import Graph
from lazyflow.operator import Operator

import ilastik
from ilastik.applets.tracking.base.trackingBaseDataExportApplet import TrackingBaseDataExportApplet


class OpFake(Operator):
    def __init__(self, *args, **kwargs):
        super(OpFake, self).__init__(*args, **kwargs)


class TestTrackingBaseDataExportAppletSerialization(object):
    ilastik_tests_file_path = os.path.join(os.path.split(os.path.realpath(ilastik.__file__))[0], "../tests/")
    TEST_PROJECT_FILE = os.path.join(ilastik_tests_file_path, 'test_tracking_project.ilp')

    def tearDown(self):
        os.remove(self.TEST_PROJECT_FILE)

    def testAppletSerialization(self):
        g = Graph()
        op = OpFake(graph=g)
        dataExportApplet = TrackingBaseDataExportApplet(op, "Tracking Result Export")
        dataExportSerializer = dataExportApplet.dataSerializers[0]

        with h5py.File(self.TEST_PROJECT_FILE) as testProject:
            opTrackingBaseDataExport = dataExportApplet.topLevelOperator
            opTrackingBaseDataExport.SelectedPlugin.setValue('Fiji-MaMuT')
            opTrackingBaseDataExport.SelectedExportSource.setValue('Plugin')
            opTrackingBaseDataExport.AdditionalPluginArguments.setValue({'bdvFilePath': '/tmp/bdv.xml'})

            dataExportSerializer.serializeToHdf5(testProject, self.TEST_PROJECT_FILE)

        # check serialized values
        with h5py.File(self.TEST_PROJECT_FILE) as testProject:
            assert testProject["Tracking Result Export/SelectedPlugin"].value.decode() == 'Fiji-MaMuT'
            assert testProject["Tracking Result Export/SelectedExportSource"].value.decode() == 'Plugin'
            assert testProject["Tracking Result Export/AdditionalPluginArguments/bdvFilePath"].value.decode() == '/tmp/bdv.xml'

    def testAppletDeserialization(self):
        g = Graph()
        op = OpFake(graph=g)
        dataExportApplet = TrackingBaseDataExportApplet(op, "Tracking Result Export")
        dataExportSerializer = dataExportApplet.dataSerializers[0]

        with h5py.File(self.TEST_PROJECT_FILE) as testProject:
            # serialize TrackingBaseDataExportApplet's topLevelOperator
            opTrackingBaseDataExport = dataExportApplet.topLevelOperator
            opTrackingBaseDataExport.SelectedPlugin.setValue('Fiji-MaMuT')
            opTrackingBaseDataExport.SelectedExportSource.setValue('Plugin')
            opTrackingBaseDataExport.AdditionalPluginArguments.setValue({'bdvFilePath': '/tmp/bdv.xml'})
            dataExportSerializer.serializeToHdf5(testProject, self.TEST_PROJECT_FILE)

            # create new instance of TrackingBaseDataExportApplet and deserialize its topLevelOperator
            dataExportApplet = TrackingBaseDataExportApplet(op, "Tracking Result Export")
            dataExportSerializer = dataExportApplet.dataSerializers[0]
            dataExportSerializer.deserializeFromHdf5(testProject, self.TEST_PROJECT_FILE)
            # check deserialized values in applet's topLevelOperator
            assert dataExportSerializer.topLevelOperator.SelectedPlugin.value == 'Fiji-MaMuT'
            assert dataExportSerializer.topLevelOperator.SelectedExportSource.value == 'Plugin'
            assert dataExportSerializer.topLevelOperator.AdditionalPluginArguments.value['bdvFilePath'] == '/tmp/bdv.xml'



if __name__ == "__main__":
    import nose

    nose.main(defaultTest=__file__)
