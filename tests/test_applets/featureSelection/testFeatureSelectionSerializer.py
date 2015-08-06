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
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
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
            testProject.create_dataset("ilastikVersion", data="1.0.0")
            
            # Create an operator to work with and give it some input
            graph = Graph()
            operatorToSave = OpFeatureSelection(graph=graph, filter_implementation='Original')
        
            # Configure scales        
            scales = [0.1, 0.2, 0.3, 0.4, 0.5]
            operatorToSave.Scales.setValue(scales)
        
            # Configure feature types
            featureIds = [ 'GaussianSmoothing',
                           'LaplacianOfGaussian' ]
            operatorToSave.FeatureIds.setValue(featureIds)
        
            # All False (no features selected)
            selectionMatrix = numpy.zeros((2, 5), dtype=bool)
        
            # Change a few to True
            selectionMatrix[0,0] = True
            selectionMatrix[1,0] = True
            selectionMatrix[0,2] = True
            selectionMatrix[1,4] = True
            operatorToSave.SelectionMatrix.setValue(selectionMatrix)
            
            # Serialize!
            serializer = FeatureSelectionSerializer(operatorToSave, 'FeatureSelections')
            serializer.serializeToHdf5(testProject, testProjectName)
            
            assert (testProject['FeatureSelections/Scales'].value == scales).all()
            assert (testProject['FeatureSelections/FeatureIds'].value == featureIds).all()
            assert (testProject['FeatureSelections/SelectionMatrix'].value == selectionMatrix).all()
        
            # Deserialize into a fresh operator
            operatorToLoad = OpFeatureSelection(graph=graph, filter_implementation='Original')
            deserializer = FeatureSelectionSerializer(operatorToLoad, 'FeatureSelections')
            deserializer.deserializeFromHdf5(testProject, testProjectName)
            
            assert isinstance(operatorToLoad.Scales.value, list)
            assert isinstance(operatorToLoad.FeatureIds.value, list)

            assert (operatorToLoad.Scales.value == scales)
            assert (operatorToLoad.FeatureIds.value == featureIds)
            assert (operatorToLoad.SelectionMatrix.value == selectionMatrix).all()

        os.remove(testProjectName)

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
