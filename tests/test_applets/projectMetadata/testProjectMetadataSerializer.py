# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

import os
import numpy
import h5py
from lazyflow.graph import Graph
from ilastik.applets.projectMetadata import ProjectMetadata
from ilastik.applets.projectMetadata.projectMetadataSerializer import ProjectMetadataSerializer

class TestProjectMetadataSerializer(object):
    
    def test(self):
        testProjectName = 'test_project.ilp'
        # Clean up: Delete any lingering test files from the previous run.
        try:
            os.remove(testProjectName)
        except:
            pass
        
        with h5py.File(testProjectName) as testProject:
            testProject.create_dataset("ilastikVersion", data="1.0.0")
            
            metadata = ProjectMetadata()
            metadata.projectName = "Test Project"
            metadata.labeler = "Test Labeler"
            metadata.description = "Test Description"
            
            # Create an empty hdf5 file to serialize to.
            serializer = ProjectMetadataSerializer(metadata, 'ProjectMetadata')
            serializer.serializeToHdf5(testProject, testProjectName)
            
            assert testProject['ProjectMetadata']['ProjectName'].value == metadata.projectName
            assert testProject['ProjectMetadata']['Labeler'].value == metadata.labeler
            assert testProject['ProjectMetadata']['Description'].value == metadata.description
            
            # Now deserialize
            newMetadata = ProjectMetadata()
            deserializer = ProjectMetadataSerializer(newMetadata, 'ProjectMetadata')
            deserializer.deserializeFromHdf5(testProject, testProjectName)
            
            assert newMetadata.projectName == metadata.projectName
            assert newMetadata.labeler == metadata.labeler
            assert newMetadata.description == metadata.description

        os.remove(testProjectName)

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
