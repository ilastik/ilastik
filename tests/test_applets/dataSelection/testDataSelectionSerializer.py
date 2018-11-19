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
import vigra
import numpy
import tempfile
import unittest

from lazyflow.graph import Graph
from ilastik.applets.dataSelection.opDataSelection import OpMultiLaneDataSelectionGroup, DatasetInfo
from ilastik.applets.dataSelection.dataSelectionSerializer import DataSelectionSerializer

import logging
logger = logging.getLogger(__name__)


class TestDataSelectionSerializer(unittest.TestCase):

    def setUp(self):
        self.tmpDir = tempfile.mkdtemp()
        self.tmpFilePath = os.path.join(self.tmpDir, "testDataSelection.npy")

        self.testProjectName = os.path.join(self.tmpDir, 'test_project.ilp')

        self.cleanupFiles = [self.tmpFilePath, self.testProjectName]

        data = numpy.indices((1,10,10,10,2)).sum(0)
        numpy.save(self.tmpFilePath, data)

    def tearDown(self):
        for f in self.cleanupFiles:
            try:
                os.remove(f)
            except:
                pass

        try:
            os.removedirs(self.tmpDir)
        except:
            pass

    def test06(self):
        """
        Test the basic functionality of the v0.6 project format serializer.
        """
        # Create an empty project
        with h5py.File(self.testProjectName) as testProject:
            testProject.create_dataset("ilastikVersion", data=b"1.0.0")

            ##
            ## Serialization
            ##

            # Create an operator to work with and give it some input
            graph = Graph()
            groupName = 'DataSelectionTest'
            info = self._createDatasetInfo()
            operatorToSave = self._createOperatorToSave(graph, testProject,
                                                        info, groupName)

            serializer = DataSelectionSerializer(operatorToSave, groupName)
            assert serializer.base_initialized

            # Now serialize!
            serializer.serializeToHdf5(testProject, self.testProjectName)

            # Check for dataset existence
            datasetInternalPath = serializer.topGroupName + '/local_data/' + info.datasetId
            dataset = testProject[datasetInternalPath][...]

            # Check axistags attribute
            assert 'axistags' in testProject[datasetInternalPath].attrs
            axistags_json = testProject[datasetInternalPath].attrs['axistags']
            axistags = vigra.AxisTags.fromJSON(axistags_json)

            originalShape = operatorToSave.Image[0].meta.shape
            originalAxisTags = operatorToSave.Image[0].meta.axistags

            # Now we can directly compare the shape and axis ordering
            assert dataset.shape == originalShape
            assert axistags == originalAxisTags

            ##
            ## Deserialization
            ##

            # Create an empty operator
            graph = Graph()
            operatorToLoad = OpMultiLaneDataSelectionGroup( graph=graph )
            operatorToLoad.DatasetRoles.setValue( ['Raw Data'] )

            deserializer = DataSelectionSerializer(operatorToLoad, serializer.topGroupName) # Copy the group name from the serializer we used.
            assert deserializer.base_initialized
            deserializer.deserializeFromHdf5(testProject, self.testProjectName)

            assert len(operatorToLoad.DatasetGroup) == len(operatorToSave.DatasetGroup)
            assert len(operatorToLoad.Image) == len(operatorToSave.Image)

            assert operatorToLoad.Image[0].meta.shape == operatorToSave.Image[0].meta.shape
            assert operatorToLoad.Image[0].meta.axistags == operatorToSave.Image[0].meta.axistags

    def testShapeAndDtypeSerialization(self):
        """
        Test the serialization of additional shape and dtype attributes added
        in order to re-create the metadata in headless mode with no raw data
        """
        # Create an empty project
        with h5py.File(self.testProjectName) as testProject:
            # Create an operator to work with and give it some input
            graph = Graph()
            groupName = 'DataSelectionTest'
            info = self._createDatasetInfo()
            operatorToSave = self._createOperatorToSave(graph, testProject,
                                                        info, groupName)

            # Serialize
            serializer = DataSelectionSerializer(operatorToSave, groupName)
            serializer.serializeToHdf5(testProject, self.testProjectName)

            # Assert lane's dtype and shape attributes exist
            rawDataPath = groupName + '/infos/lane0000/Raw Data'
            assert 'shape' in testProject[rawDataPath]
            assert 'dtype' in testProject[rawDataPath]

            # Assert their values are correct
            assert tuple(testProject[rawDataPath + '/shape'].value) == operatorToSave.Image[0].meta.shape
            assert numpy.dtype(testProject[rawDataPath + '/dtype'].value.decode('utf-8')) == operatorToSave.Image[0].meta.dtype

            # Deserialize and check datasetInfo
            graph = Graph()
            operatorToLoad = OpMultiLaneDataSelectionGroup(graph=graph)
            operatorToLoad.DatasetRoles.setValue(['Raw Data'])

            deserializer = DataSelectionSerializer(operatorToLoad, groupName)
            deserializer.deserializeFromHdf5(testProject, self.testProjectName)

            datasetInfo = operatorToLoad.DatasetGroup[0][0][:].wait()[0]

            assert datasetInfo.laneShape == operatorToLoad.Image[0].meta.shape
            assert datasetInfo.laneDtype == operatorToLoad.Image[0].meta.dtype


    def _createOperatorToSave(self, graph, projectFile, info, groupName):
        operatorToSave = OpMultiLaneDataSelectionGroup(graph=graph)
        operatorToSave.ProjectFile.setValue(projectFile)
        operatorToSave.WorkingDirectory.setValue(os.path.split(__file__)[0])
        operatorToSave.ProjectDataGroup.setValue(f'{groupName}/local_data')
        operatorToSave.DatasetRoles.setValue(['Raw Data'])
        operatorToSave.DatasetGroup.resize(1)
        operatorToSave.DatasetGroup[0][0].setValue(info)
        return operatorToSave

    def _createDatasetInfo(self):
        info = DatasetInfo()
        info.filePath = self.tmpFilePath
        info.location = DatasetInfo.Location.ProjectInternal
        return info
