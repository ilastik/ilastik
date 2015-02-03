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

import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpArrayPiper

import ilastik
import ilastik.applets
import ilastik.applets.nanshe
import ilastik.applets.nanshe.dictionaryLearning
import ilastik.applets.nanshe.dictionaryLearning.opNansheNormalizeData
from ilastik.applets.nanshe.dictionaryLearning.opNansheNormalizeData import OpNansheNormalizeData

class TestOpNansheNormalizeData(object):
    def testBasic(self):
        a = numpy.zeros((2,2,2,))
        a[1,1,1] = 1
        a[0,0,0] = 1
        a = a[..., None]
        a = vigra.taggedView(a, "tyxc")

        expected_b = numpy.array([[[ 0.86602540378443870761060452423407696187496185302734375 ,
                                    -0.288675134594812921040585251830634661018848419189453125],
                                   [-0.288675134594812921040585251830634661018848419189453125,
                                    -0.288675134594812921040585251830634661018848419189453125]],
                                  [[-0.288675134594812921040585251830634661018848419189453125,
                                    -0.288675134594812921040585251830634661018848419189453125],
                                   [-0.288675134594812921040585251830634661018848419189453125,
                                    0.86602540378443870761060452423407696187496185302734375 ]]])
        expected_b = expected_b[..., None]

        graph = Graph()
        op = OpNansheNormalizeData(graph=graph)

        opPrep = OpArrayPiper(graph=graph)
        opPrep.Input.setValue(a)

        op.Input.connect(opPrep.Output)

        op.Ord.setValue(2)

        b = op.Output[...].wait()

        assert((b == expected_b).all())


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
