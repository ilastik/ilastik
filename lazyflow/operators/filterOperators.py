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

logger = logging.getLogger(__name__)

# Sven's fast filters
try:
    import fastfilters

    WITH_FAST_FILTERS = True
    logger.info("Using fast filters.")
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
    supports_anisotropic = False
    supports_zero_scale = False
    window_size_feature = 2
    window_size_smoother = 3.5
    minimum_scale = 0.7
    output_dtype = numpy.float32
    input_dtype = numpy.float32

    def __init__(self, parent=None, graph=None, **kwargs):
        """
        If a subclass of OpBaseFilter implements any InputSlots, they have to be valid keyword arguments to the
        filter_fn.
        Args:
            kwargs: may contain input slot names with an initial value. The Operator, which inherits from this base
                    class has to implement those slots.
        """
        assert hasattr(self, "filter_fn"), 'Child class needs to implement "filter_fn"'
        super().__init__(parent=parent, graph=graph)
        # for now, the implementation supports anisotropic filters only if zero is a valid scale value, leading to no
        # filtering across that dimension (but simple batch processing instead)
        # todo: lift the restriction that anisotropic filter are only supported, if zero is a valid scale value
        self.supports_anisotropic = self.supports_anisotropic and self.supports_zero_scale

        # Initialize filter parameters
        for slot, value in kwargs.items():
            self.inputs[slot].setValue(value)

    def setupOutputs(self):
        self.invalid_z = False

        assert len(self.Input.meta.shape) == 5
        assert self.Input.meta.getAxisKeys() == list("tczyx"), self.Input.meta.getAxisKeys()

        filter_scales = {s.name: s.value for s in self.inputs.values() if s.name not in ["Input", "ComputeIn2d"]}
        z_dim = self.Input.meta.shape[2]
        self.invalid_z = z_dim == 1 or any(
            [numpy.ceil(s * self.window_size_feature) + 1 > z_dim for s in filter_scales.values()]
        )

        if self.invalid_z and z_dim > 1 and not self.ComputeIn2d.value:
            logger.warning(f"{self.name}: filtering in 2d for {filter_scales} (z dimension too small)")

        if self.invalid_z or self.ComputeIn2d.value:
            if self.supports_anisotropic:
                for name, value in filter_scales.items():
                    filter_scales[name] = (0, value, value)

        # We use 0.7 as an approximation of not doing any smoothing.
        self.max_sigma = max(0.7, *filter_scales.values())
        self.filter_kwargs = filter_scales
        if self.supports_window:
            self.filter_kwargs["window_size"] = self.window_size_feature

        # Output meta starts with a copy of the input meta, which is then modified
        self.Output.meta.assignFrom(self.Input.meta)

        inputSlot = self.Input
        numChannels = self.Input.meta.shape[1]

        self.Output.meta.dtype = self.output_dtype
        self.Output.meta.axistags = copy.copy(inputSlot.meta.axistags)
        self.Output.meta.shape = (
            self.Input.meta.shape[0],
            numChannels * self.resultingChannels(),
            *self.Input.meta.shape[2:],
        )

        # The output data range is not necessarily the same as the input data range.
        if "drange" in self.Output.meta:
            del self.Output.meta["drange"]

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

        # note: The 'full_' variable prefix refers to the full 5D shape (tczyx), without 'full_' variables mostly
        #       refer to the 3D space subregion (zyx)

        assert len(subindex) == self.Output.level == 0
        if self.supports_roi is False and self.max_sigma > 5:
            logger.warning(f"WARNING: operator {self.name} does not support roi!!")

        key = roiToSlice(output_roi.start, output_roi.stop)

        full_output_shape = self.Output.meta.shape
        full_output_start, full_output_stop = roi.sliceToRoi(key, full_output_shape)
        if self.invalid_z or self.ComputeIn2d.value:
            axes2enlarge = (0, 1, 1)
            process_in_2d = True
            axistags = vigra.defaultAxistags("cyx")
        else:
            axes2enlarge = (1, 1, 1)
            process_in_2d = False
            axistags = vigra.defaultAxistags("czyx")

        output_shape = full_output_shape[2:]  # without tc
        assert output_shape == self.Input.meta.shape[2:], (output_shape, self.Input.meta.shape[2:])
        output_start = full_output_start[2:]
        output_stop = full_output_stop[2:]

        input_start, input_stop = roi.enlargeRoiForHalo(
            output_start,
            output_stop,
            output_shape,
            self.max_sigma,
            window=self.window_size_smoother,
            enlarge_axes=axes2enlarge,
        )
        input_slice = roi.roiToSlice(input_start, input_stop)

        result_start = output_start - input_start
        result_stop = result_start + output_stop - output_start
        result_slice = roi.roiToSlice(result_start, result_stop)

        filter_kwargs = self.filter_kwargs

        def step(tstep, target_z_slice, full_input_slice, full_result_slice):
            if sourceArray is None:
                # no tmatter, if slices or indices are in 'full_input_slice', they will be converted to slices => 5d
                source = self.Input[full_input_slice].wait()[0]  # => remove singleton t dimension
                if process_in_2d:
                    source = source[:, 0]  # if processing in 2d, remove singleton z dimension

                assert source.shape[0] == 1  # single channel axis for input
            else:
                assert sourceArray.shape[1] == self.Input.meta.shape[1]
                source = sourceArray[tstep, full_input_slice[1], ...]
                if process_in_2d:
                    # eliminate singleton z dimension
                    assert isinstance(target_z_slice, int)
                    source = source[:, full_input_slice[2]]  # in 2d z is shared between source and target (like time)

            source = numpy.require(source, dtype=self.input_dtype)
            source = source.view(vigra.VigraArray)
            source.axistags = axistags

            supports_roi = self.supports_roi
            # in vigra the roi parameter does not support a channel roi
            if not WITH_FAST_FILTERS:
                if target_c_stop - target_c_start != self.resultingChannels():
                    supports_roi = False

            if supports_roi:
                if not WITH_FAST_FILTERS:
                    # filter_roi without channel axis (not supported by vigra)
                    filter_roi = roi.sliceToRoi(full_result_slice[1:], source.shape[1:])
                if self.supports_out:
                    try:
                        subtarget = target[tstep, target_c_start:target_c_stop, target_z_slice].view(vigra.VigraArray)
                        if process_in_2d:
                            subtarget = subtarget[:, 0]

                        subtarget.axistags = copy.copy(axistags)
                        logger.debug(
                            f"r o: {self.name} {source.shape} {full_result_slice} {subtarget.shape} {filter_kwargs}"
                        )

                        self.filter_fn(source, roi=filter_roi, out=subtarget, **filter_kwargs)
                        return
                    except Exception:
                        logger.error(
                            f"r o: {self.name} {source.shape} {filter_roi} {subtarget.shape} {filter_kwargs} "
                            f"{process_in_2d}"
                        )
                        raise
                else:
                    try:
                        logger.debug(f"r  : {self.name} {source.shape} {full_result_slice} {filter_kwargs}")
                        result = self.filter_fn(source, roi=filter_roi, **filter_kwargs)
                    except Exception:
                        logger.error(f"r  : {self.name} {source.shape} {target.shape} {filter_kwargs}")
                        raise
            else:
                # note: support of 'out' gives no advantage, if no roi can be specified. The filter result (including a
                #       halo) would not fit into the target (without a halo).
                # todo: implement 'no halo exception' of above note
                try:
                    logger.debug(f"   : {self.name} {source.shape} {filter_kwargs} {process_in_2d}")
                    result = self.filter_fn(source, **filter_kwargs)
                except Exception:
                    logger.error(f"   : {self.name} {source.shape} {filter_kwargs} {process_in_2d}")
                    raise
                result = result[full_result_slice]

            try:
                target[tstep, target_c_start:target_c_stop, target_z_slice] = result
            except Exception:
                logger.error(f"t  : {target.shape} {target[tstep, target_c_start:target_c_stop].shape} {result.shape}")
                logger.error(f"tstep {tstep}  c {target_c_start},{target_c_stop}  z {target_z_slice} {result.shape}")
                raise

        resC = self.resultingChannels()

        for tstep, t in enumerate(range(full_output_start[0], full_output_stop[0])):
            target_c_stop = 0
            for input_c in range(
                int(numpy.floor(full_output_start[1] / resC)), int(numpy.ceil(full_output_stop[1] / resC))
            ):
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

                if process_in_2d:
                    for target_z, input_z in enumerate(range(input_start[0], input_stop[0])):
                        step(
                            tstep,
                            target_z_slice=target_z,
                            full_input_slice=(t, input_c_slice, input_z, *input_slice[1:]),
                            full_result_slice=(result_c_slice, *result_slice[1:]),
                        )
                else:
                    step(
                        tstep,
                        target_z_slice=slice(None),
                        full_input_slice=(t, input_c_slice, *input_slice),
                        full_result_slice=(result_c_slice, *result_slice),
                    )

    def _n_per_space_axis(self, n=1):
        if self.invalid_z or self.ComputeIn2d.value:
            space_axes = "yx"
        else:
            space_axes = "zyx"

        ret = 0
        for k, s in zip(self.Input.meta.getAxisKeys(), self.Input.meta.shape):
            if k in space_axes and s > 1:
                ret += n

        return ret

    def resultingChannels(self):
        raise NotImplementedError("resultingChannels() not implemented")

    def propagateDirty(self, slot, subindex, rroi):
        # If some input we don't know about is dirty (i.e. we are subclassed by an operator with extra inputs),
        # then mark the entire output dirty.  This is the correct behavior for e.g. 'sigma' inputs.
        out_dirty = slice(None)

        # Check for proper name because subclasses may define extra inputs.
        # (but decline to override notifyDirty)
        if slot is self.Input:
            out_dirty = list(rroi.toSlice())
            out_dirty[1] = slice(None)  # todo: map dirty input channels to dirty output channels

            if self.invalid_z or self.ComputeIn2d.value:
                axes2enlarge = [0, 0, 0, 1, 1]
            else:
                axes2enlarge = [0, 0, 1, 1, 1]

            output_shape = self.Output.meta.shape
            rroi = roi.sliceToRoi(out_dirty, output_shape)

            out_dirty = roi.roiToSlice(
                *roi.enlargeRoiForHalo(
                    rroi[0],
                    rroi[1],
                    output_shape,
                    self.max_sigma,
                    window=self.window_size_smoother,
                    enlarge_axes=axes2enlarge,
                )
            )

        elif slot is self.ComputeIn2d:
            if self.invalid_z:
                # Output is computed in 2D anyway due to a small z dimension
                if not self.ComputeIn2d.value:
                    logger.warning(f"{self.name}: filtering in 2d for {self.filter_kwargs} (z dimension too small)")

                return

        self.Output.setDirty(out_dirty)


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


class OpGaussianSmoothing(OpBaseFilter):
    sigma = InputSlot()
    minimum_scale = 0.3

    supports_window = True

    if WITH_FAST_FILTERS:
        name = "GaussianSmoothingFF"
        filter_fn = staticmethod(fastfilters.gaussianSmoothing)
    else:
        name = "GaussianSmoothing"
        filter_fn = staticmethod(vigra.filters.gaussianSmoothing)
        supports_roi = True
        supports_out = True
        supports_anisotropic = True
        supports_zero_scale = True

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
            return fastfilters.gaussianSmoothing(image, sigma0, window_size) - fastfilters.gaussianSmoothing(
                image, sigma1, window_size
            )

        filter_fn = differenceOfGausssiansFF
    else:
        name = "DifferenceOfGaussians"

        @staticmethod
        def differenceOfGausssians(image, sigma0, sigma1, window_size, roi=None, out=None):
            return vigra.filters.gaussianSmoothing(
                image, sigma0, window_size=window_size, roi=roi
            ) - vigra.filters.gaussianSmoothing(image, sigma1, window_size=window_size, roi=roi)

        filter_fn = differenceOfGausssians
        supports_roi = True
        supports_anisotropic = True
        supports_zero_scale = True

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
        supports_anisotropic = True

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
    supports_anisotropic = True
    supports_zero_scale = True

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
        supports_anisotropic = True

    def resultingChannels(self):
        return self._n_per_space_axis()


class OpHessianOfGaussian(OpBaseFilter):
    sigma = InputSlot()

    name = "HessianOfGaussian"
    filter_fn = staticmethod(vigra.filters.hessianOfGaussian)
    supports_window = True
    supports_roi = True
    supports_out = True
    supports_anisotropic = True
    supports_zero_scale = True

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
        supports_anisotropic = True

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
        supports_anisotropic = True

        filter_fn = staticmethod(vigra.filters.laplacianOfGaussian)

    def resultingChannels(self):
        return 1
