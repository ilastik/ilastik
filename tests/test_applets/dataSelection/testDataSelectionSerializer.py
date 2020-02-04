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
import h5py
import vigra
import numpy
import tempfile
from pathlib import Path
import unittest
import pytest

from ilastik.applets.dataSelection.opDataSelection import (
    OpMultiLaneDataSelectionGroup,
    DatasetInfo,
    ProjectInternalDatasetInfo,
)
from ilastik.applets.dataSelection.opDataSelection import ProjectInternalDatasetInfo
from ilastik.applets.dataSelection.dataSelectionSerializer import DataSelectionSerializer


import logging

logger = logging.getLogger(__name__)

TOP_GROUP_NAME = "some_group"


@pytest.fixture
def serializer(empty_project_file, graph):
    opDataSelectionGroup = OpMultiLaneDataSelectionGroup(graph=graph)
    opDataSelectionGroup.ProjectFile.setValue(empty_project_file)
    opDataSelectionGroup.WorkingDirectory.setValue(Path(empty_project_file.filename).parent)
    opDataSelectionGroup.DatasetRoles.setValue(["Raw Data"])
    opDataSelectionGroup.DatasetGroup.resize(1)

    serializer = DataSelectionSerializer(opDataSelectionGroup, TOP_GROUP_NAME)
    return serializer


@pytest.fixture
def internal_datasetinfo(serializer, png_image) -> ProjectInternalDatasetInfo:
    inner_path = serializer.importStackAsLocalDataset([str(png_image)])
    project_file = serializer.topLevelOperator.ProjectFile.value
    info = ProjectInternalDatasetInfo(inner_path=inner_path, project_file=project_file)
    return info


def test06(serializer, internal_datasetinfo, empty_project_file, graph):
    """
    Test the basic functionality of the v0.6 project format serializer.
    """
    serializer.topLevelOperator.DatasetGroup[0][0].setValue(internal_datasetinfo)
    empty_project_file.create_dataset("ilastikVersion", data=b"1.0.0")
    serializer.serializeToHdf5(empty_project_file, empty_project_file.filename)

    # Check for dataset existence
    dataset = empty_project_file[internal_datasetinfo.inner_path]

    # Check axistags attribute
    assert "axistags" in dataset.attrs
    axistags_json = empty_project_file[internal_datasetinfo.inner_path].attrs["axistags"]
    axistags = vigra.AxisTags.fromJSON(axistags_json)

    originalShape = serializer.topLevelOperator.Image[0].meta.shape
    originalAxisTags = serializer.topLevelOperator.Image[0].meta.axistags

    # Now we can directly compare the shape and axis ordering
    assert dataset.shape == originalShape
    assert axistags == originalAxisTags

    # Create an empty operator
    operatorToLoad = OpMultiLaneDataSelectionGroup(graph=graph)
    operatorToLoad.DatasetRoles.setValue(["Raw Data"])

    deserializer = DataSelectionSerializer(
        operatorToLoad, serializer.topGroupName
    )  # Copy the group name from the serializer we used.
    assert deserializer.base_initialized
    deserializer.deserializeFromHdf5(empty_project_file, empty_project_file.filename)

    assert len(operatorToLoad.DatasetGroup) == len(serializer.topLevelOperator.DatasetGroup)
    assert len(operatorToLoad.Image) == len(serializer.topLevelOperator.Image)

    assert operatorToLoad.Image[0].meta.shape == serializer.topLevelOperator.Image[0].meta.shape
    assert operatorToLoad.Image[0].meta.axistags == serializer.topLevelOperator.Image[0].meta.axistags
