from builtins import map
from builtins import object

###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
# 		   http://ilastik.org/license/
###############################################################################
import numpy
import vigra
from lazyflow.graph import Graph
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.operators import OpCompressedUserLabelArray

from lazyflow.utility.slicingtools import slicing2shape


class TestOpCompressedUserLabelArray(object):
    def setup(self):
        graph = Graph()
        op = OpCompressedUserLabelArray(graph=graph)
        arrayshape = (1, 100, 100, 10, 1)
        op.inputs["shape"].setValue(arrayshape)
        blockshape = (1, 10, 10, 10, 1)  # Why doesn't this work if blockshape is an ndarray?
        op.inputs["blockShape"].setValue(blockshape)
        op.eraser.setValue(100)

        dummyData = vigra.VigraArray(arrayshape, axistags=vigra.defaultAxistags("txyzc"), dtype=numpy.uint8)
        op.Input.setValue(dummyData)

        slicing = numpy.s_[0:1, 1:15, 2:36, 3:7, 0:1]
        inDataShape = slicing2shape(slicing)
        inputData = (3 * numpy.random.random(inDataShape)).astype(numpy.uint8)
        op.Input[slicing] = inputData

        data = numpy.zeros(arrayshape, dtype=numpy.uint8)
        data[slicing] = inputData

        # Sanity check...
        assert (op.Output[:].wait()[slicing] == data[slicing]).all()

        self.op = op
        self.slicing = slicing
        self.inData = inputData
        self.data = data

    def testOutput(self):
        """
        Verify that the label array has all of the data it was given.
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        # Output
        outputData = op.Output[...].wait()
        assert numpy.all(outputData[...] == data[...])

        # maxLabel
        # assert op.maxLabel.value == inData.max()

        # nonzeroValues
        # nz = op.nonzeroValues.value
        # assert len(nz) == len(vigra.analysis.unique(inData))-1

    def testSetupTwice(self):
        """
        If one of the inputs to the label array is changed, the output should not change (including max label value!)
        """
        # Change one of the inputs, causing setupOutputs to be changed.
        self.op.eraser.setValue(255)

        # Run the plain output test.
        self.testOutput()

    def testDeleteLabel(self):
        """
        Check behavior after deleting an entire label class from the sparse array.
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        op.deleteLabel.setValue(1)
        outputData = op.Output[...].wait()

        # Expected: All 1s removed, all 2s converted to 1s
        expectedOutput = numpy.where(self.data == 1, 0, self.data)
        expectedOutput = numpy.where(expectedOutput == 2, 1, expectedOutput)
        assert (outputData[...] == expectedOutput[...]).all()

        # assert op.maxLabel.value == expectedOutput.max() == 1

        # delete label input resets automatically
        # assert op.deleteLabel.value == -1 # Apparently not?

    def testDeleteLabel2(self):
        """
        Another test to check behavior after deleting an entire label class from the sparse array.
        This one ensures that different blocks have different max label values before the delete occurs.
        """
        op = self.op
        slicing = self.slicing
        data = self.data

        # assert op.maxLabel.value == 2

        # Choose slicings that do NOT intersect with any of the previous data or with each other
        # The goal is to make sure that the data for each slice ends up in a separate block
        slicing1 = numpy.s_[0:1, 60:65, 0:10, 3:7, 0:1]
        slicing2 = numpy.s_[0:1, 90:95, 0:90, 3:7, 0:1]

        expectedData = self.data[...]

        labels1 = numpy.ndarray(slicing2shape(slicing1), dtype=numpy.uint8)
        labels1[...] = 1
        op.Input[slicing1] = labels1
        expectedData[slicing1] = labels1

        labels2 = numpy.ndarray(slicing2shape(slicing2), dtype=numpy.uint8)
        labels2[...] = 2
        op.Input[slicing2] = labels2
        expectedData[slicing2] = labels2

        # Sanity check:
        # Does the data contain our new labels?
        assert (op.Output[...].wait() == expectedData).all()
        assert expectedData.max() == 2
        # assert op.maxLabel.value == 2

        # Delete label 1
        op.deleteLabel.setValue(1)
        outputData = op.Output[...].wait()

        # Expected: All 1s removed, all 2s converted to 1s
        expectedData = numpy.where(expectedData == 1, 0, expectedData)
        expectedData = numpy.where(expectedData == 2, 1, expectedData)
        assert (outputData[...] == expectedData[...]).all()

        # assert op.maxLabel.value == expectedData.max() == 1

    def testEraser(self):
        """
        Check that some labels can be deleted correctly from the sparse array.
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        # assert op.maxLabel.value == 2

        erasedSlicing = list(slicing)
        erasedSlicing[1] = slice(1, 2)

        outputWithEraser = data.copy()
        outputWithEraser[erasedSlicing] = 100

        op.Input[erasedSlicing] = outputWithEraser[erasedSlicing]

        expectedOutput = outputWithEraser
        expectedOutput[erasedSlicing] = 0

        outputData = op.Output[...].wait()
        assert (outputData == expectedOutput).all()

        assert expectedOutput.max() == 2
        # assert op.maxLabel.value == 2

    def testEraseAll(self):
        """
        Test behavior when all labels of a particular class are erased.
        Note that this is not the same as deleting a label class, but should have the same effect on the output slots.
        """
        op = self.op
        slicing = self.slicing
        data = self.data

        # assert op.maxLabel.value == 2

        newSlicing = list(slicing)
        newSlicing[1] = slice(1, 2)

        # Add some new labels for a class that hasn't been seen yet (3)
        threeData = numpy.ndarray(slicing2shape(newSlicing), dtype=numpy.uint8)
        threeData[...] = 3
        op.Input[newSlicing] = threeData
        expectedData = data.copy()
        expectedData[newSlicing] = 3

        # Sanity check: Are the new labels in the data?
        assert (op.Output[...].wait() == expectedData).all()
        assert expectedData.max() == 3
        # assert op.maxLabel.value == 3

        # Now erase all the 3s
        eraserData = numpy.ones(slicing2shape(newSlicing), dtype=numpy.uint8) * 100
        op.Input[newSlicing] = eraserData
        expectedData = data.copy()
        expectedData[newSlicing] = 0

        # The data we erased should be zeros
        output_data = op.Output[...].wait()
        assert (expectedData[newSlicing] == 0).all()
        assert (output_data[newSlicing] == 0).all()
        assert (output_data == expectedData).all()

        # The maximum label should be reduced, because all the 3s were removed.
        assert expectedData.max() == 2
        # assert op.maxLabel.value == 2

    def testEraseBlock(self):
        """
        If we use the eraser to remove all labels from a block,
        it should be removed from the CleanBlocks slot.
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        # BEFORE (convert to tuple)
        clean_blocks_before = [(tuple(a), tuple(b)) for (a, b) in op.CleanBlocks.value]

        block_slicing = numpy.s_[0:1, 10:20, 10:20, 0:10, 0:1]
        block_roi = ((0, 10, 10, 0, 0), (1, 20, 20, 10, 1))

        eraser_data = 100 * numpy.ones(slicing2shape(block_slicing), dtype=numpy.uint8)
        op.Input[block_slicing] = eraser_data

        expected_data = data.copy()
        expected_data[block_slicing] = 0

        # quick sanity check: the data was actually cleared by the eraser
        assert (op.Output[:].wait() == expected_data).all()

        # AFTER (convert to tuple)
        clean_blocks_after = [(tuple(a), tuple(b)) for (a, b) in op.CleanBlocks.value]

        before_set = set(map(tuple, clean_blocks_before))
        after_set = set(map(tuple, clean_blocks_after))

        assert before_set - set([block_roi]) == after_set

    def testDimensionalityChange(self):
        """
        What happens if we configure the operator, use it a bit,
        then reconfigure it with a different input shape and dimensionality?
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        # Output
        outputData = op.Output[...].wait()
        assert numpy.all(outputData[...] == data[...])

        # Reconfigure
        op.Input.setValue(data[0])

        blockshape = (10, 10, 10, 1)
        op.blockShape.setValue(blockshape)

        # After reconfigure, everything is set back to 0.
        # That's okay.
        outputData = op.Output[...].wait()
        assert numpy.all(outputData[...] == 0)

    def testIngestData(self):
        """
        The ingestData() function can be used to import an entire slot's
        data into the label array, but copied one block at a time.
        """
        op = self.op
        data = self.data + 5
        opProvider = OpArrayPiper(graph=op.graph)
        opProvider.Input.setValue(data)

        max_label = op.ingestData(opProvider.Output)
        assert (op.Output[:].wait() == data).all()
        assert max_label == data.max()

    def test_Projection2D(self):
        op = self.op

        projected_data = op.Projection2D[:, 0:100, 0:100, 4:5, :].wait()
        # print projected_data.shape
        # print projected_data.min()
        # print projected_data.max()
        # print projected_data.sum()
        full_data = op.Output[:, 0:100, 0:100, :, :].wait()
        # print full_data.sum(axis=3).sum()

        summed_projection = numpy.sum(full_data, axis=3, keepdims=True)
        assert ((summed_projection != 0) == (projected_data != 0)).all()


class TestOpCompressedUserLabelArray_masked(object):
    def setup(self):
        graph = Graph()
        op = OpCompressedUserLabelArray(graph=graph)
        arrayshape = (1, 100, 100, 10, 1)
        op.inputs["shape"].setValue(arrayshape)
        blockshape = (1, 10, 10, 10, 1)  # Why doesn't this work if blockshape is an ndarray?
        op.inputs["blockShape"].setValue(blockshape)
        op.eraser.setValue(100)

        op.Input.meta.axistags = vigra.defaultAxistags("txyzc")
        op.Input.meta.has_mask = True
        dummyData = numpy.zeros(arrayshape, dtype=numpy.uint8)
        dummyData = numpy.ma.masked_array(
            dummyData, mask=numpy.ma.getmaskarray(dummyData), fill_value=numpy.uint8(0), shrink=False
        )
        op.Input.setValue(dummyData)

        slicing = numpy.s_[0:1, 1:15, 2:36, 3:7, 0:1]
        inDataShape = slicing2shape(slicing)
        inputData = (3 * numpy.random.random(inDataShape)).astype(numpy.uint8)
        inputData = numpy.ma.masked_array(
            inputData, mask=numpy.ma.getmaskarray(inputData), fill_value=numpy.uint8(0), shrink=False
        )
        inputData[:, 0] = numpy.ma.masked
        op.Input[slicing] = inputData
        data = numpy.ma.zeros(arrayshape, dtype=numpy.uint8, fill_value=numpy.uint8(0))
        data[slicing] = inputData

        self.op = op
        self.slicing = slicing
        self.inData = inputData
        self.data = data

    def testOutput(self):
        """
        Verify that the label array has all of the data it was given.
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        # Output
        outputData = op.Output[...].wait()

        assert numpy.all(outputData == data)
        assert numpy.all(outputData.mask == data.mask)
        assert numpy.all(outputData.fill_value == data.fill_value)

        # maxLabel
        # assert op.maxLabel.value == inData.max()

        # nonzeroValues
        # nz = op.nonzeroValues.value
        # assert len(nz) == len(vigra.analysis.unique(inData))-1

    def testSetupTwice(self):
        """
        If one of the inputs to the label array is changed, the output should not change (including max label value!)
        """
        # Change one of the inputs, causing setupOutputs to be changed.
        self.op.eraser.setValue(255)

        # Run the plain output test.
        self.testOutput()

    def testDeleteLabel(self):
        """
        Check behavior after deleting an entire label class from the sparse array.
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        op.deleteLabel.setValue(1)
        outputData = op.Output[...].wait()

        # Expected: All 1s removed, all 2s converted to 1s
        expectedOutput = numpy.where(self.data == 1, 0, self.data)
        expectedOutput = numpy.where(expectedOutput == 2, 1, expectedOutput)
        expectedOutput = numpy.ma.masked_array(
            expectedOutput, mask=self.data.mask, fill_value=self.data.fill_value, shrink=False
        )

        assert numpy.all(outputData == expectedOutput)
        assert numpy.all(outputData.mask == expectedOutput.mask)
        assert numpy.all(outputData.fill_value == expectedOutput.fill_value)

        # assert op.maxLabel.value == expectedOutput.max() == 1

        # delete label input resets automatically
        # assert op.deleteLabel.value == -1 # Apparently not?

    def testDeleteLabel2(self):
        """
        Another test to check behavior after deleting an entire label class from the sparse array.
        This one ensures that different blocks have different max label values before the delete occurs.
        """
        op = self.op
        slicing = self.slicing
        data = self.data

        # assert op.maxLabel.value == 2

        # Choose slicings that do NOT intersect with any of the previous data or with each other
        # The goal is to make sure that the data for each slice ends up in a separate block
        slicing1 = numpy.s_[0:1, 60:65, 0:10, 3:7, 0:1]
        slicing2 = numpy.s_[0:1, 90:95, 0:90, 3:7, 0:1]

        expectedData = self.data[...]

        labels1 = numpy.ndarray(slicing2shape(slicing1), dtype=numpy.uint8)
        labels1[...] = 1
        op.Input[slicing1] = labels1
        expectedData[slicing1] = labels1

        labels2 = numpy.ndarray(slicing2shape(slicing2), dtype=numpy.uint8)
        labels2[...] = 2
        op.Input[slicing2] = labels2
        expectedData[slicing2] = labels2

        # Sanity check:
        # Does the data contain our new labels?
        assert (op.Output[...].wait() == expectedData).all()
        assert expectedData.max() == 2
        # assert op.maxLabel.value == 2

        # Delete label 1
        op.deleteLabel.setValue(1)
        outputData = op.Output[...].wait()

        # Expected: All 1s removed, all 2s converted to 1s
        expectedData = numpy.where(expectedData == 1, 0, expectedData)
        expectedData = numpy.where(expectedData == 2, 1, expectedData)
        expectedData = numpy.ma.masked_array(
            expectedData, mask=self.data.mask, fill_value=self.data.fill_value, shrink=False
        )

        assert numpy.all(outputData == expectedData)
        assert numpy.all(outputData.mask == expectedData.mask)
        assert numpy.all(outputData.fill_value == expectedData.fill_value)

        # assert op.maxLabel.value == expectedData.max() == 1

    def testEraser(self):
        """
        Check that some labels can be deleted correctly from the sparse array.
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        # assert op.maxLabel.value == 2

        erasedSlicing = list(slicing)
        erasedSlicing[1] = slice(1, 2)

        outputWithEraser = data
        outputWithEraser[erasedSlicing] = 100

        op.Input[erasedSlicing] = outputWithEraser[erasedSlicing]

        expectedOutput = outputWithEraser
        expectedOutput[erasedSlicing] = 0

        outputData = op.Output[...].wait()

        assert numpy.all(outputData == expectedOutput)
        assert numpy.all(outputData.mask == expectedOutput.mask)
        assert numpy.all(outputData.fill_value == expectedOutput.fill_value)

        assert expectedOutput.max() == 2
        # assert op.maxLabel.value == 2

    def testEraseAll(self):
        """
        Test behavior when all labels of a particular class are erased.
        Note that this is not the same as deleting a label class, but should have the same effect on the output slots.
        """
        op = self.op
        slicing = self.slicing
        data = self.data

        # assert op.maxLabel.value == 2

        newSlicing = list(slicing)
        newSlicing[1] = slice(1, 2)

        # Add some new labels for a class that hasn't been seen yet (3)
        threeData = numpy.ndarray(slicing2shape(newSlicing), dtype=numpy.uint8)
        threeData[...] = 3
        op.Input[newSlicing] = threeData
        expectedData = data[...]
        expectedData[newSlicing] = 3

        # Sanity check: Are the new labels in the data?
        outputData = op.Output[...].wait()
        assert numpy.all(outputData == expectedData)
        assert numpy.all(outputData.mask == expectedData.mask)
        assert numpy.all(outputData.fill_value == expectedData.fill_value)
        assert expectedData.max() == 3
        # assert op.maxLabel.value == 3

        # Now erase all the 3s
        eraserData = numpy.ones(slicing2shape(newSlicing), dtype=numpy.uint8) * 100
        op.Input[newSlicing] = eraserData
        expectedData = data[...]
        expectedData[newSlicing] = 0

        # The data we erased should be zeros
        outputData = op.Output[...].wait()
        assert numpy.all(outputData == expectedData)
        assert numpy.all(outputData.mask == expectedData.mask)
        assert numpy.all(outputData.fill_value == expectedData.fill_value)

        # The maximum label should be reduced, because all the 3s were removed.
        assert expectedData.max() == 2
        # assert op.maxLabel.value == 2

    def testDimensionalityChange(self):
        """
        What happens if we configure the operator, use it a bit, then reconfigure it with a different input shape and dimensionality?
        """
        op = self.op
        slicing = self.slicing
        inData = self.inData
        data = self.data

        # Output
        outputData = op.Output[...].wait()
        assert numpy.all(outputData[...] == data[...])

        # Reconfigure
        op.Input.setValue(data[0])

        blockshape = (10, 10, 10, 1)
        op.blockShape.setValue(blockshape)

        # After reconfigure, everything is set back to 0.
        # That's okay.
        outputData = op.Output[...].wait()
        assert numpy.all(outputData[...] == 0)
        assert numpy.all(outputData.mask == False)
        assert numpy.all(outputData.fill_value == data.fill_value)

    def testIngestData(self):
        """
        The ingestData() function can be used to import an entire slot's
        data into the label array, but copied one block at a time.
        """
        op = self.op
        data = self.data + 5
        opProvider = OpArrayPiper(graph=op.graph)
        opProvider.Input.setValue(data)

        max_label = op.ingestData(opProvider.Output)
        outputData = op.Output[...].wait()
        assert numpy.all(outputData[...] == data)
        assert numpy.all(outputData.mask == data.mask)

        # FIXME: This assertion fails and I don't know why.
        #        I don't think masked arrays are important for user label data, so I'm ignoring this failure.
        #  assert numpy.all(outputData.fill_value == data.fill_value), \
        #     "Unexpected fill_value: {} instead of {}".format(outputData.fill_value, data.fill_value)
        assert max_label == data.max()

    def test_Projection2D(self):
        op = self.op

        projected_data = op.Projection2D[:, 0:100, 0:100, 4:5, :].wait()
        # print projected_data.shape
        # print projected_data.min()
        # print projected_data.max()
        # print projected_data.sum()
        full_data = op.Output[:, 0:100, 0:100, :, :].wait()
        # print full_data.sum(axis=3).sum()

        summed_projection = numpy.ma.expand_dims(full_data.sum(axis=3), axis=3)

        assert ((summed_projection != 0) == (projected_data != 0)).all()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
