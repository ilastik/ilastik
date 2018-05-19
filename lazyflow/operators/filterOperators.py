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
import numpy
import vigra

from lazyflow import roi
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice

from .generic import popFlagsFromTheKey

logger = logging.getLogger(__name__)

# Sven's fast filters
try:
    import fastfilters
    WITH_FAST_FILTERS = True
    logger.info('Using fast filters.')
except ImportError as e:
    WITH_FAST_FILTERS = False
    logger.warning("Failed to import fast filters: " + str(e))


class OpBaseFilter(Operator):
    Input = InputSlot()
    ComputeIn2d = InputSlot(value=False)
    Output = OutputSlot()

    name = "OpBaseFilter"
    category = "Vigra filter"

    supports_out = False
    supports_roi = False
    supports_window = False
    window_size_feature = 2
    window_size_smoother = 3.5
    output_dtype = numpy.float32
    input_dtype = numpy.float32

    def __init__(self, parent=None, graph=None, **kwargs):
        assert hasattr(self, 'filter_fn'), 'Child class needs to implement "filter_fn"'

        # We use 0.7 as an approximation of not doing any smoothing.
        if kwargs:
            self.max_sigma = max(0.7, *kwargs.values())
        else:
            self.max_sigma = 0.7

        super().__init__(parent=parent, graph=graph)

        # Initialize filter parameters
        for slot, value in kwargs.items():
            self.inputs[slot].setValue(value)

    def _n_per_space_axis(self, n=1):
        ret = 0
        for k, s in zip(self.Input.meta.getAxisKeys(), self.Input.meta.shape):
            if k in 'zyx' and s > 1:
                ret += n

        return ret

    def execute(self, slot, subindex, output_roi, target, sourceArray=None):
        assert slot == self.Output
        # explanatory notes for variable 'families':
        #   output_* : associated with Output slot
        #   target_* : associated with target area inside of output, described by output_roi
        #   input_*  : associated with Input slot (same shape as Output slot, except for channels)
        #   source_* : associated with source area inside of input, described by output_roi + halo
        #   result_* : associated with the filtered source
        #
        # relations between variable 'families': (for further clarification)
        #   TARGET is subregion of OUTPUT
        #   SOURCE is subregion of INPUT (or from sourceArray)
        #   TARGET area plus halo equals SOURCE area
        #   applying filter to SOURCE yields RESULT
        #   RESULT without halo is TARGET

        assert len(subindex) == self.Output.level == 0
        if self.supports_roi is False and self.max_sigma > 5:
            logger.warning(f"WARNING: operator {self.name} does not support roi!!")

        key = roiToSlice(output_roi.start, output_roi.stop)

        full_output_shape = self.Output.meta.shape
        full_output_start, full_output_stop = roi.sliceToRoi(key, full_output_shape)
        if self.ComputeIn2d.value:
            axes2enlarge = (0, 1, 1)
        else:
            axes2enlarge = (1, 1, 1)

        output_shape = full_output_shape[2:]  # without tc
        assert output_shape == self.Input.meta.shape[2:], (output_shape, self.Input.meta.shape[2:])
        output_start = full_output_start[2:]
        output_stop = full_output_stop[2:]

        full_axistags = self.Input.meta.axistags
        assert full_axistags == vigra.defaultAxistags('tczyx')
        axistags = vigra.defaultAxistags('czyx')

        input_start, input_stop = roi.enlargeRoiForHalo(
            output_start, output_stop, output_shape, self.max_sigma, window=self.window_size_smoother,
            enlarge_axes=axes2enlarge)
        input_slice = roi.roiToSlice(input_start, input_stop)

        result_start = output_start - input_start
        result_stop = result_start + output_stop - output_start
        result_slice = roi.roiToSlice(result_start, result_stop)

        resC = self.resultingChannels()

        filter_kwargs = {s.name: s.value for s in self.inputs.values() if s.name not in ['Input', 'ComputeIn2d']}
        if self.supports_window:
            filter_kwargs['window_size'] = self.window_size_feature

        def step(tstep, full_input_slice, full_result_slice):
            if sourceArray is None:
                source = self.Input[full_input_slice].wait()
                if source.shape[0] != 1:
                    raise Exception(f'Shape {source.shape}')
                if len(source.shape) != 5:
                    raise Exception(f'Shape {source.shape}')

                source = source[0]
            else:
                assert sourceArray.shape[1] == self.Input.meta.shape[1]
                source = sourceArray[tstep, full_input_slice[1], ...]

            source = numpy.require(source, dtype=self.input_dtype)
            source = source.view(vigra.VigraArray)
            source.axistags = axistags

            # todo: implement support out
            # supports_out = False  # disable for now due to vigra crashes! # FIXME

            if self.supports_roi:
                if self.supports_out:
                    try:
                        subtarget = target[tstep, target_c_start:target_c_stop].view(vigra.VigraArray)
                        subtarget.axistags = copy.copy(axistags)  # todo: share axistags with input (no copy)?
                        logger.debug(
                            f'r o: {self.name} {source.shape} {full_result_slice} {subtarget.shape} {filter_kwargs}')
                        self.filter_fn(source, roi=roi.sliceToRoi(full_result_slice), out=subtarget, **filter_kwargs)
                        return
                    except Exception:
                        logger.error(
                            f'r o: {self.name} {source.shape} {full_result_slice} {subtarget.shape} {filter_kwargs}')
                        raise
                else:
                    try:
                        logger.debug(
                            f'r  : {self.name} {source.shape} {full_result_slice} {filter_kwargs}')
                        result = self.filter_fn(source, roi=roi.sliceToRoi(full_result_slice), **filter_kwargs)
                    except Exception:
                        logger.error(
                            f'r  : {self.name} {source.shape} {target.shape} {filter_kwargs}')
                        raise
            else:
                # note: support of 'out' gives no advantage, if no roi can be specified. The filter result (including a
                #       halo) would not fit into the target (without a halo).
                # todo: implement 'no halo exception' of above note
                try:
                    logger.debug(f'   : {self.name} {source.shape} {filter_kwargs}')
                    result = self.filter_fn(source, **filter_kwargs)
                except Exception:
                    logger.error(f'   : {self.name} {source.shape} {filter_kwargs}')
                    raise
                result = result[full_result_slice]

            try:
                target[tstep, target_c_start:target_c_stop] = result
            except Exception:
                logger.error(f't  : {target.shape} {target[tstep, target_c_start:target_c_stop].shape} {result.shape}')
                raise

        for tstep, t in enumerate(range(full_output_start[0], full_output_stop[0])):
            target_c_stop = 0
            for input_c in range(int(numpy.floor(full_output_start[1] / resC)),
                                 int(numpy.ceil(full_output_stop[1] / resC))):
                output_c_start = resC * input_c
                output_c_stop = resC * (input_c + 1)
                result_c_start = 0
                result_c_stop = resC
                if output_c_start < full_output_start[1]:
                    result_c_start = full_output_start[1] - output_c_start
                    output_c_start = full_output_start[1]
                if output_c_stop > full_output_stop[1]:
                    result_c_stop -= output_c_stop - full_output_stop[1]
                    output_c_stop = full_output_stop[1]

                target_c_start = target_c_stop
                target_c_stop += result_c_stop - result_c_start
                result_c_slice = slice(result_c_start, result_c_stop)
                input_c_slice = slice(input_c, input_c + 1)

                if self.ComputeIn2d.value:
                    for input_z in range(input_start[0], input_stop[0]):
                        step(tstep, (t, input_c_slice, input_z, *input_slice[1:3]), (result_c_slice, *result_slice))
                else:
                    step(tstep, (t, input_c_slice, *input_slice), (result_c_slice, *result_slice))

    def setupOutputs(self):
        if len(self.Input.meta.shape) != 5:
            print('here')
        if self.Input.meta.axistags is not None:
            assert self.Input.meta.getAxisKeys() == list('tczyx')
        # Output meta starts with a copy of the input meta, which is then modified
        self.Output.meta.assignFrom(self.Input.meta)

        numChannels = 1
        inputSlot = self.Input
        if inputSlot.meta.axistags.axisTypeCount(vigra.AxisType.Channels) > 0:
            numChannels = self.Input.meta.shape[1]
            inShapeWithoutChannels = popFlagsFromTheKey(
                self.Input.meta.shape, self.Input.meta.axistags, 'c')

        self.Output.meta.dtype = self.output_dtype
        at = copy.copy(inputSlot.meta.axistags)

        self.Output.meta.axistags = at

        resC = self.resultingChannels()
        inShapeWithoutChannels = list(inShapeWithoutChannels)
        inShapeWithoutChannels.insert(1, numChannels * resC)
        self.Output.meta.shape = tuple(inShapeWithoutChannels)

        if self.Output.meta.axistags.axisTypeCount(vigra.AxisType.Channels) == 0:
            self.Output.meta.axistags.insertChannelAxis()

        # The output data range is not necessarily the same as the input data range.
        if 'drange' in self.Output.meta:
            del self.Output.meta['drange']

    def resultingChannels(self):
        raise RuntimeError('resultingChannels() not implemented')

    ##
    # FIXME: This propagateDirty() function doesn't properly
    # expand the halo according to the sigma and window!
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
    assert len(image.shape) == 2 or (len(image.shape) ==
                                     3 and image.shape[2] == 1), "Only implemented for 2 dimensional images"

    st = vigra.filters.structureTensor(image, sigma0, sigma1, window_size=window_size)
    i11 = st[:, :, 0]
    i12 = st[:, :, 1]
    i22 = st[:, :, 2]

    if out is not None:
        assert out.shape[0] == image.shape[0] and out.shape[1] == image.shape[1] and out.shape[2] == 2
        res = out
    else:
        res = numpy.ndarray((image.shape[0], image.shape[1], 2))

    res[:, :, 0] = (numpy.sqrt((i22 - i11)**2 + 4 * (i12**2)) / (i11 - i22))
    res[:, :, 1] = (numpy.arctan(2 * i12 / (i22 - i11)) / numpy.pi) + 0.5

    return res


class OpGaussianSmoothing(OpBaseFilter):
    sigma = InputSlot()

    supports_window = True

    if WITH_FAST_FILTERS:
        name = "GaussianSmoothingFF"
        filter_fn = staticmethod(fastfilters.gaussianSmoothing)
    else:
        name = "GaussianSmoothing"
        filter_fn = staticmethod(vigra.filters.gaussianSmoothing)
        supports_roi = True
        supports_out = True

    def resultingChannels(self):
        return 1


class OpDifferenceOfGaussians(OpBaseFilter):
    sigma0 = InputSlot()
    sigma1 = InputSlot()

    supports_window = True

    if WITH_FAST_FILTERS:
        name = "DifferenceOfGaussiansFF"

        @staticmethod
        def differenceOfGausssiansFF(image, sigma0, sigma1, window_size):
            return (fastfilters.gaussianSmoothing(image, sigma0, window_size) -
                    fastfilters.gaussianSmoothing(image, sigma1, window_size))

        filter_fn = differenceOfGausssiansFF
    else:
        name = "DifferenceOfGaussians"

        @staticmethod
        def differenceOfGausssians(image, sigma0, sigma1, window_size, roi=None, out=None):
            return (vigra.filters.gaussianSmoothing(image, sigma0, window_size=window_size, roi=roi) -
                    vigra.filters.gaussianSmoothing(image, sigma1, window_size=window_size, roi=roi))

        filter_fn = differenceOfGausssians
        supports_roi = True

    def resultingChannels(self):
        return 1


class OpHessianOfGaussianEigenvalues(OpBaseFilter):
    scale = InputSlot()

    supports_window = True

    if WITH_FAST_FILTERS:
        name = "HessianOfGaussianEigenvaluesFF"
        filter_fn = staticmethod(fastfilters.hessianOfGaussianEigenvalues)
    else:
        name = "HessianOfGaussianEigenvalues"
        filter_fn = staticmethod(vigra.filters.hessianOfGaussianEigenvalues)
        supports_roi = True
        supports_out = True

    def resultingChannels(self):
        return self._n_per_space_axis()


class OpHessianOfGaussianEigenvaluesFirst(OpBaseFilter):
    scale = InputSlot()

    name = "First Eigenvalue of Hessian Matrix"

    @staticmethod
    def firstHessianOfGaussianEigenvalues(image, **kwargs):
        return vigra.filters.hessianOfGaussianEigenvalues(image, **kwargs)[0:1, ...]

    filter_fn = firstHessianOfGaussianEigenvalues
    supports_window = True
    supports_roi = True

    def resultingChannels(self):
        return 1


class OpStructureTensorEigenvalues(OpBaseFilter):
    innerScale = InputSlot()
    outerScale = InputSlot()

    supports_window = True

    if WITH_FAST_FILTERS:
        name = "StructureTensorEigenvaluesFF"
        filter_fn = staticmethod(fastfilters.structureTensorEigenvalues)
    else:
        name = "StructureTensorEigenvalues"
        filter_fn = staticmethod(vigra.filters.structureTensorEigenvalues)
        supports_roi = True
        supports_out = True

    def resultingChannels(self):
        return self._n_per_space_axis()


class OpHessianOfGaussian(OpBaseFilter):
    sigma = InputSlot()

    name = "HessianOfGaussian"
    filter_fn = staticmethod(vigra.filters.hessianOfGaussian)
    supports_window = True
    supports_roi = True
    supports_out = True

    def resultingChannels(self):
        s = self._n_per_space_axis()
        return s * (s + 1) // 2


class OpGaussianGradientMagnitude(OpBaseFilter):
    sigma = InputSlot()

    supports_window = True

    if WITH_FAST_FILTERS:
        name = "GaussianGradientMagnitudeFF"
        filter_fn = staticmethod(fastfilters.gaussianGradientMagnitude)
    else:
        name = "GaussianGradientMagnitude"
        filter_fn = staticmethod(vigra.filters.gaussianGradientMagnitude)
        supports_roi = True
        supports_out = True

    def resultingChannels(self):
        return 1


class OpLaplacianOfGaussian(OpBaseFilter):
    scale = InputSlot()

    supports_window = True

    if WITH_FAST_FILTERS:
        name = "LaplacianOfGaussianFF"
        filter_fn = staticmethod(fastfilters.laplacianOfGaussian)
    else:
        name = "LaplacianOfGaussian"
        supports_out = True
        supports_roi = True

        filter_fn = staticmethod(vigra.filters.laplacianOfGaussian)

    def resultingChannels(self):
        return 1
