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
from __future__ import division
from builtins import zip
from builtins import range
import os
import math
import logging
import glob
import h5py
import z5py
from collections import OrderedDict

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

import psutil

import numpy
import vigra

from lazyflow.graph import OrderedSignal, Operator, OutputSlot, InputSlot
from lazyflow.roi import roiToSlice, roiFromShape, determineBlockShape
from lazyflow.utility.bigRequestStreamer import BigRequestStreamer


class OpImageReader(Operator):
    """
    Read an image using vigra.impex.readImage().
    Supports 2D images (output as xyc) and also multi-page tiffs (output as zyxc).
    """

    Filename = InputSlot(stype="filestring")
    Image = OutputSlot()

    def setupOutputs(self):
        filename = self.Filename.value

        info = vigra.impex.ImageInfo(filename)
        assert [tag.key for tag in info.getAxisTags()] == ["x", "y", "c"]

        shape_xyc = info.getShape()
        shape_yxc = (shape_xyc[1], shape_xyc[0], shape_xyc[2])

        self.Image.meta.dtype = info.getDtype()
        self.Image.meta.prefer_2d = True

        numImages = vigra.impex.numberImages(filename)
        if numImages == 1:
            # For 2D, we use order yxc.
            self.Image.meta.shape = shape_yxc
            v_tags = info.getAxisTags()
            self.Image.meta.axistags = vigra.AxisTags([v_tags[k] for k in "yxc"])
        else:
            # For 3D, we use zyxc
            # Insert z-axis shape
            shape_zyxc = (numImages,) + shape_yxc
            self.Image.meta.shape = shape_zyxc

            # Insert z tag
            z_tag = vigra.defaultAxistags("z")[0]
            tags_xyc = [tag for tag in info.getAxisTags()]
            tags_zyxc = [z_tag] + list(reversed(tags_xyc[:-1])) + tags_xyc[-1:]
            self.Image.meta.axistags = vigra.AxisTags(tags_zyxc)

    def execute(self, slot, subindex, rroi, result):
        filename = self.Filename.value

        if "z" in self.Image.meta.getAxisKeys():
            # Copy from each image slice into the corresponding slice of the result.
            roi_zyxc = numpy.array([rroi.start, rroi.stop])
            for z_global, z_result in zip(list(range(*roi_zyxc[:, 0])), list(range(result.shape[0]))):
                full_slice = vigra.impex.readImage(filename, index=z_global)
                full_slice = full_slice.transpose(1, 0, 2)  # xyc -> yxc
                assert full_slice.shape == self.Image.meta.shape[1:]
                result[z_result] = full_slice[roiToSlice(*roi_zyxc[:, 1:])]
        else:
            full_slice = vigra.impex.readImage(filename).transpose(1, 0, 2)  # xyc -> yxc
            assert full_slice.shape == self.Image.meta.shape
            roi_yxc = numpy.array([rroi.start, rroi.stop])
            result[:] = full_slice[roiToSlice(*roi_yxc)]
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Filename:
            self.Image.setDirty()
        else:
            assert False, "Unknown dirty input slot."


class OpStackLoader(Operator):
    """Imports an image stack.

    Note: This operator does NOT cache the images, so direct access
          via the execute() function is very inefficient, especially
          through the Z-axis. Typically, you'll want to connect this
          operator to a cache whose block size is large in the X-Y
          plane.

    :param globstring: A glob string as defined by the glob module. We
        also support the following special extension to globstring
        syntax: A single string can hold a *list* of globstrings.
        The delimiter that separates the globstrings in the list is
        OS-specific via os.path.pathsep.

        For example, on Linux the pathsep is':', so

            '/a/b/c.txt:/d/e/f.txt:../g/i/h.txt'

        is parsed as

            ['/a/b/c.txt', '/d/e/f.txt', '../g/i/h.txt']

    """

    name = "Image Stack Reader"
    category = "Input"

    globstring = InputSlot()
    SequenceAxis = InputSlot(optional=True)
    stack = OutputSlot()

    class FileOpenError(Exception):
        def __init__(self, filename):
            self.filename = filename
            self.msg = f"Unable to open file: {filename}"
            super().__init__(self.msg)

    def setupOutputs(self):
        self.fileNameList = self.expandGlobStrings(self.globstring.value)

        num_files = len(self.fileNameList)
        if len(self.fileNameList) == 0:
            self.stack.meta.NOTREADY = True
            return
        try:
            self.info = vigra.impex.ImageInfo(self.fileNameList[0])
            self.slices_per_file = vigra.impex.numberImages(self.fileNameList[0])
        except RuntimeError as e:
            logger.error(str(e))
            raise OpStackLoader.FileOpenError(self.fileNameList[0]) from e

        slice_shape = self.info.getShape()
        X, Y, C = slice_shape
        if self.slices_per_file == 1:
            if self.SequenceAxis.ready():
                sequence_axis = str(self.SequenceAxis.value)
                assert sequence_axis in "tzc"
            else:
                sequence_axis = "z"
            # For stacks of 2D images, we assume xy slices
            if sequence_axis == "c":
                shape = (X, Y, C * num_files)
                axistags = vigra.defaultAxistags("xyc")
            else:
                shape = (num_files, Y, X, C)
                axistags = vigra.defaultAxistags(sequence_axis + "yxc")
        else:
            if self.SequenceAxis.ready():
                sequence_axis = self.SequenceAxis.value
                assert sequence_axis in "tzc"
            else:
                sequence_axis = "t"

            if sequence_axis == "z":
                axistags = vigra.defaultAxistags("ztyxc")
            elif sequence_axis == "t":
                axistags = vigra.defaultAxistags("tzyxc")
            else:
                axistags = vigra.defaultAxistags("czyx")

            # For stacks of 3D volumes, we assume xyz blocks stacked along
            # sequence_axis
            if sequence_axis == "c":
                shape = (num_files * C, self.slices_per_file, Y, X)
            else:
                shape = (num_files, self.slices_per_file, Y, X, C)

        self.stack.meta.shape = shape
        self.stack.meta.axistags = axistags
        self.stack.meta.dtype = self.info.getDtype()

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.globstring
        # Any change to the globstring means our entire output is dirty.
        self.stack.setDirty()

    def execute(self, slot, subindex, roi, result):
        if len(self.stack.meta.shape) == 3:
            return self._execute_3d(roi, result)
        elif len(self.stack.meta.shape) == 4:
            return self._execute_4d(roi, result)
        elif len(self.stack.meta.shape) == 5:
            return self._execute_5d(roi, result)
        else:
            assert False, f"Unexpected output shape: {self.stack.meta.shape}"

    def _execute_3d(self, roi, result):
        traceLogger.debug("OpStackLoader: Execute for: " + str(roi))
        # roi is in xyc order; stacking over c
        x_start, y_start, c_start = roi.start
        x_stop, y_stop, c_stop = roi.stop

        # get C of slice
        C = self.info.getShape()[2]

        # Copy each c-slice one at a time.
        for i, fileName in enumerate(self.fileNameList[c_start // C : c_stop // C]):
            traceLogger.debug(f"Reading image: {fileName}")
            file_shape = vigra.impex.ImageInfo(fileName).getShape()
            if self.info.getShape() != file_shape:
                raise RuntimeError("not all files have the same shape")
            images_per_file = vigra.impex.numberImages(self.fileNameList[0])
            if self.slices_per_file != images_per_file:
                raise RuntimeError("Not all files have the same number of " "slices")

            result[:, :, i * C : (i + 1) * C] = vigra.impex.readImage(fileName)[
                x_start:x_stop, y_start:y_stop, :
            ].withAxes(*"xyc")
        return result

    def _execute_4d(self, roi, result):
        traceLogger.debug("OpStackLoader: Execute for: " + str(roi))
        # roi is in zyxc, tyxc or czyx order, depending on SequenceAxis
        z_start, y_start, x_start, c_start = roi.start
        z_stop, y_stop, x_stop, c_stop = roi.stop

        # get C of slice
        C = self.info.getShape()[2]

        # Copy each z-slice one at a time.
        for result_z, fileName in enumerate(self.fileNameList[z_start:z_stop]):
            traceLogger.debug(f"Reading image: {fileName}")
            file_shape = vigra.impex.ImageInfo(fileName).getShape()
            if self.info.getShape() != file_shape:
                raise RuntimeError("not all files have the same shape")
            images_per_file = vigra.impex.numberImages(self.fileNameList[0])
            if self.slices_per_file != images_per_file:
                raise RuntimeError("Not all files have the same number of " "slices")

            if self.stack.meta.axistags.channelIndex == 0:
                # czyx order -> read slice along z (here y)
                for result_y, y in enumerate(range(y_start, y_stop)):
                    result[result_z * C : (result_z + 1) * C, result_y, ...] = vigra.impex.readImage(fileName, index=y)[
                        c_start:c_stop, x_start:x_stop
                    ].withAxes(*"cyx")
            else:
                result[result_z, ...] = vigra.impex.readImage(fileName)[
                    x_start:x_stop, y_start:y_stop, c_start:c_stop
                ].withAxes(*"yxc")
        return result

    def _execute_5d(self, roi, result):
        # Technically, t and z might be switched depending on SequenceAxis.
        # Beware these variable names for t/z might be misleading.
        t_start, z_start, y_start, x_start, c_start = roi.start
        t_stop, z_stop, y_stop, x_stop, c_stop = roi.stop

        # Use *enumerated* range to get global t coords and result t coords
        for result_t, t in enumerate(range(t_start, t_stop)):
            file_name = self.fileNameList[t]
            for result_z, z in enumerate(range(z_start, z_stop)):
                img = vigra.readImage(file_name, index=z)
                result[result_t, result_z, :, :, :] = img[x_start:x_stop, y_start:y_stop, c_start:c_stop].withAxes(
                    *"yxc"
                )
        return result

    @staticmethod
    def expandGlobStrings(globStrings):
        ret = []
        # Parse list into separate globstrings and combine them
        for globString in globStrings.split(os.path.pathsep):
            s = globString.strip()
            ret += sorted(glob.glob(s))
        return ret


class OpStackWriter(Operator):
    name = "Stack File Writer"
    category = "Output"

    Input = InputSlot()  # The last two non-singleton axes (except 'c') are the axes of the slices.
    # Re-order the axes yourself if you want an alternative slicing direction

    FilepathPattern = InputSlot()  # A complete filepath including a {slice_index} member and a valid file extension.
    SliceIndexOffset = InputSlot(value=0)  # Added to the {slice_index} in the export filename.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()

    def run_export(self):
        """
        Request the volume in slices (running in parallel), and write each slice to a separate image.
        """
        # Make the directory first if necessary
        export_dir = os.path.split(self.FilepathPattern.value)[0]
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        # Sliceshape is the same as the input shape, except for the sliced dimension
        tagged_sliceshape = self.Input.meta.getTaggedShape()
        tagged_sliceshape[self._volume_axes[0]] = 1
        slice_shape = list(tagged_sliceshape.values())

        parallel_requests = 4

        # If ram usage info is available, make a better guess about how many requests we can launch in parallel
        ram_usage_per_requested_pixel = self.Input.meta.ram_usage_per_requested_pixel
        if ram_usage_per_requested_pixel is not None:
            pixels_per_slice = numpy.prod(slice_shape)
            if "c" in tagged_sliceshape:
                pixels_per_slice //= tagged_sliceshape["c"]

            ram_usage_per_slice = pixels_per_slice * ram_usage_per_requested_pixel

            # Fudge factor: Reduce RAM usage by a bit
            available_ram = psutil.virtual_memory().available
            available_ram *= 0.5

            parallel_requests = int(available_ram // ram_usage_per_slice)

            if parallel_requests < 1:
                raise MemoryError(
                    "Not enough RAM to export to the selected format. " "Consider exporting to hdf5 (h5)."
                )

        streamer = BigRequestStreamer(self.Input, roiFromShape(self.Input.meta.shape), slice_shape, parallel_requests)

        # Write the slices as they come in (possibly out-of-order, but probably not)
        streamer.resultSignal.subscribe(self._write_slice)
        streamer.progressSignal.subscribe(self.progressSignal)

        logger.debug(f"Starting Stack Export with slicing shape: {slice_shape}")
        streamer.execute()

    def setupOutputs(self):
        # If stacking XY images in Z-steps,
        #  then self._volume_axes = 'zxy'
        self._volume_axes = self.get_nonsingleton_axes()
        step_axis = self._volume_axes[0]
        max_slice = self.SliceIndexOffset.value + self.Input.meta.getTaggedShape()[step_axis]
        self._max_slice_digits = int(math.ceil(math.log10(max_slice + 1)))

        # Check for errors
        assert len(self._volume_axes) == 3 or len(self._volume_axes) == 4 and "c" in self._volume_axes[1:], (
            "Exported stacks must have exactly 3 non-singleton dimensions (other than the channel dimension).  "
            "Your stack dimensions are: {}".format(self.Input.meta.getTaggedShape())
        )

        # Test to make sure the filepath pattern includes slice index field
        filepath_pattern = self.FilepathPattern.value
        assert "123456789" in filepath_pattern.format(slice_index=123_456_789), (
            "Output filepath pattern must contain the '{{slice_index}}' field for formatting.\n"
            "Your format was: {}".format(filepath_pattern)
        )

    # No output slots...
    def execute(self, slot, subindex, roi, result):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass

    def get_nonsingleton_axes(self):
        return self.get_nonsingleton_axes_for_tagged_shape(self.Input.meta.getTaggedShape())

    @classmethod
    def get_nonsingleton_axes_for_tagged_shape(self, tagged_shape):
        # Find the non-singleton axes.
        # The first non-singleton axis is the step axis.
        # The last 2 non-channel non-singleton axes will be the axes of the slices.
        tagged_items = list(tagged_shape.items())
        filtered_items = [k_v for k_v in tagged_items if k_v[1] > 1]
        filtered_axes = list(zip(*filtered_items))[0]
        return filtered_axes

    def _write_slice(self, roi, slice_data):
        """
        Write the data from the given roi into a slice image.
        """
        step_axis = self._volume_axes[0]
        input_axes = self.Input.meta.getAxisKeys()
        tagged_roi = OrderedDict(list(zip(input_axes, list(zip(*roi)))))
        # e.g. tagged_roi={ 'x':(0,1), 'y':(3,4), 'z':(10,20) }
        assert tagged_roi[step_axis][1] - tagged_roi[step_axis][0] == 1, "Expected roi to be a single slice."
        slice_index = tagged_roi[step_axis][0] + self.SliceIndexOffset.value
        filepattern = self.FilepathPattern.value

        # If the user didn't provide custom formatting for the slice field,
        #  auto-format to include zero-padding
        if "{slice_index}" in filepattern:
            filepattern = filepattern.format(slice_index="{" + "slice_index:0{}".format(self._max_slice_digits) + "}")
        formatted_path = filepattern.format(slice_index=slice_index)

        squeezed_data = slice_data.squeeze()
        squeezed_data = vigra.taggedView(squeezed_data, vigra.defaultAxistags("".join(self._volume_axes[1:])))
        assert len(squeezed_data.shape) == len(self._volume_axes) - 1

        # logger.debug( "Writing slice image for roi: {}".format( roi ) )
        logger.debug("Writing slice: {}".format(formatted_path))
        vigra.impex.writeImage(squeezed_data, formatted_path)


class OpStackToH5Writer(Operator):
    name = "OpStackToH5Writer"
    category = "IO"

    GlobString = InputSlot(stype="globstring")
    hdf5Group = InputSlot(stype="object")
    hdf5Path = InputSlot(stype="string")

    # Requesting the output induces the copy from stack to h5 file.
    WriteImage = OutputSlot(stype="bool")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
        self.opStackLoader = OpStackLoader(parent=self)
        self.opStackLoader.globstring.connect(self.GlobString)

    def setupOutputs(self):
        self.WriteImage.meta.shape = (1,)
        self.WriteImage.meta.dtype = object

    def propagateDirty(self, slot, subindex, roi):
        # Any change to our inputs means we're dirty
        assert slot == self.GlobString or slot == self.hdf5Group or slot == self.hdf5Path
        self.WriteImage.setDirty(slice(None))

    def execute(self, slot, subindex, roi, result):
        if not self.opStackLoader.fileNameList:
            raise Exception(
                f"Didn't find any files to combine.  Is the glob string valid?  "
                f"globstring = {self.GlobString.value}"
            )

        # Copy the data image-by-image
        stackTags = self.opStackLoader.stack.meta.axistags
        zAxis = stackTags.index("z")
        dataShape = self.opStackLoader.stack.meta.shape
        numImages = self.opStackLoader.stack.meta.shape[zAxis]
        axistags = self.opStackLoader.stack.meta.axistags
        dtype = self.opStackLoader.stack.meta.dtype
        if isinstance(dtype, numpy.dtype):
            # Make sure we're dealing with a type (e.g. numpy.float64),
            #  not a numpy.dtype
            dtype = dtype.type

        index_ = axistags.index("c")
        if index_ >= len(dataShape):
            numChannels = 1
        else:
            numChannels = dataShape[index_]

        # Set up our chunk shape: Aim for a cube that's roughly 300k in size
        dtypeBytes = dtype().nbytes
        cubeDim = math.pow(300_000 // (numChannels * dtypeBytes), (1 / 3.0))
        cubeDim = int(cubeDim)

        chunkDims = {}
        chunkDims["t"] = 1
        chunkDims["x"] = cubeDim
        chunkDims["y"] = cubeDim
        chunkDims["z"] = cubeDim
        chunkDims["c"] = numChannels

        # h5py guide to chunking says chunks of 300k or less "work best"
        assert chunkDims["x"] * chunkDims["y"] * chunkDims["z"] * numChannels * dtypeBytes <= 300_000

        chunkShape = ()
        for i in range(len(dataShape)):
            axisKey = axistags[i].key
            # Chunk shape can't be larger than the data shape
            chunkShape += (min(chunkDims[axisKey], dataShape[i]),)

        # Create the dataset
        internalPath = self.hdf5Path.value
        internalPath = internalPath.replace("\\", "/")  # Windows fix
        group = self.hdf5Group.value
        if internalPath in group:
            del group[internalPath]

        data = group.create_dataset(
            internalPath,
            # compression='gzip',
            # compression_opts=4,
            shape=dataShape,
            dtype=dtype,
            chunks=chunkShape,
        )
        # Now copy each image
        self.progressSignal(0)

        for z in range(numImages):
            # Ask for an entire z-slice (exactly one whole image from the stack)
            slicing = [slice(None)] * len(stackTags)
            slicing[zAxis] = slice(z, z + 1)
            data[tuple(slicing)] = self.opStackLoader.stack[slicing].wait()
            self.progressSignal(z * 100 // numImages)

        data.attrs["axistags"] = axistags.toJSON()

        # We're done
        result[...] = True

        self.progressSignal(100)

        return result


class OpH5N5WriterBigDataset(Operator):
    name = "H5 and N5 File Writer BigDataset"
    category = "Output"

    h5N5File = InputSlot()  # Must be an already-open hdf5File/n5File (or group) for writing to
    h5N5Path = InputSlot()
    Image = InputSlot()
    # h5py uses single-threaded gzip comression, which really slows down export.
    CompressionEnabled = InputSlot(value=False)
    BatchSize = InputSlot(optional=True)

    WriteImage = OutputSlot()

    loggingName = __name__ + ".OpH5N5WriterBigDataset"
    logger = logging.getLogger(loggingName)
    traceLogger = logging.getLogger("TRACE." + loggingName)

    def __init__(
        self,
        h5N5File=None,
        h5N5Path=None,
        Image=None,
        BatchSize: int = None,
        CompressionEnabled: bool = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.progressSignal = OrderedSignal()
        self.d = None
        self.f = None

        self.h5N5File.setOrConnectIfAvailable(h5N5File)
        self.h5N5Path.setOrConnectIfAvailable(h5N5Path)
        self.Image.setOrConnectIfAvailable(Image)
        self.BatchSize.setOrConnectIfAvailable(BatchSize)
        self.CompressionEnabled.setOrConnectIfAvailable(CompressionEnabled)

    def cleanUp(self):
        super().cleanUp()
        # Discard the reference to the dataset, to ensure that the file can be closed.
        self.d = None
        self.f = None
        self.progressSignal.clean()

    def setupOutputs(self):
        self.outputs["WriteImage"].meta.shape = (1,)
        self.outputs["WriteImage"].meta.dtype = object

        self.f = self.inputs["h5N5File"].value
        h5N5Path = self.inputs["h5N5Path"].value

        # On windows, there may be backslashes.
        h5N5Path = h5N5Path.replace("\\", "/")

        h5N5GroupName, datasetName = os.path.split(h5N5Path)
        if h5N5GroupName == "":
            g = self.f
        else:
            if h5N5GroupName in self.f:
                g = self.f[h5N5GroupName]
            else:
                g = self.f.create_group(h5N5GroupName)

        dataShape = self.Image.meta.shape
        self.logger.info(f"Data shape: {dataShape}")

        dtype = self.Image.meta.dtype
        if isinstance(dtype, numpy.dtype):
            # Make sure we're dealing with a type (e.g. numpy.float64),
            # not a numpy.dtype
            dtype = dtype.type
        # Set up our chunk shape: Aim for a cube that's roughly 512k in size
        dtypeBytes = dtype().nbytes

        tagged_maxshape = self.Image.meta.getTaggedShape()
        if "t" in tagged_maxshape:
            # Assume that chunks should not span multiple t-slices,
            # and channels are often handled separately, too.
            tagged_maxshape["t"] = 1

        if "c" in tagged_maxshape:
            tagged_maxshape["c"] = 1

        self.chunkShape = determineBlockShape(list(tagged_maxshape.values()), 512_000.0 / dtypeBytes)

        if datasetName in list(g.keys()):
            del g[datasetName]
        kwargs = {"shape": dataShape, "dtype": dtype, "chunks": self.chunkShape}
        if self.CompressionEnabled.value:
            kwargs["compression"] = "gzip"  # <-- Would be nice to use lzf compression here, but that is h5py-specific.
            if isinstance(self.f, h5py.File):
                kwargs["compression_opts"] = 1  # <-- Optimize for speed, not disk space.
            else:  # z5py has uses different names here
                kwargs["level"] = 1  # <-- Optimize for speed, not disk space.
        else:
            if isinstance(self.f, z5py.N5File):  # n5 uses gzip level 5 as default compression.
                kwargs["compression"] = "raw"

        self.d = g.create_dataset(datasetName, **kwargs)

        if self.Image.meta.drange is not None:
            self.d.attrs["drange"] = self.Image.meta.drange
        if self.Image.meta.display_mode is not None:
            self.d.attrs["display_mode"] = self.Image.meta.display_mode

    def execute(self, slot, subindex, rroi, result):
        self.progressSignal(0)

        # Save the axistags as a dataset attribute
        self.d.attrs["axistags"] = self.Image.meta.axistags.toJSON()

        def handle_block_result(roi, data):
            slicing = roiToSlice(*roi)
            if data.flags.c_contiguous:
                self.d.write_direct(data.view(numpy.ndarray), dest_sel=slicing)
            else:
                self.d[slicing] = data

        batch_size = None
        if self.BatchSize.ready():
            batch_size = self.BatchSize.value
        requester = BigRequestStreamer(self.Image, roiFromShape(self.Image.meta.shape), batchSize=batch_size)
        requester.resultSignal.subscribe(handle_block_result)
        requester.progressSignal.subscribe(self.progressSignal)
        requester.execute()

        # Be paranoid: Flush right now.
        if isinstance(self.f, h5py.File):
            self.f.file.flush()  # not available in z5py

        # We're finished.
        result[0] = True

        self.progressSignal(100)

    def propagateDirty(self, slot, subindex, roi):
        # The output from this operator isn't generally connected to other operators.
        # If someone is using it that way, we'll assume that the user wants to know that
        # the input image has become dirty and may need to be written to disk again.
        self.WriteImage.setDirty(slice(None))


if __name__ == "__main__":
    from lazyflow.graph import Graph
    import h5py
    import sys

    traceLogger.addHandler(logging.StreamHandler(sys.stdout))
    traceLogger.setLevel(logging.DEBUG)
    traceLogger.debug("HELLO")

    f = h5py.File("/tmp/flyem_sample_stack.h5")
    internalPath = "volume/data"

    # OpStackToH5Writer
    graph = Graph()
    opStackToH5 = OpStackToH5Writer()
    opStackToH5.GlobString.setValue("/tmp/flyem_sample_stack/*.png")
    opStackToH5.hdf5Group.setValue(f)
    opStackToH5.hdf5Path.setValue(internalPath)

    success = opStackToH5.WriteImage.value
    assert success
