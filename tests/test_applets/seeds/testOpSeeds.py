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
from ilastik.applets.seeds.opSeeds import OpSeeds
#from ilastik.applets.seeds.seedsSerializer import SeedsSerializer

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()


import h5py

def export_image_to_hdf5(labelImage, name):

    with h5py.File(name, "w") as hf:
        hf.create_dataset("exported_data", data=labelImage)


def empty_t(arrayIn, shape):
    """
    add empty t-axis
    input needs to have a first axis, because ReOrderAxis does this for the user itself
    :param arrayIn: all five dimensions, with full t
    :returns: arrayIn with t dimension = 1
    """
    arrayOut= numpy.zeros((1,) + shape[1:])
    arrayOut[0] = arrayIn

    return arrayOut

def empty_t_z(arrayIn, shape):
    # add empty t, z and c-axis
    # input needs to have a first axis, because ReOrderAxis does this for the user itself
    arrayOut = numpy.zeros((1,) + shape[1:3] + (1,1,) )
    arrayOut[0,:,:,0,:] = arrayIn

    return arrayOut



def empty_t_z_c(arrayIn, shape):
    # add empty t, z and c-axis
    # input needs to have a first axis, because ReOrderAxis does this for the user itself
    arrayOut = numpy.zeros((1,) + shape[1:3] + (1,1,) )
    arrayOut[0,:,:,0,0] = arrayIn

    return arrayOut



class TestOpSeeds(object):
    """
    for a more detailed explanation on which data should be outcome at which time, 
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

                        '''
                        if z < 6:
                            zValue = z + 1
                        if z > 5:
                            zValue = 11 - z
                        array[t,x,y,z] =  xyValue * 5 + zValue
                        print xyValue * 5 + zValue
                        '''
                        if z == 1 or z == 3 or z == 5 or z == 7 or z == 9:
                            xyValue = 255 # important to receive minima for 3d and 3d with time
                        array[t,x,y,z] =  xyValue 

        array     = vigra.taggedView(array, axistags='txyzc')

        # to view the images
        #export_image_to_hdf5(array, "boundariesForGeneration.h5")

        return array




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
            op = OpSeeds(graph=graph)
        
            # set some values for the inputs
            boundariesFloat32, boundariesUint8     = self.createTestSet()
            self.taggedArray = boundariesFloat32

            self.labeledArray, self.labeledArrayBinary = self.createLabeledAndUnlabeledSeeds()
            self.boundariesForGeneration = self.createBoundariesForGenerateSeeds()

            # predefined random values
            op.RawData.setValue( self.taggedArray )
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


            def testWSMethodOutput():
                """
                test the output WSMethod
                1. Unseeded = True => WSMethod = "UnionFind"
                Unseeded = False 
                2.          => Boundaries: uint8 
                                  WSMethod = "Turbo"
                3.          => else: 
                                  WSMethod = "RegionGrowing"
                """
                
                # 1.
                op.Unseeded.setValue( True )
                assert op.WSMethod.value == "UnionFind"

                # 2.
                op.Unseeded.setValue( False )
                op.Boundaries.setValue(boundariesUint8)
                assert op.WSMethod.value == "Turbo"

                # 3.
                op.Boundaries.setValue(boundariesFloat32)
                assert op.WSMethod.value == "RegionGrowing"

            def testSeedsExistOutput():
                """
                1. Seeds not ready and GenerateSeeds = False
                    => SeedsExist = False
                2. Seeds ready or GenerateSeeds = True
                    => SeedsExist = True 

                """
                # 1.
                op.Seeds.setValue(None)
                op.GenerateSeeds.setValue(False)
                assert op.SeedsExist.value == False

                # 2.1 GenerateSeeds = True
                op.GenerateSeeds.setValue(True)
                assert op.SeedsExist.value == True
                # 2.2 both true
                op.Seeds.setValue(self.taggedArray)
                assert op.SeedsExist.value == True
                # 2.3 Seeds ready
                op.GenerateSeeds.setValue(False)
                assert op.SeedsExist.value == True




            def testGenerateSeedsOutput():
                """
                if the given Seeds change (remove and add), the GenerateSeeds needs to be False afterwards
                """
                # init and check
                op.GenerateSeeds.setValue(True)
                assert op.GenerateSeeds.value == True

                # test
                op.Seeds.setValue(None)
                op.Seeds.setValue(self.taggedArray)
                assert op.GenerateSeeds.value == False

            def SeedsBoundariesRawData_ToNone():
                op.Seeds.setValue(None)
                op.Boundaries.setValue(None)
                op.RawData.setValue(None)

            def SeedsBoundariesRawData_To(array):
                op.Seeds.setValue(array)
                op.Boundaries.setValue(array)
                op.RawData.setValue(array)

            def testSeedsOutOutput():
                """
                1. if seeds changed (removed and added):
                    => SeedsOut = Seeds
                    1.1 already labeled array
                    1.2 array is unlabeled (comparision of manual labeling and labeling in OpSeeds)
                2. if GenerateSeeds = True:
                    => SeedsOut = Generated Seeds (means: SeedsOut != Seeds && SeedsOut != 0)
                    test Generation of Seeds with gaussian smoothing (sigma = 1) and local minima
                3. no seeds and GenerateSeeds = False

                Using the cached version leads to no errors
                The array will be labeled if necessary
                """

                # 1.
                shape = self.labeledArrayBinary.shape
                # 1.1
                # set data
                SeedsBoundariesRawData_ToNone() # resets GenerateSeeds to False
                SeedsBoundariesRawData_To(self.labeledArray)

                assert (op.SeedsOutCached[:].wait() == op.Seeds[:].wait()).all()

                # 1.2
                # 1.2.1 t,x,y,z
                SeedsBoundariesRawData_ToNone()
                SeedsBoundariesRawData_To(self.labeledArrayBinary)

                # manual labeling
                seeds_labeled = numpy.zeros(shape, dtype=numpy.uint8)
                for t in range(shape[0]):
                    seeds_labeled[t] = vigra.analysis.labelMultiArrayWithBackground(self.labeledArray[t])
                assert (op.SeedsOutCached[:].wait() == seeds_labeled).all()

                # 1.2.2 x,y,z
                # add empty t-axis
                labeledArrayBinary_correctFormat = empty_t(self.labeledArrayBinary[0], shape)

                SeedsBoundariesRawData_ToNone()
                SeedsBoundariesRawData_To(labeledArrayBinary_correctFormat)

                # manual labeling
                seeds_labeled = vigra.analysis.labelMultiArrayWithBackground(self.labeledArray[0])
                
                # add empty t-axis
                seeds_labeled_correct_format = empty_t(seeds_labeled, shape)

                assert (op.SeedsOutCached[:].wait() == seeds_labeled_correct_format).all()

                # 1.2.3 x,y
                # add empty t, z and c-axis
                labeledArrayBinary_correctFormat = empty_t_z(self.labeledArrayBinary[0,:,:,0,:], shape)

                SeedsBoundariesRawData_ToNone()
                SeedsBoundariesRawData_To(labeledArrayBinary_correctFormat)

                # manual labeling
                seeds_labeled = vigra.analysis.labelMultiArrayWithBackground(self.labeledArray[0,:,:,0,:])
                
                # add empty t, z and c-axis
                seeds_labeled_correct_format = empty_t_z(seeds_labeled, shape)

                assert (op.SeedsOutCached[:].wait() == seeds_labeled_correct_format).all()

                # 2. 
                sigma = 1.0
                shape = self.boundariesForGeneration.shape
                op.SmoothingMethod.setValue( 0 ) # index 0 = Gaussian
                op.SmoothingSigma.setValue( sigma)
                op.ComputeMethod.setValue( 0 ) # index 0 = Local Minima
                

                # 2.1 t,x,y,z
                #export_image_to_hdf5(boundariesXYZ, "boundaries3dt.h5")
                SeedsBoundariesRawData_ToNone()
                SeedsBoundariesRawData_To(self.boundariesForGeneration)
                # each time before request, because changes in the seeds lead to GenerateSeeds=False
                op.GenerateSeeds.setValue(True)

                # smoothing, minima and labeling
                minima = numpy.zeros(shape, numpy.uint8)
                for t in range(shape[0]):
                    smoothed = vigra.filters.gaussianSmoothing(self.boundariesForGeneration[t,:,:,:,0], sigma)
                    minima_unlabeled = vigra.analysis.extendedLocalMinima3D(smoothed,marker=1)
                    minima[t,:,:,:,0] = vigra.analysis.labelMultiArrayWithBackground(minima_unlabeled)

                assert (op.SeedsOutCached[:].wait() == minima).all()
                #export_image_to_hdf5(minima, "minima3dt.h5")

                # 2.2 x,y,z
                # add empty t-axis
                boundariesXYZ = empty_t(self.boundariesForGeneration[0], shape).astype(numpy.uint8)
                #export_image_to_hdf5(boundariesXYZ, "boundaries3d.h5")

                SeedsBoundariesRawData_ToNone()
                SeedsBoundariesRawData_To(boundariesXYZ)
                # each time before request, because changes in the seeds lead to GenerateSeeds=False
                op.GenerateSeeds.setValue(True)

                # smoothing, minima and labeling
                smoothed = vigra.filters.gaussianSmoothing(boundariesXYZ[0,:,:,:,0], sigma)
                minima_unlabeled = vigra.analysis.extendedLocalMinima3D(smoothed,marker=1)
                minima_non_t = vigra.analysis.labelMultiArrayWithBackground(minima_unlabeled)
                # add empty t-axis
                minima = numpy.zeros((1,) + shape[1:])
                minima[0,:,:,:,0] = minima_non_t

                assert (op.SeedsOutCached[:].wait() == minima).all()
                
                #export_image_to_hdf5(minima, "minima3d.h5")


                # 2.3 x,y
                # add empty t and z-axis
                boundariesXY = empty_t_z_c(self.boundariesForGeneration[0,:,:,0,0], shape).astype(numpy.uint8)
                #export_image_to_hdf5(boundariesXY, "boundaries2d.h5")

                SeedsBoundariesRawData_ToNone()
                SeedsBoundariesRawData_To(boundariesXY)
                # each time before request, because changes in the seeds lead to GenerateSeeds=False
                op.GenerateSeeds.setValue(True)

                # smoothing, minima and labeling
                smoothed = vigra.filters.gaussianSmoothing(boundariesXY[0,:,:,0,0], sigma)
                minima_unlabeled = vigra.analysis.extendedLocalMinima(smoothed,marker=1)
                minima_non_t = vigra.analysis.labelMultiArrayWithBackground(minima_unlabeled)
                # add empty t and z-axis
                minima = numpy.zeros((1,) + shape[1:3] + (1,1))
                minima[0,:,:,0,0] = minima_non_t

                assert (op.SeedsOutCached[:].wait() == minima).all()
                #export_image_to_hdf5(minima, "minima2d.h5")


                # 3. 
                op.Seeds.setValue(None)
                op.GenerateSeeds.setValue(False)
                assert (op.SeedsOutCached[:].wait() == 0).all()


            # run all tests
            testWSMethodOutput()
            testSeedsExistOutput()
            testGenerateSeedsOutput()
            testSeedsOutOutput()

    
            

        os.remove(testProjectName)

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})

