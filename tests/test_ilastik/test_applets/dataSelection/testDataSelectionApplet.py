from unittest import mock

from ilastik.applets.dataSelection import DataSelectionApplet
from lazyflow.operator import Operator


class MockSignal:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback

    def emit(self, *args, **kwargs):
        self.callback(*args, **kwargs)


def test_locks_scale_upon_applet_change(graph):
    workflow = Operator(graph=graph)
    workflow.shell = mock.Mock()
    workflow.shell.currentAppletChanged = MockSignal()
    applet = DataSelectionApplet(workflow, "Input Data", "Input Data")
    workflow.applets = [applet, None]
    dataset_info = mock.Mock()
    dataset_info.scale_locked = False
    applet.topLevelOperator.DatasetRoles.setValue(["Raw Data"])
    applet.topLevelOperator.DatasetGroup.resize(1)
    applet.topLevelOperator.DatasetGroup[0, 0].setValue(dataset_info)

    workflow.shell.currentAppletChanged.emit(0, 0)
    assert not dataset_info.scale_locked

    workflow.shell.currentAppletChanged.emit(0, 1)
    assert dataset_info.scale_locked
