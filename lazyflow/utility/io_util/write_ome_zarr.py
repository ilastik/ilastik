###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2025, the ilastik developers
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
import logging
from functools import partial
from pathlib import Path
from typing import List, Dict, Optional, Union, Mapping

import numpy
import zarr
from zarr.storage import FSStore

from ilastik import __version__ as ilastik_version
from lazyflow import USER_LOGLEVEL
from lazyflow.base import SPATIAL_AXES, Axiskey, Shape as ShapeTuple, TaggedShape
from lazyflow.operators import OpReorderAxes
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.opResize import OpResize
from lazyflow.roi import determineBlockShape, roiFromShape, roiToSlice
from lazyflow.slot import Slot
from lazyflow.utility import OrderedSignal, PathComponents, BigRequestStreamer
from lazyflow.utility.data_semantics import ImageTypes
from lazyflow.utility.io_util.clearscale import (
    PixelSize,
    Shape,
    Translation,
    PixelOffset,
    BlueprintShapes,
    Scale,
    Unit,
    Multiscale,
)

logger = logging.getLogger(__name__)

OME_ZARR_V_0_4_KWARGS = dict(dimension_separator="/")
OME_ZARR_AXES: List[Axiskey] = ["t", "c", "z", "y", "x"]
SINGE_SCALE_DEFAULT_KEY = "s0"


def match_target_scales_to_input_excluding_upscales(
    export_shape: TaggedShape, input_scales: Multiscale, input_key: str
) -> BlueprintShapes:
    """We assume people don't generally want to upscale lower-resolution segmentations to raw scale."""
    # Since input_scales is ordered largest-to-smallest, simply drop matching scales before input_key.
    all_matching_scales = _match_target_scales_to_input(export_shape, input_scales, input_key)
    return all_matching_scales.drop_before(input_key)


def _match_target_scales_to_input(
    export_shape: TaggedShape, input_scales: Multiscale, input_key: str
) -> BlueprintShapes:
    source_scale_shape = input_scales[input_key].shape
    if source_scale_shape.matches(export_shape, only=SPATIAL_AXES):
        # Unmodified source shape - reproduce exact multiscale shapes
        shapes = BlueprintShapes.from_multiscale(input_scales)
    else:

        def two_spatials_or_is_input(scale: str, shape: Shape):
            remaining_spatial = len(shape.non_singleton_axes(SPATIAL_AXES))
            return remaining_spatial > 1 or scale == input_key

        shapes = BlueprintShapes.from_multiscale_rescaled(
            input_scales, target_shape=export_shape, source_key=input_key, scaled_axes=SPATIAL_AXES, rounding="floor"
        ).filter_items(two_spatials_or_is_input)

    return shapes.with_axes(OME_ZARR_AXES).with_sizes(export_shape, axes="tc")


def generate_default_target_scales(unscaled_shape: TaggedShape, dtype) -> BlueprintShapes:
    """
    Default target scales are isotropic 2x downscaling along x, y and z if present.
    The smallest scale included is just small enough for the entire image to fit into one chunk (per t and c).
    """
    unscaled = Shape(unscaled_shape).with_axes(OME_ZARR_AXES)
    chunk_shape = _get_chunk_shape(unscaled, dtype)
    shapes = BlueprintShapes.downscale_powers_of_2_xyz(base_shape=unscaled, shape_limit=chunk_shape, rounding="floor")
    return shapes


def _get_chunk_shape(tagged_image_shape: Shape, dtype) -> Shape:
    """Determine chunk shape for OME-Zarr storage. 1 for t and c,
    ilastik default rules for zyx, with a max of 1MB uncompressed per chunk.
    This results in (y: 506 x: 505) for 32-bit 2D and (z: 63 y: 64 x: 63) for 32-bit 3D."""
    target_max_size = 1_024_000.0  # 1MB
    if isinstance(dtype, numpy.dtype):  # Extract raw type class
        dtype = dtype.type
    dtype_bytes = dtype().nbytes
    tagged_maxshape = tagged_image_shape.with_ones("tc")
    chunk_shape: ShapeTuple = determineBlockShape(tagged_maxshape.to_list(), target_max_size / dtype_bytes)
    return Shape(zip(tagged_maxshape.keys(), chunk_shape))


def _create_empty_zarray(
    abs_export_path: str,
    scale_key: str,
    scale_shape: Shape,
    chunk_shape: Shape,
    export_dtype,
) -> zarr.Array:
    """Creates folders and zarr-internal (not OME) metadata files."""
    assert list(chunk_shape.keys()) == list(scale_shape.keys()), "chunk and image shape must have same axes"
    store = FSStore(abs_export_path, mode="w", **OME_ZARR_V_0_4_KWARGS)
    zarray = zarr.creation.zeros(
        scale_shape.to_tuple(), store=store, path=scale_key, chunks=chunk_shape.to_tuple(), dtype=export_dtype
    )
    return zarray


def _write_block(zarray: zarr.Array, roi, data):
    slicing = roiToSlice(*roi)
    logger.debug(f"Writing data with shape={data.shape} to {slicing=}")
    zarray[slicing] = data


def _write_to_dataset_attrs(ilastik_meta: Dict, za: zarr.Array):
    za.attrs["axistags"] = ilastik_meta["axistags"].toJSON()
    if ilastik_meta["axis_units"]:
        za.attrs["axis_units"] = ilastik_meta["axis_units"]
    if ilastik_meta["display_mode"]:
        za.attrs["display_mode"] = ilastik_meta["display_mode"]
    if ilastik_meta["drange"]:
        za.attrs["drange"] = ilastik_meta["drange"]


def _get_scaling_method_metadata(export_blueprint: BlueprintShapes, interpolation_order: int) -> Optional[Dict]:
    if not export_blueprint.scaled_axes():
        return None
    metadata = {
        "description": "ilastik's lazyflow.operators.opResize.OpResize is a lazy implementation of skimage.transform.resize.",
        "method": "skimage.transform.resize",
        "version": "0.24.0",
        "kwargs": {"order": interpolation_order, "anti_aliasing": True, "preserve_range": True},
    }
    return metadata


def _write_ome_zarr_and_ilastik_metadata(
    abs_export_path: str,
    export_shape: Shape,
    export_blueprint: BlueprintShapes,
    interpolation_order: int,
    export_offset: Optional[PixelOffset],
    input_scale: Optional[Scale],
    ilastik_meta: Dict,
):
    ilastik_signature = {"name": "ilastik", "version": ilastik_version, "ome_zarr_exporter_version": 2}
    export_pixel_size = PixelSize.from_vigra(ilastik_meta["axistags"])
    axes = list(export_pixel_size.keys())
    if ilastik_meta["axis_units"]:
        export_unit = Unit(ilastik_meta["axis_units"]).with_axes(axes)
    else:
        export_unit = Unit.empty(axes)

    input_translation = input_scale.translation if input_scale else Translation.identity(axes)
    export_translation = input_translation.with_axes(axes)
    if export_offset:
        export_translation += export_offset.with_axes(axes).to_physical(export_pixel_size)

    export_scale = Scale(export_shape, export_pixel_size, export_unit, export_translation)
    multiscale = export_blueprint.apply_to_scale(export_scale)
    ome_zarr_multiscale_meta = multiscale.to_ome_zarr(version="0.4", axis_types="infer")

    scaling_meta = _get_scaling_method_metadata(export_blueprint, interpolation_order)
    if scaling_meta:
        ome_zarr_multiscale_meta["metadata"] = scaling_meta

    store = FSStore(abs_export_path, mode="w", **OME_ZARR_V_0_4_KWARGS)
    root = zarr.group(store, overwrite=False)
    root.attrs["_creator"] = ilastik_signature
    root.attrs["multiscales"] = [ome_zarr_multiscale_meta]
    for path in export_blueprint.keys():
        za = zarr.Array(store, path=path)
        _write_to_dataset_attrs(ilastik_meta, za)


def write_ome_zarr(
    export_path: str,
    image_source_slot: Slot,
    progress_signal: OrderedSignal,
    export_offset: Union[ShapeTuple, None],
    target_scales: Optional[Mapping[str, Mapping[str, int]]] = None,
):
    pc = PathComponents(export_path)
    if pc.internalPath:
        raise ValueError(
            f'Internal paths are not supported by OME-Zarr export. Received internal path: "{pc.internalPath}"'
        )
    abs_export_path = pc.externalPath
    if Path(abs_export_path).exists():
        raise FileExistsError(
            "Aborting because export path already exists. Please delete it manually if you intended to overwrite it. "
            "Appending to an existing OME-Zarr store is not yet implemented."
            f"\nPath: {abs_export_path}."
        )
    export_offset = PixelOffset(zip(image_source_slot.meta.getAxisKeys(), export_offset)) if export_offset else None
    op_reorder = OpReorderAxes(parent=image_source_slot.operator)
    op_reorder.AxisOrder.setValue("".join(OME_ZARR_AXES))
    ops_to_clean = [op_reorder]
    try:
        op_reorder.Input.connect(image_source_slot)
        reordered_source = op_reorder.Output
        progress_signal(25)
        export_shape = Shape(reordered_source.meta.getTaggedShape())
        export_dtype = reordered_source.meta.dtype
        input_scale_key = reordered_source.meta.get("active_scale")
        input_multiscale = reordered_source.meta.get("scales")
        input_scale = input_multiscale[input_scale_key] if input_multiscale and input_scale_key else None
        interpolation_order = OpResize.semantics_to_interpolation[
            reordered_source.meta.get("data_semantics", ImageTypes.Intensities)
        ]

        if target_scales is None:  # single-scale export
            single_target_key = input_scale_key if input_scale_key else SINGE_SCALE_DEFAULT_KEY
            target_scales = BlueprintShapes({single_target_key: export_shape})

        chunk_shape = _get_chunk_shape(export_shape, export_dtype)

        export_blueprint = BlueprintShapes(target_scales).with_axes(export_shape)
        export_scalings = export_blueprint.to_factors(export_shape)
        combined_scaling_mag = {key: factor.magnitude() for key, factor in export_scalings.items()}

        # Upscales/raw - uncached (maybe this helps keep unscaled computation cache warm)
        # Also covers single-scale export
        upscale_mags = {k: v for k, v in combined_scaling_mag.items() if v <= 1.0}
        for upscale_key, v in reversed(sorted(upscale_mags.items(), key=lambda x: x[1])):
            scale_type = "upscaled data" if v < 1.0 else "unscaled data"
            logger.log(USER_LOGLEVEL, f"Exporting {scale_type} to scale path '{upscale_key}'")
            target_shape = export_blueprint[upscale_key]
            op_scale = None
            try:
                op_scale = OpResize(
                    parent=image_source_slot.operator,
                    RawImage=reordered_source,
                    TargetShape=target_shape.to_tuple(),
                    InterpolationOrder=interpolation_order,
                )
                requester = BigRequestStreamer(op_scale.ResizedImage, roiFromShape(op_scale.ResizedImage.meta.shape))
                zarray = _create_empty_zarray(abs_export_path, upscale_key, target_shape, chunk_shape, export_dtype)
                requester.resultSignal.subscribe(partial(_write_block, zarray))
                requester.progressSignal.subscribe(progress_signal)
                requester.execute()
            finally:
                if op_scale is not None:
                    op_scale.cleanUp()

        # Downscales - cached to avoid recomputation (noop for single-scale export)
        downscale_mags = {k: v for k, v in combined_scaling_mag.items() if v > 1.0}
        prev_slot = reordered_source
        for downscale_key, _ in sorted(downscale_mags.items(), key=lambda x: x[1]):
            target_shape = export_blueprint[downscale_key]
            logger.log(USER_LOGLEVEL, f"Exporting downscale to scale path '{downscale_key}'")
            op_scale = OpResize(
                parent=image_source_slot.operator,
                RawImage=prev_slot,
                TargetShape=target_shape.to_tuple(),
                InterpolationOrder=interpolation_order,
            )
            ops_to_clean.append(op_scale)
            op_cache = OpBlockedArrayCache(parent=image_source_slot.operator)
            ops_to_clean.append(op_cache)
            op_cache.Input.connect(op_scale.ResizedImage)
            op_cache.BlockShape.setValue(chunk_shape.to_tuple())
            requester = BigRequestStreamer(
                op_cache.Output, roiFromShape(op_cache.Output.meta.shape), blockshape=chunk_shape.to_tuple()
            )
            zarray = _create_empty_zarray(abs_export_path, downscale_key, target_shape, chunk_shape, export_dtype)
            requester.resultSignal.subscribe(partial(_write_block, zarray))
            requester.progressSignal.subscribe(progress_signal)
            requester.execute()
            prev_slot = op_cache.Output

        progress_signal(95)
        _write_ome_zarr_and_ilastik_metadata(
            abs_export_path,
            export_shape,
            export_blueprint,
            interpolation_order,
            export_offset,
            input_scale,
            {
                "axistags": reordered_source.meta.axistags,
                "axis_units": reordered_source.meta.get("axis_units"),
                "display_mode": reordered_source.meta.get("display_mode"),
                "drange": reordered_source.meta.get("drange"),
            },
        )
    finally:
        for op in reversed(ops_to_clean):
            op.cleanUp()
        logger.log(USER_LOGLEVEL, "")
