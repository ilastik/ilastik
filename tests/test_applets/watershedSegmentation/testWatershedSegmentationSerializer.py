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
from ilastik.applets.watershedSegmentation.opWatershedSegmentation import OpWatershedSegmentation
from ilastik.applets.watershedSegmentation.watershedSegmentationSerializer import WatershedSegmentationSerializer

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

class TestWatershedSegmentationSerializer(object):

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
        with h5py.File(testProjectName) as testProject:
            testProject.create_dataset("ilastikVersion", data="1.0.0")
            
            # Create an operator to work with and give it some input
            graph = Graph()
            operatorToSave = OpWatershedSegmentation(graph=graph)
            dataShape = (1,10,100,100,1)
        
            # set some values for the inputs
            operatorToSave.ShowWatershedLayer.setValue( True )
            operatorToSave.InputSeedsChanged.setValue( False )
            operatorToSave.WSNeighbors.setValue( "direct" )
                #LabelNames, LabelColors and PmapColors
            operatorToSave.LabelNames.setValue( ["Label1", "Label2"] )
            operatorToSave.LabelColors.setValue( [(255,30,30), (30,255,30)] )
            operatorToSave.PmapColors.setValue( [(255,30,30), (30,255,30)] )
            #not needed: serialblockslot
            #not needed: serialhdf5blockslot
 
            # Serialize!
            serializer = WatershedSegmentationSerializer(operatorToSave, 'WatershedSegmentation')
            serializer.serializeToHdf5(testProject, testProjectName)
            
            assert testProject['WatershedSegmentation/ShowWatershedLayer'][()] == True
            assert testProject['WatershedSegmentation/InputSeedsChanged'][()] == False
            assert testProject['WatershedSegmentation/WSNeighbors'][()] == "direct"
            assert (numpy.array(testProject['WatershedSegmentation/LabelNames'][()]) ==\
                    numpy.array(["Label1", "Label2"])).all()
            assert (numpy.array(testProject['WatershedSegmentation/LabelColors'][()]) ==\
                    numpy.array([(255,30,30), (30,255,30)])).all()
            assert (numpy.array(testProject['WatershedSegmentation/PmapColors'][()]) ==\
                    numpy.array([(255,30,30), (30,255,30)])).all()
            #not needed: serialblockslot
            #not needed: serialhdf5blockslot
        
            # Deserialize into a fresh operator
            operatorToLoad = OpWatershedSegmentation(graph=graph)
            deserializer = WatershedSegmentationSerializer(operatorToLoad, 'WatershedSegmentation')
            deserializer.deserializeFromHdf5(testProject, testProjectName)
   
            assert operatorToLoad.ShowWatershedLayer.value == True
            assert operatorToLoad.InputSeedsChanged.value == False
            assert operatorToLoad.WSNeighbors.value == "direct"
            assert operatorToSave.LabelNames.value == operatorToLoad.LabelNames.value
            assert (numpy.array(operatorToSave.LabelColors.value) == numpy.array(operatorToLoad.LabelColors.value)).all()
            assert (numpy.array(operatorToSave.PmapColors.value) == numpy.array(operatorToLoad.PmapColors.value)).all()

            #not needed: serialblockslot
            #not needed: serialhdf5blockslot


        os.remove(testProjectName)

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})

