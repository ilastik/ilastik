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

import vigra

import ilastik
import ilastik.applets
import ilastik.applets.nanshe
import ilastik.applets.nanshe.preprocessing
import ilastik.applets.nanshe.preprocessing.opNansheWaveletTransform
from ilastik.applets.nanshe.preprocessing.opNansheWaveletTransform import OpNansheWaveletTransform

class TestOpNansheWaveletTransform(object):
    def testBasic(self):
        a = numpy.eye(3, dtype = numpy.float32)
        a = a[..., None]

        a = vigra.taggedView(a, "yxc")


        expected_b = numpy.array([[ 0.59375, -0.375  , -0.34375],
                                  [-0.375  ,  0.625  , -0.375  ],
                                  [-0.34375, -0.375  ,  0.59375]], dtype=numpy.float32)
        expected_b = expected_b[..., None]
        expected_b = vigra.taggedView(expected_b, "yxc")

        graph = Graph()
        op = OpNansheWaveletTransform(graph=graph)

        op.InputImage.setValue(a)

        op.Scale.setValue(1)

        b = op.Output[...].wait()
        b = vigra.taggedView(b, "yxc")

        assert((b == expected_b).all())


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)