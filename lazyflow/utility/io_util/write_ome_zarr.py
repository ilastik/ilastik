###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2024, the ilastik developers
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
import dataclasses
import logging
from collections import OrderedDict as ODict
from functools import partial
from pathlib import Path
from typing import List, Tuple, Dict, OrderedDict, Optional, Literal

import numpy
import zarr
from zarr.storage import FSStore

from ilastik import __version__ as ilastik_version
from lazyflow.operators import OpReorderAxes
from lazyflow.roi import determineBlockShape, roiFromShape, roiToSlice
from lazyflow.slot import Slot
from lazyflow.utility import OrderedSignal, PathComponents, BigRequestStreamer
from lazyflow.utility.io_util import multiscaleStore
from lazyflow.utility.io_util.OMEZarrStore import (
    OME_ZARR_V_0_4_KWARGS,
    OMEZarrMultiscaleMeta,
    OMEZarrCoordinateTransformation,
    InvalidTransformationError,
)

logger = logging.getLogger(__name__)

Shape = Tuple[int, ...]
Axiskey = Literal["t", "z", "y", "x", "c"]
TaggedShape = OrderedDict[Axiskey, int]  # { axis: size }
OrderedScaling = OrderedTranslation = OrderedDict[Axiskey, float]  # { axis: scaling }
ScalingsByScaleKey = OrderedDict[str, OrderedScaling]  # { scale_key: { axis: scaling } }

SPATIAL_AXES = ["z", "y", "x"]


@dataclasses.dataclass
class ImageMetadata:
    path: str
    scaling: OrderedScaling
    translation: OrderedTranslation


def _get_chunk_shape(tagged_image_shape: TaggedShape, dtype) -> Shape:
    """Determine chunk shape for OME-Zarr storage. 1 for t and c,
    ilastik default rules for zyx, with a target of 512KB per chunk."""
    if isinstance(dtype, numpy.dtype):  # Extract raw type class
        dtype = dtype.type
    dtype_bytes = dtype().nbytes
    tagged_maxshape = tagged_image_shape.copy()
    tagged_maxshape["t"] = 1
    tagged_maxshape["c"] = 1
    chunk_shape = determineBlockShape(list(tagged_maxshape.values()), 512_000.0 / dtype_bytes)  # 512KB chunk size
    return chunk_shape


def _get_input_multiscale_matching_export(
    input_scales: multiscaleStore.Multiscales, input_scale_key: str
) -> multiscaleStore.Multiscales:
    """Filter for multiscales entry that matches source image."""
    matching_scales = []
    # Multiscales is ordered from highest to lowest resolution
    for key, scale_shape in input_scales.items():
        if key == input_scale_key:
            matching_scales.append((key, scale_shape))
            break
    assert len(matching_scales) > 0, "Should be impossible, input must be one of the scales"
    return ODict(matching_scales)


def _multiscale_shapes_to_factors(
    multiscales: multiscaleStore.Multiscales,
    base_shape: TaggedShape,
    output_axiskeys: List[Axiskey],
) -> List[OrderedScaling]:
    """Multiscales and base_shape may have arbitrary axes.
    Output are scaling factors relative to base_shape, with axes output_axiskeys.
    Scale factor 1.0 for axes not present in scale or base shape, and for channel."""
    scalings = []
    for scale_shape in multiscales.values():
        common_axes = [a for a in scale_shape.keys() if a in base_shape.keys()]
        scale_values = [scale_shape[a] for a in common_axes]
        base_values = [base_shape[a] for a in common_axes]
        # This scale's scaling relative to base_shape.
        # Scaling "factors" are technically divisors for the shape (factor 2.0 means half the shape).
        relative_factors = {a: base / s for a, s, base in zip(common_axes, scale_values, base_values)}
        # Account for scale_shape maybe being the result of rounding while downscaling base_shape
        rounded = {a: float(round(f)) for a, f in relative_factors.items()}
        rounding_errors = {a: (base / rounded[a]) - s for a, s, base in zip(common_axes, scale_values, base_values)}
        # Use rounded factors for axes where scale shape was result of rounding (rounding error less than 1px)
        rounded_or_relative = {
            a: rounded[a] if abs(error) < 1.0 else relative_factors[a] for a, error in rounding_errors.items()
        }
        # Pad with 1.0 for requested axes not present in scale/base, and c
        axes_matched_factors = ODict(
            [(a, rounded_or_relative[a] if a in rounded_or_relative and a != "c" else 1.0) for a in output_axiskeys]
        )
        scalings.append(axes_matched_factors)
    return scalings


def _match_or_create_scalings(
    input_scales: multiscaleStore.Multiscales, input_scale_key: str, export_shape: TaggedShape
) -> Tuple[ScalingsByScaleKey, Optional[ScalingsByScaleKey]]:
    """
    Determine scale keys and scaling factors for export.
    The second optional return value are the input's scaling factors relative to its raw scale
    (needed to provide correct metadata for the exported scale(s), which may exclude the original raw).
    """
    if input_scales:
        # Source image is already multiscale, match its scales
        filtered_input_scales = _get_input_multiscale_matching_export(input_scales, input_scale_key)
        # The export might be a crop of the source scale it corresponds to (the first one in the filtered list).
        # Need the full shape of that scale as the base for scaling factors.
        base_shape = next(iter(filtered_input_scales.values()))
        factors_relative_to_export = _multiscale_shapes_to_factors(
            filtered_input_scales, base_shape, export_shape.keys()
        )
        scalings_relative_to_export = ODict(zip(filtered_input_scales.keys(), factors_relative_to_export))
        # Factors relative to raw scale are used later to provide correct scaling metadata
        raw_shape = next(iter(input_scales.values()))
        factors_relative_to_raw = _multiscale_shapes_to_factors(filtered_input_scales, raw_shape, export_shape.keys())
        scalings_relative_to_raw = ODict(zip(filtered_input_scales.keys(), factors_relative_to_raw))
    else:
        # Compute new scale levels
        factors = [ODict([(a, 1.0) for a in export_shape.keys()])]
        scalings_relative_to_export = ODict(zip([f"s{i}" for i in range(len(factors))], factors))
        scalings_relative_to_raw = None
    return scalings_relative_to_export, scalings_relative_to_raw


def _create_empty_zarrays(
    abs_export_path: str,
    export_dtype,
    chunk_shape: Shape,
    export_shape: TaggedShape,
    output_scalings: ScalingsByScaleKey,
) -> Tuple[OrderedDict[str, zarr.Array], OrderedDict[str, ImageMetadata]]:  #
    store = FSStore(abs_export_path, mode="w", **OME_ZARR_V_0_4_KWARGS)
    zarrays = ODict()
    meta = ODict()
    for scale_key, scaling in output_scalings.items():
        zarrays[scale_key] = zarr.creation.zeros(
            export_shape.values(), store=store, path=scale_key, chunks=chunk_shape, dtype=export_dtype
        )
        meta[scale_key] = ImageMetadata(scale_key, scaling, ODict())

    return zarrays, meta


def _scale_and_write_block(scales: ScalingsByScaleKey, zarrays: OrderedDict[str, zarr.Array], roi, data):
    assert scales.keys() == zarrays.keys()
    for scale_key_, scaling_ in scales.items():
        if scaling_["x"] > 1.0 or scaling_["y"] > 1.0:
            raise NotImplementedError("Downscaling is not yet implemented.")
        else:
            slicing = roiToSlice(*roi)
            scaled_data = data
        logger.info(f"Scale {scale_key_}: Writing data with shape={scaled_data.shape} to {slicing=}")
        zarrays[scale_key_][slicing] = scaled_data


def _get_input_raw_absolute_scaling(input_ome_meta: Optional[OMEZarrMultiscaleMeta]) -> Optional[OrderedScaling]:
    if not input_ome_meta:
        return None
    raw_transforms = next(iter(input_ome_meta.dataset_transformations.values()))
    if isinstance(raw_transforms, InvalidTransformationError):
        return None
    raw_scale, _ = raw_transforms
    return ODict(zip(input_ome_meta.axis_units.keys(), raw_scale.values))


def _get_input_dataset_transformations(
    input_ome_meta: Optional[OMEZarrMultiscaleMeta], scale_key: str
) -> Tuple[Optional[OMEZarrCoordinateTransformation], Optional[OMEZarrCoordinateTransformation]]:
    input_scale = input_translation = None
    if input_ome_meta and input_ome_meta.dataset_transformations.get(scale_key):
        input_transforms = input_ome_meta.dataset_transformations[scale_key]
        if isinstance(input_transforms, InvalidTransformationError):
            logger.warning(
                "The input OME-Zarr dataset contained invalid pixel resolution or crop "
                f'position metadata for scale "{scale_key}". '
                "The exported data should be fine, but please check its metadata."
            )
            return None, None
        input_scale, input_translation = input_transforms
    return input_scale, input_translation


def _update_export_scaling_from_input(
    absolute_scaling: OrderedScaling,
    input_axiskeys: Optional[List[Axiskey]],
    input_scale: Optional[OMEZarrCoordinateTransformation],
    scale_key: str,
) -> OrderedScaling:
    if input_scale is None:
        return absolute_scaling
    input_scaling = ODict(zip(input_axiskeys, input_scale.values))
    if any([input_scaling[a] != absolute_scaling[a] for a in SPATIAL_AXES if a in input_scaling]):
        # This shouldn't happen
        logger.warning(
            "The scaling level of the exported OME-Zarr dataset was supposed to be "
            f"matched to the input dataset, but the scaling factors differ at scale {scale_key}. "
            "Your exported images should be fine, but their metadata (pixel resolution) may be incorrect. "
            "Please report this to the ilastik team. "
        )
    # The only scale to actually update is time, if it exists in the input
    updated_scaling = absolute_scaling.copy()
    if "t" in input_scaling.keys() and "t" in absolute_scaling.keys():
        updated_scaling["t"] = input_scaling["t"]
    return updated_scaling


def _make_absolute_if_possible(relative_scaling: OrderedScaling, raw_data_abs_scale: Optional[OrderedScaling]):
    if not raw_data_abs_scale:
        return relative_scaling
    # Round to avoid floating point errors leading to numbers like 1.4000000000000001
    # Presumably nobody needs scaling factors to more than 13 decimal places
    items_per_axis = [
        (a, round(s * raw_data_abs_scale[a], 13)) if a in raw_data_abs_scale and a != "c" else (a, s)
        for a, s in relative_scaling.items()
    ]
    return ODict(items_per_axis)


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


def _get_total_offset(
    absolute_scaling: OrderedScaling,
    image: ImageMetadata,
    export_offset: TaggedShape,
    input_axiskeys: Optional[List[Axiskey]],
    input_translation: Optional[OMEZarrCoordinateTransformation],
) -> OrderedTranslation:
    # Translation may be a total of scale offset, export offset, and input offset (depending on availability)
    export_axiskeys = list(absolute_scaling.keys())
    noop_translation: OrderedTranslation = ODict(zip(export_axiskeys, [0.0] * len(export_axiskeys)))
    base_translation = image.translation if image.translation else noop_translation.copy()
    reordered_export_offset = noop_translation.copy()
    reordered_input_translation = noop_translation.copy()
    if export_offset:
        # offset may still have arbitrary axes here
        # multiply by absolute scaling to obtain physical units if possible (which the final translation should be)
        reordered_export_offset = ODict(
            [(a, export_offset[a] * absolute_scaling[a] if a in export_offset else 0.0) for a in export_axiskeys]
        )
    if input_translation:
        tagged_translation = ODict(zip(input_axiskeys, input_translation.values))
        reordered_input_translation = ODict(
            [(a, tagged_translation[a] if a in tagged_translation else 0.0) for a in export_axiskeys]
        )
    combined_translation = ODict(
        [
            (a, base_translation[a] + reordered_export_offset[a] + reordered_input_translation[a])
            for a in export_axiskeys
        ]
    )
    return combined_translation


def _get_datasets_meta(
    multiscale_metadata: OrderedDict[str, ImageMetadata],
    input_ome_meta: Optional[OMEZarrMultiscaleMeta],
    scalings_relative_to_raw_input: Optional[ScalingsByScaleKey],
    export_offset: Optional[TaggedShape],
):
    """
    Dataset metadata consists of (1) path, (2) coordinate transformations (scale and translation).
    By default, scale is just pixel resolution relative to export, i.e. 1.0, 2.0, 4.0 etc. along each scaled axis.
    This gets more complex when the source dataset was multiscale (providing `scalings_relative_to_raw_input`),
    or OME-Zarr (providing `input_ome_meta`).
    """
    datasets = []
    raw_data_abs_scale = _get_input_raw_absolute_scaling(input_ome_meta)
    input_axiskeys = input_ome_meta.axis_units.keys() if input_ome_meta else None
    for scale_key, image in multiscale_metadata.items():
        if scalings_relative_to_raw_input and scale_key in scalings_relative_to_raw_input:
            relative_scaling = scalings_relative_to_raw_input[scale_key]
        else:
            relative_scaling = image.scaling
        # The scaling factors are relative to export or raw data shape now,
        # but the input dataset might contain absolute scale values, i.e. time/pixel resolution
        absolute_scaling = _make_absolute_if_possible(relative_scaling, raw_data_abs_scale)
        input_scale, input_translation = _get_input_dataset_transformations(input_ome_meta, scale_key)
        absolute_scaling = _update_export_scaling_from_input(absolute_scaling, input_axiskeys, input_scale, scale_key)
        dataset = {
            "path": image.path,
            "coordinateTransformations": [{"type": "scale", "scale": list(absolute_scaling.values())}],
        }
        combined_translation = _get_total_offset(
            absolute_scaling, image, export_offset, input_axiskeys, input_translation
        )
        # Write translation if the input had it (even if it was all 0s), or if the export offset is non-zero
        if input_translation or any(t != 0 for t in combined_translation.values()):
            dataset["coordinateTransformations"].append(
                {"type": "translation", "translation": list(combined_translation.values())}
            )
        datasets.append(dataset)
    return datasets


def _get_multiscale_transformations(
    input_ome_meta: Optional[OMEZarrMultiscaleMeta], export_axiskeys: List[Axiskey]
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


def _write_ome_zarr_and_ilastik_metadata(
    abs_export_path: str,
    export_meta: OrderedDict[str, ImageMetadata],
    scalings_relative_to_raw_input: Optional[ScalingsByScaleKey],
    export_offset: Optional[TaggedShape],
    input_ome_meta: Optional[OMEZarrMultiscaleMeta],
    ilastik_meta: Dict,
):
    ilastik_signature = {"name": "ilastik", "version": ilastik_version, "ome_zarr_exporter_version": 1}
    export_axiskeys = [tag.key for tag in ilastik_meta["axistags"]]

    axes = _get_axes_meta(export_axiskeys, input_ome_meta)
    datasets = _get_datasets_meta(export_meta, input_ome_meta, scalings_relative_to_raw_input, export_offset)
    ome_zarr_multiscale_meta = {"axes": axes, "datasets": datasets, "version": "0.4"}

    multiscale_transformations = _get_multiscale_transformations(input_ome_meta, export_axiskeys)
    if multiscale_transformations:
        ome_zarr_multiscale_meta["coordinateTransformations"] = multiscale_transformations

    store = FSStore(abs_export_path, mode="w", **OME_ZARR_V_0_4_KWARGS)
    root = zarr.group(store, overwrite=False)
    root.attrs["_creator"] = ilastik_signature
    root.attrs["multiscales"] = [ome_zarr_multiscale_meta]
    for image in export_meta.values():
        za = zarr.Array(store, path=image.path)
        _write_to_dataset_attrs(ilastik_meta, za)


def write_ome_zarr(
    export_path: str, image_source_slot: Slot, export_offset: Optional[Shape], progress_signal: OrderedSignal
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
    op_reorder.AxisOrder.setValue("tczyx")
    try:
        op_reorder.Input.connect(image_source_slot)
        reordered_source = op_reorder.Output
        progress_signal(25)
        export_shape = reordered_source.meta.getTaggedShape()
        export_dtype = reordered_source.meta.dtype
        input_scales = reordered_source.meta.scales if "scales" in reordered_source.meta else None
        input_scale_key = reordered_source.meta.active_scale if "scales" in reordered_source.meta else None
        input_ome_meta = reordered_source.meta.get("ome_zarr_meta")

        chunk_shape = _get_chunk_shape(export_shape, export_dtype)
        export_scalings, scalings_relative_to_raw_input = _match_or_create_scalings(
            input_scales, input_scale_key, export_shape
        )
        zarrays, export_meta = _create_empty_zarrays(
            abs_export_path, export_dtype, chunk_shape, export_shape, export_scalings
        )

        requester = BigRequestStreamer(reordered_source, roiFromShape(reordered_source.meta.shape))
        requester.resultSignal.subscribe(partial(_scale_and_write_block, export_scalings, zarrays))
        requester.progressSignal.subscribe(progress_signal)
        requester.execute()

        progress_signal(95)
        _write_ome_zarr_and_ilastik_metadata(
            abs_export_path,
            export_meta,
            scalings_relative_to_raw_input,
            export_offset,
            input_ome_meta,
            {
                "axistags": reordered_source.meta.axistags,
                "display_mode": reordered_source.meta.get("display_mode"),
                "drange": reordered_source.meta.get("drange"),
            },
        )
    finally:
        op_reorder.cleanUp()
