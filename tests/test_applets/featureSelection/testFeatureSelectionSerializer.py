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
import numpy
import h5py
from lazyflow.graph import Graph
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection, getFeatureIdOrder
from ilastik.applets.featureSelection.featureSelectionSerializer import FeatureSelectionSerializer

class TestFeatureSelectionSerializer(object):

    def test(self):    
        # Define the files we'll be making    
        testProjectName = 'test_project.ilp'
        # Clean up: Remove the test data files we created last time (just in case)
        for f in [testProjectName]:
            try:
                os.remove(f)
            except:
                pass
    
        # Create an empty project
        with h5py.File(testProjectName, 'w') as testProject:
            testProject.create_dataset("ilastikVersion", data=b"1.0.0")
            
            # Create an operator to work with and give it some input
            graph = Graph()
            operatorToSave = OpFeatureSelection(graph=graph)

            scales = operatorToSave.Scales.value
            featureIds = operatorToSave.FeatureIds.value

            # All False (no features selected)
            selectionMatrix = operatorToSave.MinimalFeatures
        
            # Change a few to True
            selectionMatrix[0,0] = True
            selectionMatrix[1,1] = True
            selectionMatrix[2,2] = True
            selectionMatrix[3,3] = True
            selectionMatrix[4,4] = True
            selectionMatrix[5,5] = True
            operatorToSave.SelectionMatrix.setValue(selectionMatrix)
            
            # Serialize!
            serializer = FeatureSelectionSerializer(operatorToSave, 'FeatureSelections')
            serializer.serializeToHdf5(testProject, testProjectName)

        with h5py.File(testProjectName, 'r') as testProject:
            file_feature_ids = numpy.asarray(list(map(lambda s: s.decode('utf-8'), testProject['FeatureSelections/FeatureIds'].value)))
            
            assert (testProject['FeatureSelections/Scales'].value == scales).all()
            assert (file_feature_ids == featureIds).all()
            assert (testProject['FeatureSelections/SelectionMatrix'].value == selectionMatrix).all()
        
            # Deserialize into a fresh operator
            operatorToLoad = OpFeatureSelection(graph=graph)

            deserializer = FeatureSelectionSerializer(operatorToLoad, 'FeatureSelections')
            deserializer.deserializeFromHdf5(testProject, testProjectName)
            assert operatorToLoad.FeatureIds.value == getFeatureIdOrder(), \
                "Feature IDs were deserialized to a strange order!"
            
            assert isinstance(operatorToLoad.Scales.value, list)
            assert isinstance(operatorToLoad.FeatureIds.value, list)

            assert (operatorToLoad.Scales.value == scales)
            assert (operatorToLoad.FeatureIds.value == featureIds)
            assert (operatorToLoad.SelectionMatrix.value == selectionMatrix).all()

        os.remove(testProjectName)
