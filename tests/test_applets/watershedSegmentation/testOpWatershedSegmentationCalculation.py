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
import vigra
from lazyflow.graph import Graph
from ilastik.applets.watershedSegmentation.opWatershedSegmentationCalculation import OpWatershedSegmentationCalculation

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()


import h5py

def export_image_to_hdf5(labelImage, name):

    with h5py.File(name, "w") as hf:
        hf.create_dataset("exported_data", data=labelImage)




class TestOpWatershedSegmentationCalculation(object):
    """
    for a more detailed explanation on which data should be when, 
    use the Master Thesis: Interactive Watershed Based Segmentation on Biological Images
    by Andreas Haller
    """
    def createTestSet(self):
        # set some values for the inputs
        arrayFloat32    = numpy.random.random((100,100,100,11,1)).astype(numpy.float32)
        arrayUint8      = numpy.random.random((100,100,100,11,1)).astype(numpy.uint8)
        taggedArrayFloat32   = vigra.taggedView(arrayFloat32, axistags='txyzc')
        taggedArrayUint8     = vigra.taggedView(arrayUint8, axistags='txyzc')

        return taggedArrayFloat32, taggedArrayUint8
    '''

    def createLabeledAndUnlabeledSeeds(self):
        """
        make strides with different colors or binary (for unlabeled)
        """
        shape = (10,10,10,10,1)
        array       = numpy.zeros(shape, dtype=numpy.uint8)
        arrayBinary = numpy.zeros(shape, dtype=numpy.uint8)

        # create some 3x3x3x3 squares in the 4D room with different values
        size = 2
        for t in range(0,7,3):
            for x in range(0,7,3):
                for y in range(0,7,3):
                    for z in range(0,7,3):
                        array[t:t+size, x:x+size, y:y+size, z:z+size] = t + x + y + z + 1
                        arrayBinary[t:t+size, x:x+size, y:y+size, z:z+size] = 1

        # to view the images
        #export_image_to_hdf5(array, "labeledArray.h5")
        #export_image_to_hdf5(arrayBinary, "labeledArrayBinary.h5")

        return array, arrayBinary

    def createBoundariesForGenerateSeeds(self):
        """
        a centered box with values that become smaller to the middle
        """
        shape = (11,11,11,11,1)
        array       = numpy.zeros(shape, dtype=numpy.uint8)
        for t in range(shape[0]):
            for x in range(shape[1]):
                for y in range(shape[2]):
                    for z in range(shape[3]):
                        #array[t, x, y, z] = numpy.amax([x,y,z])
                        if x < 5 and y < 5 :
                            xyValue = 10 - numpy.amin([x,y])
                        if x > 4 and y > 4 :
                            xyValue = numpy.amax([x,y])
                        if x > 4 and y < 5 :
                            xyValue = 10 - numpy.amin([10-x,y])
                        if x < 5 and y > 4 :
                            xyValue = 10 - numpy.amin([x,10-y])

                        if z == 1 or z == 3 or z == 5 or z == 7 or z == 9:
                            xyValue = 255 # important to receive minima for 3d and 3d with time
                        array[t,x,y,z] =  xyValue 

        array     = vigra.taggedView(array, axistags='txyzc')

        # to view the images
        #export_image_to_hdf5(array, "boundariesForGeneration.h5")

        return array

    '''



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
            op = OpWatershedSegmentationCalculation(graph=graph)
        
            # set some values for the inputs
            boundariesFloat32, boundariesUint8     = self.createTestSet()
            self.taggedArray = boundariesFloat32

            '''
            self.labeledArray, self.labeledArrayBinary = self.createLabeledAndUnlabeledSeeds()
            self.boundariesForGeneration = self.createBoundariesForGenerateSeeds()
            '''

            # predefined random values
            op.Boundaries.setValue( boundariesFloat32 )
            op.Seeds.setValue( self.taggedArray )
            

            '''
            # predefined settings, just that they are set, but not needed in particular
            op.GenerateSeeds.setValue( False )
            op.Unseeded.setValue( False )
            op.SmoothingMethod.setValue( "RegionGrowing" )
            op.SmoothingSigma.setValue( 7.9 )
            op.ComputeMethod.setValue( "Gaussian" )
            op.SeedsExist.setValue( True )
            '''

            def test_check_SeedsExist_plus_WSMethod_fit_together():
                """
                True if SeedsExist = True or Method = UnionFind, 
                else False
                """

                op.SeedsExist.setValue(True)
                assert op.check_SeedsExist_plus_WSMethod_fit_together()

                op.SeedsExist.setValue(False)
                op.Method.setValue( "RegionGrowing" )
                assert not op.check_SeedsExist_plus_WSMethod_fit_together()
                op.Method.setValue( "Turbo" )
                assert not op.check_SeedsExist_plus_WSMethod_fit_together()
                op.Method.setValue( "UnionFind" )
                assert op.check_SeedsExist_plus_WSMethod_fit_together()


            def test_prepareInputParameter():

                # default values
                op.Method.setValue("RegionGrowing")
                op.Neighbors.setValue("direct")
                op.MaxCost.setValue(0)
                op.Terminate.setValue(vigra.analysis.SRGType.CompleteGrow)
                dimension = 2

                # test method
                op.Method.setValue("RegionGrowing")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert method == "RegionGrowing"

                op.Method.setValue("UnionFind")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert method == "UnionFind"

                op.Method.setValue("Turbo")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert method == "Turbo"

                op.Method.setValue("rubbish")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert method == "RegionGrowing"

                # default
                op.Method.setValue("RegionGrowing")


                # test neighbors:
                # dim2
                dimension = 2
                op.Neighbors.setValue("direct")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert neighbors == 4
                op.Neighbors.setValue("indirect")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert neighbors == 8
                op.Neighbors.setValue("rubbish")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert neighbors == 4
                # dim3
                dimension = 3
                op.Neighbors.setValue("direct")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert neighbors == 6
                op.Neighbors.setValue("indirect")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert neighbors == 26
                op.Neighbors.setValue("rubbish")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert neighbors == 6

                # default
                op.Neighbors.setValue("direct")
                dimension = 2


                # test terminate:
                # uncomfortable cases will be caught by vigra itself, 
                # but in case not, they are caught here as well
                op.Method.setValue("RegionGrowing")

                op.Terminate.setValue(       vigra.analysis.SRGType.CompleteGrow)
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert terminate      == vigra.analysis.SRGType.CompleteGrow

                op.Terminate.setValue(       vigra.analysis.SRGType.KeepContours)
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert terminate      == vigra.analysis.SRGType.KeepContours
                
                op.Terminate.setValue(       vigra.analysis.SRGType.StopAtThreshold)
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert terminate      == vigra.analysis.SRGType.StopAtThreshold

                op.Terminate.setValue(       "rubbish")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert terminate      == vigra.analysis.SRGType.CompleteGrow


                # uncomfortable cases
                op.Method.setValue("Turbo")
                op.Terminate.setValue(       vigra.analysis.SRGType.KeepContours)
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert terminate      == vigra.analysis.SRGType.CompleteGrow


                op.Terminate.setValue(       vigra.analysis.SRGType.StopAtThreshold)
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert terminate      == vigra.analysis.SRGType.CompleteGrow

                
                op.Method.setValue("UnionFind")
                op.Terminate.setValue(       vigra.analysis.SRGType.KeepContours)
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert terminate      == vigra.analysis.SRGType.CompleteGrow

                op.Terminate.setValue(       vigra.analysis.SRGType.StopAtThreshold)
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert terminate      == vigra.analysis.SRGType.CompleteGrow


                op.Method.setValue("RegionGrowing")
                op.Terminate.setValue(       vigra.analysis.SRGType.StopAtThreshold)
                op.MaxCost.setValue("rubbish")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert terminate      == vigra.analysis.SRGType.CompleteGrow

                # test maxCost:
                op.MaxCost.setValue(100.00)
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert maxCost      == 100.00

                op.MaxCost.setValue(0)
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert maxCost      == 0

                op.MaxCost.setValue("rubbish")
                method, neighbors, terminate, maxCost = op.prepareInputParameter(dimension)
                assert maxCost      == 0




            test_check_SeedsExist_plus_WSMethod_fit_together()
            test_prepareInputParameter()


    
            

        os.remove(testProjectName)

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})

