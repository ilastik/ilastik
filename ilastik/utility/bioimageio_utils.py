"""
A collection of utilities for the bioimageio spec and core.
Eventually it could be integrated to the bioimageio packages.
"""

from __future__ import annotations

import pathlib
import tempfile

import numpy as np
from typing import Union, List, Optional
from collections import OrderedDict

from bioimageio.spec import load_description
from bioimageio.spec.model.v0_5 import (
    TensorDescr,
    ChannelAxis,
    SpaceAxisBase,
    InputTensorDescr,
    BatchAxis,
    SizeReference,
    ParameterizedSize,
    ModelDescr,
    AxisId,
    InputAxis,
    OutputAxis,
    WithHalo,
    OutputTensorDescr,
    InvalidDescr,
)

TaggedShape = OrderedDict[str, int]
AnyAxis = Union[InputAxis, OutputAxis]

VIGRA_TO_SPEC = {"b": "batch", "t": "time", "y": "y", "x": "x", "z": "z", "c": "channel"}
SPEC_TO_VIGRA = {spec: vigra for vigra, spec in VIGRA_TO_SPEC.items()}


def get_model_descr_from_model_bytes(model_bytes: bytes) -> ModelDescr:
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as _tmp_file:
        _tmp_file.write(model_bytes)
        temp_file_path = pathlib.Path(_tmp_file.name)
    model_descr = load_description(temp_file_path, format_version="latest")
    if isinstance(model_descr, InvalidDescr):
        raise ValueError(f"Failed to load valid model descriptor {model_descr.validation_summary}")
    return model_descr


class AxisUtils:
    def __init__(self, specs: List[TensorDescr]):
        self._specs = specs

    def realize_size_reference(self, size: SizeReference) -> AnyAxis:
        ref_tensor = self.get_spec(size.tensor_id)
        return self.get_axis(ref_tensor, size.axis_id)

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
    def is_axis_dynamic(axis: AnyAxis) -> bool:
        return not isinstance(axis, BatchAxis) and not isinstance(axis, ChannelAxis)

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
        return AxisUtils.get_axis(
            tensor, axis_id=AxisId("channel")
        )  # todo: CHANNEL_AXIS_ID from spec same as BATCH_AXIS_ID

    @staticmethod
    def get_channel_axis_strict(tensor: TensorDescr) -> ChannelAxis:
        assert AxisUtils.is_channel_axis_included(tensor)
        return AxisUtils.get_channel_axis(tensor)

    @staticmethod
    def is_channel_axis_included(tensor: TensorDescr) -> bool:
        return AxisUtils.get_channel_axis(tensor) is not None

    @staticmethod
    def num_spatial_axis(tensor: TensorDescr) -> int:
        return sum(isinstance(axis, SpaceAxisBase) for axis in tensor.axes)

    @staticmethod
    def is_vigra_default_axes(source: TaggedShape) -> bool:
        return all(axis in "tyzxc" for axis in source.keys())

    @staticmethod
    def convert_vigra_default_axes_to_spec_explicit_size(source: TaggedShape) -> TaggedShape:
        assert AxisUtils.is_vigra_default_axes(source)
        spec = OrderedDict()
        spec["batch"] = None
        for axis_name, axis_size in source.items():
            spec[VIGRA_TO_SPEC[axis_name]] = axis_size
        return spec


class InputAxisUtils(AxisUtils):
    def __init__(self, tensors: List[InputTensorDescr]):
        super().__init__(tensors)

    def get_best_tile_shape(self, tensor_id: str) -> TaggedShape:
        """Hack: pick a bigger shape than min shape

        Some models come with super tiny minimal shapes, that make the processing
        too slow. While dryrun is not implemented, we'll "guess" a sensible shape
        and hope it will fit into memory.
        """

        MIN_SIZE_2D = 512
        MIN_SIZE_3D = 64

        if self.is_2d(tensor_id):
            target_size = MIN_SIZE_2D
        elif self.is_3d(tensor_id):
            target_size = MIN_SIZE_3D
        else:
            raise ValueError

        spec = self.get_spec(tensor_id)
        best_axes: OrderedDict[str, int | ParameterizedSize] = OrderedDict()
        for axis in spec.axes:
            if not self.is_axis_dynamic(axis):
                continue

            axis_name = SPEC_TO_VIGRA[axis.id]
            axis_size = axis.size

            if isinstance(axis_size, SizeReference):
                ref_size = self.realize_size_reference(axis_size)
                n = 0
                explicit_size = axis_size.get_size(axis, ref_size, n)
                if isinstance(ref_size.size, ParameterizedSize):
                    while explicit_size < target_size:
                        n += 1
                        explicit_size = axis_size.get_size(axis, ref_size, n)
                best_axes[axis_name] = int(explicit_size)
            elif isinstance(axis_size, ParameterizedSize):
                factor = np.ceil((target_size - axis_size.min) / axis_size.step)
                best_axes[axis_name] = int(axis_size.min + factor * axis_size.step)
            elif isinstance(axis_size, int):
                best_axes[axis_name] = axis_size
            else:
                raise NotImplementedError
        return best_axes


class OutputAxisUtils(AxisUtils):
    @classmethod
    def from_model_descr(cls, model_descr: ModelDescr):
        return OutputAxisUtils(model_descr.inputs + model_descr.outputs)

    def get_halos(self, tensor_id: str) -> TaggedShape:
        assert self.is_output_tensor(tensor_id)
        spec = self.get_spec(tensor_id)
        halos = OrderedDict()
        for axis in spec.axes:
            if not self.is_axis_spatial(axis):
                continue
            axis_name = SPEC_TO_VIGRA[axis.id]
            if isinstance(axis, WithHalo):
                halos[axis_name] = axis.halo
            else:
                halos[axis_name] = 0
        return halos


class InputValidator:
    def __init__(self, specs: List[InputTensorDescr]):
        self._utils = InputAxisUtils(specs)

    def check_single_image_min_shape(self, tensor_id: str, target_vigra_shape: TaggedShape):
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
            if isinstance(axis, BatchAxis) and axis.size is None:
                continue
            if isinstance(axis.size, ParameterizedSize):
                min_size = axis.size.min
            elif isinstance(axis.size, SizeReference):
                ref_axis = self._utils.realize_size_reference(axis.size)
                min_size = axis.size.get_size(axis, ref_axis, 0)
            elif isinstance(axis.size, int):
                min_size = axis.size
            else:
                raise ValueError(f"Unexpected size {axis.size} of axis {axis}")

            target_axis_size = spec_shape[axis.id]
            if target_axis_size < min_size:
                raise ValueError(f"Incompatible axis {axis}: {target_axis_size} < {min_size}")
