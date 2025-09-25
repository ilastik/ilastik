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
from collections import OrderedDict as ODict
from functools import partial
from pathlib import Path
from typing import List, Tuple, Dict, OrderedDict, Optional, Literal, Iterable, Any, Union

import numpy
import zarr
from zarr.storage import FSStore

from ilastik import __version__ as ilastik_version
from lazyflow import USER_LOGLEVEL
from lazyflow.operators import OpReorderAxes
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.opResize import OpResize
from lazyflow.roi import determineBlockShape, roiFromShape, roiToSlice
from lazyflow.slot import Slot
from lazyflow.utility import OrderedSignal, PathComponents, BigRequestStreamer
from lazyflow.utility.data_semantics import ImageTypes
from lazyflow.utility.io_util.OMEZarrStore import (
    OMEZarrMultiscaleMeta,
    InvalidTransformationError,
)
from lazyflow.utility.io_util.multiscaleStore import Multiscales

logger = logging.getLogger(__name__)

Shape = Tuple[int, ...]
Axiskey = Literal["t", "z", "y", "x", "c"]
TaggedShape = OrderedDict[Axiskey, int]  # { axis: size }
OrderedScaling = OrderedTranslation = OrderedDict[Axiskey, float]  # { axis: scaling }
ScalingsByScaleKey = OrderedDict[str, OrderedScaling]  # { scale_key: { axis: scaling } }

OME_ZARR_V_0_4_KWARGS = dict(dimension_separator="/")
OME_ZARR_AXES: List[Axiskey] = ["t", "c", "z", "y", "x"]
SPATIAL_AXES: List[Axiskey] = ["z", "y", "x"]
SINGE_SCALE_DEFAULT_KEY = "s0"


def _rescale_size(size: int, factor: float) -> int:
    """
    Rescale a single dimension of a shape.
    Floor-round to match behavior of OpResize, and ensure minimum size is 1.
    """
    return max(int(size / factor), 1)


def match_target_scales_to_input_excluding_upscales(
    export_shape: TaggedShape, input_scales: Multiscales, input_key: str
) -> Multiscales:
    """We assume people don't generally want to upscale lower-resolution segmentations to raw scale."""
    # Since Multiscales is ordered largest-to-smallest, simply drop matching scales before input_key.
    all_matching_scales = _match_target_scales_to_input(export_shape, input_scales, input_key)
    assert input_key in all_matching_scales, "generated scales don't include source scale"
    start = list(all_matching_scales.keys()).index(input_key)
    keep_scales = list(all_matching_scales.keys())[start:]
    return ODict((k, all_matching_scales[k]) for k in keep_scales)


def _match_target_scales_to_input(export_shape: TaggedShape, input_scales: Multiscales, input_key: str) -> Multiscales:
    def _eq_shape_permissive(test: TaggedShape, ref: TaggedShape) -> bool:
        """
        Check if two shapes are equal. Ignore channel and allow `test` to have additional axes (but no dropped axes).
        """
        return all(a not in ref or a == "c" or test[a] == ref[a] for a in test.keys())

    source_scale_shape = input_scales[input_key]
    if _eq_shape_permissive(export_shape, source_scale_shape):
        # Export shape is unmodified from its source scale - then all other scales shapes should be identical.
        target_scales = input_scales
    else:
        # Export shape is modified (cropped).
        # Get source multiscale's scaling factors relative to the (uncropped) input shape and compute cropped scale
        # shapes from that.
        input_scalings = _multiscales_to_scalings(input_scales, source_scale_shape, export_shape.keys())
        target_scales_items = []
        for scale_key, scale_factors in input_scalings.items():
            scaled_shape = ODict([(a, _rescale_size(size, scale_factors[a])) for a, size in export_shape.items()])
            is_less_than_2d = len([a for a in SPATIAL_AXES if a in scaled_shape and scaled_shape[a] > 1]) < 2
            if is_less_than_2d and scale_key != input_key:
                # Avoid nonsense scales that aren't at least a 2d image,
                # but make sure the source scale stays so we don't return only upscales
                break
            target_scales_items.append((scale_key, scaled_shape))
        target_scales = ODict(target_scales_items)

    scales_items = []
    for scale_key, target_shape in target_scales.items():
        reordered_shape = _reorder(target_shape, OME_ZARR_AXES, 1)
        if "c" in export_shape:
            reordered_shape["c"] = export_shape["c"]
        reordered_item = (scale_key, reordered_shape)
        scales_items.append(reordered_item)
    return ODict(scales_items)


def generate_default_target_scales(unscaled_shape: TaggedShape, dtype) -> Multiscales:
    """
    Default target scales are isotropic 2x downscaling along x, y and z if present.
    The smallest scale included is just small enough for the entire image to fit into one chunk (per t and c).
    """
    unscaled = _reorder(unscaled_shape, OME_ZARR_AXES, 1)
    chunk_shape_tagged = ODict(zip(OME_ZARR_AXES, _get_chunk_shape(unscaled, dtype)))
    scales_items = []
    sanity_limit = 42
    for i in range(0, sanity_limit):
        scale_key = f"s{i}"
        scale_factor = 2**i
        scaled_shape = []
        for axis, size in unscaled.items():
            if axis in SPATIAL_AXES:
                scaled_shape.append(_rescale_size(size, scale_factor))
            else:
                scaled_shape.append(size)
        scaled_shape_tagged = ODict(zip(OME_ZARR_AXES, scaled_shape))
        item = (scale_key, scaled_shape_tagged)
        scales_items.append(item)
        if all(scaled_shape_tagged[axis] <= chunk_shape_tagged[axis] for axis in SPATIAL_AXES):
            break
    return ODict(scales_items)


def _reorder(
    shape: Dict[Axiskey, Union[int, float]], axes: Iterable[Axiskey], default_value: Union[int, float]
) -> TaggedShape:
    """Reorder a tagged shape to `axes`, using `default_value` for axes missing in `shape`."""
    return ODict([(a, shape[a] if a in shape else default_value) for a in axes])


def _get_chunk_shape(tagged_image_shape: TaggedShape, dtype) -> Shape:
    """Determine chunk shape for OME-Zarr storage. 1 for t and c,
    ilastik default rules for zyx, with a max of 1MB uncompressed per chunk.
    This results in (y: 506 x: 505) for 32-bit 2D and (z: 63 y: 64 x: 63) for 32-bit 3D."""
    target_max_size = 1_024_000.0  # 1MB
    if isinstance(dtype, numpy.dtype):  # Extract raw type class
        dtype = dtype.type
    dtype_bytes = dtype().nbytes
    tagged_maxshape = tagged_image_shape.copy()
    tagged_maxshape["t"] = 1
    tagged_maxshape["c"] = 1
    chunk_shape = determineBlockShape(list(tagged_maxshape.values()), target_max_size / dtype_bytes)
    return chunk_shape


def _multiscales_to_scalings(
    multiscales: Multiscales,
    base_shape: TaggedShape,
    output_axiskeys: Iterable[Axiskey],
) -> ScalingsByScaleKey:
    """Multiscales and base_shape may have arbitrary axes.
    Output are scaling factors relative to base_shape, with axes output_axiskeys.
    Scale factor 1.0 for axes not present in scale or base shape, and for channel."""
    factors = []
    for scale_shape in multiscales.values():
        common_axes = [a for a in scale_shape if a in base_shape]
        scale_values = [scale_shape[a] for a in common_axes]
        base_values = [base_shape[a] for a in common_axes]
        # This scale's scaling relative to base_shape.
        # Scaling "factors" are technically divisors for the shape (factor 2.0 means half the shape).
        relative_factors = {a: base / s for a, s, base in zip(common_axes, scale_values, base_values)}
        # Pad with 1.0 for requested axes not present in scale/base, and c
        axes_matched_factors = ODict(
            [(a, relative_factors[a] if a in relative_factors and a != "c" else 1.0) for a in output_axiskeys]
        )
        factors.append(axes_matched_factors)
    return ODict(zip(multiscales.keys(), factors))


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
    if ilastik_meta["display_mode"]:
        za.attrs["display_mode"] = ilastik_meta["display_mode"]
    if ilastik_meta["drange"]:
        za.attrs["drange"] = ilastik_meta["drange"]


def _get_axes_meta(export_axiskeys, input_ome_meta):
    axis_types = {"t": "time", "c": "channel", "z": "space", "y": "space", "x": "space"}
    axes = [{"name": a, "type": axis_types[a]} for a in export_axiskeys]
    if input_ome_meta:
        # Add unit metadata if available
        for a in axes:
            if a["name"] in input_ome_meta.axis_units and input_ome_meta.axis_units[a["name"]]:
                a["unit"] = input_ome_meta.axis_units[a["name"]]
    return axes


def _get_input_transforms_reordered(
    input_ome_meta: Optional[OMEZarrMultiscaleMeta], scale_key: str, axes: Iterable[Axiskey]
) -> Tuple[Union[OrderedScaling, None], Union[OrderedTranslation, None]]:
    """
    Returns (None, None) if input transformations at `scale_key` invalid or not present,
    otherwise (scale_transform, translation_transform | None).
    """
    reordered_scale = reordered_translation = None
    if input_ome_meta and input_ome_meta.dataset_transformations.get(scale_key):
        input_axiskeys = input_ome_meta.axis_units.keys() if input_ome_meta else None
        input_transforms = input_ome_meta.dataset_transformations[scale_key]
        if isinstance(input_transforms, InvalidTransformationError):
            logger.warning(
                "The input OME-Zarr dataset contained invalid pixel resolution or crop "
                f'position metadata for scale "{scale_key}". '
                "The exported data should be fine, but please check its metadata."
            )
            return None, None
        input_scale = dict(zip(input_axiskeys, input_transforms[0].values))
        reordered_scale = _reorder(input_scale, axes, 1.0)
        if input_transforms[1] is not None:
            input_translation = dict(zip(input_axiskeys, input_transforms[1].values))
            reordered_translation = _reorder(input_translation, axes, 0.0)
    return reordered_scale, reordered_translation


def _get_raw_scale_key(input_scales: OrderedDict[str, Any]) -> str:
    """
    Assume the first scale is the raw scale, which has the highest resolution
    in Precomputed and OME-Zarr.
    Neither format guarantees that this is the raw data (could be upscaled),
    but it's the closest we can get.
    Scaling "1.0" in the metadata also isn't guaranteed to be raw - it could
    refer to "1.0" of a physical unit (with raw e.g. being "0.5").
    """
    assert input_scales
    return next(iter(input_scales.keys()))


def _combine_scalings(
    export_axiskeys: Iterable[Axiskey],
    scaling: OrderedScaling,
    input_scaling_rel_raw: Optional[OrderedScaling],
    input_scaling_ome: Optional[OrderedScaling],
    key_matches_input: bool,
):
    if input_scaling_ome and key_matches_input and all(s == 1 for s in scaling.values()):
        # Export scale exactly matching input, carry factors over unmodified
        absolute_scaling = input_scaling_ome
    elif input_scaling_ome:
        # Other scales' factors must be relative to original (OME) input factors
        absolute_scaling = ODict([(a, scaling[a] * input_scaling_ome[a]) for a in export_axiskeys])
    elif input_scaling_rel_raw:
        # Compute precise scale factors relative to raw scale
        absolute_scaling = ODict([(a, scaling[a] * input_scaling_rel_raw[a]) for a in export_axiskeys])
    else:
        absolute_scaling = scaling
    return absolute_scaling


def _combine_offsets(
    export_axiskeys: List[Axiskey],
    export_offset: TaggedShape,
    input_scaling_rel: Optional[OrderedScaling],
    input_scaling_abs: Optional[OrderedScaling],
    input_translation: Optional[OrderedTranslation],
) -> OrderedTranslation:
    """
    The total offset is the sum of the export offset, and the input translation.
    Need to convert pixels to absolute units, reorder to export axes,
    and pad with 0.0 for axes missing in input / source slot.
    :param export_offset: Offset in pixels, ordered as original export source slot.
    :param input_scaling_abs, input_translation: In absolute units, already reordered to export_axiskeys
    """
    noop_translation: OrderedTranslation = ODict(zip(export_axiskeys, [0.0] * len(export_axiskeys)))
    reordered_export_offset = noop_translation.copy()
    if input_translation is None:
        input_translation = noop_translation.copy()
    assert list(input_translation.keys()) == export_axiskeys
    if export_offset:
        # Export offset in pixels needs to be adapted to absolute input scale if available (OME-Zarr),
        # otherwise to relative input scale if available (Precomputed).
        # Also match export axis order.
        input_scaling_rel = input_scaling_rel if input_scaling_rel else ODict()
        reordered_input_scaling_rel = _reorder(input_scaling_rel, export_axiskeys, 1.0)
        input_scaling_abs = input_scaling_abs if input_scaling_abs else reordered_input_scaling_rel
        assert list(input_scaling_abs.keys()) == export_axiskeys
        reordered_export_offset = ODict(
            [(a, export_offset[a] * input_scaling_abs[a] if a in export_offset else 0.0) for a in export_axiskeys]
        )
    combined_translation = ODict([(a, reordered_export_offset[a] + input_translation[a]) for a in export_axiskeys])
    return combined_translation


def _get_datasets_meta(
    export_scalings: ScalingsByScaleKey,
    export_offset: Optional[TaggedShape],
    input_scales: Optional[Multiscales],
    input_scale_key: Optional[str],
    input_ome_meta: Optional[OMEZarrMultiscaleMeta],
):
    """
    Dataset metadata consists of (1) path, (2) coordinate transformations (scale and translation).
    By default, scale is just pixel resolution relative to export, i.e. 1.0, 2.0, 4.0 etc. along each scaled axis.
    This gets more complex when the source dataset was multiscale (providing `input_scales`),
    or OME-Zarr (providing `input_ome_meta`).
    """
    datasets = []
    export_axiskeys = list(next(iter(export_scalings.values())).keys())
    raw_scale = _get_raw_scale_key(input_scales) if input_scales else None
    input_scalings = (
        _multiscales_to_scalings(input_scales, input_scales[raw_scale], export_axiskeys) if raw_scale else None
    )
    input_scaling_rel_raw = input_scalings[input_scale_key] if input_scalings else None
    input_scaling_ome, input_translation = _get_input_transforms_reordered(
        input_ome_meta, input_scale_key, export_axiskeys
    )
    for scale_key, scaling in export_scalings.items():
        key_matches_input = scale_key == input_scale_key
        combined_scaling = _combine_scalings(
            export_axiskeys, scaling, input_scaling_rel_raw, input_scaling_ome, key_matches_input
        )
        combined_translation = _combine_offsets(
            export_axiskeys, export_offset, input_scaling_rel_raw, input_scaling_ome, input_translation
        )
        dataset = {
            "path": scale_key,
            "coordinateTransformations": [{"type": "scale", "scale": list(combined_scaling.values())}],
        }
        # Write translation if the input had it (even if it was all 0s), or if the export offset is non-zero
        if input_translation or any(t != 0 for t in combined_translation.values()):
            dataset["coordinateTransformations"].append(
                {"type": "translation", "translation": list(combined_translation.values())}
            )
        datasets.append(dataset)
    return datasets


def _get_multiscale_transformations(
    input_ome_meta: Optional[OMEZarrMultiscaleMeta], export_axiskeys: Iterable[Axiskey]
) -> Optional[List[Dict]]:
    """Extracts multiscale transformations from input OME-Zarr metadata, if available.
    Returns None or the transformations adjusted to export axes as OME-Zarr conforming dicts."""
    if input_ome_meta and isinstance(input_ome_meta.multiscale_transformations, tuple):
        transforms_axis_matched = []
        for transform in input_ome_meta.multiscale_transformations:
            if transform is None:
                continue
            tagged_transform = ODict(zip(input_ome_meta.axis_units.keys(), transform.values))
            default_value = 0.0 if transform.type == "translation" else 1.0
            transforms_axis_matched.append(
                {
                    "type": transform.type,
                    transform.type: [
                        tagged_transform[a] if a in tagged_transform else default_value for a in export_axiskeys
                    ],
                }
            )
        return transforms_axis_matched
    elif input_ome_meta and input_ome_meta.multiscale_transformations is not None:
        logger.warning(
            "The input OME-Zarr dataset contained invalid pixel resolution or crop position metadata. "
            "The exported data should be fine, but please check its metadata."
        )


def _get_scaling_method_metadata(export_scalings: ScalingsByScaleKey, interpolation_order: int) -> Optional[Dict]:
    combined_scaling_mag = [numpy.prod(list(scale.values())) for scale in export_scalings.values()]
    if all(numpy.isclose(m, 1.0) for m in combined_scaling_mag):
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
    export_scalings: ScalingsByScaleKey,
    interpolation_order: int,
    export_offset: Optional[TaggedShape],
    input_scales: Optional[Multiscales],
    input_scale_key: Optional[str],
    input_ome_meta: Optional[OMEZarrMultiscaleMeta],
    ilastik_meta: Dict,
):
    ilastik_signature = {"name": "ilastik", "version": ilastik_version, "ome_zarr_exporter_version": 2}
    export_axiskeys = list(next(iter(export_scalings.values())).keys())

    axes = _get_axes_meta(export_axiskeys, input_ome_meta)
    datasets = _get_datasets_meta(export_scalings, export_offset, input_scales, input_scale_key, input_ome_meta)
    ome_zarr_multiscale_meta = {"axes": axes, "datasets": datasets, "version": "0.4"}

    multiscale_transformations = _get_multiscale_transformations(input_ome_meta, export_axiskeys)
    if multiscale_transformations:
        ome_zarr_multiscale_meta["coordinateTransformations"] = multiscale_transformations

    scaling_meta = _get_scaling_method_metadata(export_scalings, interpolation_order)
    if scaling_meta:
        ome_zarr_multiscale_meta["metadata"] = scaling_meta

    store = FSStore(abs_export_path, mode="w", **OME_ZARR_V_0_4_KWARGS)
    root = zarr.group(store, overwrite=False)
    root.attrs["_creator"] = ilastik_signature
    root.attrs["multiscales"] = [ome_zarr_multiscale_meta]
    for path in export_scalings.keys():
        za = zarr.Array(store, path=path)
        _write_to_dataset_attrs(ilastik_meta, za)


def write_ome_zarr(
    export_path: str,
    image_source_slot: Slot,
    progress_signal: OrderedSignal,
    export_offset: Union[Shape, None],
    target_scales: Optional[Multiscales] = None,
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
    export_offset: TaggedShape = (
        ODict(zip(image_source_slot.meta.getAxisKeys(), export_offset)) if export_offset else None
    )
    op_reorder = OpReorderAxes(parent=image_source_slot.operator)
    op_reorder.AxisOrder.setValue("".join(OME_ZARR_AXES))
    ops_to_clean = [op_reorder]
    try:
        op_reorder.Input.connect(image_source_slot)
        reordered_source = op_reorder.Output
        progress_signal(25)
        export_shape = reordered_source.meta.getTaggedShape()
        export_dtype = reordered_source.meta.dtype
        input_scales = reordered_source.meta.get("scales")
        input_scale_key = reordered_source.meta.get("active_scale")
        input_ome_meta = reordered_source.meta.get("ome_zarr_meta")
        interpolation_order = OpResize.semantics_to_interpolation[
            reordered_source.meta.get("data_semantics", ImageTypes.Intensities)
        ]

        if target_scales is None:  # single-scale export
            single_target_key = input_scale_key if input_scale_key else SINGE_SCALE_DEFAULT_KEY
            target_scales = Multiscales({single_target_key: export_shape})

        chunk_shape = _get_chunk_shape(export_shape, export_dtype)

        export_scalings = _multiscales_to_scalings(target_scales, export_shape, export_shape.keys())
        combined_scaling_mag = {key: numpy.prod(list(scale.values())) for key, scale in export_scalings.items()}

        # Upscales/raw - uncached (maybe this helps keep unscaled computation cache warm)
        # Also covers single-scale export
        upscale_mags = {k: v for k, v in combined_scaling_mag.items() if v <= 1.0}
        for upscale_key, v in reversed(sorted(upscale_mags.items(), key=lambda x: x[1])):
            scale_type = "upscaled data" if v < 1.0 else "unscaled data"
            logger.log(USER_LOGLEVEL, f"Exporting {scale_type} to scale path '{upscale_key}'")
            target_shape = tuple(target_scales[upscale_key].values())
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
                op_scale.cleanUp()

        # Downscales - cached to avoid recomputation (noop for single-scale export)
        downscale_mags = {k: v for k, v in combined_scaling_mag.items() if v > 1.0}
        prev_slot = reordered_source
        for downscale_key, _ in sorted(downscale_mags.items(), key=lambda x: x[1]):
            target_shape = tuple(target_scales[downscale_key].values())
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
            export_scalings,
            interpolation_order,
            export_offset,
            input_scales,
            input_scale_key,
            input_ome_meta,
            {
                "axistags": reordered_source.meta.axistags,
                "display_mode": reordered_source.meta.get("display_mode"),
                "drange": reordered_source.meta.get("drange"),
            },
        )
    finally:
        for op in reversed(ops_to_clean):
            op.cleanUp()
        logger.log(USER_LOGLEVEL, "")
