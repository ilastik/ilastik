###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Oct 29, 2014 19:42:43 EDT$"



import numpy

from lazyflow.graph import Graph
from lazyflow.operators import OpArrayPiper

import vigra

import synthetic_data
import synthetic_data.synthetic_data

import ilastik
import ilastik.applets
import ilastik.applets.nanshe
import ilastik.applets.nanshe.postprocessing
import ilastik.applets.nanshe.postprocessing.opNanshePostprocessData
from ilastik.applets.nanshe.postprocessing.opNanshePostprocessData import OpNanshePostprocessData,\
                                                                          OpNanshePostprocessDataCached


class TestOpNanshePostprocessData(object):
    def testBasic1(self):
        space = numpy.array([100, 100])
        radii = numpy.array([7, 6, 6, 6, 7, 6])
        magnitudes = numpy.array([15, 16, 15, 17, 16, 16])
        points = numpy.array([[30, 24],
                              [59, 65],
                              [21, 65],
                              [13, 12],
                              [72, 16],
                              [45, 32]])

        masks = synthetic_data.synthetic_data.generate_hypersphere_masks(space, points, radii)
        images = synthetic_data.synthetic_data.generate_gaussian_images(space, points, radii/3.0, magnitudes) * masks

        bases_indices = [[1,3,4], [0,2], [5]]

        bases_masks = numpy.zeros((len(bases_indices),) + masks.shape[1:] , dtype=masks.dtype)
        bases_images = numpy.zeros((len(bases_indices),) + images.shape[1:] , dtype=images.dtype)

        for i, each_basis_indices in enumerate(bases_indices):
            bases_masks[i] = masks[list(each_basis_indices)].max(axis = 0)
            bases_images[i] = images[list(each_basis_indices)].max(axis = 0)

        bases_images = vigra.taggedView(bases_images, "cyx")

        graph = Graph()

        opPrep = OpArrayPiper(graph=graph)
        opPrep.Input.setValue(bases_images)

        op = OpNanshePostprocessData(graph=graph)
        op.Input.connect(opPrep.Output)

        op.SignificanceThreshold.setValue(3.0)
        op.WaveletTransformScale.setValue(4)
        op.NoiseThreshold.setValue(3.0)
        op.AcceptedRegionShapeConstraints_MajorAxisLength_Min.setValue(0.0)
        op.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled.setValue(True)
        op.AcceptedRegionShapeConstraints_MajorAxisLength_Max.setValue(25.0)
        op.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled.setValue(True)
        op.PercentagePixelsBelowMax.setValue(0.0)
        op.MinLocalMaxDistance.setValue(10.0)
        op.AcceptedNeuronShapeConstraints_Area_Min.setValue(30)
        op.AcceptedNeuronShapeConstraints_Area_Min_Enabled.setValue(True)
        op.AcceptedNeuronShapeConstraints_Area_Max.setValue(600)
        op.AcceptedNeuronShapeConstraints_Area_Max_Enabled.setValue(True)
        op.AcceptedNeuronShapeConstraints_Eccentricity_Min.setValue(0.0)
        op.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled.setValue(True)
        op.AcceptedNeuronShapeConstraints_Eccentricity_Max.setValue(0.9)
        op.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled.setValue(True)
        op.AlignmentMinThreshold.setValue(0.6)
        op.OverlapMinThreshold.setValue(0.6)
        op.Fuse_FractionMeanNeuronMaxThreshold.setValue(0.6)

        neurons = op.Output[...].wait()

    def testBasic2(self):
        space = numpy.array([100, 100])
        radii = numpy.array([7, 6, 6, 6, 7, 6])
        magnitudes = numpy.array([15, 16, 15, 17, 16, 16])
        points = numpy.array([[30, 24],
                              [59, 65],
                              [21, 65],
                              [13, 12],
                              [72, 16],
                              [45, 32]])

        masks = synthetic_data.synthetic_data.generate_hypersphere_masks(space, points, radii)
        images = synthetic_data.synthetic_data.generate_gaussian_images(space, points, radii/3.0, magnitudes) * masks

        bases_indices = [[1,3,4], [0,2], [5]]

        bases_masks = numpy.zeros((len(bases_indices),) + masks.shape[1:] , dtype=masks.dtype)
        bases_images = numpy.zeros((len(bases_indices),) + images.shape[1:] , dtype=images.dtype)

        for i, each_basis_indices in enumerate(bases_indices):
            bases_masks[i] = masks[list(each_basis_indices)].max(axis = 0)
            bases_images[i] = images[list(each_basis_indices)].max(axis = 0)

        bases_images = vigra.taggedView(bases_images, "cyx")

        graph = Graph()

        opPrep = OpArrayPiper(graph=graph)
        opPrep.Input.setValue(bases_images)

        op = OpNanshePostprocessDataCached(graph=graph)
        op.Input.connect(opPrep.Output)

        op.SignificanceThreshold.setValue(3.0)
        op.WaveletTransformScale.setValue(4)
        op.NoiseThreshold.setValue(3.0)
        op.AcceptedRegionShapeConstraints_MajorAxisLength_Min.setValue(0.0)
        op.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled.setValue(True)
        op.AcceptedRegionShapeConstraints_MajorAxisLength_Max.setValue(25.0)
        op.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled.setValue(True)
        op.PercentagePixelsBelowMax.setValue(0.0)
        op.MinLocalMaxDistance.setValue(10.0)
        op.AcceptedNeuronShapeConstraints_Area_Min.setValue(30)
        op.AcceptedNeuronShapeConstraints_Area_Min_Enabled.setValue(True)
        op.AcceptedNeuronShapeConstraints_Area_Max.setValue(600)
        op.AcceptedNeuronShapeConstraints_Area_Max_Enabled.setValue(True)
        op.AcceptedNeuronShapeConstraints_Eccentricity_Min.setValue(0.0)
        op.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled.setValue(True)
        op.AcceptedNeuronShapeConstraints_Eccentricity_Max.setValue(0.9)
        op.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled.setValue(True)
        op.AlignmentMinThreshold.setValue(0.6)
        op.OverlapMinThreshold.setValue(0.6)
        op.Fuse_FractionMeanNeuronMaxThreshold.setValue(0.6)

        neurons = op.Output[...].wait()


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
