from __future__ import print_function
from __future__ import division
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
from builtins import range
from past.utils import old_div
import unittest
import numpy as np
import vigra
from lazyflow.graph import Graph
from lazyflow.operators import OpLabelVolume
from ilastik.applets.objectExtraction.opObjectExtraction import OpAdaptTimeListRoi, OpRegionFeatures, OpObjectExtraction
from ilastik.plugins import pluginManager

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

NAME = "Standard Object Features"

FEATURES = {
    NAME : {
        "Count" : {},
        "RegionCenter" : {},
        "Coord<Principal<Kurtosis>>" : {},
        "Coord<Minimum>" : {},
        "Coord<Maximum>" : {},
    }
}

def binaryImage():
    img = np.zeros((2, 50, 50, 50, 1), dtype=np.float32)
    img[0,  0:10,  0:10,  0:10, 0] = 1
    img[0, 20:30, 20:30, 20:30, 0] = 1
    img[0, 40:45, 40:45, 40:45, 0] = 1

    img[1, 20:30, 20:30, 20:30, 0] = 1
    img[1, 5:10, 5:10, 0, 0] = 1
    img[1, 12:15, 12:15, 0, 0] = 1
    img = img.view(vigra.VigraArray)
    img.axistags = vigra.defaultAxistags('txyzc')

    return img

def rawImage():
    img = np.zeros((2, 50, 50, 50, 1), dtype=np.float32)
    img[0,  0:10,  0:10,  0:10, 0] = 200
    img[0, 20:30, 20:30, 20:30, 0] = 100

    # this object is further out than the margin and tests
    # regionCenter feature
    img[0, 40:45, 40:45, 40:45, 0] = 75

    img[1, 20:30, 20:30, 20:30, 0] = 50

    # this and next object are in each other's excl features
    img[1, 5:10, 5:10, 0, 0] = 25
    img[1, 12:15, 12:15, 0, 0] = 13
    img = img.view(vigra.VigraArray)
    img.axistags = vigra.defaultAxistags('txyzc')

    return img


class TestOpRegionFeatures(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.labelop = OpLabelVolume(graph=g)
        self.op = OpRegionFeatures(graph=g)
        self.op.LabelVolume.connect(self.labelop.Output)

        # Raw image is arbitrary for our purposes. Just re-use the
        # label image
        self.op.RawVolume.connect(self.labelop.Output)
        self.op.Features.setValue(FEATURES)
        self.img = binaryImage()
        self.labelop.Input.setValue(self.img)

    def test_features(self):
        self.op.Output.fixed = False
        # FIXME: roi specification
        opAdapt = OpAdaptTimeListRoi(graph=self.op.graph)
        opAdapt.Input.connect(self.op.Output)

        feats = opAdapt.Output([0, 1]).wait()
        assert len(feats)== self.img.shape[0]
        for t in feats:
            assert feats[t][NAME]['Count'].shape[0] > 0
            assert feats[t][NAME]['RegionCenter'].shape[0] > 0

        assert np.any(feats[0][NAME]['Count'] != feats[1][NAME]['Count'])
        assert np.any(feats[0][NAME]['RegionCenter'] != feats[1][NAME]['RegionCenter'])


class TestPlugins(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.op = OpObjectExtraction(graph=g)

        # Raw image is arbitrary for our purposes. Just re-use the
        # label image
        rm = rawImage()
        rm = rm[:, :, :, 0:1, :]
        self.op.RawImage.setValue(rm)
        self.Features_standard = FEATURES
        self.Features_convex_hull = {'2D Convex Hull Features': {'HullVolume': {}, 'DefectVolumeKurtosis': {}}}
        self.Features_skeleton = {'2D Skeleton Features': {'Diameter': {}, 'Total Length': {}}}
        #self.op.Features.setValue(FEATURES)
        bm = binaryImage()
        bm = bm[:, :, :, 0:1, :] 
        self.op.BinaryImage.setValue(bm)

    def test_plugins(self):
        self.op.Features.setValue(self.Features_standard)
        feats = self.op.RegionFeatures([0]).wait()
        self.op.Features.setValue(self.Features_convex_hull)
        feats = self.op.RegionFeatures([0]).wait()
        self.op.Features.setValue(self.Features_skeleton)
        feats = self.op.RegionFeatures([0]).wait()


class TestOpRegionFeaturesAgainstNumpy(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.features = {
            NAME : {
                "Count" : {},
                "RegionCenter" : {},
                "Mean" : {},
                "Coord<Minimum>" : {},
                "Coord<Maximum>" : {},
                "Mean in neighborhood" : {"margin" : (30, 30, 1)},
                "Sum" : {},
                "Sum in neighborhood" : {"margin" : (30, 30, 1)}
            }
        }

        binimage = binaryImage()
        self.rawimage = rawImage()
        self.labelop = OpLabelVolume(graph=g)
        self.op = OpRegionFeatures(graph=g)
        self.op.LabelVolume.connect(self.labelop.Output)
        self.op.RawVolume.setValue(self.rawimage)
        self.op.Features.setValue(self.features)
        self.img = binaryImage()
        self.labelop.Input.setValue(binimage)

    def test(self):
        self.op.Output.fixed = False
        # FIXME: roi specification
        opAdapt = OpAdaptTimeListRoi(graph=self.op.graph)
        opAdapt.Input.connect(self.op.Output)

        feats = opAdapt.Output([0, 1]).wait()
        assert len(feats)==self.img.shape[0]
        for key in self.features[NAME]:
            assert key in list(feats[0][NAME].keys())

        labelimage = self.labelop.Output[:].wait()
        nt = labelimage.shape[0]
        for t in range(nt):
            npcounts = np.bincount(np.asarray(labelimage[t,...].flat, dtype=int))
            counts = feats[t][NAME]["Count"].astype(np.uint32)
            means = feats[t][NAME]["Mean"]
            sum_excl = feats[t][NAME]["Sum in neighborhood"] #sum, not mean, to avoid 0/0
            sum_incl = feats[t][NAME]["Sum in object and neighborhood"]
            sum = feats[t][NAME]["Sum"]
            mins = feats[t][NAME]["Coord<Minimum>"]
            maxs = feats[t][NAME]["Coord<Maximum>"]
            centers = feats[t][NAME]["RegionCenter"]
            #print mins, maxs
            nobj = npcounts.shape[0]
            for iobj in range(1, nobj):
                assert npcounts[iobj] == counts[iobj]
                objmask = labelimage[t,...]==iobj
                npmean = np.mean(np.asarray(self.rawimage)[t,...][objmask])
                assert npmean == means[iobj]
                #currently, we have a margin of 30, this assert is very dependent on it
                #FIXME: make margin visible from outside and use it here
                zmin = int(max(mins[iobj][2]-1, 0))
                zmax = int(min(maxs[iobj][2]+1, self.rawimage.shape[3]))

                exclmask = labelimage[t,:, :, zmin:zmax, :]!=iobj
                npsum_excl = np.sum(np.asarray(self.rawimage)[t,:, :, zmin:zmax,:][exclmask])
                assert npsum_excl == sum_excl[iobj]

                assert sum_incl[iobj] == sum[iobj]+sum_excl[iobj]
                #check that regionCenter wasn't shifted
                for icoord, coord in enumerate(centers[iobj]):
                    center_good = mins[iobj][icoord] + old_div((maxs[iobj][icoord]-mins[iobj][icoord]),2.)
                    assert abs(coord-center_good)<0.01
