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


import ilastik
import ilastik.applets
import ilastik.applets.nanshe
import ilastik.applets.nanshe.preprocessing
import ilastik.applets.nanshe.preprocessing.opNansheExtractF0
from ilastik.applets.nanshe.preprocessing.opNansheExtractF0 import OpNansheExtractF0

class TestOpNansheExtractF0(object):
    def testBasic(self):
        a = numpy.ones((100, 101, 102))
        a = a[..., None]

        graph = Graph()
        op = OpNansheExtractF0(graph=graph)
        op.InputImage.setValue(a)

        op.HalfWindowSize.setValue(20)
        op.WhichQuantile.setValue(0.5)
        op.TemporalSmoothingGaussianFilterStdev.setValue(5.0)
        op.SpatialSmoothingGaussianFilterStdev.setValue(5.0)
        op.Bias.setValue(100)
        op.BiasEnabled.setValue(True)

        b = op.Output[...].wait()

        assert(a.shape == b.shape)

        assert((b == 0).all())


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)