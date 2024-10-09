import dataclasses
import logging
from collections import OrderedDict as ODict
from functools import partial
from pathlib import Path
from typing import List, Tuple, Dict, OrderedDict, Optional, Literal

import numpy
import zarr
from zarr.storage import FSStore, contains_array

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
)

logger = logging.getLogger(__name__)

Shape = Tuple[int, ...]
TaggedShape = OrderedDict[str, int]  # { axis: size }
OrderedScaling = OrderedDict[str, float]  # { axis: scaling }
ScalingsByScaleKey = OrderedDict[str, OrderedScaling]  # { scale_key: { axis: scaling } }

SPATIAL_AXES = ["z", "y", "x"]


@dataclasses.dataclass
class ImageMetadata:
    path: str
    scaling: OrderedScaling
    translation: Dict[str, float]


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


def _compute_new_scaling_factors(
    original_tagged_shape: TaggedShape, chunk_shape: Shape, compute_downscales: bool
) -> List[OrderedScaling]:
    """
    Computes scaling "factors".
    Technically they are divisors for the shape (factor 2.0 means half the shape).
    Downscaling is done by a factor of 2 in all spatial dimensions until:
    - the dataset would be less than 4 x chunk size (2MiB)
    - an axis that started non-singleton would become singleton
    Returns list of scaling factor dicts by axis, starting with original scale.
    The scaling level that meets one of the exit conditions is excluded.
    Raises if more than 20 scales are computed (sanity).
    """
    assert len(chunk_shape) == len(original_tagged_shape), "Chunk shape and tagged shape must have same length"
    original_scale = ODict([(a, 1.0) for a in original_tagged_shape.keys()])
    scalings = [original_scale]
    if not compute_downscales:
        return scalings
    sanity_limit = 20
    for i in range(sanity_limit):
        if i == sanity_limit:
            raise ValueError(f"Too many scales computed, limit={sanity_limit}. Please report this to the developers.")
        new_scaling = ODict(
            [
                (a, 2.0 ** (i + 1)) if a in SPATIAL_AXES and original_tagged_shape[a] > 1 else (a, 1.0)
                for a in original_tagged_shape.keys()
            ]
        )
        new_shape = _scale_tagged_shape(original_tagged_shape, new_scaling)
        if _is_less_than_4_chunks(new_shape, chunk_shape) or _reduces_any_axis_to_singleton(
            new_shape.values(), original_tagged_shape.values()
        ):
            break
        raise NotImplementedError("See _apply_scaling_method()")  # scalings.append(new_scaling)
    return scalings


def _reduces_any_axis_to_singleton(new_shape: Shape, original_shape: Shape):
    return any(new <= 1 < orig for new, orig in zip(new_shape, original_shape))


def _is_less_than_4_chunks(new_shape: TaggedShape, chunk_shape: Shape):
    spatial_shape = [s for a, s in new_shape.items() if a in SPATIAL_AXES]
    return numpy.prod(spatial_shape) < 4 * numpy.prod(chunk_shape)


def _scale_tagged_shape(original_tagged_shape: TaggedShape, scaling: OrderedScaling) -> TaggedShape:
    assert all(s > 0 for s in scaling.values()), f"Invalid scaling: {scaling}"
    return ODict(
        [
            (a, _round_like_scaling_method(s / scaling[a]) if a in scaling else s)
            for a, s in original_tagged_shape.items()
        ]
    )


def _round_like_scaling_method(value: float) -> int:
    """For calculating scaled shape after applying the scaling method.
    Different scaling methods round differently, so we need to match that.
    E.g. scaling by stepwise downsampling like image[::2, ::2] always rounds up,
    while e.g. skimage.transform.rescale rounds mathematically like standard round()."""
    return int(value)


def _get_input_multiscales_matching_export(
    input_scales: multiscaleStore.Multiscales, export_shape: TaggedShape, compute_downscales: bool
) -> multiscaleStore.Multiscales:
    """Filter for multiscales entry that matches source image, plus lower scales if compute_downscales is True."""
    matching_scales = []
    # Multiscales is ordered from highest to lowest resolution, so start collecting once match found
    match_found = False
    for key, scale_shape in input_scales.items():
        if all(scale_shape[a] == export_shape[a] or a == "c" for a in scale_shape.keys()):
            match_found = True
            matching_scales.append((key, scale_shape))
            if not compute_downscales:
                break
        elif match_found:
            matching_scales.append((key, scale_shape))
    assert len(matching_scales) > 0, "Should be impossible, input must be one of the scales"
    return ODict(matching_scales)


def _scale_shapes_to_factors(
    multiscales: multiscaleStore.Multiscales,
    base_shape: TaggedShape,
    output_axiskeys: List[Literal["t", "c", "z", "y", "x"]],
) -> List[OrderedScaling]:
    """Multiscales and base_shape may have arbitrary axes.
    Output are scaling factors relative to base_shape, with axes output_axiskeys.
    Scale factor 1.0 for axes not present in scale or base shape, and for channel."""
    scalings = []
    for scale_shape in multiscales.values():
        common_axes = [a for a in scale_shape.keys() if a in base_shape.keys()]
        scale_values = [scale_shape[a] for a in common_axes]
        base_values = [base_shape[a] for a in common_axes]
        # This scale's scaling relative to base_shape; cf note on scaling "factors" in _compute_new_scaling_factors
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
    input_scales: multiscaleStore.Multiscales, export_shape: TaggedShape, chunk_shape, compute_downscales: bool
) -> Tuple[ScalingsByScaleKey, Optional[ScalingsByScaleKey]]:
    """
    Determine scale keys and scaling factors for export.
    The second optional return value are the input's scaling factors relative to its raw scale
    (needed to provide correct metadata for the exported scale(s), which may exclude the original raw).
    """
    if input_scales:
        # Source image is already multiscale, match its scales
        filtered_input_scales = _get_input_multiscales_matching_export(input_scales, export_shape, compute_downscales)
        factors_relative_to_export = _scale_shapes_to_factors(filtered_input_scales, export_shape, export_shape.keys())
        scalings_relative_to_export = ODict(zip(filtered_input_scales.keys(), factors_relative_to_export))
        # Factors relative to raw scale are used later to provide correct scaling metadata
        raw_shape = next(iter(input_scales.values()))
        factors_relative_to_raw = _scale_shapes_to_factors(filtered_input_scales, raw_shape, export_shape.keys())
        scalings_relative_to_raw = ODict(zip(filtered_input_scales.keys(), factors_relative_to_raw))
    else:
        # Compute new scale levels
        factors = _compute_new_scaling_factors(export_shape, chunk_shape, compute_downscales)
        scalings_relative_to_export = ODict(zip([f"s{i}" for i in range(len(factors))], factors))
        scalings_relative_to_raw = None
    return scalings_relative_to_export, scalings_relative_to_raw


def _create_empty_zarrays(
    export_path: str,
    export_dtype,
    chunk_shape: Shape,
    export_shape: TaggedShape,
    output_scalings: ScalingsByScaleKey,
) -> Tuple[OrderedDict[str, zarr.Array], OrderedDict[str, ImageMetadata]]:
    pc = PathComponents(export_path)
    external_path = pc.externalPath
    internal_path = pc.internalPath.lstrip("/") if pc.internalPath else None
    store = FSStore(external_path, mode="w", **OME_ZARR_V_0_4_KWARGS)
    zarrays = ODict()
    meta = ODict()
    for scale_key, scaling in output_scalings.items():
        scale_path = f"{internal_path}/{scale_key}" if internal_path else scale_key
        scaled_shape = _scale_tagged_shape(export_shape, scaling).values()
        zarrays[scale_key] = zarr.creation.zeros(
            scaled_shape, store=store, path=scale_path, chunks=chunk_shape, dtype=export_dtype
        )
        meta[scale_key] = ImageMetadata(scale_path, scaling, {})

    return zarrays, meta


def _apply_scaling_method(
    data: numpy.typing.NDArray, current_block_roi: Tuple[List[int], List[int]], scaling: OrderedScaling
) -> Tuple[numpy.typing.NDArray, Tuple[List[int], List[int]]]:
    """Downscaling tbd, need to investigate whether blockwise scaling is feasible.
    May have to restructure the flow instead and potentially do export blockwise, then scaling afterwards."""
    raise NotImplementedError()


def _scale_and_write_block(scales: ScalingsByScaleKey, zarrays: OrderedDict[str, zarr.Array], roi, data):
    assert scales.keys() == zarrays.keys()
    for scale_key_, scaling_ in scales.items():
        if scaling_["x"] > 1.0 or scaling_["y"] > 1.0:
            logger.info(f"Scale {scale_key_}: Applying {scaling_=} to {roi=}")
            scaled_data, scaled_roi = _apply_scaling_method(data, roi, scaling_)
            slicing = roiToSlice(*scaled_roi)
        else:
            slicing = roiToSlice(*roi)
            scaled_data = data
        logger.info(f"Scale {scale_key_}: Writing data with shape={scaled_data.shape} to {slicing=}")
        zarrays[scale_key_][slicing] = scaled_data


def _get_input_raw_absolute_scaling(input_ome_meta: Optional[OMEZarrMultiscaleMeta]) -> Optional[OrderedScaling]:
    input_scale = None
    if input_ome_meta:
        raw_transforms = next(iter(input_ome_meta.dataset_transformations.values()))
        # Spec requires that if any, first must be scale
        if len(raw_transforms) > 0:
            input_scale = raw_transforms[0]
    if input_scale is None or "scale" not in input_scale:
        return None
    return ODict(zip(input_ome_meta.axis_units.keys(), input_scale["scale"]))


def _get_input_dataset_transformations(
    input_ome_meta: Optional[OMEZarrMultiscaleMeta], scale_key: str
) -> Tuple[Optional[OMEZarrCoordinateTransformation], Optional[OMEZarrCoordinateTransformation]]:
    input_scale = None
    input_translation = None
    if input_ome_meta and input_ome_meta.dataset_transformations.get(scale_key):
        input_transforms = input_ome_meta.dataset_transformations[scale_key]
        # Spec requires that if any, first must be scale, second may be translation
        if len(input_transforms) > 0:
            input_scale = input_transforms[0]
        if len(input_transforms) > 1:
            input_translation = input_transforms[1]
    return input_scale, input_translation


def _update_export_scaling_from_input(
    absolute_scaling: OrderedScaling,
    input_ome_meta: Optional[OMEZarrMultiscaleMeta],
    input_scale: Optional[OMEZarrCoordinateTransformation],
    scale_key: str,
) -> OrderedScaling:
    if not input_scale or "scale" not in input_scale:
        return absolute_scaling
    input_scaling = ODict(zip(input_ome_meta.axis_units.keys(), input_scale["scale"]))
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


def _get_datasets_meta(
    multiscale_metadata: OrderedDict[str, ImageMetadata],
    input_ome_meta: Optional[OMEZarrMultiscaleMeta],
    scalings_relative_to_raw_input: Optional[ScalingsByScaleKey],
):
    """
    Dataset metadata consists of (1) path, (2) coordinate transformations (scale and translation).
    By default, scale is just pixel resolution relative to export, i.e. 1.0, 2.0, 4.0 etc. along each scaled axis.
    This gets more complex when the source dataset was multiscale (providing `scalings_relative_to_raw_input`),
    or OME-Zarr (providing `input_ome_meta`).
    """
    datasets = []
    raw_data_abs_scale = _get_input_raw_absolute_scaling(input_ome_meta)
    for scale_key, image in multiscale_metadata.items():
        if scalings_relative_to_raw_input and scale_key in scalings_relative_to_raw_input:
            relative_scaling = scalings_relative_to_raw_input[scale_key]
        else:
            relative_scaling = image.scaling
        # The scaling factors are relative to export or raw data shape now,
        # but the input dataset might contain absolute scale values, i.e. time/pixel resolution
        absolute_scaling = _make_absolute_if_possible(relative_scaling, raw_data_abs_scale)
        input_scale, input_translation = _get_input_dataset_transformations(input_ome_meta, scale_key)
        absolute_scaling = _update_export_scaling_from_input(absolute_scaling, input_ome_meta, input_scale, scale_key)
        dataset = {
            "path": image.path,
            "coordinateTransformations": [{"type": "scale", "scale": list(absolute_scaling.values())}],
        }
        if input_translation and "translation" in input_translation:
            tagged_translation = ODict(zip(input_ome_meta.axis_units.keys(), input_translation["translation"]))
            reordered_translation = [
                tagged_translation[a] if a in tagged_translation and a != "c" else 0.0 for a in image.scaling.keys()
            ]
            dataset["coordinateTransformations"].append({"type": "translation", "translation": reordered_translation})
        datasets.append(dataset)
    return datasets


def _write_ome_zarr_and_ilastik_metadata(
    export_path: str,
    export_meta: OrderedDict[str, ImageMetadata],
    scalings_relative_to_raw_input: Optional[ScalingsByScaleKey],
    input_ome_meta: Optional[OMEZarrMultiscaleMeta],
    ilastik_meta: Dict,
):
    pc = PathComponents(export_path)
    external_path = pc.externalPath
    multiscale_name = pc.internalPath.lstrip("/") if pc.internalPath else None
    ilastik_signature = {"name": "ilastik", "version": ilastik_version, "ome_zarr_exporter_version": 1}
    export_axiskeys = [tag.key for tag in ilastik_meta["axistags"]]

    axes = _get_axes_meta(export_axiskeys, input_ome_meta)
    datasets = _get_datasets_meta(export_meta, input_ome_meta, scalings_relative_to_raw_input)
    ome_zarr_multiscale_meta = {"axes": axes, "datasets": datasets, "version": "0.4"}

    # Optional fields
    if multiscale_name:
        ome_zarr_multiscale_meta["name"] = multiscale_name
    if input_ome_meta and input_ome_meta.multiscale_transformations:
        transforms_axis_matched = []
        for transform in input_ome_meta.multiscale_transformations:
            transform_type = transform["type"]
            tagged_transform = ODict(zip(input_ome_meta.axis_units.keys(), transform[transform_type]))
            default_value = 0.0 if transform_type == "translation" else 1.0
            transforms_axis_matched.append(
                {
                    "type": transform_type,
                    transform_type: [
                        tagged_transform[a] if a in tagged_transform else default_value for a in export_axiskeys
                    ],
                }
            )
        ome_zarr_multiscale_meta["coordinateTransformations"] = transforms_axis_matched

    store = FSStore(external_path, mode="w", **OME_ZARR_V_0_4_KWARGS)
    root = zarr.group(store, overwrite=False)
    root.attrs["_creator"] = ilastik_signature
    root.attrs["multiscales"] = [ome_zarr_multiscale_meta]
    for image in export_meta.values():
        za = zarr.Array(store, path=image.path)
        _write_to_dataset_attrs(ilastik_meta, za)


def write_ome_zarr(
    export_path: str,
    image_source_slot: Slot,
    progress_signal: OrderedSignal,
    compute_downscales: bool = False,
):
    if Path(PathComponents(export_path).externalPath).exists():
        raise FileExistsError(
            "Aborting because export path already exists. Please delete it manually if you intended to overwrite it. "
            "Appending to an existing OME-Zarr store is not yet implemented."
            f"\nPath: {PathComponents(export_path).externalPath}."
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
        input_ome_meta = reordered_source.meta.get("ome_zarr_meta")

        chunk_shape = _get_chunk_shape(export_shape, export_dtype)
        export_scalings, scalings_relative_to_raw_input = _match_or_create_scalings(
            input_scales, export_shape, chunk_shape, compute_downscales
        )
        zarrays, export_meta = _create_empty_zarrays(
            export_path, export_dtype, chunk_shape, export_shape, export_scalings
        )

        requester = BigRequestStreamer(reordered_source, roiFromShape(reordered_source.meta.shape))
        requester.resultSignal.subscribe(partial(_scale_and_write_block, export_scalings, zarrays))
        requester.progressSignal.subscribe(progress_signal)
        requester.execute()

        progress_signal(95)
        _write_ome_zarr_and_ilastik_metadata(
            export_path,
            export_meta,
            scalings_relative_to_raw_input,
            input_ome_meta,
            {
                "axistags": reordered_source.meta.axistags,
                "display_mode": reordered_source.meta.get("display_mode"),
                "drange": reordered_source.meta.get("drange"),
            },
        )
    finally:
        op_reorder.cleanUp()
