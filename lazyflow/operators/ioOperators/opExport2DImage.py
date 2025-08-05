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
import os

import numpy
import tifffile
import vigra

from lazyflow.graph import Operator, InputSlot

from .opExportToArray import OpExportToArray


class OpExport2DImage(Operator):
    """
    Export a 2D image using vigra.impex.writeImage()
    """

    Input = InputSlot()  # Allowed to have more than 2 dimensions as long as the others are singletons.
    Filepath = InputSlot()

    def __init__(self, *args, **kwargs):
        super(OpExport2DImage, self).__init__(*args, **kwargs)
        self._opExportToArray = OpExportToArray(parent=self)
        self._opExportToArray.Input.connect(self.Input)
        self.progressSignal = self._opExportToArray.progressSignal

    def setupOutputs(self):
        # Ask vigra which extensions are supported.
        # If vigra was compiled with libpng, libjpeg, etc.,
        #  then 'png', 'jpeg', etc. will be in this list.
        # Otherwise, they aren't supported.
        extension = os.path.splitext(self.Filepath.value)[1][1:]
        if extension not in vigra.impex.listExtensions().split():
            msg = "Unknown export format: '{}' is not a recognized 2D image extension.".format(extension)
            raise Exception(msg)

    # No Output slots...
    def execute(self, slot, subindex, roi, result):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass

    def run_export(self):
        """
        Requests all of the input and saves the output file.
        SYNCHRONOUSLY.
        """
        # Check for errors...
        tagged_shape = self.Input.meta.getTaggedShape()
        non_singleton_dims = [k_v for k_v in list(tagged_shape.items()) if k_v[0] != "c" and k_v[1] > 1]
        assert len(non_singleton_dims) <= 2, (
            "Image to export must have no more than 2 non-singleton dimensions.\n"
            "You are attempting to export a {}D result into a 2D file format.".format(len(non_singleton_dims))
        )

        data = self._opExportToArray.run_export_to_array()
        data = vigra.taggedView(data, self.Input.meta.axistags)
        data = data.squeeze()
        if len(data.shape) == 1 or len(data.shape) == 2 and data.axistags.channelIndex < 2:
            data = data[numpy.newaxis, :]
        assert len(data.shape) == 2 or (
            len(data.shape) == 3 and data.axistags.channelIndex < 3
        ), "Image has shape {}, channelIndex is {}".format(data.shape, data.axistags.channelIndex)

        vigra.impex.writeImage(data, self.Filepath.value)
        extension = os.path.splitext(self.Filepath.value)[1][1:]

        # now write any pixel sizes
        if (
            extension in ["tif", "tiff"]
            and self.Input.meta.axistags["x"].resolution != 0
            and self.Input.meta.axistags["y"].resolution != 0
        ):
            with tifffile.TiffFile(self.Filepath.value) as tif:
                olddata = tif.asarray()
                data = olddata.squeeze()
                x = None
                y = None
                axes = "YX"
                if tagged_shape["c"] > 1:
                    axes = "CYX"
                if self.Input.meta.axistags["x"].unit != "":
                    x = (self.Input.meta.axistags["x"].unit.encode("unicode_escape").decode("ascii"),)
                if self.Input.meta.axistags["y"].unit != "":
                    y = (self.Input.meta.axistags["y"].unit.encode("unicode_escape").decode("ascii"),)

                imagej_metadata = {
                    "spacing": 1.0,  # this is equal to the z-axis and gets handled differently in non-2d images
                    "unit": x,
                    "yunit": y,
                    "axes": axes,
                }

                tifffile.imwrite(
                    self.Filepath.value,
                    data,
                    imagej=True,
                    metadata=imagej_metadata,
                    resolution=(
                        1 / self.Input.meta.axistags["x"].resolution,
                        1 / self.Input.meta.axistags["y"].resolution,
                    ),
                )


if __name__ == "__main__":
    a = numpy.random.random((1, 100, 1, 100, 1)) * 255
    a = a.astype(numpy.uint8)
    a = vigra.taggedView(a, vigra.defaultAxistags("txyzc"))

    from lazyflow.graph import Graph

    op = OpExport2DImage(graph=Graph())
    op.Input.setValue(a)
    op.Filepath.setValue("/tmp/test.png")

    op.run_export()
