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
import logging
from functools import partial
import cPickle as pickle
import tempfile


from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import SubRegion
from lazyflow.request import Request, RequestPool
from lazyflow.roi import roiToSlice

import numpy as np

import vigra

from opDetectMissingData import *
from opDetectMissingData import _histogramIntersectionKernel

############################
############################
############################
###                      ###
###  Top Level Operator  ###
###                      ###
############################
############################
############################

logger = logging.getLogger(__name__)


class OpInterpMissingData(Operator):
    name = "OpInterpMissingData"

    InputVolume = InputSlot()
    InputSearchDepth = InputSlot(value=3)
    PatchSize = InputSlot(value=128)
    HaloSize = InputSlot(value=30)
    DetectionMethod = InputSlot(value='svm')
    InterpolationMethod = InputSlot(value='cubic')

    # be careful when using the following: setting the same thing twice will not trigger
    # the action you desire, even if something else has changed
    OverloadDetector = InputSlot(value='')

    Output = OutputSlot()
    Missing = OutputSlot()
    Detector = OutputSlot(stype=Opaque)

    _requiredMargin = {'cubic': 2, 'linear': 1, 'constant': 0}
    _dirty = False

    def __init__(self, *args, **kwargs):
        super(OpInterpMissingData, self).__init__(*args, **kwargs)

        self.detector = OpDetectMissing(parent=self)
        self.interpolator = OpInterpolate(parent=self)

        self.detector.InputVolume.connect(self.InputVolume)
        self.detector.PatchSize.connect(self.PatchSize)
        self.detector.HaloSize.connect(self.HaloSize)
        self.detector.DetectionMethod.connect(self.DetectionMethod)
        self.detector.OverloadDetector.connect(self.OverloadDetector)

        self.interpolator.InputVolume.connect(self.InputVolume)
        self.interpolator.Missing.connect(self.detector.Output)
        self.interpolator.InterpolationMethod.connect(self.InterpolationMethod)

        self.Missing.connect(self.detector.Output)
        self.Detector.connect(self.detector.Detector)

    def isDirty(self):
        return self._dirty

    def resetDirty(self):
        self._dirty = False

    def setupOutputs(self):
        # Output has the same shape/axes/dtype/drange as input
        self.Output.meta.assignFrom(self.InputVolume.meta)

        self.Detector.meta.shape = (1,)

    def execute(self, slot, subindex, roi, result):
        '''
        execute
        '''

        method = self.InterpolationMethod.value

        assert method in self._requiredMargin.keys(), \
            "Unknown interpolation method {}".format(method)

        z_index = self.InputVolume.meta.axistags.index('z')
        c_index = self.InputVolume.meta.axistags.index('c')
        t_index = self.InputVolume.meta.axistags.index('t')
        #nz = self.InputVolume.meta.getTaggedShape()['z']

        resultZYXCT = vigra.taggedView(result,
                                       self.InputVolume.meta.axistags
                                       ).withAxes(*'zyxct')

        # backup ROI
        oldStart = np.copy(roi.start)
        oldStop = np.copy(roi.stop)

        if c_index < len(roi.start):
            cRange = np.arange(roi.start[c_index], roi.stop[c_index])
        else:
            cRange = np.array([0])

        if t_index < len(roi.start):
            tRange = np.arange(roi.start[t_index], roi.stop[t_index])
        else:
            tRange = np.array([0])

        for c in cRange:
            for t in tRange:

                # change roi to single block
                if c_index < len(roi.start):
                    roi.start[c_index] = c
                    roi.stop[c_index] = c+1

                if t_index < len(roi.start):
                    roi.start[t_index] = t
                    roi.stop[t_index] = t+1

                # check if more input is needed, and how many
                z_offsets = self._extendRoi(roi)

                # get extended interpolation
                roi.start[z_index] -= z_offsets[0]
                roi.stop[z_index] += z_offsets[1]

                a = self.interpolator.Output.get(roi).wait()

                # reduce to original roi
                roi.stop = roi.stop - roi.start
                roi.start *= 0
                roi.start[z_index] += z_offsets[0]
                roi.stop[z_index] -= z_offsets[1]
                key = roiToSlice(roi.start, roi.stop)

                resultZYXCT[..., c, t] = vigra.taggedView(
                    a[key],
                    self.InputVolume.meta.axistags).withAxes(*'zyx')

                #restore ROI, will be used in other methods!!!
                roi.start = np.copy(oldStart)
                roi.stop = np.copy(oldStop)

        return result

    def propagateDirty(self, slot, subindex, roi):

        if slot == self.InputVolume:
            self.Output.setDirty(roi)

        if slot == self.OverloadDetector:
            self._dirty = True

        if slot == self.PatchSize or slot == self.HaloSize:
            self._dirty = True

    def train(self, force=False):
        return self.detector.train(force=force)

    def _extendRoi(self, roi):
        origStart = np.copy(roi.start)
        origStop = np.copy(roi.stop)

        offset_top = 0
        offset_bot = 0

        z_index = self.InputVolume.meta.axistags.index('z')

        depth = self.InputSearchDepth.value
        nRequestedSlices = roi.stop[z_index] - roi.start[z_index]
        nNeededSlices = self._requiredMargin[self.InterpolationMethod.value]

        missing = vigra.taggedView(self.detector.Output.get(roi).wait(),
                                   axistags=self.InputVolume.meta.axistags
                                   ).withAxes(*'zyx')

        nGoodSlicesTop = 0
        # go inside the roi
        for k in range(nRequestedSlices):
            if np.all(missing[k, ...] == 0):   # clean slice
                nGoodSlicesTop += 1
            else:
                break

        # are we finished yet?
        if nGoodSlicesTop >= nRequestedSlices:
            return (0, 0)

        # looks like we need more slices on top
        while nGoodSlicesTop < nNeededSlices and offset_top < depth \
                and roi.start[z_index] > 0:
            roi.stop[z_index] = roi.start[z_index]
            roi.start[z_index] -= 1
            offset_top += 1
            topmissing = self.detector.Output.get(roi).wait()
            if np.all(topmissing == 0):   # clean slice
                nGoodSlicesTop += 1
            else:   # need to start again
                nGoodSlicesTop = 0

        nGoodSlicesBot = 0
        # go inside the roi
        for k in range(1, nRequestedSlices+1):
            if np.all(missing[-k, ...] == 0):  # clean slice
                nGoodSlicesBot += 1
            else:
                break

        roi.start = np.copy(origStart)
        roi.stop = np.copy(origStop)

        # looks like we need more slices on bottom
        while roi.stop[z_index] < self.InputVolume.meta.getTaggedShape()['z'] \
                and nGoodSlicesBot < nNeededSlices and offset_bot < depth:
            roi.start[z_index] = roi.stop[z_index]
            roi.stop[z_index] += 1
            offset_bot += 1
            botmissing = self.detector.Output.get(roi).wait()
            if np.all(botmissing == 0):  # clean slice
                nGoodSlicesBot += 1
            else:  # need to start again
                nGoodSlicesBot = 0

        roi.start = np.copy(origStart)
        roi.stop = np.copy(origStop)

        return (offset_top, offset_bot)

################################
################################
################################
###                          ###
###  Interpolation Operator  ###
###                          ###
################################
################################
################################

def _cubic_mat(n=1):
    n = float(n)
    x = -1/(n+1)
    y = (n+2)/(n+1)

    A = [[1, x, x**2, x**3],
        [1, 0, 0, 0],
        [1, 1, 1, 1],
        [1, y, y**2, y**3]]

    #TODO we could implement the direct inverse here, but it's a bit lengthy
    # compare to http://www.wolframalpha.com/input/?i=invert+matrix%28[1%2Cx%2Cx^2%2Cx^3]%2C[1%2C0%2C0%2C0]%2C[1%2C1%2C1%2C1]%2C[1%2Cy%2Cy^2%2Cy^3]%29

    return np.linalg.inv(A)


class OpInterpolate(Operator):
    InputVolume = InputSlot()
    Missing = InputSlot()
    InterpolationMethod = InputSlot(value='cubic')

    Output = OutputSlot()

    _requiredMargin = {'cubic': 2, 'linear': 1, 'constant': 0}
    _maxInterpolationDistance = \
        {'cubic': 1, 'linear': np.inf, 'constant': np.inf}
    _fallbacks = {'cubic': 'linear', 'linear': 'constant', 'constant': None}

    def propagateDirty(self, slot, subindex, roi):
        # TODO
        self.Output.setDirty(roi)

    def setupOutputs(self):
        # Output has the same shape/axes/dtype/drange as input
        self.Output.meta.assignFrom(self.InputVolume.meta)

        try:
            self._iinfo = np.iinfo(self.InputVolume.meta.dtype)
        except ValueError:
            # not integer type, no casting needed
            self._iinfo = None

        assert self.InputVolume.meta.getTaggedShape() \
            == self.Missing.meta.getTaggedShape(), \
            "InputVolume and Missing must have the same shape " + \
            "({} vs {})".format(
                self.InputVolume.meta.getTaggedShape(),
                self.Missing.meta.getTaggedShape())

    def execute(self, slot, subindex, roi, result):

        # prefill result
        result[:] = self.InputVolume.get(roi).wait()

        resultZYXCT = vigra.taggedView(result,
                                       self.InputVolume.meta.axistags
                                       ).withAxes(*'zyxct')
        missingZYXCT = vigra.taggedView(self.Missing.get(roi).wait(),
                                        self.Missing.meta.axistags
                                        ).withAxes(*'zyxct')

        for t in range(resultZYXCT.shape[4]):
            for c in range(resultZYXCT.shape[3]):
                missingLabeled = vigra.analysis.labelVolumeWithBackground(
                    missingZYXCT[..., c, t])
                maxLabel = missingLabeled.max()
                for i in range(1, maxLabel+1):
                    self._interpolate(resultZYXCT[..., c, t],
                                      missingLabeled == i)

        return result

    def _cast(self, x):
        '''
        casts the array to expected range (i.e. 0..255 for uint8 types, ...)
        '''
        if not self._iinfo is None:
            x = np.where(x > self._iinfo.max, self._iinfo.max, x)
            x = np.where(x < self._iinfo.min, self._iinfo.min, x)
        return x

    def _interpolate(self, volume, missing, method=None):
        '''
        interpolates in z direction
        :param volume: 3d block with axistags 'zyx'
        :type volume: array-like
        :param missing: True where data is missing
        :type missing: bool, 3d block with axistags 'zyx'
        :param method: 'cubic' or 'linear' or 'constant'
        :type method: str
        '''

        method = self.InterpolationMethod.value if method is None else method
        # sanity checks
        assert method in self._requiredMargin.keys(), \
            "Unknown method '{}'".format(method)

        assert volume.axistags.index('z') == 0 \
            and volume.axistags.index('y') == 1 \
            and volume.axistags.index('x') == 2 \
            and len(volume.shape) == 3, \
            "Data must be 3d with z as first axis."

        # number and z-location of missing slices (z-axis is at zero)
        black_z_ind, black_y_ind, black_x_ind = np.where(missing)

        if len(black_z_ind) == 0:  # no need for interpolation
            return

        if black_z_ind.max() - black_z_ind.min() + 1 \
                > self._maxInterpolationDistance[method]:
            self._interpolate(volume, missing, self._fallbacks[method])
            return

        # indices with respect to the required margin around the missing values
        minZ = black_z_ind.min() - self._requiredMargin[method]
        maxZ = black_z_ind.max() + self._requiredMargin[method]

        n = maxZ-minZ-2*self._requiredMargin[method]+1

        if not (minZ > -1 and maxZ < volume.shape[0]):
            # this method is not applicable, try another one
            logger.warning(" ".join((
                "Margin not big enough for interpolation ",
                "(need at least {} pixels for '{}')".format(
                    self._requiredMargin[method], method))))

            if self._fallbacks[method] is not None:
                logger.warning("Falling back to method '{}'".format(
                    self._fallbacks[method]))
                self._interpolate(volume, missing, self._fallbacks[method])
                return
            else:
                assert False, " ".join((
                    "Margin not big enough for interpolation",
                    "(need at least {} pixels for '{}')".format(
                        self._requiredMargin[method], method),
                    "and no fallback available"))

        minY, maxY = (black_y_ind.min(), black_y_ind.max())
        minX, maxX = (black_x_ind.min(), black_x_ind.max())

        if method == 'linear' or method == 'cubic' and n > 1:
            # do a convex combination of the boundary slices
            xs = np.linspace(0, 1, n+2)
            left = volume[minZ, minY:maxY+1, minX:maxX+1]
            right = volume[maxZ, minY:maxY+1, minX:maxX+1]

            for i in range(n):
                # interpolate every slice
                volume[minZ+i+1, minY:maxY+1, minX:maxX+1] = \
                    self._cast((1-xs[i+1])*left + xs[i+1]*right)

        elif method == 'cubic':
            # interpolation coefficients

            D = np.rollaxis(volume[
                [minZ, minZ+1, maxZ-1, maxZ], minY:maxY+1, minX:maxX+1
                ], 0, 3)
            F = np.tensordot(D, _cubic_mat(n), ([2, ], [1, ]))

            xs = np.linspace(0, 1, n+2)
            for i in range(n):
                # interpolate every slice
                x = xs[i+1]
                volume[minZ+i+2, minY:maxY+1, minX:maxX+1] = \
                    self._cast(
                        F[..., 0] + F[..., 1]*x +
                        F[..., 2]*x**2 + F[..., 3]*x**3)

        else:  # constant
            if minZ > 0:
                # fill right hand side with last good slice
                for i in range(maxZ-minZ+1):
                    volume[minZ+i, minY:maxY+1, minX:maxX+1] = \
                        volume[minZ-1, minY:maxY+1, minX:maxX+1]
            elif maxZ < volume.shape[0]-1:
                # fill left hand side with last good slice
                for i in range(maxZ-minZ+1):
                    volume[minZ+i, minY:maxY+1, minX:maxX+1] = \
                        volume[maxZ+1, minY:maxY+1, minX:maxX+1]
            else:
                # nothing to do for empty block
                logger.warning(",".join((
                    "Not enough data for interpolation"
                    "leaving slice as is ...")))
