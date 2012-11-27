import os
import numpy
import numpy.testing
import h5py
import vigra
import unittest
import shutil
import tempfile
from lazyflow.roi import roiToSlice
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow.operators import OpTrainRandomForestBlocked, OpValueCache

from ilastik.applets.base.appletSerializer import SerialSlot, AppletSerializer

class OpMock(Operator):
    """A simple operator for testing serializers."""
    name = "OpMock"
    TestSlot = InputSlot(name="TestSlot")
    TestMultiSlot = InputSlot(name="TestMultiSlot", level=1)

    def __init__(self, *args, **kwargs):
        super(OpMock, self).__init__(*args, **kwargs)

    def propagateDirty(self, slot, subindex, roi):
        pass


class OpMockSerializer(AppletSerializer):
    SerializerVersion = 0.1
    def __init__(self, operator, groupName):
        slots = [SerialSlot(operator.TestSlot),
                 SerialSlot(operator.TestMultiSlot)]
        super(OpMockSerializer, self).__init__(groupName,
                                               self.SerializerVersion,
                                               slots)


def randArray():
    return numpy.random.randn(10, 10)


class TestSerializer(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.operator = OpMock(graph=g)
        self.serializer = OpMockSerializer(self.operator,"TestApplet")
        self.tmpDir = tempfile.mkdtemp()
        self.projectFilePath = os.path.join(self.tmpDir, "tmp_project.ilp")
        self.projectFile = h5py.File(self.projectFilePath)
        self.projectFile.create_dataset("ilastikVersion", data=0.6)

    def tearDown(self):
        self.projectFile.close()
        shutil.rmtree(self.tmpDir)

    def testSlot(self):
        """test whether serialzing and then deserializing works for a
        level-0 slot

        """
        value = randArray()
        rvalue = randArray()
        slot = self.operator.TestSlot
        ss = self.serializer.serialSlots[0]
        slot.setValue(value)
        self.assertTrue(ss.dirty)
        self.serializer.serializeToHdf5(self.projectFile, self.projectFilePath)
        self.assertTrue(not ss.dirty)
        slot.setValue(rvalue)
        self.assertTrue(ss.dirty)
        self.assertTrue(numpy.any(slot.value != value))
        self.serializer.deserializeFromHdf5(self.projectFile, self.projectFilePath)
        self.assertTrue(numpy.all(slot.value == value))
        self.assertTrue(not ss.dirty)

    def testMultiSlot(self):
        """test whether serialzing and then deserializing works for a
        level-1 slot

        """
        value = randArray()
        rvalue = randArray()
        mslot = self.operator.TestMultiSlot
        mss = self.serializer.serialSlots[1]
        mslot.resize(1)
        mslot[0].setValue(value)
        self.assertTrue(mss.dirty)
        self.serializer.serializeToHdf5(self.projectFile, self.projectFilePath)
        self.assertTrue(not mss.dirty)
        mslot[0].setValue(rvalue)
        self.assertTrue(mss.dirty)
        self.assertTrue(numpy.any(mslot[0].value != value))
        self.serializer.deserializeFromHdf5(self.projectFile, self.projectFilePath)
        self.assertTrue(numpy.all(mslot[0].value == value))
        self.assertTrue(not mss.dirty)


if __name__ == "__main__":
    unittest.main()