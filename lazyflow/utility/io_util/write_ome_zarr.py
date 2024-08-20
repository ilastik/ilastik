import logging
from typing import List, Literal, Optional, Tuple

import ngff_zarr
import numpy
import zarr
from zarr.storage import FSStore

from lazyflow.operators import OpReorderAxes
from lazyflow.roi import determineBlockShape
from lazyflow.slot import Slot, SlotAsNDArray
from lazyflow.utility import OrderedSignal, PathComponents
from lazyflow.utility.io_util.OMEZarrStore import OME_ZARR_V_0_4_KWARGS

logger = logging.getLogger(__name__)


def _get_chunk_shape(image_source_slot) -> Tuple[int, ...]:
    """Determine chunk shape for OME-Zarr storage based on image source slot.
    Chunk size is 1 for t and c, and determined by ilastik default rules for zyx, with a target of 512KB per chunk."""
    dtype = image_source_slot.meta.dtype
    if isinstance(dtype, numpy.dtype):  # Extract raw type class
        dtype = dtype.type
    dtype_bytes = dtype().nbytes
    tagged_maxshape = image_source_slot.meta.getTaggedShape()
    tagged_maxshape["t"] = 1
    tagged_maxshape["c"] = 1
    chunk_shape = determineBlockShape(list(tagged_maxshape.values()), 512_000.0 / dtype_bytes)
    return chunk_shape


def write_ome_zarr(
    export_path: str,
    image_source_slot: Slot,
    progress_signal: OrderedSignal,
    downscale_method: Optional[ngff_zarr.methods.Methods] = None,
):
    pc = PathComponents(export_path)
    external_path = pc.externalPath
    internal_path = pc.internalPath

    op_reorder = OpReorderAxes(parent=image_source_slot.operator)
    op_reorder.AxisOrder.setValue("tczyx")  # OME-Zarr convention
    try:
        op_reorder.Input.connect(image_source_slot)
        image_source = SlotAsNDArray(op_reorder.Output)
        chunk_shape = _get_chunk_shape(op_reorder.Output)
        dims: List[Literal["t", "c", "z", "y", "x"]] = list(op_reorder.Output.meta.axistags.keys())
        scale = {k: 1.0 for k in dims}
        translation = {k: 0.0 for k in dims}
        image = ngff_zarr.to_ngff_image(
            image_source, name=internal_path or "image", dims=dims, scale=scale, translation=translation
        )
        progress_signal(25)
        multiscales = ngff_zarr.to_multiscales(image, scale_factors=2, chunks=chunk_shape, method=downscale_method)
        progress_signal(50)
        store = FSStore(external_path, mode="w", **OME_ZARR_V_0_4_KWARGS)
        ngff_zarr.to_ngff_zarr(store, multiscales, overwrite=False)
        # Write ilastik metadata
        for image in multiscales.images:
            # ngff-zarr does not record the storage path in the image object, so we have to look it up.
            # The only way we can know that a metadata entry corresponds to this image is the scale factor.
            dataset = None
            for d in multiscales.metadata.datasets:
                scale_transforms = [t for t in d.coordinateTransformations if t.type == "scale"]
                dataset_scale_factors = scale_transforms[0].scale  # Should only be one
                if all(image_scale_factor in dataset_scale_factors for image_scale_factor in image.scale.values()):
                    dataset = d
                    break
            assert dataset is not None, f"Could not find metadata for image, must be an error in to_ngff_zarr. {image=}"
            za = zarr.Array(store, path=dataset.path)
            za.attrs["axistags"] = op_reorder.Output.meta.axistags.toJSON()
            za.attrs["display_mode"] = image_source_slot.meta.display_mode
            za.attrs["drange"] = image_source_slot.meta.get("drange")
    finally:
        op_reorder.cleanUp()
