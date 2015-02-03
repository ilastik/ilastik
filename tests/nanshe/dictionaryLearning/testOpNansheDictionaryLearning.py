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

import nanshe
import nanshe.advanced_image_processing

import synthetic_data
import synthetic_data.synthetic_data

from lazyflow.graph import Graph
from lazyflow.operators import OpArrayPiper

import ilastik
import ilastik.applets
import ilastik.applets.nanshe
import ilastik.applets.nanshe.dictionaryLearning
import ilastik.applets.nanshe.dictionaryLearning.opNansheDictionaryLearning
from ilastik.applets.nanshe.dictionaryLearning.opNansheDictionaryLearning import OpNansheDictionaryLearning

class TestOpNansheDictionaryLearning(object):
    def test_OpNansheDictionaryLearning(self):
        p = numpy.array([[27, 51],
                         [66, 85],
                         [77, 45]])

        space = numpy.array((100, 100))
        radii = numpy.array((5, 6, 7))

        g = synthetic_data.synthetic_data.generate_hypersphere_masks(space, p, radii)
        gv = g[..., None]
        gv = gv.astype(float)
        gv = vigra.taggedView(gv, "tyxc")

        graph = Graph()
        op = OpNansheDictionaryLearning(graph=graph)

        opPrep = OpArrayPiper(graph=graph)
        opPrep.Input.setValue(gv)

        op.Input.connect(opPrep.Output)

        op.K.setValue(len(g))
        op.Gamma1.setValue(0)
        op.Gamma2.setValue(0)
        op.NumThreads.setValue(1)
        op.Batchsize.setValue(256)
        op.NumIter.setValue(10)
        op.Lambda1.setValue(0.2)
        op.Lambda2.setValue(0)
        op.PosAlpha.setValue(True)
        op.PosD.setValue(True)
        op.Clean.setValue(True)
        op.Mode.setValue(2)
        op.ModeD.setValue(0)

        d = op.Output[...].wait()

        d = (d != 0)

        assert(g.shape == d.shape)

        assert((g.astype(bool).max(axis = 0) == d.astype(bool).max(axis = 0)).all())

        unmatched_g = range(len(g))
        matched = dict()

        for i in xrange(len(d)):
            new_unmatched_g = []
            for j in unmatched_g:
                if not (d[i] == g[j]).all():
                    new_unmatched_g.append(j)
                else:
                    matched[i] = j

            unmatched_g = new_unmatched_g

        print(unmatched_g)

        assert(len(unmatched_g) == 0)


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)