import dataclasses
import logging
from functools import partial
from typing import List, Tuple, Dict, Optional, OrderedDict

import numpy
import zarr
from zarr.storage import FSStore

from ilastik import __version__ as ilastik_version
from lazyflow.operators import OpReorderAxes
from lazyflow.roi import determineBlockShape, roiFromShape, roiToSlice
from lazyflow.slot import Slot
from lazyflow.utility import OrderedSignal, PathComponents, BigRequestStreamer
from lazyflow.utility.io_util.OMEZarrStore import OME_ZARR_V_0_4_KWARGS

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ImageMetadata:
    path: str
    scale: Dict[str, float]
    translation: Dict[str, float]


def _get_chunk_shape(image_source_slot: Slot) -> Tuple[int, ...]:
    """Determine chunk shape for OME-Zarr storage based on image source slot.
    Chunk size is 1 for t and c, and determined by ilastik default rules for zyx, with a target of 512KB per chunk."""
    dtype = image_source_slot.meta.dtype
    if isinstance(dtype, numpy.dtype):  # Extract raw type class
        dtype = dtype.type
    dtype_bytes = dtype().nbytes
    tagged_maxshape = image_source_slot.meta.getTaggedShape()
    tagged_maxshape["t"] = 1
    tagged_maxshape["c"] = 1
    chunk_shape = determineBlockShape(list(tagged_maxshape.values()), 512_000.0 / dtype_bytes)  # 512KB chunk size
    return chunk_shape


def _get_scalings(
    original_tagged_shape: OrderedDict[str, int], chunk_shape: Tuple[int, ...], min_length: Optional[int]
) -> List[Dict[str, float]]:
    """
    Computes scaling "factors".
    Technically they are divisors for the shape (factor 2.0 means half the shape).
    Downscaling is done by a factor of 2 in all spatial dimensions until:
    - the dataset would be less than 4 x chunk size (2MiB)
    - an axis that started non-singleton would become singleton
    - the largest axis would be smaller than min_length (if defined).
    Returns list of scaling factor dicts by axis, starting with original scale.
    The scaling level that meets one of the exit conditions is excluded.
    Raises if more than 20 scales are computed (sanity).
    """
    assert len(chunk_shape) == len(original_tagged_shape), "Chunk shape and tagged shape must have same length"
    spatial = ["z", "y", "x"]
    original_scale = {a: 1.0 for a in original_tagged_shape.keys()}
    scalings = [original_scale]
    sanity_limit = 20
    for i in range(sanity_limit):
        if i == sanity_limit:
            raise ValueError(f"Too many scales computed, limit={sanity_limit}. Please report this to the developers.")
        previous_scaling = scalings[-1]
        new_scaling = {
            a: s * 2.0 if a in spatial and original_tagged_shape[a] > 1 else 1.0 for a, s in previous_scaling.items()
        }
        new_shape = _get_scaled_slot_shape(original_tagged_shape, new_scaling)
        if (
            _is_less_than_4_chunks(new_shape, chunk_shape)
            or _reduces_any_axis_to_singleton(new_shape, tuple(original_tagged_shape.values()))
            or (min_length and max(new_shape) < min_length)
        ):
            break
        scalings.append(new_scaling)
    return scalings


def _reduces_any_axis_to_singleton(new_shape: Tuple[int, ...], original_shape: Tuple[int, ...]):
    return any(new <= 1 < orig for new, orig in zip(new_shape, original_shape))


def _is_less_than_4_chunks(new_shape: Tuple[int, ...], chunk_shape: Tuple[int, ...]):
    return numpy.prod(new_shape) < 4 * numpy.prod(chunk_shape)


def _get_scaled_slot_shape(
    original_tagged_shape: OrderedDict[str, int], new_scaling: Dict[str, float]
) -> Tuple[int, ...]:
    assert all(s > 0 for s in new_scaling.values()), f"Invalid scaling: {new_scaling}"
    return tuple(int(s // new_scaling[a]) if a in new_scaling else s for a, s in original_tagged_shape.items())


def _compute_and_write_scales(
    export_path: str, image_source_slot: Slot, progress_signal: OrderedSignal, min_length: Optional[int]
) -> List[ImageMetadata]:
    pc = PathComponents(export_path)
    external_path = pc.externalPath
    internal_path = pc.internalPath
    store = FSStore(external_path, mode="w", **OME_ZARR_V_0_4_KWARGS)
    chunk_shape = _get_chunk_shape(image_source_slot)
    scalings = _get_scalings(image_source_slot.meta.getTaggedShape(), chunk_shape, min_length)
    meta = []

    for i, scaling in enumerate(scalings):
        scale_path = f"{internal_path}/s{i}" if internal_path else f"s{i}"
        scaled_shape = _get_scaled_slot_shape(image_source_slot.meta.getTaggedShape(), scaling)
        zarray = zarr.creation.empty(
            scaled_shape, store=store, path=scale_path, chunks=chunk_shape, dtype=image_source_slot.meta.dtype
        )

        def scale_and_write_block(scale_index, scaling_, zarray_, roi, data):
            if scale_index > 0:
                logger.info(f"Scale {scale_index}: Applying {scaling_=} to {roi=}")
            slicing = roiToSlice(*roi)
            logger.info(f"Scale {scale_index}: Writing to {slicing=}: {data=}")
            zarray_[slicing] = data

        requester = BigRequestStreamer(image_source_slot, roiFromShape(image_source_slot.meta.shape))
        requester.resultSignal.subscribe(partial(scale_and_write_block, i, scaling, zarray))
        requester.progressSignal.subscribe(progress_signal)
        requester.execute()

        meta.append(ImageMetadata(scale_path, scaling, {}))

    return meta


def _write_ome_zarr_and_ilastik_metadata(
    export_path: str, multiscale_metadata: List[ImageMetadata], ilastik_meta: Dict
):
    pc = PathComponents(export_path)
    external_path = pc.externalPath
    multiscale_name = pc.internalPath
    ilastik_signature = {"name": "ilastik", "version": ilastik_version, "ome_zarr_exporter_version": 1}
    axis_types = {"t": "time", "c": "channel", "z": "space", "y": "space", "x": "space"}
    axes = [{"name": tag.key, "type": axis_types[tag.key]} for tag in ilastik_meta["axistags"]]
    datasets = [
        {
            "path": image.path,
            "coordinateTransformations": [
                {"type": "scale", "scale": [image.scale[tag.key] for tag in ilastik_meta["axistags"]]}
            ],
        }
        for image in multiscale_metadata
    ]
    ome_zarr_multiscale_meta = {"_creator": ilastik_signature, "version": "0.4", "axes": axes, "datasets": datasets}
    if multiscale_name:
        ome_zarr_multiscale_meta["name"] = multiscale_name
    store = FSStore(external_path, mode="w", **OME_ZARR_V_0_4_KWARGS)
    root = zarr.group(store, overwrite=False)
    root.attrs["multiscales"] = [ome_zarr_multiscale_meta]
    for image in multiscale_metadata:
        za = zarr.Array(store, path=image.path)
        za.attrs["axistags"] = ilastik_meta["axistags"].toJSON()
        if ilastik_meta["display_mode"]:
            za.attrs["display_mode"] = ilastik_meta["display_mode"]
        if ilastik_meta["drange"]:
            za.attrs["drange"] = ilastik_meta["drange"]


def write_ome_zarr(
    export_path: str,
    image_source_slot: Slot,
    progress_signal: OrderedSignal,
    min_length: Optional[int] = None,
):
    op_reorder = OpReorderAxes(parent=image_source_slot.operator)
    op_reorder.AxisOrder.setValue("tczyx")
    try:
        op_reorder.Input.connect(image_source_slot)
        image_source = op_reorder.Output
        progress_signal(25)
        ome_zarr_meta = _compute_and_write_scales(export_path, image_source, progress_signal, min_length)
        progress_signal(95)
        _write_ome_zarr_and_ilastik_metadata(
            export_path,
            ome_zarr_meta,
            {
                "axistags": op_reorder.Output.meta.axistags,
                "display_mode": image_source_slot.meta.get("display_mode"),
                "drange": image_source_slot.meta.get("drange"),
            },
        )
    finally:
        op_reorder.cleanUp()
