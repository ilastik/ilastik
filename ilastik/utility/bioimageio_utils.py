###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
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
"""
A collection of utilities for the bioimageio spec and core.
Eventually it could be integrated to the bioimageio packages.
"""

from __future__ import annotations

import pathlib
import tempfile
from collections import OrderedDict
from functools import partial
from typing import Callable, List, Literal, Mapping, Optional, Sequence, Union

import numpy as np
from bioimageio.spec import ResourceDescr, load_description
from bioimageio.spec.model.v0_5 import (
    AxisId,
    BatchAxis,
    ChannelAxis,
    DataDependentSize,
    InputAxis,
    InputTensorDescr,
    InvalidDescr,
    ModelDescr,
    OutputAxis,
    OutputTensorDescr,
    ParameterizedSize,
    SizeReference,
    SpaceAxisBase,
    TensorDescr,
    WithHalo,
)
from typing_extensions import TypeGuard, assert_never

SPEC_AXES_KEYS = Literal["batch", "time", "y", "x", "z", "channel"]
VIGRA_AXES_KEYS = Literal["b", "t", "y", "x", "z", "c"]

TaggedShapeVigra = OrderedDict[VIGRA_AXES_KEYS, int]
TaggedShapeSpec = OrderedDict[SPEC_AXES_KEYS, int]
AnyAxis = Union[InputAxis, OutputAxis]

VIGRA_TO_SPEC: Mapping[VIGRA_AXES_KEYS, SPEC_AXES_KEYS] = {
    "b": "batch",
    "t": "time",
    "y": "y",
    "x": "x",
    "z": "z",
    "c": "channel",
}
SPEC_TO_VIGRA: Mapping[SPEC_AXES_KEYS, VIGRA_AXES_KEYS] = {spec: vigra for vigra, spec in VIGRA_TO_SPEC.items()}


def get_model_descr_from_model_bytes(model_bytes: bytes) -> ResourceDescr:
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as _tmp_file:
        _tmp_file.write(model_bytes)
        temp_file_path = pathlib.Path(_tmp_file.name)
    model_descr = load_description(temp_file_path, format_version="latest")
    if isinstance(model_descr, InvalidDescr):
        raise ValueError(f"Failed to load valid model descriptor {model_descr.validation_summary}")
    return model_descr


class AxisUtils:
    def __init__(self, specs: Sequence[TensorDescr]):
        self._specs = specs

    def realize_size_reference(self, size: SizeReference) -> AnyAxis:
        ref_tensor = self.get_spec(size.tensor_id)
        axis = self.get_axis(ref_tensor, size.axis_id)
        assert axis
        return axis

    def get_spec(self, tensor_id: str) -> TensorDescr:
        specs = [spec for spec in self._specs if tensor_id == spec.id]
        if len(specs) == 0:
            raise ValueError(
                f"Spec '{tensor_id}' doesn't exist for specs {','.join([spec.id for spec in self._specs])}"
            )
        assert len(specs) == 1, "ids of tensor specs should be unique"
        return specs[0]

    def is_input_tensor(self, tensor_id: str) -> bool:
        return isinstance(self.get_spec(tensor_id), InputTensorDescr)

    def is_output_tensor(self, tensor_id: str) -> bool:
        return isinstance(self.get_spec(tensor_id), OutputTensorDescr)

    def is_2d(self, tensor_id: str) -> bool:
        spec = self.get_spec(tensor_id)
        return self.num_spatial_axis(spec) == 2

    def is_3d(self, tensor_id: str) -> bool:
        spec = self.get_spec(tensor_id)
        return self.num_spatial_axis(spec) == 3

    @staticmethod
    def is_axis_spatial(axis: AnyAxis) -> bool:
        return isinstance(axis, SpaceAxisBase)

    @staticmethod
    def get_axis(tensor: TensorDescr, axis_id: AxisId) -> Optional[AnyAxis]:
        ref_axes = [axis for axis in tensor.axes if axis.id == axis_id]
        if len(ref_axes) == 0:
            return None
        elif len(ref_axes) == 1:
            return ref_axes[0]
        else:
            raise ValueError(f"Multiple reference axes found {ref_axes} for {axis_id} and tensor {tensor}")

    @staticmethod
    def get_channel_axis(tensor: TensorDescr) -> Optional[ChannelAxis]:
        channel_axis = AxisUtils.get_axis(
            tensor, axis_id=AxisId("channel")
        )  # todo: CHANNEL_AXIS_ID from spec same as BATCH_AXIS_ID

        if channel_axis:
            if not isinstance(channel_axis, ChannelAxis):
                raise ValueError(f"Channel axis not of required Axis type `ChannelAxis`. Got {type(channel_axis)}.")
        return channel_axis

    @staticmethod
    def get_channel_axis_strict(tensor: TensorDescr) -> ChannelAxis:
        channel_axis = AxisUtils.get_channel_axis(tensor)
        assert channel_axis
        return channel_axis

    @staticmethod
    def is_channel_axis_included(tensor: TensorDescr) -> bool:
        return AxisUtils.get_channel_axis(tensor) is not None

    @staticmethod
    def num_spatial_axis(tensor: TensorDescr) -> int:
        return sum(isinstance(axis, SpaceAxisBase) for axis in tensor.axes)

    @staticmethod
    def is_vigra_default_axes(source: TaggedShapeVigra) -> bool:
        return all(axis in "tyzxc" for axis in source.keys())

    @staticmethod
    def is_expected_bioimageio_axis_str(axis_key: str) -> TypeGuard[SPEC_AXES_KEYS]:
        return axis_key in SPEC_TO_VIGRA

    @staticmethod
    def is_expected_vigra_axis_str(axis_key: str) -> TypeGuard[VIGRA_AXES_KEYS]:
        return axis_key in VIGRA_TO_SPEC

    @staticmethod
    def convert_vigra_default_axes_to_spec_explicit_size(source: TaggedShapeVigra) -> TaggedShapeSpec:
        assert AxisUtils.is_vigra_default_axes(source)
        spec = OrderedDict()
        spec["batch"] = None
        for axis_name, axis_size in source.items():
            spec[VIGRA_TO_SPEC[axis_name]] = axis_size
        return spec


class InputAxisUtils(AxisUtils):

    MIN_SIZE_2D = 512
    MIN_SIZE_3D = 64

    def __init__(self, tensors: Sequence[InputTensorDescr]):
        super().__init__(tensors)

    def get_best_tile_shape(self, tensor_id: str) -> TaggedShapeVigra:
        """Hack: pick a bigger shape than min shape

        Axes in the spec don't necessarily come with a defined size (e.g.
        Parametrized size). This function determines a fixed size for each axis.

        In addition, this function also imposes a minimal size in case of
        parametrized sizes to avoid non-optimal (too small) tiles.
        While dryrun is not implemented, we'll "guess" a sensible shape
        and hope it will fit into memory.

        This function finds the factor n such that at least one size of the tensor
        will be MIN_SIZE_2D/3D

        Ignores batch axis (this returns the shape for a tile).
        """
        if self.is_2d(tensor_id):
            target_size = self.MIN_SIZE_2D
        elif self.is_3d(tensor_id):
            target_size = self.MIN_SIZE_3D
        else:
            raise ValueError

        # get all axes without batch axis
        spec_axes = [ax for ax in self.get_spec(tensor_id).axes if not isinstance(ax, BatchAxis)]

        sized_axes: OrderedDict[VIGRA_AXES_KEYS, int] = OrderedDict()

        size_funcs: OrderedDict[VIGRA_AXES_KEYS, Union[int, Callable[[int], int]]] = OrderedDict()
        factors: list[int] = []

        # functions to determine the final shape, will be used as partials
        # with only the factor `n` undefined
        def param_size(min_, step, n: int) -> int:
            return int(min_ + n * step)

        # find the ideal factor for each axis and a function of to determine the size
        for axis in spec_axes:
            # FIXME: cannot properly enforce axis.id type here
            axis_id = str(axis.id)
            assert AxisUtils.is_expected_bioimageio_axis_str(axis_id)

            axis_name = SPEC_TO_VIGRA[axis_id]
            axis_size = axis.size

            if isinstance(axis_size, SizeReference):
                n = 0
                ref_size = self.realize_size_reference(axis_size)
                assert not isinstance(ref_size, BatchAxis)
                explicit_size = axis_size.get_size(axis, ref_size, n)
                if isinstance(ref_size.size, ParameterizedSize):
                    while explicit_size < target_size:
                        n += 1
                        explicit_size = axis_size.get_size(axis, ref_size, n)
                factors.append(n)
                size_funcs[axis_name] = partial(axis_size.get_size, axis, ref_size)
            elif isinstance(axis_size, ParameterizedSize):
                size_diff = target_size - axis_size.min
                if size_diff > 0:
                    factor = np.ceil(size_diff / axis_size.step)
                else:
                    factor = 0
                size_funcs[axis_name] = partial(param_size, axis_size.min, axis_size.step)
                factors.append(factor)
            elif isinstance(axis_size, DataDependentSize):
                raise NotImplementedError()
            elif isinstance(axis_size, int):
                size_funcs[axis_name] = axis_size
            else:
                assert_never(axis_size)

        # if all sizes are fixed, factors might be empty
        min_factor = min(factors) if factors else None
        if min_factor is not None:
            for k, f in size_funcs.items():
                if isinstance(f, int):
                    sized_axes[k] = f
                else:
                    sized_axes[k] = f(min_factor)
        else:
            for k, f in size_funcs.items():
                if isinstance(f, int):
                    sized_axes[k] = f
                else:
                    raise ValueError("If size is not an integer, factor needs to be not None.")

        return sized_axes


class OutputAxisUtils(AxisUtils):
    @classmethod
    def from_model_descr(cls, model_descr: ModelDescr):
        return OutputAxisUtils(tuple(model_descr.inputs) + tuple(model_descr.outputs))

    def get_halos(self, tensor_id: str) -> TaggedShapeVigra:
        assert self.is_output_tensor(tensor_id)
        spec = self.get_spec(tensor_id)
        halos = OrderedDict()
        for axis in spec.axes:
            if not self.is_axis_spatial(axis):
                continue
            axis_id = str(axis.id)
            assert AxisUtils.is_expected_bioimageio_axis_str(axis_id)
            axis_name = SPEC_TO_VIGRA[axis_id]
            if isinstance(axis, WithHalo):
                halos[axis_name] = axis.halo
            else:
                halos[axis_name] = 0
        return halos


class InputValidator:
    def __init__(self, specs: List[InputTensorDescr]):
        self._utils = InputAxisUtils(specs)

    def check_single_image_min_shape(self, tensor_id: str, target_vigra_shape: TaggedShapeVigra):
        """
        Check if image shape is smaller than the minimum that the model can support.

        We assume that op image readers use `vigra.defaultAxis` to assign axis tags ('t','y','x','x','c').

        When comparing the shapes, we neglect the order.
        Furthermore, a model that does not have a z-axis, or a time axis will be compatible with data that
        has those axes -> model can be applied per time / through z.
        """
        spec_shape = self._utils.convert_vigra_default_axes_to_spec_explicit_size(target_vigra_shape)
        input_spec = self._utils.get_spec(tensor_id)

        dims_spec = sorted(tuple(axis.id for axis in input_spec.axes))
        dims_target = sorted(tuple(spec_shape.keys()))

        if "z" in dims_target and "z" not in dims_spec:
            dims_target.remove("z")

        if "time" in dims_target and "time" not in dims_spec:
            dims_target.remove("time")

        if dims_spec != dims_target:
            raise ValueError(f"Incompatible axes names, got {dims_target} expected {dims_spec}")

        for axis in input_spec.axes:
            if isinstance(axis, BatchAxis):
                continue
            if isinstance(axis.size, ParameterizedSize):
                min_size = axis.size.min
            elif isinstance(axis.size, SizeReference):
                ref_axis = self._utils.realize_size_reference(axis.size)
                assert not isinstance(ref_axis, BatchAxis)
                min_size = axis.size.get_size(axis, ref_axis, 0)
            elif isinstance(axis.size, int):
                min_size = axis.size
            else:
                raise ValueError(f"Unexpected size {axis.size} of axis {axis}")

            axis_id = str(axis.id)
            assert AxisUtils.is_expected_bioimageio_axis_str(
                axis_id
            ), f"Axis {axis_id} not an expected bioimage io axis string {SPEC_TO_VIGRA.keys()}."

            target_axis_size = spec_shape[axis_id]
            if isinstance(axis, ChannelAxis):
                if target_axis_size != min_size:
                    raise ValueError(
                        f"Incompatible axis {axis}: Number of channels in data: {target_axis_size} != Number of channels expected by model: {min_size}"
                    )
            else:
                if target_axis_size < min_size:
                    raise ValueError(f"Incompatible axis {axis}: {target_axis_size} < {min_size}")
