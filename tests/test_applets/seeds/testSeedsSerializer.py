###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2017, the ilastik developers
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
from ilastik.applets.seeds.opSeeds import OpSeeds
from ilastik.applets.seeds.seedsSerializer import SeedsSerializer

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

class TestSeedsSerializer(object):

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
            operatorToSave = OpSeeds(graph=graph)
        
            # set some values for the inputs
            operatorToSave.SeedsExist.setValue( True )
            operatorToSave.Unseeded.setValue( False )
            operatorToSave.SmoothingMethod.setValue( "RegionGrowing" )
            operatorToSave.SmoothingSigma.setValue( 7.9 )
            operatorToSave.ComputeMethod.setValue( "Gaussian" )
            #TODO serialhdf5blockslot
            array = numpy.random.random((100,100,100,11,1))
            operatorToSave.Seeds.setValue( array )
    
            # Serialize!
            serializer = SeedsSerializer(operatorToSave, 'Seeds')
            serializer.serializeToHdf5(testProject, testProjectName)
            
            assert testProject['Seeds/SeedsExist'][()] == True
            assert testProject['Seeds/Unseeded'][()] == False
            assert testProject['Seeds/SmoothingMethod'][()] == "RegionGrowing"
            assert testProject['Seeds/SmoothingSigma'][()] == 7.9
            assert testProject['Seeds/ComputeMethod'][()] == "Gaussian"
            #TODO serialhdf5blockslot
            for i in testProject['Seeds']:
                print "X:" + i
            print testProject['Seeds/StorageVersion'][()] 
        
            # Deserialize into a fresh operator
            operatorToLoad = OpSeeds(graph=graph)
            deserializer = SeedsSerializer(operatorToLoad, 'Seeds')
            deserializer.deserializeFromHdf5(testProject, testProjectName)
   
            assert operatorToLoad.SeedsExist.value == True
            assert operatorToLoad.Unseeded.value == False
            assert operatorToLoad.SmoothingMethod.value == "RegionGrowing"
            assert operatorToLoad.SmoothingSigma.value == 7.9
            assert operatorToLoad.ComputeMethod.value == "Gaussian"
            #TODO serialhdf5blockslot


        os.remove(testProjectName)

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})

