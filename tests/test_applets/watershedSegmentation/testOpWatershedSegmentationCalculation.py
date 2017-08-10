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


    def createBoundariesAndSeedsForWatershed(self):
        """
        boundaries: a square in the middle
        seeds: background seeds on each top left; on other seeds in the total middle
        """
        shape = (1,11,11,11,1)
        data = [ 3,4,5,6,7]
        dataB = [ 0]
        dataS1 = [ 5]
        arrayBoundaries = numpy.zeros(shape, dtype=numpy.uint8)
        arraySeeds      = numpy.zeros(shape, dtype=numpy.uint8)
        for t in range(shape[0]):
            for x in range(shape[1]):
                for y in range(shape[2]):
                    for z in range(shape[3]):
                        if x in data and y in data and z in data:
                            arrayBoundaries[t,x,y,z] =  255
                        # background seed
                        if x in dataB and y in dataB: # and z in dataB: # on all slides
                            arraySeeds[t,x,y,z] =  1
                        if x in dataS1 and y in dataS1 and z in dataS1:
                            arraySeeds[t,x,y,z] =  2

        arrayBoundaries = vigra.taggedView(arrayBoundaries, axistags='txyzc')
        arraySeeds      = vigra.taggedView(arraySeeds, axistags='txyzc')



        # 2D, with frame 5
        arrayBoundaries2D = numpy.zeros(arrayBoundaries.shape[:3] + (1,1,), dtype=numpy.uint8)
        arrayBoundaries2D[:,:,:,0,:] = arrayBoundaries[:,:,:,5,:]
        arrayBoundaries2D   = vigra.taggedView(arrayBoundaries2D, axistags='txyzc')
        arraySeeds2D = numpy.zeros(arraySeeds.shape[:3] + (1,1,), dtype=numpy.uint8)
        arraySeeds2D[:,:,:,0,:] = arraySeeds[:,:,:,5,:]
        arraySeeds2D   = vigra.taggedView(arraySeeds2D, axistags='txyzc')

        # to view the images
        #export_image_to_hdf5(arrayBoundaries, "boundariesForWatershed.h5")
        #export_image_to_hdf5(arraySeeds, "seedsForWatershed.h5")
        #export_image_to_hdf5(arrayBoundaries2D, "boundaries2DForWatershed.h5")
        #export_image_to_hdf5(arraySeeds2D, "seeds2DForWatershed.h5")

        return arrayBoundaries, arraySeeds, arrayBoundaries2D, arraySeeds2D




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

            # get boundaries, also for 2D
            self.boundariesWS, self.seedsWS, self.boundariesWS2D, self.seedsWS2D = \
                    self.createBoundariesAndSeedsForWatershed()

            # predefined random values
            op.Boundaries.setValue( boundariesFloat32 )
            op.Seeds.setValue( self.taggedArray )
            


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
                """
                methods need to remain and have its correct default value
                neighbors need to be converted correctly with given dimension
                terminate is tested, also for cases: e.g. unionfind + keepContours -> unionfind + completeGrow
                max_cost is tested
                """

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




            def WS3D():
                """
                prepare watershed for 3D case
                """
                shape = self.boundariesWS.shape
                watershed = numpy.zeros(shape, dtype=numpy.uint8)
                t=0
                if op.Neighbors.value == "direct":
                    neighbors = 6
                else:
                    neighbors = 26
                if op.Method.value == "UnionFind":
                        watershed    = executeWSAlgorithm(self.boundariesWS[t],\
                                None, neighbors)
                else:
                        watershed    = executeWSAlgorithm(self.boundariesWS[t],\
                                self.seedsWS[t].astype(numpy.uint32), neighbors)
                return watershed

            def WS2D():
                """
                prepare watershed for 2D case
                """
                shape = self.boundariesWS2D.shape
                watershed = numpy.zeros(shape, dtype=numpy.uint8)
                t=0
                if op.Neighbors.value == "direct":
                    neighbors = 4
                else:
                    neighbors = 8
                if op.Method.value == "UnionFind":
                    watershed[0,:,:,0,:]    = executeWSAlgorithm(self.boundariesWS2D[t,:,:,0,:],\
                            None, neighbors)
                else:
                    watershed[0,:,:,0,:]    = executeWSAlgorithm(self.boundariesWS2D[t,:,:,0,:],\
                            self.seedsWS2D[t,:,:,0,:].astype(numpy.uint32), neighbors)
                return watershed



            def executeWSAlgorithm(boundaries, seeds, neighbors):
                """
                take the parameters from the operators (except neighbors) and execute the algorithm
                """
                method      = op.Method.value
                terminate   = op.Terminate.value
                maxCost     = op.MaxCost.value

                (labelImage, maxRegionLabel) = vigra.analysis.watershedsNew(\
                image           = boundaries,
                seeds           = seeds,
                neighborhood    = neighbors,
                method          = method,
                terminate       = terminate,
                max_cost        = maxCost)

                return labelImage




            def testWatershedCalculations():
                """
                test the Watershed with RegionGrowing (with all parameters),
                Turbo and UnionFind for direct & indirect

                0. t,x,y,z: in ilastik, the roi will be always without t, so don't test this here
                1. WS2D for x,y
                2. WS3D for x,y,z
                """

                for function in [WS2D, WS3D]:
                    # default seetings
                    op.SeedsExist.setValue(True)
                    op.Boundaries.setValue(None)
                    op.Seeds.setValue(None)
                    op.MaxCost.setValue(0)
                    op.Terminate.setValue(       vigra.analysis.SRGType.CompleteGrow)
                    # different boundaries/seeds for 2D and 3D
                    if function == WS3D:
                        op.Boundaries.setValue(self.boundariesWS)
                        op.Seeds.setValue(self.seedsWS)
                    if function == WS2D:
                        op.Boundaries.setValue(self.boundariesWS2D)
                        op.Seeds.setValue(self.seedsWS2D)


                    # UnionFind
                    op.Method.setValue("UnionFind")
                    op.Neighbors.setValue("direct") 
                    watershed = function()
                    assert (op.Output[:].wait() == watershed).all()

                    op.Neighbors.setValue("indirect") 
                    watershed = function()
                    assert (op.Output[:].wait() == watershed).all()

                    # Turbo
                    op.Method.setValue("Turbo")
                    op.Neighbors.setValue("direct") 
                    watershed = function()
                    assert (op.Output[:].wait() == watershed).all()
                    op.Neighbors.setValue("indirect") 
                    watershed = function()
                    assert (op.Output[:].wait() == watershed).all()

                    # RegionGrowing: CompleteGrow
                    op.Method.setValue("RegionGrowing")
                    op.Neighbors.setValue("direct") 
                    watershed = function()
                    assert (op.Output[:].wait() == watershed).all()
                    op.Neighbors.setValue("indirect") 
                    watershed = function()
                    assert (op.Output[:].wait() == watershed).all()

                    # Region Growing: KeepContours
                    op.Terminate.setValue(       vigra.analysis.SRGType.KeepContours)
                    op.Neighbors.setValue("direct") 
                    watershed = function()
                    assert (op.Output[:].wait() == watershed).all()
                    op.Neighbors.setValue("indirect") 
                    watershed = function()
                    assert (op.Output[:].wait() == watershed).all()

                    # Region Growing: KeepContours
                    op.Terminate.setValue(       vigra.analysis.SRGType.StopAtThreshold)
                    op.MaxCost.setValue(5)
                    op.Neighbors.setValue("direct") 
                    watershed = function()
                    assert (op.Output[:].wait() == watershed).all()
                    op.Neighbors.setValue("indirect") 
                    watershed = function()
                    assert (op.Output[:].wait() == watershed).all()


            # execute the tests
            testWatershedCalculations()
            test_check_SeedsExist_plus_WSMethod_fit_together()
            test_prepareInputParameter()


        os.remove(testProjectName)

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})

