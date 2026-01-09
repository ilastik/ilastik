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
from typing import List, Tuple, Dict, OrderedDict, Optional, Iterable, Any, Union

import numpy
import vigra
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
from lazyflow.utility.io_util.multiscaleStore import DEFAULT_VIGRA_RESOLUTION

logger = logging.getLogger(__name__)

OrderedScaling = OrderedTranslation = OrderedDict[Axiskey, float]  # { axis: scaling }
ScalingsByScaleKey = OrderedDict[str, OrderedScaling]  # { scale_key: { axis: scaling } }
ShapesByScaleKey = OrderedDict[str, TaggedShape]  # { scale_key: { axis: size } }

OME_ZARR_V_0_4_KWARGS = dict(dimension_separator="/")
OME_ZARR_AXES: List[Axiskey] = ["t", "c", "z", "y", "x"]
SINGE_SCALE_DEFAULT_KEY = "s0"


def _rescale_size(size: int, factor: float) -> int:
    """
    Rescale a single dimension of a shape.
    Floor-round to match behavior of OpResize, and ensure minimum size is 1.
    """
    return max(int(size / factor), 1)


def match_target_scales_to_input_excluding_upscales(
    export_shape: TaggedShape, input_scales: ShapesByScaleKey, input_key: str
) -> ShapesByScaleKey:
    """We assume people don't generally want to upscale lower-resolution segmentations to raw scale."""
    # Since input_scales is ordered largest-to-smallest, simply drop matching scales before input_key.
    all_matching_scales = _match_target_scales_to_input(export_shape, input_scales, input_key)
    assert input_key in all_matching_scales, "generated scales don't include source scale"
    start = list(all_matching_scales.keys()).index(input_key)
    keep_scales = list(all_matching_scales.keys())[start:]
    return ODict((k, all_matching_scales[k]) for k in keep_scales)


def _match_target_scales_to_input(
    export_shape: TaggedShape, input_scales: ShapesByScaleKey, input_key: str
) -> ShapesByScaleKey:
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
        input_scalings = _multiscale_to_scalings(input_scales, source_scale_shape, export_shape.keys())
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


def generate_default_target_scales(unscaled_shape: TaggedShape, dtype) -> ShapesByScaleKey:
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


def _multiscale_to_scalings(
    multiscale: ShapesByScaleKey,
    base_shape: TaggedShape,
    output_axiskeys: Iterable[Axiskey],
) -> ScalingsByScaleKey:
    """Multiscale and base_shape may have arbitrary axes.
    Output are scaling factors relative to base_shape, with axes output_axiskeys.
    Scale factor 1.0 for axes not present in scale or base shape, and for channel."""
    factors = []
    for scale_shape in multiscale.values():
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
    return ODict(zip(multiscale.keys(), factors))


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


def _get_axes_meta(export_axiskeys, ilastik_meta):
    axis_types = {"t": "time", "c": "channel", "z": "space", "y": "space", "x": "space"}
    axes = [{"name": a, "type": axis_types[a]} for a in export_axiskeys]
    # Don't write empty unit entries
    if ilastik_meta["axis_units"]:
        for a in axes:
            if a["name"] in ilastik_meta["axis_units"] and ilastik_meta["axis_units"][a["name"]]:
                a["unit"] = ilastik_meta["axis_units"][a["name"]]
    return axes


def _get_datasets_meta(
    export_scalings: ScalingsByScaleKey,
    export_resolution: OrderedScaling,
):
    """
    Dataset metadata consists of (1) path, (2) coordinate transformations (scale and translation).
    Transformations should be in physical / absolute units if available.
    Hence, the scale transformation is simply the pixel size.
    Translation is not applicable for our export on individual datasets. This is intended for reporting offsets
    introduced by the scaling method (e.g. half-pixel shift), which OpResize doesn't.

    :param export_scalings: relative scaling factors for each scale-level
    :param export_resolution: pixel size
    """
    datasets = []
    export_axiskeys = list(next(iter(export_scalings.values())).keys())
    for scale_key, scaling in export_scalings.items():
        absolute_scaling = ODict([(a, scaling[a] * export_resolution[a]) for a in export_axiskeys])
        dataset = {
            "path": scale_key,
            "coordinateTransformations": [{"type": "scale", "scale": list(absolute_scaling.values())}],
        }
        datasets.append(dataset)
    return datasets


def _get_tagged_resolution(axistags: vigra.AxisTags) -> OrderedScaling:
    return ODict([(tag.key, tag.resolution if tag.resolution != DEFAULT_VIGRA_RESOLUTION else 1.0) for tag in axistags])


def _get_multiscale_transformations(
    export_resolution_along_unscaled: OrderedScaling,
    export_offset: Optional[TaggedShape],
    export_axiskeys: List[Axiskey],
    ilastik_meta: Dict,
    input_ome_meta: Optional[OMEZarrTranslations],
    input_scale_key: Optional[str],
) -> Optional[List[Dict]]:
    """
    Multiscale-level scale transform = pixel size along unscaled axes (usually t).
    Multiscale-level translation transform = export offset + input translation.
    Whereby "input translation" is the sum of input dataset translation and input multiscale translation.

    In OME-Zarr 0.4, since transformations are in absolute units, it makes no difference
    whether we put them at multiscale-level or dataset-level. We try to match convention:
    - scale transform: Convention is to put scale for unscaled axes in multiscale transforms.
    - translation transform: There is no convention. We interpret export_offset as a global translation
      of the multiscale export, so multiscale transforms seems appropriate.

    :param export_resolution_along_unscaled: For the multiscale "scale" metadata (pixel size along unscaled axes like t)
    :param export_offset: From export subregion settings, in export source slot's axis order (not export target axes)
    :param export_axiskeys: Export target axes
    :param ilastik_meta: To get resolution from axistags (to convert offset to translation)
    :param input_ome_meta: To extract existing dataset and multiscale translations
    :param input_scale_key: To extract existing dataset translations from input_ome_meta

    Returns None or the transformations adjusted to export axes as OME-Zarr conforming dicts.
    """

    def combine_offsets(
        axes: List[Axiskey],
        offset: Optional[TaggedShape],
        resolution: OrderedScaling,
        input_ome_meta: Optional[OMEZarrTranslations],
    ) -> OrderedTranslation:
        """
        Translation = offset from export settings + input translation (if exists).
        Need to convert offset pixels to absolute units and reorder to export axes (with 0 for missing axes).
        """
        sum_translation: OrderedTranslation = ODict(zip(axes, [0.0] * len(axes)))
        if offset:
            reordered_offset = _reorder(offset, axes, 0)
            sum_translation = ODict([(a, reordered_offset[a] * resolution[a]) for a in axes])
        if input_ome_meta:
            input_dataset_translation = input_ome_meta.dataset_translations.get(input_scale_key)
            input_multiscale_translation = input_ome_meta.multiscale_translation
            if input_dataset_translation:
                reordered_dataset = _reorder(input_dataset_translation, axes, 0.0)
                sum_translation = ODict([(a, sum_translation[a] + reordered_dataset[a]) for a in axes])
            if input_multiscale_translation:
                reordered_multiscale = _reorder(input_multiscale_translation, axes, 0.0)
                sum_translation = ODict([(a, sum_translation[a] + reordered_multiscale[a]) for a in axes])
        return sum_translation

    combined_translation = combine_offsets(
        export_axiskeys, export_offset, _get_tagged_resolution(ilastik_meta["axistags"]), input_ome_meta
    )

    multiscale_transforms = []
    if any(v != 1 for v in export_resolution_along_unscaled.values()):
        multiscale_transforms.append({"type": "scale", "scale": list(export_resolution_along_unscaled.values())})
    if any(v != 0 for v in combined_translation.values()):
        if not multiscale_transforms:
            # Must have a scale transform before translation transform
            multiscale_transforms.append({"type": "scale", "scale": [1.0] * len(export_axiskeys)})
        multiscale_transforms.append({"type": "translation", "translation": list(combined_translation.values())})
    return multiscale_transforms or None


def _get_resolution_as_split_scaling(
    export_axiskeys: List[Axiskey],
    ilastik_meta: Dict,
    export_scalings: ScalingsByScaleKey,
    input_scales: Optional[ShapesByScaleKey],
) -> Tuple[OrderedScaling, OrderedScaling]:
    """
    Extract resolution from axistags and split it to return
    - axes that are scaled in either the export (if it's multiscale) or the input (if it's multiscale)
    - axes that are not scaled in either.
    With resolution = 1.0 for the respective other axes.

    We want to report physical pixel size (absolute scale) on the dataset-level in OME-Zarr for axes
    along which the pyramid is scaled, and the pixel size for unscaled axes on multiscale-level.
    Scaling from input OME meta not required, the reader already factors it into the axistags.
    """

    def is_scaling_axis(axis):
        if len(export_scalings) > 1 and any(scale[axis] != 1 for scale in export_scalings.values()):
            return True
        # In case of single-scale export, we still consider this a scaling axis if it's scaled in the input
        if not input_scales:
            return False
        tagged_shapes = list(input_scales.values())
        base_size = tagged_shapes[0].get(axis)
        if not base_size:
            return False
        return any(scale_shape[axis] != base_size for scale_shape in tagged_shapes)

    assert export_axiskeys == [tag.key for tag in ilastik_meta["axistags"]], "wat"
    tagged_resolution = _get_tagged_resolution(ilastik_meta["axistags"])
    resolution_scaled = ODict([(a, tagged_resolution[a] if is_scaling_axis(a) else 1.0) for a in export_axiskeys])
    resolution_unscaled = ODict([(a, tagged_resolution[a] if not is_scaling_axis(a) else 1.0) for a in export_axiskeys])
    return resolution_scaled, resolution_unscaled


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
    input_scales: Optional[ShapesByScaleKey],
    input_scale_key: Optional[str],
    input_ome_meta: Optional[OMEZarrTranslations],
    ilastik_meta: Dict,
):
    ilastik_signature = {"name": "ilastik", "version": ilastik_version, "ome_zarr_exporter_version": 2}
    export_axiskeys = list(next(iter(export_scalings.values())).keys())
    export_resolution_along_scaled, export_resolution_along_unscaled = _get_resolution_as_split_scaling(
        export_axiskeys, ilastik_meta, export_scalings, input_scales
    )

    axes = _get_axes_meta(export_axiskeys, ilastik_meta)
    datasets = _get_datasets_meta(export_scalings, export_resolution_along_scaled)
    ome_zarr_multiscale_meta = {"axes": axes, "datasets": datasets, "version": "0.4"}

    multiscale_transformations = _get_multiscale_transformations(
        export_resolution_along_unscaled,
        export_offset,
        export_axiskeys,
        ilastik_meta,
        input_ome_meta,
        input_scale_key,
    )
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
            target_scales = ShapesByScaleKey({single_target_key: export_shape})

        chunk_shape = _get_chunk_shape(export_shape, export_dtype)

        export_scalings = _multiscale_to_scalings(target_scales, export_shape, export_shape.keys())
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
                "axis_units": reordered_source.meta.get("axis_units"),
                "display_mode": reordered_source.meta.get("display_mode"),
                "drange": reordered_source.meta.get("drange"),
            },
        )
    finally:
        for op in reversed(ops_to_clean):
            op.cleanUp()
        logger.log(USER_LOGLEVEL, "")
