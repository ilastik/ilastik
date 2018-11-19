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
import numpy
import vigra
np = numpy

from lazyflow.graph import Graph
from lazyflow.operators import OpArrayPiper
from ilastik.applets.thresholdTwoLevels.opThresholdTwoLevels import OpThresholdTwoLevels
from ilastik.applets.thresholdTwoLevels.thresholdingTools import OpSelectLabels

from ilastik.applets.thresholdTwoLevels.opGraphcutSegment import haveGraphCut

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
import unittest

##
## Note: Several of these tests used to test internal operators that were part of OpTwoLevelThresholding,
##       but now those operators don't exist any more.  The tests all just exercise the 'top-level' operator instead.
##       Therefore, some of these tests are redundant now.
##

## for testing ThresholdOneLevel
class Generator1(unittest.TestCase):

    def generateData(self, xxx_todo_changeme):

        (nz, ny, nx) = xxx_todo_changeme
        clusters = []

        #cluster of 4 points
        cluster1 = numpy.zeros((nz, ny, nx))
        cluster1[1:3, 1:3, 1] = 0.9
        clusters.append(cluster1)

        #cluster of 18 points
        cluster2 = numpy.zeros((nz, ny, nx))
        cluster2[5:8, 5:8, 5:8] = 0.7
        clusters.append(cluster2)

        #cluster of lower probability (18 points)
        cluster3 = numpy.zeros((nz, ny, nx))
        cluster3[4:7, 11:14, 9:11] = 0.3
        clusters.append(cluster3)

        #cluster of 64 points
        cluster4 = numpy.zeros((nz, ny, nx))
        cluster4[2:10, 2:10, 15] = 0.9
        clusters.append(cluster4)

        #dual cluster
        cluster5 = numpy.zeros((nz, ny, nx))
        cluster5[20:30, 20:30, 20] = 0.4  # bigger cluster of lower prob
        cluster5[25:30, 25:30, 20] = 0.95  # smaller core of high prob
        clusters.append(cluster5)

        return clusters

    def setUp(self):
        self.nz = 50
        self.ny = 51
        self.nx = 52
        self.nc = 3

        clusters = self.generateData((self.nz, self.ny, self.nx))
        self.data = clusters[0] + clusters[1] + clusters[2] + clusters[3] + clusters[4]
        self.data = self.data.reshape(self.data.shape+(1,))
        self.data5d = self.data.reshape((1,)+self.data.shape)
        self.data = self.data.view(vigra.VigraArray)
        self.data.axistags = vigra.VigraArray.defaultAxistags('zyxc')
        self.data5d = self.data5d.view(vigra.VigraArray)
        self.data5d.axistags = vigra.VigraArray.defaultAxistags('tzyxc')

        self.minSize = 0
        self.maxSize = 50

        self.sigma = {'x': 0.3, 'y': 0.3, 'z': 0.3}
        self.data = vigra.filters.gaussianSmoothing(
            self.data.astype(numpy.float32), 0.3)


class TestThresholdOneLevelInternal(Generator1):

    @unittest.skip("Not supported anymore, test kept for reference")
    def test4d(self):
        g = Graph()
        oper = OpThresholdOneLevel(graph=g)
        oper.MinSize.setValue(self.minSize)
        oper.MaxSize.setValue(self.maxSize)
        oper.LowThreshold.setValue(0.5)
        oper.InputImage.setValue(self.data)

        output = oper.Output[:].wait()
        assert numpy.all(output.shape == self.data.shape)

        clusters = self.generateData((self.nz, self.ny, self.nx))

        cluster1 = numpy.logical_and(output, clusters[0])
        assert numpy.any(cluster1 != 0)

        oper.MinSize.setValue(5)
        output = oper.Output[:].wait()
        cluster1 = numpy.logical_and(output, clusters[0])
        assert numpy.all(cluster1 == 0)

        cluster4 = numpy.logical_and(output.squeeze(), clusters[3])
        assert numpy.all(cluster4 == 0)

        cluster5 = numpy.logical_and(output.squeeze(), clusters[2])
        assert numpy.all(cluster5 == 0)
        oper.LowThreshold.setValue(0.2)
        output = oper.Output[:].wait()
        cluster5 = numpy.logical_and(output.squeeze(), clusters[2])
        assert numpy.any(cluster5 != 0)

    def test5d(self):
        g = Graph()
        oper = OpThresholdTwoLevels(graph=g)
        oper.MinSize.setValue(self.minSize)
        oper.MaxSize.setValue(self.maxSize)
        oper.SmootherSigma.setValue({'z': 0.0, 'y': 0.0, 'x': 0.0})
        oper.LowThreshold.setValue(0.5)
        oper.InputImage.setValue(self.data5d)

        output = oper.Output[:].wait()
        assert numpy.all(output.shape == self.data5d.shape)

        output = vigra.taggedView(output, axistags=oper.Output.meta.axistags)
        output = output.withAxes(*'zyx')

        clusters = self.generateData((self.nz, self.ny, self.nx))

        cluster1 = numpy.logical_and(output, clusters[0])
        assert numpy.any(cluster1 != 0)

        oper.MinSize.setValue(5)
        output = oper.Output[:].wait()
        output = vigra.taggedView(output, axistags=oper.Output.meta.axistags)
        output = output.withAxes(*'zyx')
        cluster1 = numpy.logical_and(output, clusters[0])
        assert numpy.all(cluster1 == 0)

        cluster4 = numpy.logical_and(output.squeeze(), clusters[3])
        assert numpy.all(cluster4 == 0)

        cluster5 = numpy.logical_and(output.squeeze(), clusters[2])
        assert numpy.all(cluster5 == 0)
        oper.LowThreshold.setValue(0.2)
        output = oper.Output[:].wait()
        output = vigra.taggedView(output, axistags=oper.Output.meta.axistags)
        output = output.withAxes(*'zyx')
        cluster5 = numpy.logical_and(output.squeeze(), clusters[2])
        assert numpy.any(cluster5 != 0)

    def testFunnyAxes(self):
        vol = self.data.withAxes(*'ztxcy')
        g = Graph()
        oper = OpThresholdTwoLevels(graph=g)
        oper.MinSize.setValue(self.minSize)
        oper.MaxSize.setValue(self.maxSize)
        oper.LowThreshold.setValue(0.5)
        oper.SmootherSigma.setValue({'z': 0.0, 'y': 0.0, 'x': 0.0})
        oper.InputImage.setValue(vol)

        output = oper.Output[:, 0, :, 0, :].wait()
        assert numpy.all(output.shape == vol.shape)

        clusters = self.generateData((self.nz, self.ny, self.nx))
        output = vigra.taggedView(output, axistags=oper.Output.meta.axistags)
        output = output.withAxes(*'zyx')

        cluster1 = numpy.logical_and(output, clusters[0])
        assert numpy.any(cluster1 != 0)

        oper.MinSize.setValue(5)
        output = oper.Output[:, 0, :, 0, :].wait()
        output = vigra.taggedView(output, axistags=oper.Output.meta.axistags)
        output = output.withAxes(*'zyx')
        cluster1 = numpy.logical_and(output, clusters[0])
        assert numpy.all(cluster1 == 0)

        cluster4 = numpy.logical_and(output.squeeze(), clusters[3])
        assert numpy.all(cluster4 == 0)

        cluster5 = numpy.logical_and(output.squeeze(), clusters[2])
        assert numpy.all(cluster5 == 0)
        oper.LowThreshold.setValue(0.2)
        output = oper.Output[:, 0, :, 0, :].wait()
        output = vigra.taggedView(output, axistags=oper.Output.meta.axistags)
        output = output.withAxes(*'zyx')
        cluster5 = numpy.logical_and(output.squeeze(), clusters[2])
        assert numpy.any(cluster5 != 0)


class TestThresholdOneLevel(Generator1):
    def setUp(self):
        super(TestThresholdOneLevel, self).setUp()
        self.curOperator = 0
        self.usePreThreshold = False

    def testSimpleUsage(self):
        oper5d = OpThresholdTwoLevels(graph=Graph())
        oper5d.InputImage.setValue(self.data5d)
        oper5d.MinSize.setValue(self.minSize)
        oper5d.MaxSize.setValue(self.maxSize)
        oper5d.LowThreshold.setValue(0.5)
        oper5d.SmootherSigma.setValue(self.sigma)
        oper5d.Channel.setValue(0)
        oper5d.CoreChannel.setValue(0)
        oper5d.CurOperator.setValue(self.curOperator)

        out5d = oper5d.Output[:].wait()
        numpy.testing.assert_array_equal(out5d.shape, self.data5d.shape)

    def testWrongChannel(self):
        oper5d = OpThresholdTwoLevels(graph=Graph())
        oper5d.InputImage.setValue(self.data5d)
        oper5d.MinSize.setValue(self.minSize)
        oper5d.MaxSize.setValue(self.maxSize)
        oper5d.LowThreshold.setValue(0.5)
        oper5d.SmootherSigma.setValue(self.sigma)
        # the operator should be able to figure out that this channel index is wrong
        oper5d.Channel.setValue(15)
        oper5d.CoreChannel.setValue(15)
        oper5d.CurOperator.setValue(self.curOperator)

        with self.assertRaises(Exception):
            out5d = oper5d.Output[:].wait()

    def testNoOp(self):
        oper5d = OpThresholdTwoLevels(graph=Graph())
        oper5d.InputImage.setValue(self.data5d)
        oper5d.MinSize.setValue(1)
        oper5d.MaxSize.setValue(self.data5d.size)
        oper5d.LowThreshold.setValue(-0.01)
        oper5d.SmootherSigma.setValue({'z': 0.0, 'y': 0.0, 'x': 0.0})
        oper5d.Channel.setValue(0)
        oper5d.CoreChannel.setValue(0)
        oper5d.CurOperator.setValue(self.curOperator)

        out5d = oper5d.Output[:].wait()
        numpy.testing.assert_array_equal(out5d.shape, self.data5d.shape)

        # the image should be white, because of negative threshold
        assert numpy.all(out5d > 0),\
            "{}% elements <= 0".format((out5d <= 0).sum()/float(out5d.size)*100)

        oper5d.LowThreshold.setValue(1.01)
        out5d = oper5d.Output[:].wait()

        # the image should be black, because of threshold larger than 1
        assert numpy.all(out5d == 0),\
            "{}% elements > 0".format((out5d > 0).sum()/float(out5d.size)*100)

    def testEvenFunnierAxes(self):
        vol = numpy.random.randint(0, 255, size=(5, 17, 31, 42, 11))
        vol = vol.astype(numpy.uint8)
        # don't care about corner cases
        vol[vol == 128] = 129
        vol[vol == 127] = 126
        desiredResult = numpy.where(vol > 128, 1, 0)
        vol = vigra.taggedView(vol, axistags='xtycz')

        oper5d = OpThresholdTwoLevels(graph=Graph())
        oper5d.InputImage.setValue(vol)
        oper5d.MinSize.setValue(1)
        oper5d.MaxSize.setValue(vol.size)
        oper5d.LowThreshold.setValue(128)
        oper5d.SmootherSigma.setValue({'z': 0.0, 'y': 0.0, 'x': 0.0})
        oper5d.CurOperator.setValue(self.curOperator)

        #for i in range(vol.shape[3]):
        for i in range(2, 5):  # just test some sample slices (runtime :)
            oper5d.Channel.setValue(i)
            oper5d.CoreChannel.setValue(i)
            out5d = oper5d.Output[:].wait()
            out5d[out5d > 0] = 1
            numpy.testing.assert_array_equal(out5d.squeeze(), desiredResult[..., i, :])


# class TestObjectsSegment(TestThresholdOneLevel):
#     @unittest.skipIf(not haveGraphCut(), "opengm not available")
#     def setUp(self):
#         super(TestObjectsSegment, self).setUp()
#         self.curOperator = 2
#         self.usePreThreshold = True
# 
#     # time axes not implemented
#     @unittest.expectedFailure
#     def testEvenFunnierAxes(self):
#         super(TestObjectsSegment, self).testEvenFunnierAxes()
# 
#     # NoOp uses threshold value -> not meaningful for graphcut
#     @unittest.skip("Makes no sense with graph cut")
#     def testNoOp(self):
#         super(TestGraphCut, self).testNoOp()


# class TestGraphCut(TestObjectsSegment):
#     @unittest.skipIf(not haveGraphCut(), "opengm not available")
#     def setUp(self):
#         super(TestGraphCut, self).setUp()
#         self.usePreThreshold = False


class Generator2(Generator1):
    def setUp(self):

        self.nz = 50
        self.ny = 51
        self.nx = 52
        self.nc = 3

        clusters = self.generateData((self.nz, self.ny, self.nx))
        self.data = clusters[0] + clusters[1] + clusters[2] + clusters[3] + clusters[4]
        self.data = self.data.reshape(self.data.shape+(1,))
        self.data = vigra.taggedView(self.data, axistags='zyxc')

        self.minSize = 5  # first cluster doesn't pass this
        self.maxSize = 30  # fourth and fifth cluster don't pass this
        self.highThreshold = 0.65  # third cluster doesn't pass
        self.lowThreshold = 0.1

        # Replicate the 4d data for multiple time slices
        self.data5d = numpy.concatenate(3*(self.data[numpy.newaxis, ...],),
                                        axis=0)
        self.data5d = vigra.taggedView(self.data5d, axistags="tzyxc")

        self.sigma = {'z': 0.3, 'y': 0.3, 'x': 0.3}
        #pre-smooth 4d data
        self.data = vigra.filters.gaussianSmoothing(
            self.data.astype(numpy.float32), 0.3)

    ## check thresholding results for parameters stored in attributes
    def checkResult(self, result):
        result = result.withAxes(*'zyxc')
        clusters = self.generateData((self.nz, self.ny, self.nx))

        failed = 0
        msg = []

        # the cluster 2 and 5 must pass, others mustn't
        for i in (1,):
            cluster = result[clusters[i] != 0]
            if not numpy.all(cluster != 0):
                failed += 1
                msg.append("Cluster {} did not pass.".format(i+1))
        for i in (0, 2, 3, 4):
            cluster = result[clusters[i] != 0]
            if not numpy.all(cluster == 0):
                failed += 1
                msg.append("Cluster {} passed.".format(i+1))

        assert failed == 0, "\n".join(msg)


class TestThresholdTwoLevelsInternal(Generator2):

    def testNoOp(self):
        oper5d = OpThresholdTwoLevels(graph=Graph())
        oper5d.InputImage.setValue(self.data5d[0:1, ..., 0:1])
        oper5d.MinSize.setValue(1)
        oper5d.MaxSize.setValue(self.data5d.size)
        oper5d.HighThreshold.setValue(-0.01)
        oper5d.LowThreshold.setValue(-0.01)

        out5d = oper5d.Output[:].wait()
        assert numpy.all(out5d > 0),\
            "{}% elements <= 0".format((out5d <= 0).sum()/float(out5d.size)*100)


class TestThresholdTwoLevels(Generator2):

    def testOpSelectLabels(self):
        op = OpSelectLabels(graph=Graph())

        small = numpy.asarray(
            [[0, 0, 0],
             [0, 1, 0],
             [0, 0, 0]]).astype(np.uint32)
        big = numpy.asarray(
            [[0, 1, 0],
             [1, 1, 1],
             [0, 1, 0]]).astype(np.uint32)

        small = vigra.taggedView(small[:,:,None], 'yxc')
        big = vigra.taggedView(big[:,:,None], 'yxc')

        op.BigLabels.setValue(big)
        op.SmallLabels.setValue(small)
        out = op.Output[...].wait()
        numpy.testing.assert_array_equal(out, big)

        op.BigLabels.setValue(big)
        op.SmallLabels.setValue(small*0)
        out = op.Output[...].wait()
        numpy.testing.assert_array_equal(out, big*0)

    def testSimpleUsage(self):
        oper5d = OpThresholdTwoLevels(graph=Graph())
        oper5d.InputImage.setValue(self.data5d)
        oper5d.MinSize.setValue(self.minSize)
        oper5d.MaxSize.setValue(self.maxSize)
        oper5d.HighThreshold.setValue(self.highThreshold)
        oper5d.LowThreshold.setValue(self.lowThreshold)
        oper5d.SmootherSigma.setValue(self.sigma)
        oper5d.Channel.setValue(0)
        oper5d.CoreChannel.setValue(0)
        oper5d.CurOperator.setValue(1)

        out5d = oper5d.Output[:].wait()
        numpy.testing.assert_array_equal(out5d.shape, self.data5d.shape)

    def testReconnect(self):
        """
        Can we connect an image, then replace it with a differently-ordered image?
        """
        predRaw = np.zeros((20, 22, 21, 3), dtype=np.uint32)
        pred1 = vigra.taggedView(predRaw, axistags='zyxc')
        pred2 = vigra.taggedView(predRaw, axistags='tyxc')

        oper5d = OpThresholdTwoLevels(graph=Graph())
        oper5d.InputImage.setValue(pred1)
        oper5d.MinSize.setValue(self.minSize)
        oper5d.MaxSize.setValue(self.maxSize)
        oper5d.HighThreshold.setValue(self.highThreshold)
        oper5d.LowThreshold.setValue(self.lowThreshold)
        oper5d.SmootherSigma.setValue(self.sigma)
        oper5d.Channel.setValue(0)
        oper5d.CoreChannel.setValue(0)
        oper5d.CurOperator.setValue(1)

        out5d = oper5d.CachedOutput[:].wait()

        oper5d.InputImage.disconnect() # FIXME: Why is this line necessary? Ideally, it shouldn't be...
        oper5d.InputImage.setValue(pred2)
        out5d = oper5d.CachedOutput[:].wait()

    def testNoOp(self):
        oper5d = OpThresholdTwoLevels(graph=Graph())
        oper5d.InputImage.setValue(self.data5d)
        oper5d.MinSize.setValue(1)
        oper5d.MaxSize.setValue(self.data5d.size)
        oper5d.HighThreshold.setValue(-0.01)
        oper5d.LowThreshold.setValue(-0.01)
        oper5d.SmootherSigma.setValue({'z': 0.0, 'y': 0.0, 'x': 0.0})
        oper5d.Channel.setValue(0)
        oper5d.CoreChannel.setValue(0)
        oper5d.CurOperator.setValue(1)

        out5d = oper5d.Output[:].wait()
        big = vigra.taggedView(oper5d.BigRegions[:].wait(),
                               axistags=oper5d.BigRegions.meta.axistags)
        assert numpy.all(big > 0)
        small = vigra.taggedView(oper5d.SmallRegions[:].wait(),
                                 axistags=oper5d.SmallRegions.meta.axistags)
        assert numpy.all(small > 0)
        numpy.testing.assert_array_equal(out5d.shape, self.data5d.shape)
        assert numpy.all(out5d > 0)

    def testChannel(self):
        shape = (200, 100, 1)
        tags = 'xyc'
        zeros = numpy.zeros(shape)
        ones = numpy.ones(shape)
        vol = numpy.concatenate((zeros, ones), axis=2)
        vol = vigra.taggedView(vol, axistags=tags)
        assert vol.shape[vol.axistags.index('c')] == 2

        oper5d = OpThresholdTwoLevels(graph=Graph())
        oper5d.InputImage.setValue(vol)
        oper5d.MinSize.setValue(1)
        oper5d.MaxSize.setValue(zeros.size)
        oper5d.HighThreshold.setValue(.5)
        oper5d.LowThreshold.setValue(.5)
        oper5d.SmootherSigma.setValue({'z': 0.0, 'y': 0.0, 'x': 0.0})
        oper5d.CurOperator.setValue(1)

        # channel 0
        oper5d.Channel.setValue(0)
        oper5d.CoreChannel.setValue(0)
        out5d = oper5d.Output[:].wait()
        assert numpy.all(out5d == 0), str(numpy.histogram(out5d))

        # channel 0
        oper5d.Channel.setValue(1)
        oper5d.CoreChannel.setValue(1)
        out5d = oper5d.Output[:].wait()
        assert numpy.all(out5d > 0), str(numpy.histogram(out5d))

    def testSingletonx(self):
        shape = (200, 100, 1)
        tags = 'xyc'
        zeros = numpy.zeros(shape)
        ones = numpy.ones(shape)
        vol = numpy.concatenate((zeros, ones), axis=2)
        vol = vigra.taggedView(vol, axistags=tags)
        assert vol.shape[vol.axistags.index('c')] == 2

        oper5d = OpThresholdTwoLevels(graph=Graph())
        oper5d.InputImage.setValue(vol)
        oper5d.MinSize.setValue(1)
        oper5d.MaxSize.setValue(zeros.size)
        oper5d.HighThreshold.setValue(.5)
        oper5d.LowThreshold.setValue(.5)
        oper5d.Channel.setValue(0)
        oper5d.CoreChannel.setValue(0)
        oper5d.CurOperator.setValue(1)

        # no smoothing
        oper5d.SmootherSigma.setValue({'z': 0.0, 'y': 0.0, 'x': 0.0})
        out5d = oper5d.Output[:].wait()
        assert numpy.all(out5d == 0), str(numpy.histogram(out5d))

        # smoothing
        oper5d.SmootherSigma.setValue({'z': 1.0, 'y': 1.0, 'x': 1.0})
        out5d = oper5d.Output[:].wait()
        assert numpy.all(out5d == 0), str(numpy.histogram(out5d))

    def test4dAnd5d(self):
        g = Graph()

        oper = OpThresholdTwoLevels(graph=g)
        oper.InputImage.setValue(self.data.withAxes(*'tzyxc'))
        oper.MinSize.setValue(self.minSize)
        oper.MaxSize.setValue(self.maxSize)
        oper.HighThreshold.setValue(self.highThreshold)
        oper.LowThreshold.setValue(self.lowThreshold)
        oper.SmootherSigma.setValue(self.sigma)
        oper.CurOperator.setValue(1)

        output = oper.Output[:].wait()
        output = vigra.taggedView(output, axistags=oper.Output.meta.axistags)

        self.checkResult(output)

        oper5d = OpThresholdTwoLevels(graph=g)
        oper5d.InputImage.setValue(self.data5d)
        oper5d.MinSize.setValue(self.minSize)
        oper5d.MaxSize.setValue(self.maxSize)
        oper5d.HighThreshold.setValue(self.highThreshold)
        oper5d.LowThreshold.setValue(self.lowThreshold)
        oper5d.SmootherSigma.setValue({'z': 0, 'y': 0, 'x': 0})
        oper5d.Channel.setValue(0)
        oper5d.CoreChannel.setValue(0)
        oper5d.CurOperator.setValue(1)

        out5d = oper5d.Output[0:1, ...].wait()
        out5d = vigra.taggedView(out5d, axistags=oper5d.Output.meta.axistags)

        self.checkResult(out5d)
        numpy.testing.assert_array_equal(out5d, output)

    def thresholdTwoLevels(self, data):
        #this function is the same as the operator, but without any lazyflow stuff
        #or memory management

        th_high = data > self.highThreshold
        th_low = data > self.lowThreshold

        cc_high = vigra.analysis.labelVolumeWithBackground(th_high.astype(numpy.uint8))
        cc_low = vigra.analysis.labelVolumeWithBackground(th_low.astype(numpy.uint8))

        # Must explicitly convert to int on 32-bit systems (mostly for VM testing)
        sizes = numpy.bincount(numpy.asarray(cc_high.flat, dtype=int))
        new_labels = numpy.zeros((sizes.shape[0]+1,))
        for icomp, comp in enumerate(sizes):
            if comp < self.minSize or comp > self.maxSize:
                new_labels[icomp] = 0
            else:
                new_labels[icomp] = 1

        cc_high_filtered = numpy.asarray(new_labels[cc_high]).astype(numpy.bool)

        prod = cc_high_filtered.astype(numpy.uint8) * numpy.asarray(cc_low)

        passed = numpy.sort(vigra.analysis.unique(prod))
        del prod
        all_label_values = numpy.zeros((cc_low.max()+1,), dtype=numpy.uint8)
        for i, l in enumerate(passed):
            all_label_values[l] = i+1
        all_label_values[0] = 0

        filtered1 = all_label_values[cc_low]

        sizes2 = numpy.bincount(filtered1.flat)
        final_label_values = numpy.zeros((filtered1.max()+1,))
        for icomp, comp in enumerate(sizes2):
            if comp < self.minSize or comp > self.maxSize:
                final_label_values[icomp] = 0
            else:
                final_label_values[icomp] = 1
        filtered2 = final_label_values[filtered1]
        return filtered2.squeeze()

    def testAgainstOwn(self):
        g = Graph()
        oper = OpThresholdTwoLevels(graph=g)
        oper.InputImage.setValue(self.data5d)
        oper.MinSize.setValue(self.minSize)
        oper.MaxSize.setValue(self.maxSize)
        oper.HighThreshold.setValue(self.highThreshold)
        oper.LowThreshold.setValue(self.lowThreshold)
        oper.SmootherSigma.setValue({'z': 0, 'y': 0, 'x': 0})
        oper.CurOperator.setValue(1)

        output = oper.Output[0, ..., 0].wait()
        output = vigra.taggedView(output, axistags=oper.Output.meta.axistags)
        output = output.withAxes(*'zyx')

        output2 = self.thresholdTwoLevels(self.data5d[0, ..., 0])
        output2 = vigra.taggedView(output2, axistags='zyx')

        ref = output*output2
        idx = np.where(ref != output)
        
#         print(str(oper.Output.meta.getTaggedShape()))
#         print(str(output.shape))
#         print(str(idx))
#         print(str(output[idx]))
#         print(str(output2[idx]))
        numpy.testing.assert_array_almost_equal(ref, output)

    def testPropagateDirty(self):
        g = Graph()
        oper = OpThresholdTwoLevels(graph=g)
        oper.InputImage.setValue(self.data5d)
        oper.MinSize.setValue(1)
        oper.MaxSize.setValue(np.prod(self.data5d.shape[1:]))
        oper.HighThreshold.setValue(.7)
        oper.LowThreshold.setValue(.3)
        oper.SmootherSigma.setValue({'z': 0, 'y': 0, 'x': 0})
        oper.CurOperator.setValue(1)

        inspector = DirtyAssert(graph=g)
        inspector.Input.connect(oper.CachedOutput)

        with self.assertRaises(DirtyAssert.WasSetDirty):
            oper.CurOperator.setValue(0)


# class TestThresholdGC(Generator2):
# 
#     def setUp(self):
#         super(TestThresholdGC, self).setUp()
# 
#     def testWithout(self):
#         oper5d = OpThresholdTwoLevels(graph=Graph())
#         oper5d.InputImage.setValue(self.data5d)
#         oper5d.MinSize.setValue(self.minSize)
#         oper5d.MaxSize.setValue(self.maxSize)
#         oper5d.HighThreshold.setValue(self.highThreshold)
#         oper5d.LowThreshold.setValue(self.lowThreshold)
#         oper5d.SmootherSigma.setValue(self.sigma)
#         oper5d.Channel.setValue(0)
#         oper5d.CoreChannel.setValue(0)
#         oper5d.CurOperator.setValue(2)
#         oper5d.UsePreThreshold.setValue(False)
# 
#         out5d = oper5d.CachedOutput[:].wait()
#         numpy.testing.assert_array_equal(out5d.shape, self.data5d.shape)
# 
#     def testWith(self):
#         oper5d = OpThresholdTwoLevels(graph=Graph())
#         oper5d.InputImage.setValue(self.data5d)
#         oper5d.MinSize.setValue(self.minSize)
#         oper5d.MaxSize.setValue(self.maxSize)
#         oper5d.HighThreshold.setValue(self.highThreshold)
#         oper5d.LowThreshold.setValue(self.lowThreshold)
#         oper5d.SmootherSigma.setValue(self.sigma)
#         oper5d.Channel.setValue(0)
#         oper5d.CoreChannel.setValue(0)
#         oper5d.CurOperator.setValue(2)
#         oper5d.UsePreThreshold.setValue(True)
# 
#         out5d = oper5d.CachedOutput[:].wait()
#         numpy.testing.assert_array_equal(out5d.shape, self.data5d.shape)
# 
#     def testStrangeAxesWith(self):
#         pred = np.zeros((20, 22, 21, 3), dtype=np.uint32)
#         pred = vigra.taggedView(pred, axistags='tyxc')
# 
#         oper5d = OpThresholdTwoLevels(graph=Graph())
#         oper5d.InputImage.setValue(pred)
#         oper5d.MinSize.setValue(self.minSize)
#         oper5d.MaxSize.setValue(self.maxSize)
#         oper5d.HighThreshold.setValue(self.highThreshold)
#         oper5d.LowThreshold.setValue(self.lowThreshold)
#         oper5d.SmootherSigma.setValue(self.sigma)
#         oper5d.Channel.setValue(0)
#         oper5d.CoreChannel.setValue(0)
#         oper5d.CurOperator.setValue(2)
#         oper5d.UsePreThreshold.setValue(True)
# 
#         out5d = oper5d.CachedOutput[:].wait()
# 
#     def testStrangeAxesWithout(self):
#         pred = np.zeros((20, 22, 21, 3), dtype=np.uint32)
#         pred = vigra.taggedView(pred, axistags='tyxc')
# 
#         oper5d = OpThresholdTwoLevels(graph=Graph())
#         oper5d.InputImage.setValue(pred)
#         oper5d.MinSize.setValue(self.minSize)
#         oper5d.MaxSize.setValue(self.maxSize)
#         oper5d.HighThreshold.setValue(self.highThreshold)
#         oper5d.LowThreshold.setValue(self.lowThreshold)
#         oper5d.SmootherSigma.setValue(self.sigma)
#         oper5d.Channel.setValue(0)
#         oper5d.CoreChannel.setValue(0)
#         oper5d.CurOperator.setValue(2)
#         oper5d.UsePreThreshold.setValue(False)
# 
#         out5d = oper5d.CachedOutput[:].wait()


from lazyflow.operator import Operator, InputSlot

class DirtyAssert(Operator):
    Input = InputSlot()
    class WasSetDirty(Exception):
        pass
    def propagateDirty(self, slot, subindex, roi):
        raise DirtyAssert.WasSetDirty()


class TestTTLUseCase(unittest.TestCase):
    def setUp(self):
        # The setting:
        # We have a 3-dimensional plus sign (3 bars crossing) that wanders
        # around as time passes. The predictions are noisy. Predictions for the
        # plus are around .9, predictions for background are around .1. The
        # axis order is a bit strange.

        shift = np.asarray((5, 4, 3), dtype=np.int)
        vol = np.ones((70, 60, 50))*.1
        vol[11:13, 12:14, 5:15] = .9  # bar in z direction
        vol[11:13, 8:18, 9:11] = .9  # bar in y direction
        vol[7:17, 12:14, 9:11] = .9  # bar in x direction

        nt = 5
        tvol = np.zeros((nt,)+vol.shape)
        for i in range(nt):
            for a in range(len(shift)):
                vol = np.roll(vol, shift[a], axis=a)
            tvol[i, ...] = vol + (np.random.random(size=vol.shape)-.5)*.1

        tvol = vigra.taggedView(tvol, axistags='tzyx')
        self.tvol = tvol.withAxes(*'ztyx')

    def checkCorrect(self, vol):
        vol = vol.withAxes(*'tzyx')
        tvol = self.tvol.withAxes(*'tzyx')
        assert np.all(vol[tvol > .5] > 0)
        assert np.all(vol[tvol < .5] == 0)

    def testSimpleUseCase(self):
        g = Graph()
        oper = OpThresholdTwoLevels(graph=g)
        oper.InputImage.setValue(self.tvol)
        oper.MinSize.setValue(1)
        oper.MaxSize.setValue(np.prod(self.tvol.shape[1:]))
        oper.HighThreshold.setValue(.7)
        oper.LowThreshold.setValue(.3)
        oper.SmootherSigma.setValue({'z': 0, 'y': 0, 'x': 0})
        oper.CurOperator.setValue(1)

        output = oper.Output[:].wait()
        output = vigra.taggedView(output, axistags=oper.Output.meta.axistags)
        self.checkCorrect(output)
