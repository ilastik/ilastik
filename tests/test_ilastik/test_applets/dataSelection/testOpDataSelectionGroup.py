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
import os
import shutil
import tempfile
from typing import Tuple

import numpy
import vigra

from ilastik.applets.dataSelection.opDataSelection import DatasetInfo, FilesystemDatasetInfo, OpDataSelectionGroup
from lazyflow.graph import Graph


class TestOpDataSelectionGroup(object):
    @classmethod
    def setup_class(cls):
        cls.workingDir = tempfile.mkdtemp()

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.workingDir)

    def make_test_data(
        self, filename: str, axislabels: str, shape: Tuple[int, ...]
    ) -> Tuple[DatasetInfo, numpy.ndarray]:
        filepath = os.path.join(self.workingDir, filename)
        data = numpy.random.random(shape)
        numpy.save(filepath, data)
        dataset_info = FilesystemDatasetInfo(filePath=filepath, axistags=vigra.defaultAxistags(axislabels))
        return dataset_info, data

    def test_handles_roles(self):
        """
        Make sure that the dataset roles work the way we expect them to.
        """
        info_A, data_A = self.make_test_data("A.npy", "xyc", (100, 100, 1))
        info_C, data_C = self.make_test_data("C.npy", "xyc", (100, 100, 1))
        example_roles = ["Raw Data", "Segmentation", "Fancy Augmentation"]

        op = OpDataSelectionGroup(graph=Graph())
        op.WorkingDirectory.setValue(self.workingDir)
        op.DatasetRoles.setValue(example_roles)

        op.DatasetGroup.resize(len(example_roles))
        op.DatasetGroup[0].setValue(info_A)
        # Leave second role blank -- datasets other than the first are optional
        op.DatasetGroup[2].setValue(info_C)

        assert op.ImageGroup[0].ready()
        assert op.Image.ready()  # Alias for op.ImageGroup[0]
        assert op.ImageGroup[2].ready()

        dataFromOpA = op.ImageGroup[0][:].wait()
        dataFromAlias = op.Image[:].wait()

        assert dataFromOpA.dtype == data_A.dtype
        assert dataFromOpA.shape == data_A.shape
        assert (dataFromOpA == data_A).all()
        assert (dataFromAlias == data_A).all()

        dataFromOpC = op.ImageGroup[2][:].wait()

        assert dataFromOpC.dtype == data_C.dtype
        assert dataFromOpC.shape == data_C.shape
        assert (dataFromOpC == data_C).all()

        # Ensure that files opened by the inner operators are closed before we exit.
        op.DatasetGroup.resize(0)

    def testWeirdAxisInfos(self):
        """
        If we add a dataset that has the channel axis in the wrong place,
        the operator should automatically transpose it to be last.
        """
        info, expected_data = self.make_test_data("WeirdAxes.npy", "cxy", (3, 100, 100))

        op = OpDataSelectionGroup(graph=Graph(), forceAxisOrder=False)
        op.WorkingDirectory.setValue(self.workingDir)
        op.DatasetRoles.setValue(["RoleA"])

        op.DatasetGroup.resize(1)
        op.DatasetGroup[0].setValue(info)

        assert op.ImageGroup[0].ready()

        data_from_op = op.ImageGroup[0][:].wait()

        assert data_from_op.dtype == expected_data.dtype
        assert data_from_op.shape == expected_data.shape, (data_from_op.shape, expected_data.shape)
        assert (data_from_op == expected_data).all()

        # op.Image is a synonym for op.ImageGroup[0]
        assert op.Image.ready()
        assert (op.Image[:].wait() == expected_data).all()

        # Ensure that files opened by the inner operators are closed before we exit.
        op.DatasetGroup.resize(0)

    def testNoChannelAxis(self):
        """
        If we add a dataset that is missing a channel axis altogether,
        the operator should automatically append a channel axis.
        """
        info, noChannelData = self.make_test_data("NoChannelAxis.npy", "xy", (100, 100))
        op = OpDataSelectionGroup(graph=Graph())
        op.WorkingDirectory.setValue(self.workingDir)
        op.DatasetRoles.setValue(["RoleA"])

        op.DatasetGroup.resize(1)
        op.DatasetGroup[0].setValue(info)

        assert op.ImageGroup[0].ready()

        # Note that we expect a channel axis to be appended to the data.
        expected_data = noChannelData[:, :, numpy.newaxis]
        data_from_op = op.ImageGroup[0][:].wait()

        assert data_from_op.dtype == expected_data.dtype
        assert data_from_op.shape == expected_data.shape
        assert (data_from_op == expected_data).all()

        # op.Image is a synonym for op.ImageGroup[0]
        assert op.Image.ready()
        assert (op.Image[:].wait() == expected_data).all()

        # Ensure that files opened by the inner operators are closed before we exit.
        op.DatasetGroup.resize(0)
