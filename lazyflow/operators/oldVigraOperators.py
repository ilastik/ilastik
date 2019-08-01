# -*- coding: utf-8 -*-
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
#          http://ilastik.org/license/
###############################################################################
# legacy code for comparing to new implementation (tests in testNewFeatureSelection.py)
# todo: remove this code after testing period

# Python
from __future__ import absolute_import
from __future__ import division
from builtins import zip

from builtins import range
import os
from collections import deque
import itertools
import math
import traceback
from functools import partial
import logging
import copy
import time

logger = logging.getLogger(__name__)

# SciPy
import numpy, vigra

# lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot, OrderedSignal
from lazyflow import roi
from lazyflow.roi import sliceToRoi, roiToSlice
from lazyflow.request import RequestPool
from .operators import OpArrayPiper
from lazyflow.rtype import SubRegion
from .generic import OpMultiArrayStacker, popFlagsFromTheKey

# Sven's fast filters
try:
    import fastfilters

    WITH_FAST_FILTERS = True
    logger.info("Using fast filters.")
except ImportError as e:
    WITH_FAST_FILTERS = False
    logger.warning("Failed to import fast filters: " + str(e))


class OpPixelFeaturesPresmoothed(Operator):
    name = "OpPixelFeaturesPresmoothed"
    category = "Vigra filter"

    Input = InputSlot()
    Matrix = InputSlot()
    Scales = InputSlot()
    FeatureIds = InputSlot()

    Output = OutputSlot()  # The entire block of features as a single image (many channels)
    Features = OutputSlot(level=1)  # Each feature image listed separately, with feature name provided in metadata

    # Specify a default set & order for the features we compute
    DefaultFeatureIds = [
        "GaussianSmoothing",
        "LaplacianOfGaussian",
        "GaussianGradientMagnitude",
        "DifferenceOfGaussians",
        "StructureTensorEigenvalues",
        "HessianOfGaussianEigenvalues",
    ]

    WINDOW_SIZE = 3.5

    class InvalidScalesError(Exception):
        def __init__(self, invalid_scales):
            self.invalid_scales = invalid_scales

    def __init__(self, *args, **kwargs):
        Operator.__init__(self, *args, **kwargs)
        self.source = OpArrayPiper(parent=self)
        self.source.inputs["Input"].connect(self.inputs["Input"])

        # Give our feature IDs input a default value (connected out of the box, but can be changed)
        self.inputs["FeatureIds"].setValue(self.DefaultFeatureIds)

    def getInvalidScales(self):
        """
        Check each of the scales the user selected against the shape of the input dataset (in space only).
        Return a list of the selected scales that are too large for the input dataset.

        .. note:: This function is NOT called automatically.  Clients are expected to call it after
                  configuring the operator, before they attempt to execute() the operator.
                  If this function returns a non-empty list of scales, then calling execute()
                  would generate errors.
        """
        invalid_scales = []
        for j, scale in enumerate(self.scales):
            if self.matrix[:, j].any():
                tagged_shape = self.Input.meta.getTaggedShape()
                spatial_axes_shape = [k_v for k_v in list(tagged_shape.items()) if k_v[0] in "xyz"]
                spatial_shape = list(zip(*spatial_axes_shape))[1]

                if (scale * self.WINDOW_SIZE > numpy.array(spatial_shape)).any():
                    invalid_scales.append(scale)
        return invalid_scales

    def setupOutputs(self):
        assert self.Input.meta.getAxisKeys()[-1] == "c", "This code assumes channel is the last axis"

        self.scales = self.inputs["Scales"].value
        self.matrix = self.inputs["Matrix"].value

        if not isinstance(self.matrix, numpy.ndarray):
            raise RuntimeError("OpPixelFeatures: Please input a numpy.ndarray as 'Matrix'")

        dimCol = len(self.scales)
        dimRow = len(self.inputs["FeatureIds"].value)

        assert dimRow == self.matrix.shape[0], (
            "Please check the matrix or the scales they are not the same (scales = %r, matrix.shape = %r)"
            % (self.scales, self.matrix.shape)
        )
        assert dimCol == self.matrix.shape[1], (
            "Please check the matrix or the scales they are not the same (scales = %r, matrix.shape = %r)"
            % (self.scales, self.matrix.shape)
        )

        featureNameArray = []
        oparray = []
        for j in range(dimRow):
            oparray.append([])
            featureNameArray.append([])

        self.newScales = []

        for j in range(dimCol):
            destSigma = 1.0
            if self.scales[j] > destSigma:
                self.newScales.append(destSigma)
            else:
                self.newScales.append(self.scales[j])

            logger.debug("Replacing scale %f with new scale %f" % (self.scales[j], self.newScales[j]))

        for i, featureId in enumerate(self.inputs["FeatureIds"].value):
            if featureId == "GaussianSmoothing":
                for j in range(dimCol):
                    oparray[i].append(OpGaussianSmoothing(self))

                    oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                    oparray[i][j].inputs["sigma"].setValue(self.newScales[j])
                    featureNameArray[i].append("Gaussian Smoothing (σ=" + str(self.scales[j]) + ")")

            elif featureId == "LaplacianOfGaussian":
                for j in range(dimCol):
                    oparray[i].append(OpLaplacianOfGaussian(self))

                    oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                    oparray[i][j].inputs["scale"].setValue(self.newScales[j])
                    featureNameArray[i].append("Laplacian of Gaussian (σ=" + str(self.scales[j]) + ")")

            elif featureId == "StructureTensorEigenvalues":
                for j in range(dimCol):
                    oparray[i].append(OpStructureTensorEigenvalues(self))

                    oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                    # Note: If you need to change the inner or outer scale,
                    #  you must make a new feature (with a new feature ID) and
                    #  leave this feature here to preserve backwards compatibility
                    oparray[i][j].inputs["innerScale"].setValue(self.newScales[j])
                    # FIXME, FIXME, FIXME
                    # sigma1 = [x*0.5 for x in self.newScales[j]]
                    # oparray[i][j].inputs["outerScale"].setValue(sigma1)
                    oparray[i][j].inputs["outerScale"].setValue(self.newScales[j] * 0.5)
                    featureNameArray[i].append("Structure Tensor Eigenvalues (σ=" + str(self.scales[j]) + ")")

            elif featureId == "HessianOfGaussianEigenvalues":
                for j in range(dimCol):
                    oparray[i].append(OpHessianOfGaussianEigenvalues(self))

                    oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                    oparray[i][j].inputs["scale"].setValue(self.newScales[j])
                    featureNameArray[i].append("Hessian of Gaussian Eigenvalues (σ=" + str(self.scales[j]) + ")")

            elif featureId == "GaussianGradientMagnitude":
                for j in range(dimCol):
                    oparray[i].append(OpGaussianGradientMagnitude(self))

                    oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                    oparray[i][j].inputs["sigma"].setValue(self.newScales[j])
                    featureNameArray[i].append("Gaussian Gradient Magnitude (σ=" + str(self.scales[j]) + ")")

            elif featureId == "DifferenceOfGaussians":
                for j in range(dimCol):
                    oparray[i].append(OpDifferenceOfGaussians(self))

                    oparray[i][j].inputs["Input"].connect(self.source.outputs["Output"])
                    # Note: If you need to change sigma0 or sigma1, you must make a new
                    #  feature (with a new feature ID) and leave this feature here
                    #  to preserve backwards compatibility
                    oparray[i][j].inputs["sigma0"].setValue(self.newScales[j])
                    # FIXME, FIXME, FIXME
                    # sigma1 = [x*0.66 for x in self.newScales[j]]
                    # oparray[i][j].inputs["sigma1"].setValue(sigma1)
                    oparray[i][j].inputs["sigma1"].setValue(self.newScales[j] * 0.66)
                    featureNameArray[i].append("Difference of Gaussians (σ=" + str(self.scales[j]) + ")")

        channelCount = 0
        featureCount = 0
        self.Features.resize(0)
        self.featureOutputChannels = []
        channel_names = []
        # connect individual operators
        for i in range(dimRow):
            for j in range(dimCol):
                if self.matrix[i, j]:
                    # Feature names are provided via metadata
                    oparray[i][j].outputs["Output"].meta.description = featureNameArray[i][j]

                    # Prepare the individual features
                    featureCount += 1
                    self.Features.resize(featureCount)

                    featureMeta = oparray[i][j].outputs["Output"].meta
                    featureChannels = featureMeta.shape[featureMeta.axistags.index("c")]

                    if featureChannels == 1:
                        channel_names.append(featureNameArray[i][j])
                    else:
                        for feature_channel_index in range(featureChannels):
                            channel_names.append(featureNameArray[i][j] + " [{}]".format(feature_channel_index))

                    self.Features[featureCount - 1].meta.assignFrom(featureMeta)
                    self.Features[featureCount - 1].meta.axistags[
                        "c"
                    ].description = ""  # Discard any semantics related to the input channels
                    self.Features[
                        featureCount - 1
                    ].meta.display_mode = ""  # Discard any semantics related to the input channels
                    self.featureOutputChannels.append((channelCount, channelCount + featureChannels))
                    channelCount += featureChannels

        if self.matrix.any():
            self.maxSigma = 0
            # determine maximum sigma
            for i in range(dimRow):
                for j in range(dimCol):
                    val = self.matrix[i, j]
                    if val:
                        self.maxSigma = max(self.scales[j], self.maxSigma)

            self.featureOps = oparray

        # Output meta is a modified copy of the input meta
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.float32
        self.Output.meta.axistags["c"].description = ""  # Discard any semantics related to the input channels
        self.Output.meta.display_mode = "grayscale"
        self.Output.meta.channel_names = channel_names
        self.Output.meta.shape = self.Input.meta.shape[:-1] + (channelCount,)
        self.Output.meta.ideal_blockshape = self._get_ideal_blockshape()

        # FIXME: Features are float, so we need AT LEAST 4 bytes per output channel,
        #        but vigra functions may use internal RAM as well.
        self.Output.meta.ram_usage_per_requested_pixel = 4.0 * self.Output.meta.shape[-1]

    def _get_ideal_blockshape(self):
        tagged_blockshape = self.Output.meta.getTaggedShape()
        if "t" in tagged_blockshape:
            # There is no advantage to grouping time slices in a single request.
            tagged_blockshape["t"] = 1
        for k in "xyz":
            # There is no natural blockshape for spatial dimensions.
            if k in tagged_blockshape:
                tagged_blockshape[k] = 0
        output_blockshape = list(tagged_blockshape.values())

        ## NOTE:
        ##   Previously, we would pass along the input's ideal_blockshape
        ##   untouched for spatial dimensions, via the commented-out lines below.
        ##   But that causes major trouble for cases where the input blockshape
        ##   might be large in some dimensions, like TIFF (where the blockshape is a full slice),
        ##   or for blockwise caches with large blocks.
        ##   The cost of feature computation (and the cost of halos in the feature computation)
        ##   is much larger than file I/O overhead, so we prefer to aim for isotropic blocks instead.
        ##
        # input_blockshape = self.Input.meta.ideal_blockshape
        # if input_blockshape is None:
        #    input_blockshape = (0,) * len( self.Input.meta.shape )
        # output_blockshape = numpy.maximum( input_blockshape, output_blockshape )

        return tuple(output_blockshape)

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot == self.Input:
            channelAxis = self.Input.meta.axistags.index("c")
            numChannels = self.Input.meta.shape[channelAxis]
            dirtyChannels = roi.stop[channelAxis] - roi.start[channelAxis]

            # If all the input channels were dirty, the dirty output region is a contiguous block
            if dirtyChannels == numChannels:
                dirtyKey = list(roiToSlice(roi.start, roi.stop))
                dirtyKey[channelAxis] = slice(None)
                dirtyRoi = sliceToRoi(dirtyKey, self.Output.meta.shape)
                self.Output.setDirty(dirtyRoi[0], dirtyRoi[1])
            else:
                # Only some input channels were dirty,
                #  so we must mark each dirty output region separately.
                numFeatures = self.Output.meta.shape[channelAxis] // numChannels
                for featureIndex in range(numFeatures):
                    startChannel = numChannels * featureIndex + roi.start[channelAxis]
                    stopChannel = startChannel + roi.stop[channelAxis]
                    dirtyRoi = copy.copy(roi)
                    dirtyRoi.start[channelAxis] = startChannel
                    dirtyRoi.stop[channelAxis] = stopChannel
                    self.Output.setDirty(dirtyRoi)

        elif inputSlot == self.Matrix or inputSlot == self.Scales or inputSlot == self.FeatureIds:
            self.Output.setDirty(slice(None))
        else:
            assert False, "Unknown dirty input slot."

    def execute(self, slot, subindex, rroi, result):
        assert slot == self.Features or slot == self.Output
        if slot == self.Features:
            key = roiToSlice(rroi.start, rroi.stop)
            index = subindex[0]
            key = list(key)
            channelIndex = self.Input.meta.axistags.index("c")

            # Translate channel slice to the correct location for the output slot.
            key[channelIndex] = slice(
                self.featureOutputChannels[index][0] + key[channelIndex].start,
                self.featureOutputChannels[index][0] + key[channelIndex].stop,
            )
            rroi = SubRegion(self.Output, pslice=key)

            # Get output slot region for this channel
            return self.execute(self.Output, (), rroi, result)
        elif slot == self.outputs["Output"]:
            key = rroi.toSlice()

            logger.debug("OpPixelFeaturesPresmoothed: request %s" % (rroi.pprint(),))

            cnt = 0
            written = 0
            assert (rroi.stop <= self.outputs["Output"].meta.shape).all()
            flag = "c"
            channelAxis = self.inputs["Input"].meta.axistags.index("c")
            axisindex = channelAxis
            oldkey = list(key)
            oldkey.pop(axisindex)

            inShape = self.inputs["Input"].meta.shape
            hasChannelAxis = self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Channels) > 0
            # if (self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Channels) == 0):
            #    noChannels = True
            inAxistags = self.inputs["Input"].meta.axistags

            shape = self.outputs["Output"].meta.shape
            axistags = self.outputs["Output"].meta.axistags

            result = result.view(vigra.VigraArray)
            result.axistags = copy.copy(axistags)

            hasTimeAxis = self.inputs["Input"].meta.axistags.axisTypeCount(vigra.AxisType.Time)
            timeAxis = self.inputs["Input"].meta.axistags.index("t")

            subkey = popFlagsFromTheKey(key, axistags, "c")
            subshape = popFlagsFromTheKey(shape, axistags, "c")
            at2 = copy.copy(axistags)
            at2.dropChannelAxis()
            subshape = popFlagsFromTheKey(subshape, at2, "t")
            subkey = popFlagsFromTheKey(subkey, at2, "t")

            oldstart, oldstop = roi.sliceToRoi(key, shape)

            start, stop = roi.sliceToRoi(subkey, subshape)
            maxSigma = max(0.7, self.maxSigma)  # we use 0.7 as an approximation of not doing any smoothing
            # smoothing was already applied previously

            # The region of the smoothed image we need to give to the feature filter (in terms of INPUT coordinates)
            # 0.7, because the features receive a pre-smoothed array and don't need much of a neighborhood
            vigOpSourceStart, vigOpSourceStop = roi.enlargeRoiForHalo(start, stop, subshape, 0.7, self.WINDOW_SIZE)

            # The region of the input that we need to give to the smoothing operator (in terms of INPUT coordinates)
            newStart, newStop = roi.enlargeRoiForHalo(
                vigOpSourceStart, vigOpSourceStop, subshape, maxSigma, self.WINDOW_SIZE
            )

            newStartSmoother = roi.TinyVector(start - vigOpSourceStart)
            newStopSmoother = roi.TinyVector(stop - vigOpSourceStart)
            roiSmoother = roi.roiToSlice(newStartSmoother, newStopSmoother)

            # Translate coordinates (now in terms of smoothed image coordinates)
            vigOpSourceStart = roi.TinyVector(vigOpSourceStart - newStart)
            vigOpSourceStop = roi.TinyVector(vigOpSourceStop - newStart)

            readKey = roi.roiToSlice(newStart, newStop)

            writeNewStart = start - newStart
            writeNewStop = writeNewStart + stop - start

            treadKey = list(readKey)

            if hasTimeAxis:
                if timeAxis < channelAxis:
                    treadKey.insert(timeAxis, key[timeAxis])
                else:
                    treadKey.insert(timeAxis - 1, key[timeAxis])
            if self.inputs["Input"].meta.axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
                treadKey = popFlagsFromTheKey(treadKey, axistags, "c")
            else:
                treadKey.insert(channelAxis, slice(None, None, None))

            treadKey = tuple(treadKey)

            req = self.inputs["Input"][treadKey]

            sourceArray = req.wait()
            req.clean()
            # req.result = None
            req.destination = None
            if sourceArray.dtype != numpy.float32:
                sourceArrayF = sourceArray.astype(numpy.float32)
                try:
                    sourceArray.resize((1,), refcheck=False)
                except:
                    pass
                del sourceArray
                sourceArray = sourceArrayF

            # if (self.Input.meta.axistags.axisTypeCount(vigra.AxisType.Channels) == 0):
            # add a channel dimension to make the code afterwards more uniform
            #    sourceArray = sourceArray.view(numpy.ndarray)
            #    sourceArray = sourceArray.reshape(sourceArray.shape+(1,))
            sourceArrayV = sourceArray.view(vigra.VigraArray)
            sourceArrayV.axistags = copy.copy(inAxistags)

            dimCol = len(self.scales)
            dimRow = self.matrix.shape[0]

            sourceArraysForSigmas = [None] * dimCol

            # connect individual operators
            try:
                for j in range(dimCol):
                    hasScale = False
                    for i in range(dimRow):
                        if self.matrix[i, j]:
                            hasScale = True
                    if not hasScale:
                        continue
                    destSigma = 1.0
                    if self.scales[j] > destSigma:
                        tempSigma = math.sqrt(self.scales[j] ** 2 - destSigma ** 2)
                    else:
                        destSigma = 0.0
                        tempSigma = self.scales[j]
                    vigOpSourceShape = list(vigOpSourceStop - vigOpSourceStart)

                    if hasTimeAxis:
                        if timeAxis < channelAxis:
                            vigOpSourceShape.insert(timeAxis, (oldstop - oldstart)[timeAxis])
                        else:
                            vigOpSourceShape.insert(timeAxis - 1, (oldstop - oldstart)[timeAxis])
                        vigOpSourceShape.insert(channelAxis, inShape[channelAxis])

                        sourceArraysForSigmas[j] = numpy.ndarray(tuple(vigOpSourceShape), numpy.float32)

                        for i, vsa in enumerate(sourceArrayV.timeIter()):
                            droi = (tuple(vigOpSourceStart._asint()), tuple(vigOpSourceStop._asint()))
                            tmp_key = getAllExceptAxis(len(sourceArraysForSigmas[j].shape), timeAxis, i)
                            sourceArraysForSigmas[j][tmp_key] = self._computeGaussianSmoothing(vsa, tempSigma, droi)

                    else:
                        droi = (tuple(vigOpSourceStart._asint()), tuple(vigOpSourceStop._asint()))
                        sourceArraysForSigmas[j] = self._computeGaussianSmoothing(sourceArrayV, tempSigma, droi)

            except RuntimeError as e:
                if e.message.find("kernel longer than line") > -1:
                    message = (
                        "Feature computation error:\nYour image is too small to apply a filter with sigma=%.1f. Please select features with smaller sigmas."
                        % self.scales[j]
                    )
                    raise RuntimeError(message)
                else:
                    raise e

            del sourceArrayV
            try:
                sourceArray.resize((1,), refcheck=False)
            except ValueError:
                # Sometimes this fails, but that's okay.
                logger.debug("Failed to free array memory.")
            del sourceArray

            closures = []

            # connect individual operators
            for i in range(dimRow):
                for j in range(dimCol):
                    val = self.matrix[i, j]
                    if val:
                        vop = self.featureOps[i][j]
                        oslot = vop.outputs["Output"]
                        req = None
                        # inTagKeys = [ax.key for ax in oslot.meta.axistags]
                        # print inTagKeys, flag
                        if hasChannelAxis:
                            slices = oslot.meta.shape[axisindex]
                            if (
                                cnt + slices >= rroi.start[axisindex]
                                and rroi.start[axisindex] - cnt < slices
                                and rroi.start[axisindex] + written < rroi.stop[axisindex]
                            ):
                                begin = 0
                                if cnt < rroi.start[axisindex]:
                                    begin = rroi.start[axisindex] - cnt
                                end = slices
                                if cnt + end > rroi.stop[axisindex]:
                                    end -= cnt + end - rroi.stop[axisindex]
                                key_ = copy.copy(oldkey)
                                key_.insert(axisindex, slice(begin, end, None))
                                reskey = [slice(None, None, None) for x in range(len(result.shape))]
                                reskey[axisindex] = slice(written, written + end - begin, None)

                                destArea = result[tuple(reskey)]
                                # readjust the roi for the new source array
                                roiSmootherList = list(roiSmoother)

                                roiSmootherList.insert(axisindex, slice(begin, end, None))

                                if hasTimeAxis:
                                    # The time slice in the ROI doesn't matter:
                                    # The sourceArrayParameter below overrides the input data to be used.
                                    roiSmootherList.insert(timeAxis, 0)
                                roiSmootherRegion = SubRegion(oslot, pslice=roiSmootherList)

                                closure = partial(
                                    oslot.operator.execute,
                                    oslot,
                                    (),
                                    roiSmootherRegion,
                                    destArea,
                                    sourceArray=sourceArraysForSigmas[j],
                                )
                                closures.append(closure)

                                written += end - begin
                            cnt += slices
                        else:
                            if cnt >= rroi.start[axisindex] and rroi.start[axisindex] + written < rroi.stop[axisindex]:
                                reskey = [slice(None, None, None) for x in range(len(result.shape))]
                                slices = oslot.meta.shape[axisindex]
                                reskey[axisindex] = slice(written, written + slices, None)
                                # print "key: ", key, "reskey: ", reskey, "oldkey: ", oldkey, "resshape:", result.shape
                                # print "roiSmoother:", roiSmoother
                                destArea = result[tuple(reskey)]
                                # print "destination area:", destArea.shape
                                logger.debug(oldkey, destArea.shape, sourceArraysForSigmas[j].shape)
                                oldroi = SubRegion(oslot, pslice=oldkey)
                                # print "passing roi:", oldroi
                                closure = partial(
                                    oslot.operator.execute,
                                    oslot,
                                    (),
                                    oldroi,
                                    destArea,
                                    sourceArray=sourceArraysForSigmas[j],
                                )
                                closures.append(closure)

                                written += 1
                            cnt += 1
            pool = RequestPool()
            for c in closures:
                r = pool.request(c)
            pool.wait()
            pool.clean()

            for i in range(len(sourceArraysForSigmas)):
                if sourceArraysForSigmas[i] is not None:
                    try:
                        sourceArraysForSigmas[i].resize((1,))
                    except:
                        sourceArraysForSigmas[i] = None

    def _computeGaussianSmoothing(self, vol, sigma, roi):
        if WITH_FAST_FILTERS:
            # Use fast filters (if available)
            if vol.channels > 1:
                result = numpy.zeros(vol.shape).astype(vol.dtype)
                chInd = vol.channelIndex
                chSlice = [slice(None) for dim in range(len(vol.shape))]

                for channel in range(vol.channels):
                    chSlice[chInd] = slice(channel, channel + 1)
                    result[chSlice] = fastfilters.gaussianSmoothing(vol[chSlice], sigma, window_size=self.WINDOW_SIZE)
            else:
                result = fastfilters.gaussianSmoothing(vol, sigma, window_size=self.WINDOW_SIZE)

            roi = roiToSlice(*roi)
            return result[roi]
        else:
            # Use Vigra's filters
            return vigra.filters.gaussianSmoothing(vol, sigma, roi=roi, window_size=self.WINDOW_SIZE)


def getAllExceptAxis(ndim, index, slicer):
    res = [slice(None, None, None)] * ndim
    res[index] = slicer
    return tuple(res)


class OpBaseFilter(Operator):
    Input = InputSlot()
    Output = OutputSlot()

    # Subclasses have some subset of these slots:
    #
    # sigma = InputSlot()
    # sigma0 = InputSlot()
    # sigma1 = InputSlot()
    # scale = InputSlot()
    # innerScale = InputSlot()
    # outerScale = InputSlot()

    name = "OpBaseFilter"
    category = "Vigra filter"

    vigraFilter = None
    outputDtype = numpy.float32
    inputDtype = numpy.float32
    supportsOut = True
    window_size_feature = 2
    window_size_smoother = 3.5
    supportsRoi = False
    supportsWindow = False

    def execute(self, slot, subindex, rroi, result, sourceArray=None):
        assert len(subindex) == self.Output.level == 0
        key = roiToSlice(rroi.start, rroi.stop)

        kwparams = {}
        for islot in list(self.inputs.values()):
            if islot.name != "Input":
                kwparams[islot.name] = islot.value

        if "sigma" in self.inputs:
            sigma = self.inputs["sigma"].value
        elif "scale" in self.inputs:
            sigma = self.inputs["scale"].value
        elif "sigma0" in self.inputs:
            sigma = self.inputs["sigma0"].value
        elif "innerScale" in self.inputs:
            sigma = self.inputs["innerScale"].value

        windowSize = 3.5
        if self.supportsWindow:
            kwparams["window_size"] = self.window_size_feature
            windowSize = self.window_size_smoother

        largestSigma = max(0.7, sigma)  # we use 0.7 as an approximation of not doing any smoothing
        # smoothing was already applied previously

        shape = self.outputs["Output"].meta.shape

        axistags = self.inputs["Input"].meta.axistags
        hasChannelAxis = self.inputs["Input"].meta.axistags.axisTypeCount(vigra.AxisType.Channels)
        channelAxis = self.inputs["Input"].meta.axistags.index("c")
        hasTimeAxis = self.inputs["Input"].meta.axistags.axisTypeCount(vigra.AxisType.Time)
        timeAxis = self.inputs["Input"].meta.axistags.index("t")
        zAxis = self.inputs["Input"].meta.axistags.index("z")

        subkey = popFlagsFromTheKey(key, axistags, "c")
        subshape = popFlagsFromTheKey(shape, axistags, "c")
        at2 = copy.copy(axistags)
        at2.dropChannelAxis()
        subshape = popFlagsFromTheKey(subshape, at2, "t")
        subkey = popFlagsFromTheKey(subkey, at2, "t")

        oldstart, oldstop = roi.sliceToRoi(key, shape)

        start, stop = roi.sliceToRoi(subkey, subshape)

        if sourceArray is not None and zAxis < len(axistags):
            if timeAxis > zAxis:
                subshape[at2.index("z")] = sourceArray.shape[zAxis]
            else:
                subshape[at2.index("z") - 1] = sourceArray.shape[zAxis]

        newStart, newStop = roi.enlargeRoiForHalo(start, stop, subshape, largestSigma, window=windowSize)
        readKey = roi.roiToSlice(newStart, newStop)

        writeNewStart = start - newStart
        writeNewStop = writeNewStart + stop - start

        if (writeNewStart == 0).all() and (newStop == writeNewStop).all():
            fullResult = True
        else:
            fullResult = False

        writeKey = roi.roiToSlice(writeNewStart, writeNewStop)
        writeKey = list(writeKey)
        if timeAxis < channelAxis:
            writeKey.insert(channelAxis - 1, slice(None, None, None))
        else:
            writeKey.insert(channelAxis, slice(None, None, None))
        writeKey = tuple(writeKey)

        # print writeKey

        channelsPerChannel = self.resultingChannels()

        if self.supportsRoi is False and largestSigma > 5:
            logger.warning(f"WARNING: operator {self.name} does not support roi!!")

        i2 = 0
        for i in range(
            int(numpy.floor(1.0 * oldstart[channelAxis] / channelsPerChannel)),
            int(numpy.ceil(1.0 * oldstop[channelAxis] / channelsPerChannel)),
        ):
            newReadKey = list(readKey)  # add channel and time axis if needed
            if hasTimeAxis:
                if channelAxis > timeAxis:
                    newReadKey.insert(timeAxis, key[timeAxis])
                else:
                    newReadKey.insert(timeAxis - 1, key[timeAxis])
            if hasChannelAxis:
                newReadKey.insert(channelAxis, slice(i, i + 1, None))

            if sourceArray is None:
                req = self.inputs["Input"][newReadKey]
                t = req.wait()
            else:
                if hasChannelAxis:
                    t = sourceArray[getAllExceptAxis(len(newReadKey), channelAxis, slice(i, i + 1, None))]
                else:
                    fullkey = [slice(None, None, None)] * len(newReadKey)
                    t = sourceArray[fullkey]

            t = numpy.require(t, dtype=self.inputDtype)
            t = t.view(vigra.VigraArray)
            t.axistags = copy.copy(axistags)
            t = t.insertChannelAxis()

            sourceBegin = 0

            if oldstart[channelAxis] > i * channelsPerChannel:
                sourceBegin = oldstart[channelAxis] - i * channelsPerChannel
            sourceEnd = channelsPerChannel
            if oldstop[channelAxis] < (i + 1) * channelsPerChannel:
                sourceEnd = channelsPerChannel - ((i + 1) * channelsPerChannel - oldstop[channelAxis])
            destBegin = i2
            destEnd = i2 + sourceEnd - sourceBegin

            if channelsPerChannel > 1:
                tkey = getAllExceptAxis(len(shape), channelAxis, slice(destBegin, destEnd, None))
                resultArea = result[tkey]
            else:
                tkey = getAllExceptAxis(len(shape), channelAxis, slice(i2, i2 + 1, None))
                resultArea = result[tkey]

            i2 += destEnd - destBegin

            supportsOut = self.supportsOut
            if destEnd - destBegin != channelsPerChannel:
                supportsOut = False

            supportsOut = False  # disable for now due to vigra crashes! #FIXME
            for step, image in enumerate(t.timeIter()):
                nChannelAxis = channelAxis - 1

                if timeAxis > channelAxis or not hasTimeAxis:
                    nChannelAxis = channelAxis
                twriteKey = getAllExceptAxis(image.ndim, nChannelAxis, slice(sourceBegin, sourceEnd, None))

                if hasTimeAxis > 0:
                    tresKey = getAllExceptAxis(resultArea.ndim, timeAxis, step)
                else:
                    tresKey = slice(None, None, None)

                # print tresKey, twriteKey, resultArea.shape, temp.shape
                vres = resultArea[tresKey]

                if supportsOut:
                    if self.supportsRoi:
                        vroi = (tuple(writeNewStart._asint()), tuple(writeNewStop._asint()))
                        try:
                            vres = vres.view(vigra.VigraArray)
                            vres.axistags = copy.copy(image.axistags)
                            logger.debug(
                                "FAST LANE {} {} {} {}".format(self.name, vres.shape, image[twriteKey].shape, vroi)
                            )
                            temp = self.vigraFilter(image[twriteKey], roi=vroi, out=vres, **kwparams)
                        except:
                            logger.error("{} {} {} {}".format(self.name, image.shape, vroi, kwparams))
                            raise
                    else:
                        try:
                            temp = self.vigraFilter(image, **kwparams)
                        except:
                            logger.error("{} {} {} {}".format(self.name, image.shape, vroi, kwparams))
                            raise
                        temp = temp[writeKey]
                else:
                    if self.supportsRoi:
                        vroi = (tuple(writeNewStart._asint()), tuple(writeNewStop._asint()))
                        try:
                            temp = self.vigraFilter(image, roi=vroi, **kwparams)
                        except Exception as e:
                            logger.error("EXCEPT 2.1 {} {} {} {}".format(self.name, image.shape, vroi, kwparams))
                            traceback.print_exc(e)
                            import sys

                            sys.exit(1)
                    else:
                        try:
                            temp = self.vigraFilter(image, **kwparams)
                        except Exception as e:
                            logger.error("EXCEPT 2.2 {} {} {}".format(self.name, image.shape, kwparams))
                            traceback.print_exc(e)
                            import sys

                            sys.exit(1)
                        temp = temp[writeKey]

                    try:
                        vres[:] = temp[twriteKey]
                    except:
                        logger.error("EXCEPT3 {} {} {}".format(vres.shape, temp.shape, twriteKey))
                        logger.error("EXCEPT3 {} {} {}".format(resultArea.shape, tresKey, twriteKey))
                        logger.error("EXCEPT3 {} {} {}".format(step, t.shape, timeAxis))
                        raise

                # print "(in.min=",image.min(),",in.max=",image.max(),") (vres.min=",vres.min(),",vres.max=",vres.max(),")"

    def setupOutputs(self):

        # Output meta starts with a copy of the input meta, which is then modified
        self.Output.meta.assignFrom(self.Input.meta)

        numChannels = 1
        inputSlot = self.inputs["Input"]
        if inputSlot.meta.axistags.axisTypeCount(vigra.AxisType.Channels) > 0:
            channelIndex = self.inputs["Input"].meta.axistags.channelIndex
            numChannels = self.inputs["Input"].meta.shape[channelIndex]
            inShapeWithoutChannels = popFlagsFromTheKey(
                self.inputs["Input"].meta.shape, self.inputs["Input"].meta.axistags, "c"
            )
        else:
            inShapeWithoutChannels = inputSlot.meta.shape
            channelIndex = len(inputSlot.meta.shape)

        self.outputs["Output"].meta.dtype = self.outputDtype
        p = self.inputs["Input"].upstream_slot
        at = copy.copy(inputSlot.meta.axistags)

        if at.axisTypeCount(vigra.AxisType.Channels) == 0:
            at.insertChannelAxis()

        self.outputs["Output"].meta.axistags = at

        channelsPerChannel = self.resultingChannels()
        inShapeWithoutChannels = list(inShapeWithoutChannels)
        inShapeWithoutChannels.insert(channelIndex, numChannels * channelsPerChannel)
        self.outputs["Output"].meta.shape = tuple(inShapeWithoutChannels)

        if self.outputs["Output"].meta.axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
            self.outputs["Output"].meta.axistags.insertChannelAxis()

        # The output data range is not necessarily the same as the input data range.
        if "drange" in self.Output.meta:
            del self.Output.meta["drange"]

    def resultingChannels(self):
        raise RuntimeError("resultingChannels() not implemented")

    ##
    ## FIXME: This propagateDirty() function doesn't properly
    ##        expand the halo according to the sigma and window!
    ##
    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        # Check for proper name because subclasses may define extra inputs.
        # (but decline to override notifyDirty)
        if slot is self.Input:
            self.Output.setDirty(key)
        else:
            # If some input we don't know about is dirty (i.e. we are subclassed by an operator with extra inputs),
            # then mark the entire output dirty.  This is the correct behavior for e.g. 'sigma' inputs.
            self.Output.setDirty(slice(None))

    def setInSlot(self, slot, subindex, roi, value):
        # Forward to output
        assert subindex == ()
        assert slot == self.Input
        key = roi.toSlice()
        self.Output[key] = value


# difference of Gaussians
def differenceOfGausssians(image, sigma0, sigma1, window_size, roi, out=None):
    """ difference of gaussian function"""
    return vigra.filters.gaussianSmoothing(
        image, sigma0, window_size=window_size, roi=roi
    ) - vigra.filters.gaussianSmoothing(image, sigma1, window_size=window_size, roi=roi)


def firstHessianOfGaussianEigenvalues(image, **kwargs):
    return vigra.filters.hessianOfGaussianEigenvalues(image, **kwargs)[..., 0:1]


def coherenceOrientationOfStructureTensor(image, sigma0, sigma1, window_size, out=None):
    """
    coherence Orientation of Structure tensor function:
    input:  M*N*1ch VigraArray
            sigma corresponding to the inner scale of the tensor
            scale corresponding to the outher scale of the tensor

    output: M*N*2 VigraArray, the firest channel correspond to coherence
                              the second channel correspond to orientation
    """

    # FIXME: make more general

    # assert image.spatialDimensions==2, "Only implemented for 2 dimensional images"
    assert len(image.shape) == 2 or (
        len(image.shape) == 3 and image.shape[2] == 1
    ), "Only implemented for 2 dimensional images"

    st = vigra.filters.structureTensor(image, sigma0, sigma1, window_size=window_size)
    i11 = st[:, :, 0]
    i12 = st[:, :, 1]
    i22 = st[:, :, 2]

    if out is not None:
        assert out.shape[0] == image.shape[0] and out.shape[1] == image.shape[1] and out.shape[2] == 2
        res = out
    else:
        res = numpy.ndarray((image.shape[0], image.shape[1], 2))

    res[:, :, 0] = numpy.sqrt((i22 - i11) ** 2 + 4 * (i12 ** 2)) / (i11 - i22)
    res[:, :, 1] = (numpy.arctan(2 * i12 / (i22 - i11)) / numpy.pi) + 0.5

    return res


class OpDifferenceOfGaussians(OpBaseFilter):
    outputDtype = numpy.float32
    supportsOut = False
    supportsWindow = True

    def resultingChannels(self):
        return 1

    sigma0 = InputSlot()
    sigma1 = InputSlot()

    if WITH_FAST_FILTERS:
        name = "DifferenceOfGaussiansFF"
        supportsRoi = False

        def differenceOfGausssiansFF(image, sigma0, sigma1, window_size):
            return fastfilters.gaussianSmoothing(image, sigma0, window_size) - fastfilters.gaussianSmoothing(
                image, sigma1, window_size
            )

        vigraFilter = staticmethod(differenceOfGausssiansFF)
    else:
        name = "DifferenceOfGaussians"
        supportsRoi = True

        vigraFilter = staticmethod(differenceOfGausssians)


class OpGaussianSmoothing(OpBaseFilter):
    outputDtype = numpy.float32
    supportsWindow = True

    def resultingChannels(self):
        return 1

    sigma = InputSlot()

    if WITH_FAST_FILTERS:
        name = "GaussianSmoothingFF"
        supportsRoi = False
        supportsOut = False

        vigraFilter = staticmethod(fastfilters.gaussianSmoothing)
    else:
        name = "GaussianSmoothing"
        supportsRoi = True
        supportsOut = True

        vigraFilter = staticmethod(vigra.filters.gaussianSmoothing)


class OpHessianOfGaussianEigenvalues(OpBaseFilter):
    outputDtype = numpy.float32
    supportsWindow = True

    def resultingChannels(self):
        temp = self.inputs["Input"].meta.axistags.axisTypeCount(vigra.AxisType.Space)
        return temp

    scale = InputSlot()

    if WITH_FAST_FILTERS:
        name = "HessianOfGaussianEigenvaluesFF"
        supportsRoi = False
        supportsOut = False

        vigraFilter = staticmethod(fastfilters.hessianOfGaussianEigenvalues)
    else:
        name = "HessianOfGaussianEigenvalues"
        supportsRoi = True
        supportsOut = True

        vigraFilter = staticmethod(vigra.filters.hessianOfGaussianEigenvalues)


class OpStructureTensorEigenvalues(OpBaseFilter):
    outputDtype = numpy.float32
    supportsWindow = True

    def resultingChannels(self):
        temp = self.inputs["Input"].meta.axistags.axisTypeCount(vigra.AxisType.Space)
        return temp

    innerScale = InputSlot()
    outerScale = InputSlot()

    if WITH_FAST_FILTERS:
        name = "StructureTensorEigenvaluesFF"
        supportsRoi = False
        supportsOut = False

        vigraFilter = staticmethod(fastfilters.structureTensorEigenvalues)
    else:
        name = "StructureTensorEigenvalues"
        supportsRoi = True
        supportsOut = True

        vigraFilter = staticmethod(vigra.filters.structureTensorEigenvalues)


class OpHessianOfGaussianEigenvaluesFirst(OpBaseFilter):
    name = "First Eigenvalue of Hessian Matrix"
    vigraFilter = staticmethod(firstHessianOfGaussianEigenvalues)
    outputDtype = numpy.float32
    supportsOut = False
    supportsWindow = True
    supportsRoi = True

    scale = InputSlot()

    def resultingChannels(self):
        return 1


class OpHessianOfGaussian(OpBaseFilter):
    name = "HessianOfGaussian"
    vigraFilter = staticmethod(vigra.filters.hessianOfGaussian)
    outputDtype = numpy.float32
    supportsWindow = True
    supportsRoi = True
    supportsOut = True

    sigma = InputSlot()

    def resultingChannels(self):
        temp = (
            self.inputs["Input"].meta.axistags.axisTypeCount(vigra.AxisType.Space)
            * (self.inputs["Input"].meta.axistags.axisTypeCount(vigra.AxisType.Space) + 1)
            // 2
        )
        return temp


class OpGaussianGradientMagnitude(OpBaseFilter):
    outputDtype = numpy.float32
    supportsWindow = True

    def resultingChannels(self):
        return 1

    sigma = InputSlot()

    if WITH_FAST_FILTERS:
        name = "GaussianGradientMagnitudeFF"
        supportsRoi = False
        supportsOut = False

        vigraFilter = staticmethod(fastfilters.gaussianGradientMagnitude)
    else:
        name = "GaussianGradientMagnitude"
        supportsRoi = True
        supportsOut = True

        vigraFilter = staticmethod(vigra.filters.gaussianGradientMagnitude)


class OpLaplacianOfGaussian(OpBaseFilter):
    outputDtype = numpy.float32
    supportsWindow = True

    def resultingChannels(self):
        return 1

    scale = InputSlot()

    if WITH_FAST_FILTERS:
        name = "LaplacianOfGaussianFF"
        supportsOut = False
        supportsRoi = False

        vigraFilter = staticmethod(fastfilters.laplacianOfGaussian)
    else:
        name = "LaplacianOfGaussian"
        supportsOut = True
        supportsRoi = True

        vigraFilter = staticmethod(vigra.filters.laplacianOfGaussian)


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
#          http://ilastik.org/license.html
###############################################################################
import h5py

# lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpSlicedBlockedArrayCache, OpMultiArraySlicer2
from lazyflow.operators import OpReorderAxes, OperatorWrapper

from ilastik.applets.base.applet import DatasetConstraintError


# Constants
ScalesList = [0.3, 0.7, 1.0, 1.6, 3.5, 5.0, 10.0]

# Map feature groups to lists of feature IDs
FeatureGroups = [
    ("Color/Intensity", ["GaussianSmoothing"]),
    ("Edge", ["LaplacianOfGaussian", "GaussianGradientMagnitude", "DifferenceOfGaussians"]),
    ("Texture", ["StructureTensorEigenvalues", "HessianOfGaussianEigenvalues"]),
]

# Map feature IDs to feature names
FeatureNames = {
    "GaussianSmoothing": "Gaussian Smoothing",
    "LaplacianOfGaussian": "Laplacian of Gaussian",
    "GaussianGradientMagnitude": "Gaussian Gradient Magnitude",
    "DifferenceOfGaussians": "Difference of Gaussians",
    "StructureTensorEigenvalues": "Structure Tensor Eigenvalues",
    "HessianOfGaussianEigenvalues": "Hessian of Gaussian Eigenvalues",
}


def getFeatureIdOrder():
    featureIrdOrder = []
    for group, featureIds in FeatureGroups:
        featureIrdOrder += featureIds
    return featureIrdOrder


class OpFeatureSelectionNoCache(Operator):
    """
    The top-level operator for the feature selection applet for headless workflows.
    """

    name = "OpFeatureSelection"
    category = "Top-level"

    ScalesList = ScalesList
    FeatureGroups = FeatureGroups
    FeatureNames = FeatureNames

    MinimalFeatures = numpy.zeros((len(FeatureNames), len(ScalesList)), dtype=bool)
    MinimalFeatures[0, 0] = True

    # Multiple input images
    InputImage = InputSlot()

    # The following input slots are applied uniformly to all input images
    Scales = InputSlot(value=ScalesList)  # The list of possible scales to use when computing features
    FeatureIds = InputSlot(value=getFeatureIdOrder())  # The list of features to compute
    SelectionMatrix = InputSlot(value=MinimalFeatures)  # A matrix of bools indicating which features to output.
    # The matrix rows correspond to feature types in the order specified by the FeatureIds input.
    #  (See OpPixelFeaturesPresmoothed for the available feature types.)
    # The matrix columns correspond to the scales provided in the Scales input,
    #  which requires that the number of matrix columns must match len(Scales.value)

    FeatureListFilename = InputSlot(stype="str", optional=True)

    # Features are presented in the channels of the output image
    # Output can be optionally accessed via an internal cache.
    # (Training a classifier benefits from caching, but predicting with an existing classifier does not.)
    OutputImage = OutputSlot()

    FeatureLayers = OutputSlot(
        level=1
    )  # For the GUI, we also provide each feature as a separate slot in this multislot

    def __init__(self, *args, **kwargs):
        super(OpFeatureSelectionNoCache, self).__init__(*args, **kwargs)

        # Create the operator that actually generates the features
        self.opPixelFeatures = OpPixelFeaturesPresmoothed(parent=self)

        # Connect our internal operators to our external inputs
        self.opPixelFeatures.Scales.connect(self.Scales)
        self.opPixelFeatures.FeatureIds.connect(self.FeatureIds)
        self.opReorderIn = OpReorderAxes(parent=self)
        self.opReorderIn.Input.connect(self.InputImage)
        self.opPixelFeatures.Input.connect(self.opReorderIn.Output)
        self.opReorderOut = OpReorderAxes(parent=self)
        self.opReorderOut.Input.connect(self.opPixelFeatures.Output)
        self.opReorderLayers = OperatorWrapper(OpReorderAxes, parent=self, broadcastingSlotNames=["AxisOrder"])
        self.opReorderLayers.Input.connect(self.opPixelFeatures.Features)

        # We don't connect SelectionMatrix here because we want to
        #  check it for errors (See setupOutputs)
        # self.opPixelFeatures.SelectionMatrix.connect( self.SelectionMatrix )

        self.WINDOW_SIZE = self.opPixelFeatures.WINDOW_SIZE

    def setupOutputs(self):
        # drop non-channel singleton axes
        allAxes = "txyzc"
        ts = self.InputImage.meta.getTaggedShape()
        oldAxes = "".join(list(ts.keys()))
        newAxes = "".join([a for a in allAxes if a in ts and ts[a] > 1 or a == "c"])
        self.opReorderIn.AxisOrder.setValue(newAxes)
        self.opReorderOut.AxisOrder.setValue(oldAxes)
        self.opReorderLayers.AxisOrder.setValue(oldAxes)

        # Get features from external file
        if self.FeatureListFilename.ready() and len(self.FeatureListFilename.value) > 0:

            self.OutputImage.disconnect()
            self.FeatureLayers.disconnect()

            axistags = self.InputImage.meta.axistags

            with h5py.File(self.FeatureListFilename.value, "r") as f:
                dset_names = []
                f.visit(dset_names.append)
                if len(dset_names) != 1:
                    sys.stderr.write("Input external features HDF5 file should have exactly 1 dataset.\n")
                    sys.exit(1)

                dset = f[dset_names[0]]
                chnum = dset.shape[-1]
                shape = dset.shape
                dtype = dset.dtype.type

            # Set the metadata for FeatureLayers. Unlike OutputImage and CachedOutputImage,
            # FeatureLayers has one slot per channel and therefore the channel dimension must be 1.
            self.FeatureLayers.resize(chnum)
            for i in range(chnum):
                self.FeatureLayers[i].meta.shape = shape[:-1] + (1,)
                self.FeatureLayers[i].meta.dtype = dtype
                self.FeatureLayers[i].meta.axistags = axistags
                self.FeatureLayers[i].meta.display_mode = "default"
                self.FeatureLayers[i].meta.description = "feature_channel_" + str(i)

            self.OutputImage.meta.shape = shape
            self.OutputImage.meta.dtype = dtype
            self.OutputImage.meta.axistags = axistags

        else:
            # Set the new selection matrix and check if it creates an error.
            selections = self.SelectionMatrix.value
            self.opPixelFeatures.Matrix.setValue(selections)
            invalid_scales = self.opPixelFeatures.getInvalidScales()
            if invalid_scales:
                msg = (
                    "Some of your selected feature scales are too large for your dataset.\n"
                    "Choose smaller scales (sigma) or use a larger dataset.\n"
                    "The invalid scales are: {}".format(invalid_scales)
                )
                raise DatasetConstraintError("Feature Selection", msg)

            # Connect our external outputs to our internal operators
            self.OutputImage.connect(self.opReorderOut.Output)
            self.FeatureLayers.connect(self.opReorderLayers.Output)

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass

    def execute(self, slot, subindex, rroi, result):
        if len(self.FeatureListFilename.value) == 0:
            return

        # Set the channel corresponding to the slot(subindex) of the feature layers
        if slot == self.FeatureLayers:
            rroi.start[-1] = subindex[0]
            rroi.stop[-1] = subindex[0] + 1

        key = roiToSlice(rroi.start, rroi.stop)

        # Read features from external file
        with h5py.File(self.FeatureListFilename.value, "r") as f:
            dset_names = []
            f.visit(dset_names.append)

            if len(dset_names) != 1:
                sys.stderr.write("Input external features HDF5 file should have exactly 1 dataset.")
                return

            dset = f[dset_names[0]]
            result[...] = dset[key]

        return result


class OpFeatureSelection(OpFeatureSelectionNoCache):
    """
    This is the top-level operator of the feature selection applet when used in a GUI.
    It provides an extra output for cached data.
    """

    BypassCache = InputSlot(value=False)
    CachedOutputImage = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpFeatureSelection, self).__init__(*args, **kwargs)

        # Create the cache
        self.opPixelFeatureCache = OpSlicedBlockedArrayCache(parent=self)
        self.opPixelFeatureCache.name = "opPixelFeatureCache"
        self.opPixelFeatureCache.BypassModeEnabled.connect(self.BypassCache)

        # Connect the cache to the feature output
        self.opPixelFeatureCache.Input.connect(self.OutputImage)
        self.opPixelFeatureCache.fixAtCurrent.setValue(False)

    def change_feature_cache_size(self):
        curr_size = self.opPixelFeatureCache.BlockShape.value
        a = [list(i) for i in curr_size]
        a[2][3] = 1
        c = [tuple(i) for i in a]
        c = tuple(c)
        self.opPixelFeatureCache.BlockShape.setValue(c)

    def setupOutputs(self):
        super(OpFeatureSelection, self).setupOutputs()

        if self.FeatureListFilename.ready() and len(self.FeatureListFilename.value) > 0:
            self.CachedOutputImage.disconnect()
            self.CachedOutputImage.meta.assignFrom(self.OutputImage.meta)

        else:
            # We choose block shapes that have only 1 channel because the channels may be
            #  coming from different features (e.g different filters) and probably shouldn't be cached together.
            blockDimsX = {
                "t": (1, 1),
                "z": (256, 256),
                "y": (256, 256),
                "x": (32, 32),
                "c": (1000, 1000),
            }  # Overestimate number of feature channels:
            # Cache block dimensions will be clipped to the size of the actual feature image

            blockDimsY = {"t": (1, 1), "z": (256, 256), "y": (32, 32), "x": (256, 256), "c": (1000, 1000)}

            blockDimsZ = {"t": (1, 1), "z": (32, 32), "y": (256, 256), "x": (256, 256), "c": (1000, 1000)}

            axisOrder = [tag.key for tag in self.InputImage.meta.axistags]
            blockShapeX = tuple(blockDimsX[k][1] for k in axisOrder)
            blockShapeY = tuple(blockDimsY[k][1] for k in axisOrder)
            blockShapeZ = tuple(blockDimsZ[k][1] for k in axisOrder)

            # Configure the cache
            self.opPixelFeatureCache.BlockShape.setValue((blockShapeX, blockShapeY, blockShapeZ))

            # Connect external output to internal output
            self.CachedOutputImage.connect(self.opPixelFeatureCache.Output)
