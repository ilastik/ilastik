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
__date__ = "$Dec 19, 2014 15:35:22 EST$"



import numpy

import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpArrayPiper

import ilastik
import ilastik.applets
import ilastik.applets.nanshe
import ilastik.applets.nanshe.opMaxProjection
from ilastik.applets.nanshe.opMaxProjection import OpMaxProjection, OpMaxProjectionCached

class TestOpMaxProjection(object):
    def testBasic1(self):
        a = numpy.zeros((2,2,2,))
        a[1,1,1] = 1
        a[0,0,0] = 1
        a = a[..., None]
        a = vigra.taggedView(a, "tyxc")

        expected_b = a.max(axis=0)
        expected_b = vigra.taggedView(expected_b, "yxc")


        graph = Graph()
        op = OpMaxProjection(graph=graph)

        opPrep = OpArrayPiper(graph=graph)
        opPrep.Input.setValue(a)

        op.InputImage.connect(opPrep.Output)
        op.Axis.setValue(0)

        b = op.Output[...].wait()
        b = vigra.taggedView(b, "yxc")


        assert((b == expected_b).all())

    def testBasic2(self):
        a = numpy.zeros((2,2,2,))
        a[1,1,1] = 1
        a[0,0,0] = 1
        a = a[..., None]
        a = vigra.taggedView(a, "tyxc")

        expected_b = a.max(axis=0)
        expected_b = vigra.taggedView(expected_b, "yxc")


        graph = Graph()
        op = OpMaxProjectionCached(graph=graph)

        opPrep = OpArrayPiper(graph=graph)
        opPrep.Input.setValue(a)

        op.InputImage.connect(opPrep.Output)
        op.Axis.setValue(0)

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
