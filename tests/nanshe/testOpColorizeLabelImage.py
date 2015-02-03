###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Dec 19, 2014 16:00:58 EST$"



import numpy

import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpArrayPiper

from nanshe.nanshe.expanded_numpy import expand_view, array_to_matrix

import ilastik
import ilastik.applets
import ilastik.applets.nanshe
import ilastik.applets.nanshe.opColorizeLabelImage
from ilastik.applets.nanshe.opColorizeLabelImage import OpColorizeLabelImage, OpColorizeLabelImageCached

class TestOpColorizeLabelImage(object):
    def testBasic1(self):
        a = numpy.arange(256)
        a = expand_view(a, 256)
        a = a[..., None]
        a = vigra.taggedView(a, "xyc")


        graph = Graph()
        op = OpColorizeLabelImage(graph=graph)

        opPrep = OpArrayPiper(graph=graph)
        opPrep.Input.setValue(a)

        op.Input.connect(opPrep.Output)

        b = op.Output[...].wait()

        b_colors = set([tuple(_) for _ in list(array_to_matrix(b.T).T)])
        assert(len(b_colors) == 256)

    def testBasic2(self):
        a = numpy.arange(256)
        a = expand_view(a, 256)
        a = a[..., None]
        a = vigra.taggedView(a, "xyc")


        graph = Graph()
        op = OpColorizeLabelImageCached(graph=graph)

        opPrep = OpArrayPiper(graph=graph)
        opPrep.Input.setValue(a)

        op.Input.connect(opPrep.Output)

        b = op.Output[...].wait()

        b_colors = set([tuple(_) for _ in list(array_to_matrix(b.T).T)])
        assert(len(b_colors) == 256)


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
