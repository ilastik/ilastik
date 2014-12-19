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
from lazyflow.operators import OpArrayPiper

import vigra

import nanshe.expanded_numpy

import ilastik
import ilastik.applets
import ilastik.applets.nanshe
import ilastik.applets.nanshe.preprocessing
import ilastik.applets.nanshe.preprocessing.opNansheRemoveZeroedLines
from ilastik.applets.nanshe.preprocessing.opNansheRemoveZeroedLines import OpNansheRemoveZeroedLines

class TestOpNansheRemoveZeroedLines(object):
    def testBasic(self):
        a = numpy.ones((1, 100, 101))
        a = a[..., None]
        a = vigra.taggedView(a, "tyxc")

        r = numpy.array([[0, 0, 0], [1, 3, 4]]).T.copy()

        ar = a.copy()
        for each_r in r:
            nanshe.expanded_numpy.index_axis_at_pos(nanshe.expanded_numpy.index_axis_at_pos(ar, 0, each_r[0]), -2, each_r[-1])[:] = 0


        graph = Graph()

        opPrep = OpArrayPiper(graph=graph)
        opPrep.Input.setValue(ar)

        op = OpNansheRemoveZeroedLines(graph=graph)
        op.InputImage.connect(opPrep.Output)

        op.ErosionShape.setValue([21, 1])
        op.DilationShape.setValue([1, 3])


        b = op.Output[...].wait()
        b = vigra.taggedView(b, "tyxc")

        assert((a == b).all())


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)