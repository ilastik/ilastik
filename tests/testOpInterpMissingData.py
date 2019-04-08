from __future__ import print_function
from builtins import zip
from builtins import range

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
# 		   http://ilastik.org/license/
###############################################################################
from lazyflow.graph import Graph

import numpy as np
import vigra
from lazyflow.operators.opInterpMissingData import OpInterpMissingData, OpInterpolate, OpDetectMissing, havesklearn

import unittest
from numpy.testing import assert_array_almost_equal, assert_array_equal

from nose import SkipTest

try:
    from scipy.interpolate import UnivariateSpline

    haveScipy = True
except ImportError:
    haveScipy = False

np.set_printoptions(precision=3, linewidth=80)

_testDescriptions = [
    "large block empty",
    "single layer empty",
    "last layer empty",
    "first block empty",
    "second to last layer empty",
    "second layer empty",
    "first layer empty",
    "multiple blocks empty",
    "all layers empty",
    "different regions empty",
]


def _getTestVolume(description, method):

    if description == "large block empty":
        # expected_output = _volume(nz=100, method=method)
        expected_output = _volume(nz=100, method="linear" if not method == "constant" else "constant")
        volume = vigra.VigraArray(expected_output)
        missing = vigra.VigraArray(expected_output, dtype=np.uint8)
        volume[:, :, 30:50] = 0
        missing[:] = 0
        missing[:, :, 30:50] = 1
    elif description == "single layer empty":
        (volume, missing, expected_output) = _singleMissingLayer(layer=30, method=method)
    elif description == "last layer empty":
        (volume, missing, expected_output) = _singleMissingLayer(nz=100, layer=99)
        # expect constant interpolation at border
        expected_output[:, :, -1] = volume[:, :, -2]
    elif description == "second to last layer empty":
        (volume, missing, expected_output) = _singleMissingLayer(nz=100, layer=98, method="linear")
    elif description == "first layer empty":
        (volume, missing, expected_output) = _singleMissingLayer(nz=100, layer=0)
        # expect constant interpolation at border
        expected_output[:, :, 0] = volume[:, :, 1]
    elif description == "second layer empty":
        (volume, missing, expected_output) = _singleMissingLayer(nz=100, layer=1, method="linear")
    elif description == "first block empty":
        expected_output = _volume(method=method)
        volume = vigra.VigraArray(expected_output)
        missing = vigra.VigraArray(expected_output, dtype=np.uint8)
        volume[:, :, 0:10] = 0
        missing[:] = 0
        missing[:, :, 0:10] = 1
        # expect constant interpolation at border
        expected_output[..., 0:10] = volume[..., 10].withAxes(*"xyz")
    elif description == "multiple blocks empty":
        expected_output = _volume(method="linear" if not method == "constant" else "constant")
        volume = vigra.VigraArray(expected_output)
        missing = vigra.VigraArray(expected_output, dtype=np.uint8)
        volume[:, :, [10, 11, 30, 31]] = 0
        missing[:] = 0
        missing[:, :, [10, 11, 30, 31]] = 1
    elif description == "all layers empty":
        expected_output = _volume(method=method) * 0
        volume = vigra.VigraArray(expected_output)
        missing = vigra.VigraArray(expected_output, dtype=np.uint8)
        missing[:, :, [10, 11, 30, 31]] = 1
    elif description == "different regions empty":
        (volume, missing, expected_output) = _singleMissingLayer(layer=30, method=method)

        (volume2, missing2, expected_output2) = _singleMissingLayer(layer=60, method=method)
        volume2 = 256 - volume2
        volume2[np.where(missing2 > 0)] = 0
        expected_output2 = 256 - expected_output2

        volume[..., 45:] = volume2[..., 45:]
        expected_output[..., 45:] = expected_output2[..., 45:]
        missing += missing2

    else:
        raise NotImplementedError("test cube '{}' not available.".format(description))

    return (volume, missing, expected_output)


def _volume(nx=64, ny=64, nz=100, method="linear"):
    b = vigra.VigraArray(np.ones((nx, ny, nz)), axistags=vigra.defaultAxistags("xyz"))
    if method == "linear":
        for i in range(b.shape[2]):
            b[:, :, i] *= (i + 1) + 50
    elif method == "cubic":
        s = nz // 3
        for z in range(b.shape[2]):
            b[:, :, z] = (z - s) ** 2 * z * 150.0 / (nz * (nz - s) ** 2) + 30
    elif method == "constant":
        b[:] = 124
    else:
        raise NotImplementedError("unknown method '{}'.".format(method))

    return b


def _singleMissingLayer(layer=30, nx=64, ny=64, nz=100, method="linear"):
    expected_output = _volume(nx=nx, ny=ny, nz=nz, method=method)
    volume = vigra.VigraArray(expected_output)
    missing = vigra.VigraArray(np.zeros(volume.shape), axistags=volume.axistags, dtype=np.uint8)
    volume[:, :, layer] = 0
    missing[:] = 0
    missing[:, :, layer] = 1
    return (volume, missing, expected_output)


class TestBasics(unittest.TestCase):
    def testVersionDetection(self):
        from lazyflow.operators.opDetectMissingData import extractVersion

        assert extractVersion("0.11") == 11
        assert extractVersion("0.14.1") == 14
        assert extractVersion("haiku_os-0.9") == 9
        assert extractVersion("0.21-git") == 21


class TestDetection(unittest.TestCase):
    def setup_method(self, method):
        v = _volume()
        self.op = OpDetectMissing(graph=Graph())
        self.op.InputVolume.setValue(v)
        self.op.PatchSize.setValue(64)
        self.op.HaloSize.setValue(0)
        self.op.DetectionMethod.setValue("svm")
        self.op.train(force=True)

    def testDetectorOmnipresence(self):
        if not havesklearn:
            raise SkipTest
        assert self.op.has(self.op.NHistogramBins.value, method="svm"), "Detector is untrained after call to train()"
        assert not self.op.has(self.op.NHistogramBins.value + 2, method="svm"), "Wrong bin size trained."

        op2 = OpDetectMissing(graph=Graph())
        assert op2.has(self.op.NHistogramBins.value, method="svm"), "Trained detectors are not global"

        self.op.reset()
        assert not self.op.has(self.op.NHistogramBins.value, method="svm"), "Detector not reset."
        assert not op2.has(self.op.NHistogramBins.value, method="svm"), "Detector not reset globally."

    def testDetectorPropagation(self):
        if not havesklearn:
            raise SkipTest
        s = self.op.Detector[:].wait()
        self.op.reset()
        assert not self.op.has(self.op.NHistogramBins.value, method="svm"), "Detector not reset."
        self.op.OverloadDetector.setValue(s)
        assert self.op.has(self.op.NHistogramBins.value, method="svm"), "Detector not loaded."

    def testClassicDetection(self):
        self.op.DetectionMethod.setValue("classic")
        self.op.PatchSize.setValue(1)
        self.op.HaloSize.setValue(0)
        (v, m, _) = _singleMissingLayer(layer=15, nx=1, ny=1, nz=50, method="linear")
        self.op.InputVolume.setValue(v)

        assert_array_equal(
            self.op.Output[:].wait().view(type=np.ndarray),
            m.view(type=np.ndarray),
            err_msg="input with single black layer",
        )

    def testSVMDetection(self):
        if not havesklearn:
            raise SkipTest
        self.op.DetectionMethod.setValue("svm")
        self.op.PatchSize.setValue(1)
        self.op.HaloSize.setValue(0)
        (v, m, _) = _singleMissingLayer(layer=15, nx=1, ny=1, nz=50, method="linear")
        self.op.InputVolume.setValue(v)

        assert_array_equal(
            self.op.Output[:].wait().view(type=np.ndarray),
            m.view(type=np.ndarray),
            err_msg="input with single black layer",
        )

    def testSVMDetectionWithHalo(self):
        nBlack = 15
        if not havesklearn:
            raise SkipTest
        self.op.DetectionMethod.setValue("svm")
        self.op.PatchSize.setValue(5)
        self.op.HaloSize.setValue(2)
        (v, m, _) = _singleMissingLayer(layer=nBlack, nx=10, ny=15, nz=50, method="linear")
        self.op.InputVolume.setValue(v)

        assert_array_equal(
            self.op.Output[:].wait()[..., nBlack].view(type=np.ndarray),
            m[..., nBlack].view(type=np.ndarray),
            err_msg="input with single black layer",
        )

    def testSVMWithHalo(self):
        if not havesklearn:
            raise SkipTest
        self.op.DetectionMethod.setValue("svm")
        self.op.PatchSize.setValue(2)
        self.op.HaloSize.setValue(1)
        (v, m, _) = _singleMissingLayer(layer=15, nx=4, ny=4, nz=50, method="linear")
        self.op.InputVolume.setValue(v)

        assert_array_equal(
            self.op.Output[:].wait().view(type=np.ndarray),
            m.view(type=np.ndarray),
            err_msg="input with single black layer",
        )

    def testSingleMissingLayer(self):
        (v, m, _) = _singleMissingLayer(layer=15, nx=64, ny=64, nz=50, method="linear")
        self.op.InputVolume.setValue(v)

        assert_array_equal(
            self.op.Output[:].wait().view(type=np.ndarray),
            m.view(type=np.ndarray),
            err_msg="input with single black layer",
        )

    def testDoubleMissingLayer(self):
        (v, m, _) = _singleMissingLayer(layer=15, nx=64, ny=64, nz=50, method="linear")
        (v2, m2, _) = _singleMissingLayer(layer=35, nx=64, ny=64, nz=50, method="linear")
        m2[np.where(m2 == 1)] = 2
        self.op.InputVolume.setValue(np.sqrt(v * v2))

        assert_array_equal(
            self.op.Output[:].wait().view(type=np.ndarray) > 0,
            (m + m2).view(type=np.ndarray) > 0,
            err_msg="input with two black layers",
        )

    def test4D(self):
        vol = vigra.VigraArray(np.ones((10, 64, 64, 3)), axistags=vigra.defaultAxistags("cxyz"))
        self.op.InputVolume.setValue(vol)
        self.op.Output[:].wait()

    def test5D(self):
        vol = vigra.VigraArray(np.ones((15, 64, 10, 3, 64)), axistags=vigra.defaultAxistags("cxzty"))
        self.op.InputVolume.setValue(vol)
        self.op.Output[:].wait()

    def testPersistence(self):
        dumpedString = self.op.dumps()
        self.op.loads(dumpedString)

    def testPatchify(self):
        from lazyflow.operators.opDetectMissingData import _patchify as patchify

        X = np.vander(np.arange(2, 5))
        """ results in
        X = array([[ 4,  2,  1],
                   [ 9,  3,  1],
                   [16,  4,  1]])
        """
        (patches, slices) = patchify(X, 1, 1)

        expected = [
            np.array([[4, 2], [9, 3]]),
            np.array([[4, 2, 1], [9, 3, 1]]),
            np.array([[2, 1], [3, 1]]),
            np.array([[4, 2], [9, 3], [16, 4]]),
            np.array([[4, 2, 1], [9, 3, 1], [16, 4, 1]]),
            np.array([[2, 1], [3, 1], [4, 1]]),
            np.array([[9, 3], [16, 4]]),
            np.array([[9, 3, 1], [16, 4, 1]]),
            np.array([[3, 1], [4, 1]]),
        ]

        expSlices = [
            (slice(0, 1), slice(0, 1)),
            (slice(0, 1), slice(1, 2)),
            (slice(0, 1), slice(2, 3)),
            (slice(1, 2), slice(0, 1)),
            (slice(1, 2), slice(1, 2)),
            (slice(1, 2), slice(2, 3)),
            (slice(2, 3), slice(0, 1)),
            (slice(2, 3), slice(1, 2)),
            (slice(2, 3), slice(2, 3)),
        ]

        for ep, s in zip(expected, expSlices):
            # check if patch is in the result
            has = False
            for i, p in enumerate(patches):
                if np.array_equal(p, ep):
                    has = True
                    # check if slice is ok
                    self.assertEqual(s, slices[i])

            assert has, "Mising patch {}".format(ep)
            pass

    def testPatchDetection(self):
        vol = vigra.taggedView(np.ones((5, 5), dtype=np.uint8) * 128, axistags=vigra.defaultAxistags("xy"))
        vol[2:5, 2:5] = 0
        expected = np.zeros((5, 5))
        expected[3:5, 3:5] = 1

        self.op.PatchSize.setValue(2)
        self.op.HaloSize.setValue(1)
        self.op.DetectionMethod.setValue("classic")
        self.op.InputVolume.setValue(vol)

        out = self.op.Output[:].wait()

        assert_array_equal(expected[3:5, 3:5], out[3:5, 3:5])


class TestInterpolation(unittest.TestCase):
    """
    tests for the interpolation
    """

    def setup_method(self, method):
        g = Graph()
        op = OpInterpolate(graph=g)
        self.op = op

    def testLinearAlgorithm(self):
        (v, m, orig) = _singleMissingLayer(layer=15, nx=1, ny=1, nz=50, method="linear")
        v[:, :, 10:15] = 0
        m[:, :, 10:15] = 1
        interpolationMethod = "linear"

        self.op.InputVolume.setValue(v)
        self.op.Missing.setValue(m)
        self.op.InterpolationMethod.setValue(interpolationMethod)

        assert_array_almost_equal(
            self.op.Output[:].wait().view(np.ndarray),
            orig.view(np.ndarray),
            decimal=3,
            err_msg="direct comparison to linear data",
        )

    def testCubicAlgorithm(self):
        (v, m, orig) = _singleMissingLayer(layer=15, nx=1, ny=1, nz=50, method="cubic")
        v[:, :, 10] = 0
        m[:, :, 10] = 1
        interpolationMethod = "cubic"
        self.op.InputVolume.setValue(v)
        self.op.Missing.setValue(m)
        self.op.InterpolationMethod.setValue(interpolationMethod)

        # natural comparison
        assert_array_almost_equal(
            self.op.Output[:].wait().view(np.ndarray),
            orig.view(np.ndarray),
            decimal=3,
            err_msg="direct comparison to cubic data",
        )

        if not haveScipy:
            return

        # scipy spline interpolation
        x = np.zeros(v.shape)
        x[:, :, :] = np.arange(v.shape[2])
        (i, j, k) = np.where(m == 0)
        xs = x[i, j, k]
        ys = v.view(np.ndarray)[i, j, k]
        spline = UnivariateSpline(x[:, :, [8, 9, 11, 12]], v[:, :, [8, 9, 11, 12]], k=3, s=0)
        e = spline(np.arange(v.shape[2]))

        assert_array_almost_equal(
            self.op.Output[:].wait()[:, :, 10].squeeze().view(np.ndarray),
            e[10],
            decimal=3,
            err_msg="scipy.interpolate.UnivariateSpline comparison",
        )

    def test4D(self):
        vol = vigra.VigraArray(np.ones((50, 50, 10, 3)), axistags=vigra.defaultAxistags("cxyz"))
        miss = vigra.VigraArray(vol)
        miss[:, :, 3, 2] = 1
        self.op.InputVolume.setValue(vol)
        self.op.Missing.setValue(miss)

        self.op.Output[:].wait()

    def test5D(self):
        vol = vigra.VigraArray(np.ones((50, 50, 10, 3, 7)), axistags=vigra.defaultAxistags("cxzty"))
        miss = vigra.VigraArray(vol)
        miss[:, :, 3, 2, 4] = 1
        self.op.InputVolume.setValue(vol)
        self.op.Missing.setValue(miss)

        self.op.Output[:].wait()

    def testNothingToInterpolate(self):
        vol = vigra.VigraArray(np.ones((50, 50, 10, 3, 7)), axistags=vigra.defaultAxistags("cxzty"))
        miss = vigra.VigraArray(vol) * 0

        self.op.InputVolume.setValue(vol)
        self.op.Missing.setValue(miss)

        assert_array_equal(
            self.op.Output[:].wait(), vol.view(np.ndarray), err_msg="interpolation where nothing had to be interpolated"
        )

    def testIntegerRange(self):
        """
        test if the output is in the right integer range
        in particular, too large values should be set to max and too small
        values to min
        """
        v = np.zeros((1, 1, 5), dtype=np.uint8)
        v[0, 0, :] = [220, 255, 0, 255, 220]
        v = vigra.VigraArray(v, axistags=vigra.defaultAxistags("xyz"), dtype=np.uint8)
        m = vigra.VigraArray(v, axistags=vigra.defaultAxistags("xyz"), dtype=np.uint8)
        m[:] = 0
        m[0, 0, 2] = 1

        for interpolationMethod in ["cubic"]:
            self.op.InputVolume.setValue(v)
            self.op.Missing.setValue(m)
            self.op.InterpolationMethod.setValue(interpolationMethod)
            self.op.InputVolume.setValue(v)
            out = self.op.Output[:].wait().view(np.ndarray)
            # natural comparison
            self.assertEqual(out[0, 0, 2], 255)

        v = np.zeros((1, 1, 5), dtype=np.uint8)
        v[0, 0, :] = [220, 255, 0, 255, 220]
        v = 255 - vigra.VigraArray(v, axistags=vigra.defaultAxistags("xyz"), dtype=np.uint8)
        m = vigra.VigraArray(v, axistags=vigra.defaultAxistags("xyz"), dtype=np.uint8)
        m[:] = 0
        m[0, 0, 2] = 1

        for interpolationMethod in ["cubic"]:
            self.op.InputVolume.setValue(v)
            self.op.Missing.setValue(m)
            self.op.InterpolationMethod.setValue(interpolationMethod)
            self.op.InputVolume.setValue(v)
            out = self.op.Output[:].wait().view(np.ndarray)
            # natural comparison
            self.assertEqual(out[0, 0, 2], 0)


class TestInterpMissingData(unittest.TestCase):
    """
    tests for the whole detection/interpolation workflow
    """

    def setup_method(self, method):
        g = Graph()
        op = OpInterpMissingData(graph=g)
        op.DetectionMethod.setValue("svm")
        op.train(force=True)
        assert op.detector.has(op.detector.NHistogramBins.value, method="svm"), "Detector not trained."
        self.op = op

    def testDetectorPropagation(self):
        if not havesklearn:
            raise SkipTest
        method = "svm"
        self.op.DetectionMethod.setValue(method)
        v = _volume()
        self.op.InputVolume.setValue(v)
        s = self.op.Detector[:].wait()

        self.op.detector.reset()
        assert not self.op.detector.has(self.op.detector.NHistogramBins.value, method=method), "Detector not reset."

        self.op.OverloadDetector.setValue(s)
        assert self.op.detector.has(self.op.detector.NHistogramBins.value, method=method), "Detector not loaded."

    def testLinearBasics(self):
        self.op.InputSearchDepth.setValue(0)

        interpolationMethod = "linear"
        self.op.InterpolationMethod.setValue(interpolationMethod)

        for desc in _testDescriptions:
            (volume, _, expected) = _getTestVolume(desc, interpolationMethod)
            self.op.InputVolume.setValue(volume)
            self.op.PatchSize.setValue(volume.shape[0])
            print(self.op.Output[:].wait().view(np.ndarray)[0, 0, :])
            print(self.op.Missing[:].wait().view(np.ndarray)[0, 0, :])
            print(" != ")
            print(expected.view(np.ndarray)[0, 0, :])
            assert_array_almost_equal(
                self.op.Output[:].wait().view(np.ndarray),
                expected.view(np.ndarray),
                decimal=2,
                err_msg="method='{}', test='{}'".format(interpolationMethod, desc),
            )

    def testCubicBasics(self):
        self.op.InputSearchDepth.setValue(0)

        interpolationMethod = "cubic"
        self.op.InterpolationMethod.setValue(interpolationMethod)

        for desc in _testDescriptions:
            (volume, _, expected) = _getTestVolume(desc, interpolationMethod)
            self.op.InputVolume.setValue(volume)
            self.op.PatchSize.setValue(volume.shape[0])
            assert_array_almost_equal(
                self.op.Output[:].wait().view(np.ndarray),
                expected.view(np.ndarray),
                decimal=2,
                err_msg="method='{}', test='{}'".format(interpolationMethod, desc),
            )

    def testSwappedAxesLinear(self):
        self.op.InputSearchDepth.setValue(0)

        interpolationMethod = "linear"
        self.op.InterpolationMethod.setValue(interpolationMethod)

        for desc in _testDescriptions:
            (volume, _, expected) = _getTestVolume(desc, interpolationMethod)
            self.op.PatchSize.setValue(volume.shape[0])
            volume = volume.transpose()
            expected = expected.transpose()
            self.op.InputVolume.setValue(volume)

            assert_array_almost_equal(
                self.op.Output[:].wait().view(np.ndarray),
                expected.view(np.ndarray),
                decimal=2,
                err_msg="method='{}', test='{}'".format(interpolationMethod, desc),
            )

    def testSwappedAxesCubic(self):
        self.op.InputSearchDepth.setValue(0)

        interpolationMethod = "cubic"
        self.op.InterpolationMethod.setValue(interpolationMethod)

        for desc in _testDescriptions:
            (volume, _, expected) = _getTestVolume(desc, interpolationMethod)
            self.op.PatchSize.setValue(volume.shape[0])
            volume = volume.transpose()
            expected = expected.transpose()
            self.op.InputVolume.setValue(volume)

            assert_array_almost_equal(
                self.op.Output[:].wait().view(np.ndarray),
                expected.view(np.ndarray),
                decimal=2,
                err_msg="method='{}', test='{}'".format(interpolationMethod, desc),
            )

    def testDepthSearch(self):
        # TODO extend
        nz = 30
        interpolationMethod = "cubic"
        self.op.InterpolationMethod.setValue(interpolationMethod)
        (vol, _, exp) = _singleMissingLayer(layer=nz, method=interpolationMethod)

        self.op.InputVolume.setValue(vol)
        self.op.InputSearchDepth.setValue(15)
        self.op.PatchSize.setValue(vol.shape[0])

        result = self.op.Output[:, :, nz].wait()

        assert_array_almost_equal(result.squeeze(), exp[:, :, nz].view(np.ndarray).squeeze(), decimal=3)

    def testRoi(self):
        nz = 30
        interpolationMethod = "linear"
        self.op.InterpolationMethod.setValue(interpolationMethod)
        (vol, _, exp) = _singleMissingLayer(layer=nz, method=interpolationMethod)
        (vol2, _, _) = _singleMissingLayer(layer=nz + 1, method=interpolationMethod)
        vol = np.sqrt(vol * vol2)

        self.op.InputVolume.setValue(vol)
        self.op.InputSearchDepth.setValue(5)
        self.op.PatchSize.setValue(vol.shape[0])

        result = self.op.Output[:, :, nz + 1].wait()

        assert_array_almost_equal(result.squeeze(), exp[:, :, nz + 1].view(np.ndarray).squeeze(), decimal=3)
        pass

    def testBadImageSize(self):
        # TODO implement
        raise SkipTest

    def testHaloSize(self):
        # TODO implement
        raise SkipTest

    def test4D(self):
        vol = vigra.VigraArray(np.ones((10, 64, 64, 3)), axistags=vigra.defaultAxistags("cxyz"))
        self.op.InputVolume.setValue(vol)
        x = self.op.Output[:].wait()
        assert x.shape == vol.shape

    def test5D(self):
        vol = vigra.VigraArray(np.ones((15, 64, 10, 3, 64)), axistags=vigra.defaultAxistags("cxzty"))
        self.op.InputVolume.setValue(vol)
        x = self.op.Output[:].wait()
        assert x.shape == vol.shape


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
