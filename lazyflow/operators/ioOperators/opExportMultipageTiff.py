###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
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
import pathlib
import textwrap
import uuid
import xml.etree.ElementTree as ET
from typing import Any, Iterable, Sequence

import numpy as np
import psutil
import tifffile
import vigra

from lazyflow.graph import InputSlot, Operator
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.utility import OrderedSignal, RoiRequestBatch

logger = logging.getLogger(__name__)


class OpExportMultipageTiff(Operator):
    """Export to multi-page OME-TIFF.

    Attributes:
        Input: Image data source (input slot).
        Filepath: Path to the exported image (input slot).
        progressSignal: Subscribe to this signal to receive export progress updates.
    """

    Input = InputSlot()
    Filepath = InputSlot()

    _DEFAULT_BATCH_SIZE = 4
    # OME-TIFF requires 5D with arbitrary order.
    _EXPORT_AXES = "tzcyx"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.progressSignal = OrderedSignal()

        self._opReorderAxes = OpReorderAxes(parent=self)
        self._opReorderAxes.Input.connect(self.Input)
        self._opReorderAxes.AxisOrder.setValue(self._EXPORT_AXES)

        self._page_buf = None

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass

    def run_export(self) -> None:
        """Export an image from Input to Filepath."""
        path = pathlib.Path(self.Filepath.value)
        if path.exists():
            path.unlink()

        self._page_buf = _NdBuf(self._opReorderAxes.Output.meta.shape[:-2])

        batch = RoiRequestBatch(
            outputSlot=self._opReorderAxes.Output,
            roiIterator=_page_rois(*self._opReorderAxes.Output.meta.shape),
            totalVolume=np.prod(self._opReorderAxes.Output.meta.shape),
            batchSize=self._batch_size,
        )
        batch.progressSignal.subscribe(self.progressSignal)
        batch.resultSignal.subscribe(self._write_buffered_pages)
        batch.execute()

    def _write_buffered_pages(self, roi, page) -> None:
        """Store a new page in the buffer and write all in-order buffered pages to the file."""
        page_axes = self._EXPORT_AXES[-2:]
        page = vigra.taggedView(page, self._EXPORT_AXES).withAxes(page_axes)

        page_idx = roi[0][:-2]
        self._page_buf[page_idx] = page

        for i, page in self._page_buf:
            if not i:
                self._write_first_page(page)
            else:
                vigra.impex.writeImage(page, self.Filepath.value, dtype="", compression="NONE", mode="a")

    def _write_first_page(self, page) -> None:
        """Write the first page differently: it needs the OME-XML `ImageDescription` field."""
        dtype = self._opReorderAxes.Output.meta.dtype
        if isinstance(dtype, type):
            dtype = dtype().dtype

        desc = _image_desc_xml(
            dtype=dtype,
            axes=self._opReorderAxes.Output.meta.getAxisKeys(),
            shape=self._opReorderAxes.Output.meta.shape,
            file_uuid=str(uuid.uuid1()),
            file_name=pathlib.Path(self.Filepath.value).name,
        )

        if logger.isEnabledFor(logging.DEBUG):
            import xml.dom.minidom

            pretty_desc = xml.dom.minidom.parseString(desc).toprettyxml()
            logger.debug(f"Generated OME-TIFF metadata:\n{pretty_desc}")

        with tifffile.TiffWriter(self.Filepath.value, software="ilastik", byteorder="<") as writer:
            writer.save(page, description=desc, planarconfig="planar")

    @property
    def _batch_size(self) -> int:
        bytes_per_pixel = self.Input.meta.ram_usage_per_requested_pixel
        if not bytes_per_pixel:
            return self._DEFAULT_BATCH_SIZE

        shape = self._opReorderAxes.Output.meta.shape

        nchannels = self.Input.meta.getTaggedShape().get("c", 1)
        pixels_per_page = np.prod(shape[-2:]) // nchannels
        bytes_per_page = bytes_per_pixel * pixels_per_page

        total_bytes = psutil.virtual_memory().available // 2
        batch_size = total_bytes // bytes_per_page

        npages = np.prod(shape[:-2])
        return min(batch_size, npages)


class _NdBuf:
    """Store ND-indexed items and give them back in the strict ND-ascending order."""

    def __init__(self, shape: Iterable[int]):
        self._items = {}
        self._index = 0
        self._shape = tuple(shape)

    def __setitem__(self, key: Iterable[int], value: Any):
        i = np.ravel_multi_index(key, self._shape)
        self._items[i] = value

    def __iter__(self) -> Iterable[Any]:
        while self._index in self._items:
            i = self._index
            item = self._items.pop(i)
            self._index += 1
            yield i, item


def _page_rois(*shape: int):
    """Yield ROIs matching the TIFF pages from the input image shape."""
    for page_idx in np.ndindex(*shape[:-2]):
        start = page_idx + (0, 0)
        stop = tuple(i + 1 for i in page_idx) + shape[-2:]
        yield start, stop


def _image_desc_xml(*, dtype: np.dtype, axes: Sequence[str], shape: Sequence[int], file_uuid="", file_name="") -> str:
    """Create XML string for the OME-TIFF `ImageDescription` field."""
    ome_types = {
        "B": "uint8",
        "H": "uint16",
        "I": "uint32",
        "b": "int8",
        "h": "int16",
        "i": "int32",
        "f": "float",
        "d": "double",
        "F": "complex",
        "D": "double-complex",
    }
    ome_type = ome_types.get(dtype.char)
    if ome_type is None:
        raise ValueError(f"dtype {dtype.name} does not have a matching OME-XML type")

    if len(axes) != len(shape):
        raise ValueError(f"axes and shape have different lengths: {len(axes)} != {len(shape)}")
    if len(axes) < 2:
        raise ValueError(f"expected at least 2 dimensions, got {len(axes)}")
    # OME-XML uses Fortran order.
    dims = "".join(reversed(axes)).upper()
    sizes = tuple(reversed(shape))

    if file_name and not file_uuid:
        raise ValueError("file_name requires file_uuid")

    ome = ET.Element("OME")
    ome.set("xmlns", "http://www.openmicroscopy.org/Schemas/OME/2015-01")
    ome.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    ome.set(
        "xsi:schemaLocation",
        "http://www.openmicroscopy.org/Schemas/OME/2015-01 "
        "http://www.openmicroscopy.org/Schemas/OME/2015-01/ome.xsd",
    )
    if file_uuid:
        ome.set("UUID", f"urn:uuid:{file_uuid}")

    image = ET.SubElement(ome, "Image")
    image.set("ID", "Image:0")
    image.set("Name", "exported-data")

    pixels = ET.SubElement(image, "Pixels")
    pixels.set("ID", "Pixels:0")
    pixels.set("BigEndian", "true")  # TODO: Figure out what endianness we actually use.
    pixels.set("Type", ome_type)
    pixels.set("DimensionOrder", dims)
    for dim, size in zip(dims, sizes):
        pixels.set(f"Size{dim}", str(size))

    npages = np.prod(sizes[2:])
    for i in range(npages):
        tiff_data = ET.SubElement(pixels, "TiffData")
        tiff_data.set("PlaneCount", "1")
        tiff_data.set("IFD", str(i))

        offsets = ()
        if npages > 1:
            offsets = np.unravel_index(i, sizes[2:], order="F")
        for dim, offset in zip(dims[2:], offsets):
            tiff_data.set(f"First{dim}", str(offset))

        if file_uuid:
            uuid_elem = ET.SubElement(tiff_data, "UUID")
            uuid_elem.text = ome.get("UUID")
            if file_name:
                uuid_elem.set("FileName", file_name)

    header = textwrap.dedent(
        """\
        <?xml version="1.0" encoding="utf-8"?>
        <!-- Warning: this comment is an OME-XML metadata block, which contains
        crucial dimensional parameters and other important metadata. Please edit
        cautiously (if at all), and back up the original data before doing so.
        For more information, see the OME-TIFF documentation:
        https://docs.openmicroscopy.org/latest/ome-model/ome-tiff/ -->
        """
    )
    return header + ET.tostring(ome, encoding="unicode")


if __name__ == "__main__":
    import sys

    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)

    from lazyflow.graph import Graph
    from lazyflow.operators.ioOperators import OpTiffReader

    graph = Graph()
    opReader = OpTiffReader(graph=graph)
    opReader.Filepath.setValue("/tmp/xyz.ome.tiff")

    opWriter = OpExportMultipageTiff(graph=graph)
    opWriter.Filepath.setValue("/tmp/xyz-converted.ome.tiff")
    opWriter.Input.connect(opReader.Output)

    opWriter.run_export()
    print("DONE.")
