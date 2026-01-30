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
from typing import List, Dict, OrderedDict, Optional, Union

import numpy
import zarr
from zarr.storage import FSStore

from ilastik import __version__ as ilastik_version
from lazyflow import USER_LOGLEVEL
from lazyflow.base import SPATIAL_AXES, Axiskey, Shape, TaggedShape
from lazyflow.operators import OpReorderAxes
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.opResize import OpResize
from lazyflow.roi import determineBlockShape, roiFromShape, roiToSlice
from lazyflow.slot import Slot
from lazyflow.utility import OrderedSignal, PathComponents, BigRequestStreamer
from lazyflow.utility.data_semantics import ImageTypes
from lazyflow.utility.io_util.OMEZarrStore import OMEZarrTranslations
from lazyflow.utility.io_util.clearscale import (
    Spacing,
    Shape as MShape,
    Translation,
    Offset,
    BlueprintShapes,
    BlueprintFactors,
    Scale,
    Unit,
)

logger = logging.getLogger(__name__)

ShapesByScaleKey = OrderedDict[str, TaggedShape]  # { scale_key: { axis: size } }

OME_ZARR_V_0_4_KWARGS = dict(dimension_separator="/")
OME_ZARR_AXES: List[Axiskey] = ["t", "c", "z", "y", "x"]
SINGE_SCALE_DEFAULT_KEY = "s0"


def match_target_scales_to_input_excluding_upscales(
    export_shape: TaggedShape, input_scales: ShapesByScaleKey, input_key: str
) -> ShapesByScaleKey:
    """We assume people don't generally want to upscale lower-resolution segmentations to raw scale."""
    # Since input_scales is ordered largest-to-smallest, simply drop matching scales before input_key.
    all_matching_scales = _match_target_scales_to_input(export_shape, input_scales, input_key)
    assert input_key in all_matching_scales, "generated scales don't include source scale"
    return all_matching_scales.drop_before(input_key)


def _match_target_scales_to_input(
    export_shape: TaggedShape, input_scales: ShapesByScaleKey, input_key: str
) -> BlueprintShapes:
    source_scale_shape = input_scales[input_key]
    export_shape = MShape(export_shape)
    if export_shape.matches(source_scale_shape, only=SPATIAL_AXES):
        # Export shape is unmodified from its source scale -> output shapes = input shapes
        export_shapes = BlueprintShapes(input_scales).reorder(OME_ZARR_AXES).with_sizes(export_shape, axes="tc")
    else:
        # Export shape is modified (cropped) -> apply input scaling factors to export shape
        def two_spatials_or_is_input(scale: str, shape: MShape):
            remaining_spatial = len(shape.non_singleton_axes(SPATIAL_AXES))
            return remaining_spatial > 1 or scale == input_key

        input_scalings = BlueprintFactors.from_shapes(input_scales, reference=source_scale_shape).with_identity("tc")
        export_shapes = (
            input_scalings.to_shapes(reference=export_shape, rounding="floor")
            .reorder(OME_ZARR_AXES)
            .filter_items(two_spatials_or_is_input)
        )

    return export_shapes


def generate_default_target_scales(unscaled_shape: TaggedShape, dtype) -> ShapesByScaleKey:
    """
    Default target scales are isotropic 2x downscaling along x, y and z if present.
    The smallest scale included is just small enough for the entire image to fit into one chunk (per t and c).
    """
    unscaled = MShape(unscaled_shape).reorder(OME_ZARR_AXES)
    chunk_shape_tagged = dict(zip(unscaled.keys(), _get_chunk_shape(unscaled, dtype)))
    shapes = BlueprintShapes.downscale_powers_of_2_xyz(
        base_shape=unscaled, shape_limit=chunk_shape_tagged, rounding="floor"
    )
    return shapes.to_dict()


def _get_chunk_shape(tagged_image_shape: TaggedShape, dtype) -> Shape:
    """Determine chunk shape for OME-Zarr storage. 1 for t and c,
    ilastik default rules for zyx, with a max of 1MB uncompressed per chunk.
    This results in (y: 506 x: 505) for 32-bit 2D and (z: 63 y: 64 x: 63) for 32-bit 3D."""
    target_max_size = 1_024_000.0  # 1MB
    if isinstance(dtype, numpy.dtype):  # Extract raw type class
        dtype = dtype.type
    dtype_bytes = dtype().nbytes
    tagged_maxshape = MShape(tagged_image_shape).with_ones("tc")
    chunk_shape = determineBlockShape(tagged_maxshape.to_list(), target_max_size / dtype_bytes)
    return chunk_shape


def _create_empty_zarray(
    abs_export_path: str,
    scale_key: str,
    scale_shape: Shape,
    chunk_shape: Shape,
    export_dtype,
) -> zarr.Array:
    """Creates folders and zarr-internal (not OME) metadata files."""
    assert len(chunk_shape) == len(scale_shape), "chunk and image shape must have same dimensions"
    store = FSStore(abs_export_path, mode="w", **OME_ZARR_V_0_4_KWARGS)
    zarray = zarr.creation.zeros(scale_shape, store=store, path=scale_key, chunks=chunk_shape, dtype=export_dtype)
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


def _resolve_translations(export_axiskeys, export_offset, export_spacing, input_translations, input_scale_key):
    export_translation = Translation.identity(export_axiskeys)
    input_translation = Translation.identity(export_axiskeys)
    if export_offset:
        export_translation = export_offset.reorder(export_axiskeys).to_physical(export_spacing)
    if input_translations:
        input_translation = input_translations.resolve_at_scale(input_scale_key, export_axiskeys)
    sum_translation = export_translation + input_translation
    return sum_translation


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
    export_shape: TaggedShape,
    export_blueprint: BlueprintShapes,
    interpolation_order: int,
    export_offset: Optional[Offset],
    input_scale_key: Optional[str],
    input_translations: Optional[OMEZarrTranslations],
    ilastik_meta: Dict,
):
    ilastik_signature = {"name": "ilastik", "version": ilastik_version, "ome_zarr_exporter_version": 2}
    export_spacing = Spacing.from_vigra(ilastik_meta["axistags"])
    if ilastik_meta["axis_units"]:
        export_unit = Unit(ilastik_meta["axis_units"]).reorder(export_spacing)
    else:
        export_unit = Unit.empty(export_spacing)
    export_translation = _resolve_translations(
        export_shape.keys(), export_offset, export_spacing, input_translations, input_scale_key
    )

    export_scale = Scale(export_shape, export_spacing, export_unit, export_translation)
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
    export_offset: Union[Shape, None],
    target_scales: Optional[ShapesByScaleKey] = None,
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
    export_offset = Offset(zip(image_source_slot.meta.getAxisKeys(), export_offset)) if export_offset else None
    op_reorder = OpReorderAxes(parent=image_source_slot.operator)
    op_reorder.AxisOrder.setValue("".join(OME_ZARR_AXES))
    ops_to_clean = [op_reorder]
    try:
        op_reorder.Input.connect(image_source_slot)
        reordered_source = op_reorder.Output
        progress_signal(25)
        export_shape = MShape(reordered_source.meta.getTaggedShape())
        export_dtype = reordered_source.meta.dtype
        input_scale_key = reordered_source.meta.get("active_scale")
        input_translations = reordered_source.meta.get("ome_zarr_translations")
        interpolation_order = OpResize.semantics_to_interpolation[
            reordered_source.meta.get("data_semantics", ImageTypes.Intensities)
        ]

        if target_scales is None:  # single-scale export
            single_target_key = input_scale_key if input_scale_key else SINGE_SCALE_DEFAULT_KEY
            target_scales = BlueprintShapes({single_target_key: export_shape})

        chunk_shape = _get_chunk_shape(export_shape, export_dtype)

        export_blueprint = BlueprintShapes(target_scales).reorder(export_shape)
        export_scalings = export_blueprint.to_factors(export_shape)
        combined_scaling_mag = {key: factor.magnitude() for key, factor in export_scalings.items()}

        # Upscales/raw - uncached (maybe this helps keep unscaled computation cache warm)
        # Also covers single-scale export
        upscale_mags = {k: v for k, v in combined_scaling_mag.items() if v <= 1.0}
        for upscale_key, v in reversed(sorted(upscale_mags.items(), key=lambda x: x[1])):
            scale_type = "upscaled data" if v < 1.0 else "unscaled data"
            logger.log(USER_LOGLEVEL, f"Exporting {scale_type} to scale path '{upscale_key}'")
            target_shape = export_blueprint[upscale_key].to_tuple()
            op_scale = None
            try:
                op_scale = OpResize(
                    parent=image_source_slot.operator,
                    RawImage=reordered_source,
                    TargetShape=target_shape,
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
            target_shape = export_blueprint[downscale_key].to_tuple()
            logger.log(USER_LOGLEVEL, f"Exporting downscale to scale path '{downscale_key}'")
            op_scale = OpResize(
                parent=image_source_slot.operator,
                RawImage=prev_slot,
                TargetShape=target_shape,
                InterpolationOrder=interpolation_order,
            )
            ops_to_clean.append(op_scale)
            op_cache = OpBlockedArrayCache(parent=image_source_slot.operator)
            ops_to_clean.append(op_cache)
            op_cache.Input.connect(op_scale.ResizedImage)
            op_cache.BlockShape.setValue(chunk_shape)
            requester = BigRequestStreamer(
                op_cache.Output, roiFromShape(op_cache.Output.meta.shape), blockshape=chunk_shape
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
            input_scale_key,
            input_translations,
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
