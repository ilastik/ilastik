import logging
from typing import List, Literal

import ngff_zarr
import numpy

from lazyflow.operators import OpReorderAxes
from lazyflow.roi import determineBlockShape, roiToSlice, roiFromShape
from lazyflow.slot import Slot, SlotAsNDArray
from lazyflow.utility import BigRequestStreamer, OrderedSignal, PathComponents
from zarr.storage import FSStore

from lazyflow.utility.io_util.OMEZarrStore import OME_ZARR_V_0_4_KWARGS

logger = logging.getLogger(__name__)


def write_ome_zarr(export_path: str, image_source_slot: Slot, progress_signal: OrderedSignal):
    export_path = PathComponents(export_path)
    op_reorder = OpReorderAxes(parent=image_source_slot.operator)
    op_reorder.AxisOrder.setValue("tczyx")  # OME-Zarr convention
    try:
        op_reorder.Input.connect(image_source_slot)
        dims: List[Literal["t", "c", "z", "y", "x"]] = list(op_reorder.Output.meta.axistags.keys())
        scale = {k: 1.0 for k in dims}
        translation = {k: 0.0 for k in dims}
        image_source = SlotAsNDArray(op_reorder.Output)
        image = ngff_zarr.to_ngff_image(image_source, dims=dims, scale=scale, translation=translation)
        progress_signal(50)

        multiscales = ngff_zarr.to_multiscales(image, scale_factors=2, chunks=64)
        store = FSStore(export_path.externalPath, mode="w", **OME_ZARR_V_0_4_KWARGS)
        ngff_zarr.to_ngff_zarr(store, multiscales)
        print(export_path.externalPath)
        print(multiscales)
    finally:
        op_reorder.cleanUp()
    return
    # h5N5GroupName, datasetName = os.path.split(h5N5Path)
    # if h5N5GroupName == "":
    #     g = self.f
    # else:
    #     if h5N5GroupName in self.f:
    #         g = self.f[h5N5GroupName]
    #     else:
    #         g = self.f.create_group(h5N5GroupName)

    data_shape = image_source_slot.meta.shape
    logger.info(f"Data shape: {data_shape}")

    dtype = image_source_slot.meta.dtype
    if isinstance(dtype, numpy.dtype):
        # Make sure we're dealing with a type (e.g. numpy.float64),
        # not a numpy.dtype
        dtype = dtype.type
    # Set up our chunk shape: Aim for a cube that's roughly 512k in size
    dtypeBytes = dtype().nbytes

    tagged_maxshape = image_source_slot.meta.getTaggedShape()
    if "t" in tagged_maxshape:
        # Assume that chunks should not span multiple t-slices,
        # and channels are often handled separately, too.
        tagged_maxshape["t"] = 1

    if "c" in tagged_maxshape:
        tagged_maxshape["c"] = 1

    chunkShape = determineBlockShape(list(tagged_maxshape.values()), 512_000.0 / dtypeBytes)

    # if datasetName in list(g.keys()):
    #     del g[datasetName]
    kwargs = {"shape": data_shape, "dtype": dtype, "chunks": chunkShape}

    # self.d = g.create_dataset(datasetName, **kwargs)

    progress_signal(0)

    display_mode = image_source_slot.meta.display_mode
    axistags = image_source_slot.meta.axistags.toJSON()
    neuroglancer_axes = "".join(tag.key for tag in image_source_slot.meta.axistags)[::-1]
    drange = image_source_slot.meta.get("drange")

    def handle_block_result(roi, data):
        slicing = roiToSlice(*roi)
        if data.flags.c_contiguous:
            self.d.write_direct(data.view(numpy.ndarray), dest_sel=slicing)
        else:
            self.d[slicing] = data

    requester = BigRequestStreamer(image_source_slot, roiFromShape(data_shape))
    requester.resultSignal.subscribe(handle_block_result)
    requester.progressSignal.subscribe(progress_signal)
    requester.execute()
