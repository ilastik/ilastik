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
from __future__ import division
import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

from ilastik.applets.objectClassification.opObjectClassification import OpObjectClassification
import numpy

class TestTransferLabelsFunction(object):
    def test(self):
        coords_old = dict()
        coords_old["Coord<Minimum>"]=numpy.array([[0, 0, 0], [0, 0, 0], [0, 0, 0], [15, 15, 15], [22, 22, 22], [31, 31, 31]])
        coords_old["Coord<Maximum>"]=numpy.array([[50, 50, 50], [10, 10, 10], [3, 3, 3], [20, 20, 20], [30, 30, 30], [35, 35, 35]])
        
        coords_new = dict()
        coords_new["Coord<Minimum>"]=numpy.array([[0, 0, 0], [2, 2, 2], [17, 17, 17], [22, 22, 22], [26, 26, 26]])
        coords_new["Coord<Maximum>"]=numpy.array([[50, 50, 50], [5, 5, 5], [20, 20, 20], [25, 25, 25], [33, 33, 33]])
        
        labels = numpy.zeros((6,))
        labels[0]=0
        labels[1]=1
        labels[2]=0
        labels[3]=2
        labels[4]=3
        labels[5]=4
       
        newlabels, oldlost, newlost = OpObjectClassification.transferLabels(labels, coords_old, coords_new, None)
        assert numpy.all(newlabels == [0, 1, 2, 0, 0])
        assert len(oldlost["full"])==0
        assert len(oldlost["partial"])==1
        min4 = coords_old["Coord<Minimum>"][4]
        max4 = coords_old["Coord<Maximum>"][4]
        assert numpy.all(oldlost["partial"]==(min4+(max4-min4)//2))
        newmin4 =  coords_new["Coord<Minimum>"][4]
        newmax4 = coords_new["Coord<Maximum>"][4]
        assert numpy.all(newlost["conflict"]==(newmin4+(newmax4-newmin4)/2.))
