###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
#		   http://ilastik.org/license.html
###############################################################################
import os
import h5py
import numpy
import vigra
import unittest
import shutil
import tempfile
from copy import deepcopy
from ilastik.applets.base.appletSerializer import SerialObjectFeatureNamesSlot
from lazyflow.graph import Graph, Operator, InputSlot, Slot, OperatorWrapper
from lazyflow.operators import OpCompressedUserLabelArray
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.stype import Opaque
from lazyflow.rtype import List

from ilastik.applets.base.appletSerializer import \
    getOrCreateGroup, deleteIfPresent, \
    SerialSlot, SerialListSlot, AppletSerializer, SerialDictSlot, SerialBlockSlot

class OpMock(Operator):
    """A simple operator for testing serializers."""
    name = "OpMock"
    TestSlot = InputSlot(name="TestSlot")
    TestMultiSlot = InputSlot(name="TestMultiSlot", level=1)
    TestListSlot = InputSlot(name='TestListSlot')
    OpaqueListSlot = InputSlot(rtype=List, stype=Opaque)

    def __init__(self, *args, **kwargs):
        super(OpMock, self).__init__(*args, **kwargs)

    def propagateDirty(self, slot, subindex, roi):
        pass


class OpMockSerializer(AppletSerializer):
    def __init__(self, operator, groupName):
        self.TestSerialSlot = SerialSlot(operator.TestSlot)
        self.TestMultiSerialSlot = SerialSlot(operator.TestMultiSlot)
        self.TestSerialListSlot = SerialListSlot(operator.TestListSlot,
                                                 selfdepends=True)
        slots = (self.TestSerialSlot,
                 self.TestMultiSerialSlot,
                 self.TestSerialListSlot)
        super(OpMockSerializer, self).__init__(groupName,
                                               slots)


def randArray():
    return numpy.random.randn(10, 10)


class TestHDF5HelperFunctions(unittest.TestCase):
    def setUp(self):
        self.tmpDir = tempfile.mkdtemp()
        self.tmpFile = h5py.File(os.path.join(self.tmpDir, "test.h5"), "a")
        self.tmpFile.create_group("a")
        self.tmpFile.create_dataset("c", (2,2), dtype=numpy.int)

    def test_getOrCreateGroup_1(self):
        self.assertTrue("a" in self.tmpFile)
        self.assertTrue(isinstance(self.tmpFile["a"], h5py.Group))

        group = getOrCreateGroup(self.tmpFile, "a")

        self.assertEqual(group.name, "/a")
        self.assertTrue("a" in self.tmpFile)
        self.assertTrue(isinstance(self.tmpFile["a"], h5py.Group))

    def test_getOrCreateGroup_2(self):
        self.assertTrue("b" not in self.tmpFile)

        group = getOrCreateGroup(self.tmpFile, "b")

        self.assertEqual(group.name, "/b")
        self.assertTrue("b" in self.tmpFile)
        self.assertTrue(isinstance(self.tmpFile["b"], h5py.Group))

    def test_getOrCreateGroup_3(self):
        self.assertTrue("c" in self.tmpFile)
        self.assertTrue(isinstance(self.tmpFile["c"], h5py.Dataset))

        self.assertRaises(TypeError, lambda : getOrCreateGroup(self.tmpFile, "c"))

        self.assertTrue("c" in self.tmpFile)
        self.assertTrue(isinstance(self.tmpFile["c"], h5py.Dataset))

    def test_deleteIfPresent_1(self):
        self.assertTrue("a" in self.tmpFile)

        deleteIfPresent(self.tmpFile, "a")

        self.assertTrue("a" not in self.tmpFile)

    def test_deleteIfPresent_2(self):
        self.assertTrue("b" not in self.tmpFile)

        deleteIfPresent(self.tmpFile, "b")

        self.assertTrue("b" not in self.tmpFile)

    def tearDown(self):
        self.tmpFile.close()
        shutil.rmtree(self.tmpDir)


class TestSerializer(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.operator = OpMock(graph=g)
        self.serializer = OpMockSerializer(self.operator, "TestApplet")
        self.tmpDir = tempfile.mkdtemp()
        self.projectFilePath = os.path.join(self.tmpDir, "tmp_project.ilp")
        self.projectFile = h5py.File(self.projectFilePath)
        self.projectFile.create_dataset("ilastikVersion", data=b'1.0.0')

    def tearDown(self):
        self.projectFile.close()
        shutil.rmtree(self.tmpDir)

    def _testSlot(self, slot, ss, value, rvalue):
        """test whether serialzing and then deserializing works for a
        level-0 slot

        """
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

    def _testMultiSlot(self, mslot, mss, values, rvalues):
        """test whether serializing and then deserializing works for a
        level-1 slot

        """
        mslot.resize(len(values))
        for subslot, value in zip(mslot, values):
            subslot.setValue(value)
        if len(mslot) > 0:
            self.assertTrue(mss.dirty)
        self.serializer.serializeToHdf5(self.projectFile, self.projectFilePath)
        if len(mslot) > 0:
            self.assertFalse(mss.dirty)

        mslot.resize(len(rvalues))
        for subslot, value in zip(mslot, rvalues):
            subslot.setValue(value)
        if len(mslot) > 0:
            self.assertTrue(mss.dirty)

        for subslot, value in zip(mslot, values):
            self.assertTrue(numpy.any(subslot.value != value))

        self.serializer.deserializeFromHdf5(self.projectFile, self.projectFilePath)
        for subslot, value in zip(mslot, values):
            self.assertTrue(numpy.all(subslot.value == value))

        # If the multi-slot started with MORE subslots than were stored in the project file,
        #  the extra subslots are NOT removed.  Instead, they are simply disconnected.
        # Verify that the the number of ready() slots matches the number we attempted to save.
        ready_subslots = list(filter(Slot.ready, mss.slot))
        self.assertEqual(len(ready_subslots), len(values))

        self.assertFalse(mss.dirty)

    def _testList(self, slot, ss, value, rvalue):
        """test whether serialzing and then deserializing works for a
        list slot.

        """
        slot.setValue(value)
        self.assertTrue(ss.dirty)
        self.serializer.serializeToHdf5(self.projectFile, self.projectFilePath)
        self.assertTrue(not ss.dirty)

        slot.setValue(rvalue)
        self.assertTrue(ss.dirty)
        self.assertTrue(slot.value != value)

        self.serializer.deserializeFromHdf5(self.projectFile, self.projectFilePath)
        self.assertTrue(slot.value == value)
        self.assertTrue(not ss.dirty)

    def testSlot(self):
        slot = self.operator.TestSlot
        ss = self.serializer.TestSerialSlot
        self._testSlot(slot, ss, randArray(), randArray())

    def testMultiSlot10(self):
        slot = self.operator.TestMultiSlot
        ss = self.serializer.TestMultiSerialSlot
        self._testMultiSlot(slot, ss, [randArray()], [])

    def testMultiSlot01(self):
        slot = self.operator.TestMultiSlot
        ss = self.serializer.TestMultiSerialSlot

        # FIXME: test fails because multislot is not set to length 0
        # upon deserialization.

        # self._testMultiSlot(slot, ss, [], [randArray()])

    def testMultiSlot11(self):
        slot = self.operator.TestMultiSlot
        ss = self.serializer.TestMultiSerialSlot
        self._testMultiSlot(slot, ss, [randArray()], [randArray()])

    def testMultiSlot22(self):
        slot = self.operator.TestMultiSlot
        ss = self.serializer.TestMultiSerialSlot
        self._testMultiSlot(slot, ss,
                            [randArray(), randArray()],
                            [randArray(), randArray()],)

    def testMultiSlot12(self):
        slot = self.operator.TestMultiSlot
        ss = self.serializer.TestMultiSerialSlot
        self._testMultiSlot(slot, ss,
                            [randArray()],
                            [randArray(), randArray()],)

    def testMultiSlot21(self):
        slot = self.operator.TestMultiSlot
        ss = self.serializer.TestMultiSerialSlot
        self._testMultiSlot(slot, ss,
                            [randArray(), randArray()],
                            [randArray()],)

    def testList01(self):
        slot = self.operator.TestListSlot
        ss = self.serializer.TestSerialListSlot
        self._testList(slot, ss, [], [1, 2, 3])

    def testList10(self):
        slot = self.operator.TestListSlot
        ss = self.serializer.TestSerialListSlot
        self._testList(slot, ss, [4, 5, 6], [])

    def testList11(self):
        slot = self.operator.TestListSlot
        ss = self.serializer.TestSerialListSlot
        self._testList(slot, ss, [7, 8, 9], [10, 11, 12])

class TestSerialDictSlot(unittest.TestCase):
    
    class OpWithDictSlot(Operator):
        InputDict = InputSlot()

        def setupOutputs(self):
            pass
        
        def execute(self, *args, **kwargs):
            pass
        
        def propagateDirty(self, *args, **kwargs):
            pass
    
    class SerializerForOpWithDictSlot(AppletSerializer):
        def __init__(self, operator, groupName):
            self.ss = SerialDictSlot( operator.InputDict )
            super(TestSerialDictSlot.SerializerForOpWithDictSlot, self).__init__(groupName, [self.ss])
        
    
    def setUp(self):
        g = Graph()
        self.operator = self.OpWithDictSlot(graph=g)
        self.serializer = self.SerializerForOpWithDictSlot(self.operator, "TestApplet")
        self.tmpDir = tempfile.mkdtemp()
        self.projectFilePath = os.path.join(self.tmpDir, "tmp_project.ilp")
        self.projectFile = h5py.File(self.projectFilePath)
        self.projectFile.create_dataset("ilastikVersion", data=b'0.6')

    def tearDown(self):
        self.projectFile.close()
        shutil.rmtree(self.tmpDir)

    def testBasic(self):
        op = self.operator
        ss = self.serializer.ss
        d = {'a' : 'A', 'b' : 'B'}
        op.InputDict.setValue( d )
        
        self.assertTrue( ss.dirty )
        self.serializer.serializeToHdf5(self.projectFile, self.projectFilePath)
        self.assertFalse( ss.dirty )

        # Verify that the values are read back.
        d.clear()
        self.serializer.deserializeFromHdf5(self.projectFile, self.projectFilePath)
        d_read = op.InputDict.value
        self.assertTrue( d_read['a'] == 'A' )
        self.assertTrue( d_read['b'] == 'B' )

        d2 = {'a' : 'A', 'b' : 'B', 'c' : 'C'}
        op.InputDict.setValue( d2 )

        self.assertTrue( ss.dirty )
        self.serializer.serializeToHdf5(self.projectFile, self.projectFilePath)
        self.assertFalse( ss.dirty )
        
        # Verify that the values are read back.
        del d2['b'] # Touch the dict so we know the values are really being read from the file.
        #d2.clear()
        self.assertTrue( len(op.InputDict.value) == 2 )
        self.serializer.deserializeFromHdf5(self.projectFile, self.projectFilePath)
        d2_read = op.InputDict.value
        self.assertTrue( d2_read['a'] == 'A' )
        self.assertTrue( d2_read['b'] == 'B' )
        self.assertTrue( d2_read['c'] == 'C' )

class TestSerialObjectFeatureNamesSlot(unittest.TestCase):
    def setUp(self):
        self.mockInput = {
            "Standard Object Features": {
                "Coord<Principal<Kurtosis>>": {},
                "Coord<Principal<Skewness>>": {},
                "Count": {},
                "Kurtosis": {},
                "Maximum": {},
                "Mean": {},
                "Minimum": {},
                "Quantiles": {"something": 123456},
                "RegionCenter": {},
                "RegionRadii": {},
                "Skewness": {},
                "Sum": {},
                "Variance": {}
            }
        }
        self.legacyMockInput = {'0': deepcopy(self.mockInput)}
        self.operator = OpMock(graph=Graph())
        self.objFeaturesNameSlot = self.operator.OpaqueListSlot
        self.serializer = SerialObjectFeatureNamesSlot(self.objFeaturesNameSlot)
        self.testFilePath = os.path.join(tempfile.gettempdir(), 'objFeatureNames.h5')


    def testSerialization(self):
        for inp in (self.mockInput, self.legacyMockInput):
            h5file = h5py.File(self.testFilePath, 'w')
            h5group = h5file.create_group('Some Group')

            self.objFeaturesNameSlot.setValue(deepcopy(inp))
            self.assertEqual(self.objFeaturesNameSlot([]).wait(), inp)
            self.serializer.serialize(h5group)

            self.objFeaturesNameSlot.setValue({"something": "else"})
            self.assertNotEqual(self.objFeaturesNameSlot([]).wait(), inp)

            self.serializer.deserialize(h5group)
            self.assertEqual(self.objFeaturesNameSlot([]).wait(), self.mockInput)
            h5file.close()


class TestSerialBlockSlot(unittest.TestCase):
    
    def _init_objects(self):
        raw_data = numpy.zeros((100,100,100,1), dtype=numpy.uint32)
        raw_data = vigra.taggedView(raw_data, 'zyxc')
    
        opLabelArrays = OperatorWrapper( OpCompressedUserLabelArray, graph=Graph() )
        opLabelArrays.Input.resize(1)
        opLabelArrays.Input[0].setValue( raw_data )
        opLabelArrays.shape.setValue( raw_data.shape )
        opLabelArrays.eraser.setValue( 255 )
        opLabelArrays.deleteLabel.setValue( -1 )
        opLabelArrays.blockShape.setValue( (10,10,10,1) )
        
        # This will serialize/deserialize data to the h5 file.
        slotSerializer = SerialBlockSlot( opLabelArrays.Output, opLabelArrays.Input, opLabelArrays.nonzeroBlocks )
        return opLabelArrays, slotSerializer

    def testBasic1(self):
        tmp_dir = tempfile.mkdtemp()
        h5_filepath = os.path.join(tmp_dir , 'serial_blockslot_test.h5' )

        # Create an operator and a serializer to write the data.
        opLabelArrays, slotSerializer = self._init_objects()
    
        # Give it some data.
        opLabelArrays.Input[0][10:11, 10:20, 10:20, 0:1] = 1*numpy.ones((1,10,10,1), dtype=numpy.uint8)
        opLabelArrays.Input[0][11:12, 10:20, 10:20, 0:1] = 2*numpy.ones((1,10,10,1), dtype=numpy.uint8)
        
        with h5py.File(h5_filepath, 'w') as f:
            label_group = f.create_group('label_data')
            slotSerializer.serialize( label_group )
    
        # Now start again with fresh objects.
        # This time we'll read the data.
        opLabelArrays, slotSerializer = self._init_objects()
    
        with h5py.File(h5_filepath, 'r') as f:
            label_group = f['label_data']
            slotSerializer.deserialize( label_group )

        # Verify that we get the same data back.
        assert ( opLabelArrays.Output[0][10:11, 10:20, 10:20, 0:1].wait() == 1 ).all()
        assert ( opLabelArrays.Output[0][11:12, 10:20, 10:20, 0:1].wait() == 2 ).all()

        os.remove(h5_filepath)
        shutil.rmtree(tmp_dir)

    def testBasic2(self):
        tmp_dir = tempfile.mkdtemp()
        h5_filepath = os.path.join(tmp_dir , 'serial_blockslot_test.h5' )

        # Create an operator and a serializer to write the data.
        opLabelArrays, slotSerializer = self._init_objects()

        # Give it some data.
        opLabelArrays.Input[0][10:11, 10:20, 10:20, 0:1] = 1*numpy.ones((1,10,10,1), dtype=numpy.uint8)
        opLabelArrays.Input[0][11:12, 10:20, 10:20, 0:1] = 2*numpy.ones((1,10,10,1), dtype=numpy.uint8)

        with h5py.File(h5_filepath, 'w') as f:
            label_group = f.create_group('label_data')
            slotSerializer.serialize( label_group )

            # Try smashing the data that was saved
            for each_item in label_group:
                del label_group[each_item]

            # See if it will write again anyways.
            slotSerializer.serialize( label_group )

        # Now start again with fresh objects.
        # This time we'll read the data.
        opLabelArrays, slotSerializer = self._init_objects()

        with h5py.File(h5_filepath, 'r') as f:
            label_group = f['label_data']
            slotSerializer.deserialize( label_group )

        # Verify that we get the same data back.
        assert ( opLabelArrays.Output[0][10:11, 10:20, 10:20, 0:1].wait() == 1 ).all()
        assert ( opLabelArrays.Output[0][11:12, 10:20, 10:20, 0:1].wait() == 2 ).all()

        os.remove(h5_filepath)
        shutil.rmtree(tmp_dir)

    def testBasic3(self):
        tmp_dir = tempfile.mkdtemp()
        h5_filepath = os.path.join(tmp_dir , 'serial_blockslot_test.h5' )

        # Create an operator and a serializer to write the data.
        opLabelArrays, slotSerializer = self._init_objects()

        # Give it some data.
        opLabelArrays.Input[0][10:11, 10:20, 10:20, 0:1] = 1*numpy.ones((1,10,10,1), dtype=numpy.uint8)
        opLabelArrays.Input[0][30:31, 30:40, 30:40, 0:1] = 2*numpy.ones((1,10,10,1), dtype=numpy.uint8)

        with h5py.File(h5_filepath, 'w') as f:
            label_group = f.create_group('label_data')
            slotSerializer.serialize( label_group )

        # Now start again with fresh objects.
        # This time we'll read the data.
        opLabelArrays, slotSerializer = self._init_objects()

        with h5py.File(h5_filepath, 'r') as f:
            label_group = f['label_data']
            slotSerializer.deserialize( label_group )

        # Verify that we get the same data back.
        assert ( opLabelArrays.Output[0][10:11, 10:20, 10:20, 0:1].wait() == 1 ).all()
        assert ( opLabelArrays.Output[0][30:31, 30:40, 30:40, 0:1].wait() == 2 ).all()

        os.remove(h5_filepath)
        shutil.rmtree(tmp_dir)

    def testBasic4(self):
        tmp_dir = tempfile.mkdtemp()
        h5_filepath = os.path.join(tmp_dir , 'serial_blockslot_test.h5' )

        # Create an operator and a serializer to write the data.
        opLabelArrays, slotSerializer = self._init_objects()

        # Give it some data.
        opLabelArrays.Input[0][10:11, 10:20, 10:20, 0:1] = 1*numpy.ones((1,10,10,1), dtype=numpy.uint8)
        opLabelArrays.Input[0][30:31, 30:40, 30:40, 0:1] = 2*numpy.ones((1,10,10,1), dtype=numpy.uint8)

        with h5py.File(h5_filepath, 'w') as f:
            label_group = f.create_group('label_data')
            slotSerializer.serialize( label_group )

            # Get all dataset names
            def iter_dataset_names(name):
                if isinstance(label_group[name], h5py.Dataset):
                    yield(name)

            # Then delete them
            for each_dataset_name in label_group.visit(iter_dataset_names):
                del label_group[each_dataset_name]

            # See if it will write again anyways.
            slotSerializer.serialize( label_group )

        # Now start again with fresh objects.
        # This time we'll read the data.
        opLabelArrays, slotSerializer = self._init_objects()

        with h5py.File(h5_filepath, 'r') as f:
            label_group = f['label_data']
            slotSerializer.deserialize( label_group )

        # Verify that we get the same data back.
        assert ( opLabelArrays.Output[0][10:11, 10:20, 10:20, 0:1].wait() == 1 ).all()
        assert ( opLabelArrays.Output[0][30:31, 30:40, 30:40, 0:1].wait() == 2 ).all()

        os.remove(h5_filepath)
        shutil.rmtree(tmp_dir)


class TestSerialBlockSlot2(unittest.TestCase):

    def _init_objects(self):
        raw_data = numpy.zeros((100,100,100,1), dtype=numpy.uint32)

        raw_data[0:15, 0:15, 0:15, 0:1] = numpy.ma.masked

        opLabelArrays = OperatorWrapper( OpCompressedUserLabelArray, graph=Graph() )
        opLabelArrays.Input.resize(1)
        opLabelArrays.Input[0].meta.has_mask = True
        opLabelArrays.Input[0].meta.axistags = vigra.AxisTags('zyxc')
        opLabelArrays.Input[0].setValue( raw_data )
        opLabelArrays.shape.setValue( raw_data.shape )
        opLabelArrays.eraser.setValue( 255 )
        opLabelArrays.deleteLabel.setValue( -1 )
        opLabelArrays.blockShape.setValue( (10,10,10,1) )

        # This will serialize/deserialize data to the h5 file.
        slotSerializer = SerialBlockSlot( opLabelArrays.Output, opLabelArrays.Input, opLabelArrays.nonzeroBlocks )
        return opLabelArrays, slotSerializer

    def testBasic1(self):
        tmp_dir = tempfile.mkdtemp()
        h5_filepath = os.path.join(tmp_dir , 'serial_blockslot_test.h5' )

        # Create an operator and a serializer to write the data.
        opLabelArrays, slotSerializer = self._init_objects()

        # Pick some slicings
        slicing_1 = numpy.s_[10:11, 10:20, 10:20, 0:1]
        slicing_2 = numpy.s_[11:12, 10:20, 10:20, 0:1]

        # Give it some data.
        opLabelArrays.Input[0][slicing_1] = 1*numpy.ones((1,10,10,1), dtype=numpy.uint8)
        opLabelArrays.Input[0][slicing_2] = 2*numpy.ones((1,10,10,1), dtype=numpy.uint8)

        with h5py.File(h5_filepath, 'w') as f:
            label_group = f.create_group('label_data')
            slotSerializer.serialize( label_group )

        # Now start again with fresh objects.
        # This time we'll read the data.
        opLabelArrays, slotSerializer = self._init_objects()

        with h5py.File(h5_filepath, 'r') as f:
            label_group = f['label_data']
            slotSerializer.deserialize( label_group )

        # Verify that we get the same data back.
        result_1 = opLabelArrays.Output[0][slicing_1].wait()
        result_2 = opLabelArrays.Output[0][slicing_2].wait()

        assert ( result_1 == 1 ).all()
        assert ( result_2 == 2 ).all()

        expected_mask = numpy.zeros(
            opLabelArrays.Input[0].meta.shape,
            dtype=bool
        )
        expected_mask[0:15, 0:15, 0:15, 0:1] = True
        expected_mask[slicing_1] = False
        expected_mask[slicing_2] = False

        assert ( result_1.mask == expected_mask[slicing_1] ).all()
        assert ( result_2.mask == expected_mask[slicing_2] ).all()

        os.remove(h5_filepath)
        shutil.rmtree(tmp_dir)

    def testBasic2(self):
        tmp_dir = tempfile.mkdtemp()
        h5_filepath = os.path.join(tmp_dir , 'serial_blockslot_test.h5' )

        # Create an operator and a serializer to write the data.
        opLabelArrays, slotSerializer = self._init_objects()

        # Pick some slicings
        slicing_1 = numpy.s_[10:11, 10:20, 10:20, 0:1]
        slicing_2 = numpy.s_[11:12, 10:20, 10:20, 0:1]

        # Give it some data.
        opLabelArrays.Input[0][slicing_1] = 1*numpy.ones((1,10,10,1), dtype=numpy.uint8)
        opLabelArrays.Input[0][slicing_2] = 2*numpy.ones((1,10,10,1), dtype=numpy.uint8)

        with h5py.File(h5_filepath, 'w') as f:
            label_group = f.create_group('label_data')
            slotSerializer.serialize( label_group )

            # Try smashing the data that was saved
            for each_item in label_group:
                del label_group[each_item]

            # See if it will write again anyways.
            slotSerializer.serialize( label_group )

        # Now start again with fresh objects.
        # This time we'll read the data.
        opLabelArrays, slotSerializer = self._init_objects()

        with h5py.File(h5_filepath, 'r') as f:
            label_group = f['label_data']
            slotSerializer.deserialize( label_group )

        # Verify that we get the same data back.
        result_1 = opLabelArrays.Output[0][slicing_1].wait()
        result_2 = opLabelArrays.Output[0][slicing_2].wait()

        assert ( result_1 == 1 ).all()
        assert ( result_2 == 2 ).all()

        expected_mask = numpy.zeros(
            opLabelArrays.Input[0].meta.shape,
            dtype=bool
        )
        expected_mask[0:15, 0:15, 0:15, 0:1] = True
        expected_mask[slicing_1] = False
        expected_mask[slicing_2] = False

        assert ( result_1.mask == expected_mask[slicing_1] ).all()
        assert ( result_2.mask == expected_mask[slicing_2] ).all()

        os.remove(h5_filepath)
        shutil.rmtree(tmp_dir)

    def testBasic3(self):
        tmp_dir = tempfile.mkdtemp()
        h5_filepath = os.path.join(tmp_dir , 'serial_blockslot_test.h5' )

        # Create an operator and a serializer to write the data.
        opLabelArrays, slotSerializer = self._init_objects()

        # Pick some slicings
        slicing_1 = numpy.s_[10:11, 10:20, 10:20, 0:1]
        slicing_2 = numpy.s_[30:31, 30:40, 30:40, 0:1]

        # Give it some data.
        opLabelArrays.Input[0][slicing_1] = 1*numpy.ones((1,10,10,1), dtype=numpy.uint8)
        opLabelArrays.Input[0][slicing_2] = 2*numpy.ones((1,10,10,1), dtype=numpy.uint8)

        with h5py.File(h5_filepath, 'w') as f:
            label_group = f.create_group('label_data')
            slotSerializer.serialize( label_group )

        # Now start again with fresh objects.
        # This time we'll read the data.
        opLabelArrays, slotSerializer = self._init_objects()

        with h5py.File(h5_filepath, 'r') as f:
            label_group = f['label_data']
            slotSerializer.deserialize( label_group )

        # Verify that we get the same data back.
        result_1 = opLabelArrays.Output[0][slicing_1].wait()
        result_2 = opLabelArrays.Output[0][slicing_2].wait()

        assert ( result_1 == 1 ).all()
        assert ( result_2 == 2 ).all()

        expected_mask = numpy.zeros(
            opLabelArrays.Input[0].meta.shape,
            dtype=bool
        )
        expected_mask[0:15, 0:15, 0:15, 0:1] = True
        expected_mask[slicing_1] = False
        expected_mask[slicing_2] = False

        assert ( result_1.mask == expected_mask[slicing_1] ).all()
        assert ( result_2.mask == expected_mask[slicing_2] ).all()

        os.remove(h5_filepath)
        shutil.rmtree(tmp_dir)

    def testBasic4(self):
        tmp_dir = tempfile.mkdtemp()
        h5_filepath = os.path.join(tmp_dir , 'serial_blockslot_test.h5' )

        # Create an operator and a serializer to write the data.
        opLabelArrays, slotSerializer = self._init_objects()

        # Pick some slicings
        slicing_1 = numpy.s_[0:20, 0:20, 0:20, 0:1]
        slicing_2 = numpy.s_[30:31, 30:40, 30:40, 0:1]

        # Give it some data.
        opLabelArrays.Input[0][slicing_1] = 1*numpy.ones((20,20,20,1), dtype=numpy.uint8)
        opLabelArrays.Input[0][slicing_2] = 2*numpy.ones((1,10,10,1), dtype=numpy.uint8)

        with h5py.File(h5_filepath, 'w') as f:
            label_group = f.create_group('label_data')
            slotSerializer.serialize( label_group )

        # Now start again with fresh objects.
        # This time we'll read the data.
        opLabelArrays, slotSerializer = self._init_objects()

        with h5py.File(h5_filepath, 'r') as f:
            label_group = f['label_data']
            slotSerializer.deserialize( label_group )

        # Verify that we get the same data back.
        result_1 = opLabelArrays.Output[0][slicing_1].wait()
        result_2 = opLabelArrays.Output[0][slicing_2].wait()

        assert ( result_1 == 1 ).all()
        assert ( result_2 == 2 ).all()

        expected_mask = numpy.zeros(
            opLabelArrays.Input[0].meta.shape,
            dtype=bool
        )
        expected_mask[0:15, 0:15, 0:15, 0:1] = True

        assert ( result_1.mask == False ).all()
        assert ( result_2.mask == expected_mask[slicing_2] ).all()

        os.remove(h5_filepath)
        shutil.rmtree(tmp_dir)

    def testBasic5(self):
        tmp_dir = tempfile.mkdtemp()
        h5_filepath = os.path.join(tmp_dir , 'serial_blockslot_test.h5' )

        # Create an operator and a serializer to write the data.
        opLabelArrays, slotSerializer = self._init_objects()

        # Give it some data.
        data_1 = numpy.ones((1,10,10,1), dtype=numpy.uint8)
        data_2 = 2*data_1

        data_1 = numpy.ma.masked_array(
            data_1,
            mask=numpy.zeros(data_1.shape, dtype=bool),
            shrink=False
        )
        data_2 = numpy.ma.masked_array(
            data_2,
            mask=numpy.zeros(data_1.shape, dtype=bool),
            shrink=False
        )

        data_1[0:1, 0:1, 0:1, 0:1] = numpy.ma.masked
        data_2[0:1, 9:10, 9:10, 0:1] = numpy.ma.masked

        # Pick some slicings
        slicing_1 = numpy.s_[10:11, 10:20, 10:20, 0:1]
        slicing_2 = numpy.s_[30:31, 30:40, 30:40, 0:1]

        # Give it some data.
        opLabelArrays.Input[0][slicing_1] = data_1
        opLabelArrays.Input[0][slicing_2] = data_2

        with h5py.File(h5_filepath, 'w') as f:
            label_group = f.create_group('label_data')
            slotSerializer.serialize( label_group )

            # Get all dataset names
            def iter_dataset_names(name):
                if isinstance(label_group[name], h5py.Dataset):
                    yield(name)

            # Then delete them
            for each_dataset_name in label_group.visit(iter_dataset_names):
                del label_group[each_dataset_name]

            # See if it will write again anyways.
            slotSerializer.serialize( label_group )

        # Now start again with fresh objects.
        # This time we'll read the data.
        opLabelArrays, slotSerializer = self._init_objects()

        with h5py.File(h5_filepath, 'r') as f:
            label_group = f['label_data']
            slotSerializer.deserialize( label_group )

        # Verify that we get the same data back.
        result_1 = opLabelArrays.Output[0][slicing_1].wait()
        result_2 = opLabelArrays.Output[0][slicing_2].wait()


        assert ( result_1.filled(1) == 1 ).all()
        assert ( result_2.filled(2) == 2 ).all()

        assert ( result_1.mask == data_1.mask ).all()
        assert ( result_2.mask == data_2.mask ).all()

        os.remove(h5_filepath)
        shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    unittest.main()
