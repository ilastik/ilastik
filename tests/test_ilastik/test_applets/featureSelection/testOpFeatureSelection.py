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
# 		   http://ilastik.org/license.html
###############################################################################
from builtins import range
import os
import numpy
from lazyflow.roi import sliceToRoi
from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.ioOperators import OpInputDataReader
from ilastik.applets.featureSelection.opFeatureSelection import (
    OpFeatureSelection,
    OpFeatureSelectionNoCache,
    FeatureSelectionConstraintError,
)
from unittest.mock import MagicMock, patch, PropertyMock
import pytest
import vigra

import ilastik.ilastik_logging

ilastik.ilastik_logging.default_config.init()

import unittest
import tempfile


class TestOpFeatureSelection(unittest.TestCase):
    def setUp(self):
        data = numpy.random.random((2, 100, 100, 100, 3))

        self.filePath = tempfile.mkdtemp() + "/featureSelectionTestData.npy"
        numpy.save(self.filePath, data)

        graph = Graph()

        # Define operators
        opFeatures = OperatorWrapper(OpFeatureSelection, graph=graph)
        opReader = OpInputDataReader(graph=graph)

        # Set input data
        opReader.FilePath.setValue(self.filePath)

        # Connect input
        opFeatures.InputImage.resize(1)
        opFeatures.InputImage[0].connect(opReader.Output)

        # Configure scales
        scales = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        opFeatures.Scales.setValue(scales)

        # Configure feature types
        featureIds = [
            "GaussianSmoothing",
            "LaplacianOfGaussian",
            "StructureTensorEigenvalues",
            "HessianOfGaussianEigenvalues",
            "GaussianGradientMagnitude",
            "DifferenceOfGaussians",
        ]
        opFeatures.FeatureIds.setValue(featureIds)

        # Configure matrix
        #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
        selections = numpy.array(
            [
                [True, False, False, False, False, False, False],  # Gaussian
                [False, True, False, False, False, False, False],  # L of G
                [False, False, True, False, False, False, False],  # ST EVs
                [False, False, False, False, False, False, False],  # H of G EVs
                [False, False, False, False, False, False, False],  # GGM
                [False, False, False, False, False, False, False],
            ]
        )  # Diff of G
        opFeatures.SelectionMatrix.setValue(selections)

        self.opFeatures = opFeatures
        self.opReader = opReader

    def tearDown(self):
        self.opFeatures.cleanUp()
        self.opReader.cleanUp()
        try:
            os.remove(self.filePath)
        except:
            pass

    def test_basicFunctionality(self):
        opFeatures = self.opFeatures

        # Compute results for the top slice only
        topSlice = [0, slice(None), slice(None), 0, slice(None)]
        result = opFeatures.OutputImage[0][topSlice].wait()

        numFeatures = numpy.sum(opFeatures.SelectionMatrix.value)
        outputChannels = result.shape[-1]

        # Input has 3 channels, and one of our features outputs a 3D vector
        assert outputChannels == 15  # (3 + 3 + 9)

        # Debug only -- Inspect the resulting images
        if False:
            # Export the first slice of each channel of the results as a separate image for display purposes.
            import vigra

            numFeatures = result.shape[-1]
            for featureIndex in range(0, numFeatures):
                featureSlice = list(topSlice)
                featureSlice[-1] = featureIndex
                vigra.impex.writeImage(result[featureSlice], "test_feature" + str(featureIndex) + ".bmp")

    def test_2d(self):
        graph = Graph()
        data2d = numpy.random.random((2, 100, 100, 1, 3))
        data2d = vigra.taggedView(data2d, axistags="txyzc")
        # Define operators
        opFeatures = OpFeatureSelection(graph=graph)
        opFeatures.Scales.connect(self.opFeatures.Scales[0])
        opFeatures.FeatureIds.connect(self.opFeatures.FeatureIds[0])
        opFeatures.SelectionMatrix.connect(self.opFeatures.SelectionMatrix[0])

        # Set input data
        opFeatures.InputImage.setValue(data2d)

        # Compute results for the top slice only
        topSlice = [0, slice(None), slice(None), 0, slice(None)]
        result = opFeatures.OutputImage[topSlice].wait()

    def testDirtyPropagation(self):
        opFeatures = self.opFeatures

        dirtyRois = []

        def handleDirty(slot, roi):
            dirtyRois.append(roi)

        opFeatures.OutputImage[0].notifyDirty(handleDirty)

        # Change the matrix
        selections = numpy.array(
            [
                [True, False, False, False, False, False, False],  # Gaussian
                [False, True, False, False, False, False, False],  # L of G
                [False, False, True, False, False, False, False],  # ST EVs
                [False, False, False, True, False, False, False],  # H of G EVs
                [False, False, False, False, False, False, False],  # GGM
                [False, False, False, False, False, False, False],
            ]
        )  # Diff of G
        opFeatures.SelectionMatrix.setValue(selections)

        assert len(dirtyRois) == 1
        assert (dirtyRois[0].start, dirtyRois[0].stop) == sliceToRoi(
            slice(None), self.opFeatures.OutputImage[0].meta.shape
        )


class TestOpFeatureSelectionAppletLookup:
    """
    Tests that OpFeatureSelectionNoCache.setupOutputs() correctly finds the
    feature selection applet in both regular and Autocontext workflows by
    actually calling into the production code in opFeatureSelection.py.

    Fixes #3106: 'AutocontextTwoStage' object has no attribute 'featureSelectionApplet'
    """

    @pytest.fixture
    def invalid_selection(self) -> numpy.ndarray:
        test_selections = numpy.zeros((6, 7), dtype=bool)
        test_selections[:, 6] = True  # sigma=10.0, invalid for 5x5 image
        return test_selections

    @pytest.fixture
    def mock_workflow(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def op_with_invalid_scales(self, graph: Graph, mock_workflow: MagicMock) -> OpFeatureSelectionNoCache:
        """
        Create a real OpFeatureSelectionNoCache whose parent.parent resolves
        to mock_workflow, configured so setupOutputs() hits the invalid-scales
        branch and exercises the applet-lookup code in production.

        We patch the operator's parent property because lazyflow calls
        setupOutputs() immediately on setValue() and the parent chain must
        be in place by then. The patch.object context manager handles cleanup.
        """
        inner_mock = MagicMock()
        inner_mock.parent = mock_workflow

        with patch.object(
            OpFeatureSelectionNoCache,
            "parent",
            new_callable=PropertyMock,
        ) as mock_parent:
            mock_parent.return_value = inner_mock
            op = OpFeatureSelectionNoCache(graph=graph)

            # Tiny image: too small for large sigma scales -> triggers invalid_scales path
            tiny = numpy.zeros((1, 5, 5, 1, 1), dtype=numpy.float32)
            tiny = vigra.taggedView(tiny, "txyzc")
            op.InputImage.setValue(tiny)
            yield op

    def test_regular_workflow_uses_singular_applet(
        self,
        mock_workflow: MagicMock,
        op_with_invalid_scales: OpFeatureSelectionNoCache,
        invalid_selection: numpy.ndarray,
    ):
        """
        In a regular workflow, setupOutputs() finds featureSelectionApplet
        (singular) and includes its callback in fixing_dialogs.
        """
        mock_callback = MagicMock()
        mock_applet = MagicMock()
        mock_applet._gui.currentGui.return_value.onFeatureButtonClicked = mock_callback
        mock_workflow.featureSelectionApplet = mock_applet

        with pytest.raises(FeatureSelectionConstraintError) as ex:
            op_with_invalid_scales.SelectionMatrix.setValue(invalid_selection)

        assert mock_callback in ex.value.fixing_dialogs

    def test_autocontext_workflow_uses_plural_applets(
        self,
        mock_workflow: MagicMock,
        op_with_invalid_scales: OpFeatureSelectionNoCache,
        invalid_selection: numpy.ndarray,
    ):
        """
        In an Autocontext workflow, setupOutputs() falls back to
        featureSelectionApplets (plural) and picks the applet whose
        topLevelOperator matches self.parent.
        """
        mock_callback_0 = MagicMock()
        mock_applet_0 = MagicMock()
        mock_applet_0._gui.currentGui.return_value.onFeatureButtonClicked = mock_callback_0
        mock_applet_1 = MagicMock()

        del mock_workflow.featureSelectionApplet  # ensure singular attribute absent
        mock_workflow.featureSelectionApplets = [mock_applet_0, mock_applet_1]
        mock_applet_0.topLevelOperator = op_with_invalid_scales.parent

        with pytest.raises(FeatureSelectionConstraintError) as ex:
            op_with_invalid_scales.SelectionMatrix.setValue(invalid_selection)

        assert mock_callback_0 in ex.value.fixing_dialogs

    def test_headless_produces_empty_fix_dlgs(
        self,
        mock_workflow: MagicMock,
        op_with_invalid_scales: OpFeatureSelectionNoCache,
        invalid_selection: numpy.ndarray,
    ):
        """
        In headless mode, the feature applet exists but its _gui attribute is
        None (unset). setupOutputs() must raise FeatureSelectionConstraintError
        with an empty fixing_dialogs rather than crashing.
        """
        mock_applet = MagicMock()
        mock_applet._gui = None  # _gui is unset/None in headless mode
        mock_workflow.featureSelectionApplet = mock_applet

        with pytest.raises(FeatureSelectionConstraintError) as ex:
            op_with_invalid_scales.SelectionMatrix.setValue(invalid_selection)

        assert ex.value.fixing_dialogs == []
