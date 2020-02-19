###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2018, the ilastik developers
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
import copy
import logging
import math
import numpy
import vigra

from functools import partial

from lazyflow import roi
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.request import RequestPool
from lazyflow.roi import sliceToRoi, roiToSlice
from lazyflow.rtype import SubRegion

from .operators import OpArrayPiper
from .filterOperators import (
    OpGaussianSmoothing,
    OpDifferenceOfGaussians,
    OpHessianOfGaussianEigenvalues,
    OpStructureTensorEigenvalues,
    OpGaussianGradientMagnitude,
    OpLaplacianOfGaussian,
    WITH_FAST_FILTERS,
)

if WITH_FAST_FILTERS:
    import fastfilters

logger = logging.getLogger(__name__)


class OpPixelFeaturesPresmoothed(Operator):
    name = "OpPixelFeaturesPresmoothed"
    category = "Vigra filter"

    Input = InputSlot()
    Scales = InputSlot()
    SelectionMatrix = InputSlot()
    ComputeIn2d = InputSlot()

    # Specify a default set & order for the features we compute
    FeatureIds = InputSlot(
        value=[
            "GaussianSmoothing",
            "LaplacianOfGaussian",
            "GaussianGradientMagnitude",
            "DifferenceOfGaussians",
            "StructureTensorEigenvalues",
            "HessianOfGaussianEigenvalues",
        ]
    )

    Output = OutputSlot()  # The entire block of features as a single image (many channels)
    Features = OutputSlot(level=1)  # Each feature image listed separately, with feature name provided in metadata

    WINDOW_SIZE = 3.5

    def __init__(self, *args, **kwargs):
        Operator.__init__(self, *args, **kwargs)
        self.source = OpArrayPiper(parent=self)
        self.source.Input.connect(self.Input)

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
        invalid_z_scales = []
        if self.Input.ready():
            z, y, x = self.Input.meta.shape[2:]
            for j, scale in enumerate(self.Scales.value):
                minimum_len = numpy.ceil(scale * self.WINDOW_SIZE) + 1
                if self.SelectionMatrix.value[:, j].any():
                    if minimum_len > x or minimum_len > y:
                        invalid_scales.append(scale)
                    if minimum_len > z and not self.ComputeIn2d.value[j]:
                        invalid_z_scales.append(scale)

        return invalid_scales, invalid_z_scales

    def setupOutputs(self):
        if not self.ComputeIn2d.value:
            if self.Input.meta.shape[2] == 1:
                self.parent.ComputeIn2d.setValue([True] * len(self.Scales.value))
            else:
                self.parent.ComputeIn2d.setValue([False] * len(self.Scales.value))

        assert self.Input.meta.getAxisKeys() == list("tczyx"), self.Input.meta.getAxisKeys()
        assert isinstance(self.ComputeIn2d.value, list), type(self.ComputeIn2d.value)
        self.scales = self.Scales.value
        self.matrix = self.SelectionMatrix.value

        assert isinstance(self.matrix, numpy.ndarray)

        dimCol = len(self.scales)
        dimRow = len(self.FeatureIds.value)

        assert (
            dimRow == self.matrix.shape[0]
        ), f"Number of features ({dimRow}) is incompatible with feature matrix ({self.matrix.shape})"
        assert (
            dimCol == self.matrix.shape[1]
        ), f"Number of scales ({dimCol}) is incompatible with feature matrix ({self.matrix.shape})"

        featureNameArray = []
        oparray = []
        for j in range(dimRow):
            oparray.append([])
            featureNameArray.append([])

        self.newScales = []

        for j in range(dimCol):
            if self.scales[j] > 1.0:
                self.newScales.append(1.0)
                logger.debug(f"Replacing scale {self.scales[j]} with new scale {self.newScales[j]}")
            else:
                self.newScales.append(self.scales[j])

        channelCount = 0
        featureCount = 0
        self.Features.resize(0)
        self.featureOutputChannels = []
        channel_names = []
        # create and connect individual operators
        for i, featureId in enumerate(self.FeatureIds.value):
            for j in range(dimCol):
                if self.matrix[i, j]:
                    if featureId == "GaussianSmoothing":
                        op = OpGaussianSmoothing(self, sigma=self.newScales[j])
                        featureName = f"Gaussian Smoothing (σ={self.scales[j]})"
                    elif featureId == "LaplacianOfGaussian":
                        op = OpLaplacianOfGaussian(self, scale=self.newScales[j])
                        featureName = f"Laplacian of Gaussian (σ={self.scales[j]})"
                    elif featureId == "StructureTensorEigenvalues":
                        op = OpStructureTensorEigenvalues(
                            self, innerScale=self.newScales[j], outerScale=self.newScales[j] * 0.5
                        )
                        # Note: If you need to change the inner or outer scale,
                        #       you must make a new feature (with a new feature ID) and
                        #       leave this feature here to preserve backwards compatibility
                        featureName = f"Structure Tensor Eigenvalues (σ={self.scales[j]})"
                    elif featureId == "HessianOfGaussianEigenvalues":
                        op = OpHessianOfGaussianEigenvalues(self, scale=self.newScales[j])
                        featureName = f"Hessian of Gaussian Eigenvalues (σ={self.scales[j]})"
                    elif featureId == "GaussianGradientMagnitude":
                        op = OpGaussianGradientMagnitude(self, sigma=self.newScales[j])
                        featureName = f"Gaussian Gradient Magnitude (σ={self.scales[j]})"
                    elif featureId == "DifferenceOfGaussians":
                        op = OpDifferenceOfGaussians(self, sigma0=self.newScales[j], sigma1=self.newScales[j] * 0.66)
                        # Note: If you need to change sigma0 or sigma1, you must make a new
                        #       feature (with a new feature ID) and leave this feature here
                        #       to preserve backwards compatibility
                        featureName = f"Difference of Gaussians (σ={self.scales[j]})"

                    if self.ComputeIn2d.value[j]:
                        featureName += " in 2D"

                    # note: set ComputeIn2d first, to avoid a second call of setupOutputs, due to ComptueIn2d's default
                    op.ComputeIn2d.setValue(self.ComputeIn2d.value[j])
                    op.Input.connect(self.source.Output)

                    # Feature names are provided via metadata
                    op.Output.meta.description = featureName

                    # Prepare the individual features
                    self.Features.resize(featureCount + 1)

                    featureMeta = op.Output.meta
                    featureChannels = op.Output.meta.shape[1]
                    assert featureChannels == featureMeta.shape[1]
                    assert featureMeta.axistags.index("c") == 1

                    if featureChannels == 1:
                        channel_names.append(featureName)
                    else:
                        for feature_channel_index in range(featureChannels):
                            channel_names.append(featureName + f" [{feature_channel_index}]")

                    self.Features[featureCount].meta.assignFrom(featureMeta)
                    # Discard any semantics related to the input channels
                    self.Features[featureCount].meta.axistags["c"].description = ""
                    # Discard any semantics related to the input channels
                    self.Features[featureCount].meta.display_mode = ""
                    self.featureOutputChannels.append((channelCount, channelCount + featureChannels))
                    channelCount += featureChannels
                    featureCount += 1

                    oparray[i].append(op)
                    featureNameArray[i].append(featureName)
                else:
                    oparray[i].append(None)
                    featureNameArray[i].append(None)

        # We use 0.7 as an approximation of not doing any smoothing.
        if self.matrix.any():
            self.max_sigma = max(0.7, max(numpy.asarray(self.scales)[self.matrix.any(axis=0)]))
        else:
            self.max_sigma = 0.7

        self.featureOps = oparray

        # Output meta is a modified copy of the input meta
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.float32
        self.Output.meta.axistags["c"].description = ""  # Discard any semantics related to the input channels
        self.Output.meta.display_mode = "grayscale"
        self.Output.meta.channel_names = channel_names
        self.Output.meta.shape = self.Input.meta.shape[:1] + (channelCount,) + self.Input.meta.shape[2:]
        self.Output.meta.ideal_blockshape = self._get_ideal_blockshape()

        # FIXME: Features are float, so we need AT LEAST 4 bytes per output channel,
        #        but vigra functions may use internal RAM as well.
        self.Output.meta.ram_usage_per_requested_pixel = 4.0 * self.Output.meta.shape[1]

    def _get_ideal_blockshape(self):
        assert self.Output.meta.getAxisKeys() == list("tczyx")

        # There is no advantage to grouping time in a single request.
        t = 1

        # Input channels are independent. Output channels partially. It is not trivial to distinguish which output
        # channels come from a single input channel and which do not, therefore we ask for all/arbitrary many.
        # The way the pre-smoothing is implemented currently (saved only temporarily per request), it is best to
        # request all channels at once to only pre-smooth once for all input channels and filters.
        c = self.Output.meta.shape[1]

        if self.Output.meta.shape[2] == 1:
            ideal = (t, c, 1, 0, 0)  # 2d filter
        else:
            ideal = (t, c, 0, 0, 0)  # 3d filter

        return ideal

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot == self.Input:
            numChannels = self.Input.meta.shape[1]
            dirtyChannels = roi.stop[1] - roi.start[1]

            # If all the input channels were dirty, the dirty output region is a contiguous block
            if dirtyChannels == numChannels:
                dirtyKey = list(roiToSlice(roi.start, roi.stop))
                dirtyKey[1] = slice(None)
                dirtyRoi = sliceToRoi(dirtyKey, self.Output.meta.shape)
                self.Output.setDirty(dirtyRoi[0], dirtyRoi[1])
            else:
                # Only some input channels were dirty,
                #  so we must mark each dirty output region separately.
                numFeatures = self.Output.meta.shape[1] // numChannels
                for featureIndex in range(numFeatures):
                    startChannel = numChannels * featureIndex + roi.start[1]
                    stopChannel = startChannel + roi.stop[1]
                    dirtyRoi = copy.copy(roi)
                    dirtyRoi.start[1] = startChannel
                    dirtyRoi.stop[1] = stopChannel
                    self.Output.setDirty(dirtyRoi)

        elif (
            inputSlot == self.SelectionMatrix
            or inputSlot == self.Scales
            or inputSlot == self.FeatureIds
            or inputSlot == self.ComputeIn2d
        ):
            self.Output.setDirty(slice(None))
        else:
            assert False, "Unknown dirty input slot."

    def execute(self, slot, subindex, slot_roi, target):
        assert slot == self.Features or slot == self.Output
        if slot == self.Features:
            feature_slice = roiToSlice(slot_roi.start, slot_roi.stop)
            index = subindex[0]
            feature_slice = list(feature_slice)

            # Translate channel slice of this feature to the channel slice of the output slot.
            output_channel_offset = self.featureOutputChannels[index][0]
            feature_slice[1] = slice(
                output_channel_offset + feature_slice[1].start, output_channel_offset + feature_slice[1].stop
            )
            slot_roi = SubRegion(self.Output, pslice=feature_slice)

            # Get output slot region for this channel
            return self.execute(self.Output, (), slot_roi, target)
        elif slot == self.Output:
            # Correlation of variable 'families' representing reference frames:
            #  ______________________________
            # | input/output frame           |  input/output shape given by slots
            # |  _________________________   |
            # | | smooth frame            |  |  pre-smoothing op needs halo around filter roi
            # | |  ____________________   |  |
            # | | |filter frame        |  |  |  filter needs halo around target roi
            # | | |  _______________   |  |  |
            # | | | | target frame  |  |  |  |  target is given by output_roi

            # note: The 'full_' variable prefix refers to the full 5D shape (tczyx), without 'full_' variables mostly
            #       refer to the 3D space subregion (zyx)

            full_output_slice = slot_roi.toSlice()

            logger.debug(f"OpPixelFeaturesPresmoothed: request {slot_roi.pprint()}")

            assert (slot_roi.stop <= self.Output.meta.shape).all()

            full_output_shape = self.Output.meta.shape
            full_output_start, full_output_stop = sliceToRoi(full_output_slice, full_output_shape)
            assert len(full_output_shape) == 5
            if all(self.ComputeIn2d.value):  # todo: check for this particular slice
                axes2enlarge = (0, 1, 1)
            else:
                axes2enlarge = (1, 1, 1)

            output_shape = full_output_shape[2:]
            output_start = full_output_start[2:]
            output_stop = full_output_stop[2:]

            axistags = self.Output.meta.axistags
            target = target.view(vigra.VigraArray)
            target.axistags = copy.copy(axistags)

            # filter roi in input frame
            # sigma = 0.7, because the features receive a pre-smoothed array and don't need much of a neighborhood
            input_filter_start, input_filter_stop = roi.enlargeRoiForHalo(
                output_start, output_stop, output_shape, 0.7, self.WINDOW_SIZE, enlarge_axes=axes2enlarge
            )

            # smooth roi in input frame
            input_smooth_start, input_smooth_stop = roi.enlargeRoiForHalo(
                input_filter_start,
                input_filter_stop,
                output_shape,
                self.max_sigma,
                self.WINDOW_SIZE,
                enlarge_axes=axes2enlarge,
            )

            # target roi in filter frame
            filter_target_start = roi.TinyVector(output_start - input_filter_start)
            filter_target_stop = roi.TinyVector(output_stop - input_filter_start)

            # filter roi in smooth frame
            smooth_filter_start = roi.TinyVector(input_filter_start - input_smooth_start)
            smooth_filter_stop = roi.TinyVector(input_filter_stop - input_smooth_start)

            filter_target_slice = roi.roiToSlice(filter_target_start, filter_target_stop)
            input_smooth_slice = roi.roiToSlice(input_smooth_start, input_smooth_stop)

            # pre-smooth for all requested time slices and all channels
            full_input_smooth_slice = (full_output_slice[0], slice(None), *input_smooth_slice)
            req = self.Input[full_input_smooth_slice]
            source = req.wait()
            req.clean()
            req.destination = None
            if source.dtype != numpy.float32:
                sourceF = source.astype(numpy.float32)
                try:
                    source.resize((1,), refcheck=False)
                except Exception:
                    pass
                del source
                source = sourceF

            sourceV = source.view(vigra.VigraArray)
            sourceV.axistags = copy.copy(self.Input.meta.axistags)

            dimCol = len(self.scales)
            dimRow = self.matrix.shape[0]

            presmoothed_source = [None] * dimCol

            source_smooth_shape = tuple(smooth_filter_stop - smooth_filter_start)
            full_source_smooth_shape = (
                full_output_stop[0] - full_output_start[0],
                self.Input.meta.shape[1],
            ) + source_smooth_shape
            try:
                for j in range(dimCol):
                    for i in range(dimRow):
                        if self.matrix[i, j]:
                            # There is at least one filter op with this scale
                            break
                    else:
                        # There is no filter op at this scale
                        continue

                    if self.scales[j] > 1.0:
                        tempSigma = math.sqrt(self.scales[j] ** 2 - 1.0)
                    else:
                        tempSigma = self.scales[j]

                    presmoothed_source[j] = numpy.ndarray(full_source_smooth_shape, numpy.float32)

                    droi = (
                        (0, *tuple(smooth_filter_start._asint())),
                        (sourceV.shape[1], *tuple(smooth_filter_stop._asint())),
                    )
                    for i, vsa in enumerate(sourceV.timeIter()):
                        presmoothed_source[j][i, ...] = self._computeGaussianSmoothing(
                            vsa, tempSigma, droi, in2d=self.ComputeIn2d.value[j]
                        )

            except RuntimeError as e:
                if "kernel longer than line" in str(e):
                    raise RuntimeError(
                        "Feature computation error:\nYour image is too small to apply a filter with "
                        f"sigma={self.scales[j]:.1f}. Please select features with smaller sigmas."
                    )
                else:
                    raise e

            del sourceV
            try:
                source.resize((1,), refcheck=False)
            except ValueError:
                # Sometimes this fails, but that's okay.
                logger.debug("Failed to free array memory.")
            del source

            cnt = 0
            written = 0
            closures = []
            # connect individual operators
            for i in range(dimRow):
                for j in range(dimCol):
                    if self.matrix[i, j]:
                        oslot = self.featureOps[i][j].Output
                        req = None
                        slices = oslot.meta.shape[1]
                        if (
                            cnt + slices >= slot_roi.start[1]
                            and slot_roi.start[1] - cnt < slices
                            and slot_roi.start[1] + written < slot_roi.stop[1]
                        ):
                            begin = 0
                            if cnt < slot_roi.start[1]:
                                begin = slot_roi.start[1] - cnt
                            end = slices
                            if cnt + end > slot_roi.stop[1]:
                                end = slot_roi.stop[1] - cnt

                            # feature slice in output frame
                            feature_slice = (slice(None), slice(written, written + end - begin)) + (slice(None),) * 3

                            subtarget = target[feature_slice]
                            # readjust the roi for the new source array
                            full_filter_target_slice = [full_output_slice[0], slice(begin, end), *filter_target_slice]
                            filter_target_roi = SubRegion(oslot, pslice=full_filter_target_slice)

                            closure = partial(
                                oslot.operator.call_execute,
                                oslot,
                                (),
                                filter_target_roi,
                                subtarget,
                                sourceArray=presmoothed_source[j],
                            )
                            closures.append(closure)

                            written += end - begin
                        cnt += slices
            pool = RequestPool()
            for c in closures:
                pool.request(c)
            pool.wait()
            pool.clean()

            for i in range(len(presmoothed_source)):
                if presmoothed_source[i] is not None:
                    try:
                        presmoothed_source[i].resize((1,))
                    except Exception:
                        presmoothed_source[i] = None

    def _computeGaussianSmoothing(self, vol, sigma, roi, in2d):
        if WITH_FAST_FILTERS:
            # Use fast filters (if available)
            result = numpy.zeros(vol.shape).astype(vol.dtype)
            assert vol.channelIndex == 0

            for channel in range(vol.shape[0]):
                c_slice = slice(channel, channel + 1)
                if in2d:

                    for z in range(vol.shape[1]):
                        result[c_slice, z : z + 1] = fastfilters.gaussianSmoothing(
                            vol[c_slice, z : z + 1], sigma, window_size=self.WINDOW_SIZE
                        )
                else:
                    result[c_slice] = fastfilters.gaussianSmoothing(vol[c_slice], sigma, window_size=self.WINDOW_SIZE)

            roi = roiToSlice(*roi)
            return result[roi]
        else:
            # Use Vigra's filters
            if in2d:
                sigma = (0, sigma, sigma)

            # vigra's filter functions need roi without channels axis
            vigra_roi = (roi[0][1:], roi[1][1:])
            return vigra.filters.gaussianSmoothing(vol, sigma, roi=vigra_roi, window_size=self.WINDOW_SIZE)
