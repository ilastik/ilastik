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
import numpy
from lazyflow.graph import Graph

import synthetic_data.synthetic_data


import ilastik
import ilastik.applets
import ilastik.applets.nanshe
import ilastik.applets.nanshe.preprocessing
import ilastik.applets.nanshe.preprocessing.opNanshePreprocessing
from ilastik.applets.nanshe.preprocessing.opNanshePreprocessing import OpNanshePreprocessing

class TestOpNanshePreprocessing(object):
    def testBasic(self):
        # Does NOT test accuracy.

        space = numpy.array([100, 100, 100])
        radii = numpy.array([5, 6])
        magnitudes = numpy.array([15, 16])
        points = numpy.array([[20, 30, 24],
                              [70, 59, 65]])

        masks = synthetic_data.synthetic_data.generate_hypersphere_masks(space, points, radii)
        images = synthetic_data.synthetic_data.generate_gaussian_images(space, points, radii/3.0, magnitudes) * masks
        image_stack = images.max(axis = 0)

        graph = Graph()
        op = OpNanshePreprocessing(graph=graph)
        op.InputImage.setValue(image_stack)


        op.ToRemoveZeroedLines.setValue(True)
        op.ErosionShape.setValue([21, 1])
        op.DilationShape.setValue([1, 3])

        op.ToExtractF0.setValue(True)
        op.HalfWindowSize.setValue(20)
        op.WhichQuantile.setValue(0.5)
        op.TemporalSmoothingGaussianFilterStdev.setValue(5.0)
        op.SpatialSmoothingGaussianFilterStdev.setValue(5.0)
        op.Bias.setValue(100)

        op.ToWaveletTransform.setValue(True)
        op.Scale.setValue([3, 4, 4])

        op.Ord.setValue(2)

        b = op.Output[...].wait()


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)