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
#          http://ilastik.org/license/
###############################################################################
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpBlockedArrayCache, OpMetadataInjector, OpSubRegion
from .opNpyFileReader import OpNpyFileReader
from lazyflow.operators.ioOperators import (
    OpBlockwiseFilesetReader,
    OpKlbReader,
    OpRESTfulBlockwiseFilesetReader,
    OpStreamingH5N5Reader,
    OpStreamingH5N5SequenceReaderS,
    OpStreamingH5N5SequenceReaderM,
    OpTiffReader,
    OpTiffSequenceReader,
    OpCachedTiledVolumeReader,
    OpRawBinaryFileReader,
    OpStackLoader,
    OpRESTfulPrecomputedChunkedVolumeReader,
    OpImageReader,
)
from lazyflow.utility.jsonConfig import JsonConfigParser
from lazyflow.utility.pathHelpers import lsH5N5, isUrl, isRelative, splitPath, PathComponents

from .opStreamingUfmfReader import OpStreamingUfmfReader
from .opStreamingMmfReader import OpStreamingMmfReader

try:
    from .opBigTiffReader import OpBigTiffReader

    _supports_bigtiff = True
except ImportError:
    _supports_bigtiff = False

try:
    from lazyflow.operators.ioOperators import OpDvidVolume, OpDvidRoi

    _supports_dvid = True
except ImportError as ex:
    if "OpDvidVolume" not in ex.args[0] and "OpDvidRoi" not in ex.args[0]:
        raise
    _supports_dvid = False

try:
    from lazyflow.operators.ioOperators.opH5BlockStoreReader import OpH5BlockStoreReader

    _supports_h5blockreader = True
except ImportError as ex:
    _supports_h5blockreader = False

import h5py
import vigra
import os
import re
import logging
from typing import List, Tuple

from lazyflow.utility.io_util.multiprocessHdf5File import MultiProcessHdf5File


class OpInputDataReader(Operator):
    """
    This operator can read input data of any supported type.
    The data format is determined from the file extension.
    """

    name = "OpInputDataReader"
    category = "Input"

    videoExts = ["ufmf", "mmf"]
    h5_n5_Exts = ["h5", "hdf5", "ilp", "n5"]
    n5Selection = ["json"]  # n5 stores data in a directory, containing a json-file which we use to select the n5-file
    klbExts = ["klb"]
    npyExts = ["npy"]
    npzExts = ["npz"]
    rawExts = ["dat", "bin", "raw"]
    blockwiseExts = ["json"]
    tiledExts = ["json"]
    tiffExts = ["tif", "tiff"]
    vigraImpexExts = vigra.impex.listExtensions().split()

    SupportedExtensions = (
        h5_n5_Exts + n5Selection + npyExts + npzExts + rawExts + vigraImpexExts + blockwiseExts + videoExts + klbExts
    )

    if _supports_dvid:
        dvidExts = ["dvidvol"]
        SupportedExtensions += dvidExts

    if _supports_h5blockreader:
        h5blockstoreExts = ["json"]
        SupportedExtensions += h5blockstoreExts

    # FilePath is inspected to determine data type.
    # For hdf5 files, append the internal path to the filepath,
    #  e.g. /mydir/myfile.h5/internal/path/to/dataset
    # For stacks, provide a globstring, e.g. /mydir/input*.png
    # Other types are determined via file extension
    WorkingDirectory = InputSlot(stype="filestring", optional=True)
    FilePath = InputSlot(stype="filestring")
    SequenceAxis = InputSlot(optional=True)

    # FIXME: Document this.
    SubVolumeRoi = InputSlot(optional=True)  # (start, stop)

    Output = OutputSlot()

    loggingName = __name__ + ".OpInputDataReader"
    logger = logging.getLogger(loggingName)

    class DatasetReadError(Exception):
        pass

    def __init__(
        self,
        WorkingDirectory: str = None,
        FilePath: str = None,
        SequenceAxis: str = None,
        SubVolumeRoi: Tuple[int, int] = None,
        *args,
        **kwargs,
    ):
        super(OpInputDataReader, self).__init__(*args, **kwargs)
        self.internalOperators = []
        self.internalOutput = None
        self._file = None

        self.WorkingDirectory.setOrConnectIfAvailable(WorkingDirectory)
        self.FilePath.setOrConnectIfAvailable(FilePath)
        self.SequenceAxis.setOrConnectIfAvailable(SequenceAxis)
        self.SubVolumeRoi.setOrConnectIfAvailable(SubVolumeRoi)

    def cleanUp(self):
        super(OpInputDataReader, self).cleanUp()
        if self._file is not None:
            self._file.close()
            self._file = None

    def setupOutputs(self):
        """
        Inspect the file name and instantiate and connect an internal operator of the appropriate type.
        TODO: Handle datasets of non-standard (non-5d) dimensions.
        """
        path_components = splitPath(self.FilePath.value)

        cwd = self.WorkingDirectory.value if self.WorkingDirectory.ready() else None
        abs_paths = []
        for path in path_components:
            if isRelative(path):
                if cwd is None:
                    return  # FIXME: this mirrors old logic but I'm not sure if it's safe
                abs_paths.append(os.path.normpath(os.path.join(cwd, path)).replace("\\", "/"))
            else:
                abs_paths.append(path)
        filePath = os.path.pathsep.join(abs_paths)

        # Clean up before reconfiguring
        if self.internalOperators:
            self.Output.disconnect()
            self.opInjector.cleanUp()
            for op in self.internalOperators[::-1]:
                op.cleanUp()
            self.internalOperators = []
            self.internalOutput = None
        if self._file is not None:
            self._file.close()

        openFuncs = [
            self._attemptOpenAsKlb,
            self._attemptOpenAsUfmf,
            self._attemptOpenAsMmf,
            self._attemptOpenAsRESTfulPrecomputedChunkedVolume,
            self._attemptOpenAsDvidVolume,
            self._attemptOpenAsH5N5Stack,
            self._attemptOpenAsTiffStack,
            self._attemptOpenAsStack,
            self._attemptOpenAsH5N5,
            self._attemptOpenAsNpy,
            self._attemptOpenAsRawBinary,
            self._attemptOpenAsTiledVolume,
            self._attemptOpenAsH5BlockStore,
            self._attemptOpenAsBlockwiseFileset,
            self._attemptOpenAsRESTfulBlockwiseFileset,
            self._attemptOpenAsBigTiff,
            self._attemptOpenAsTiff,
            self._attemptOpenWithVigraImpex,
        ]

        # Try every method of opening the file until one works.
        iterFunc = openFuncs.__iter__()
        while not self.internalOperators:
            try:
                openFunc = next(iterFunc)
            except StopIteration:
                break
            self.internalOperators, self.internalOutput = openFunc(filePath)

        if self.internalOutput is None:
            raise RuntimeError("Can't read " + filePath + " because it has an unrecognized format.")

        # If we've got a ROI, append a subregion operator.
        if self.SubVolumeRoi.ready():
            self._opSubRegion = OpSubRegion(parent=self)
            self._opSubRegion.Roi.setValue(self.SubVolumeRoi.value)
            self._opSubRegion.Input.connect(self.internalOutput)
            self.internalOutput = self._opSubRegion.Output

        self.opInjector = OpMetadataInjector(parent=self)
        self.opInjector.Input.connect(self.internalOutput)

        # Add metadata for estimated RAM usage if the internal operator didn't already provide it.
        if self.internalOutput.meta.ram_per_pixelram_usage_per_requested_pixel is None:
            ram_per_pixel = self.internalOutput.meta.dtype().nbytes
            if "c" in self.internalOutput.meta.getTaggedShape():
                ram_per_pixel *= self.internalOutput.meta.getTaggedShape()["c"]
            self.opInjector.Metadata.setValue({"ram_per_pixelram_usage_per_requested_pixel": ram_per_pixel})
        else:
            # Nothing to add
            self.opInjector.Metadata.setValue({})

        # Directly connect our own output to the internal output
        self.Output.connect(self.opInjector.Output)

    def _attemptOpenAsKlb(self, filePath):
        if not os.path.splitext(filePath)[1].lower() == ".klb":
            return ([], None)

        opReader = OpKlbReader(parent=self)
        opReader.FilePath.setValue(filePath)
        return [opReader, opReader.Output]

    def _attemptOpenAsMmf(self, filePath):
        if ".mmf" in filePath:
            mmfReader = OpStreamingMmfReader(parent=self)
            mmfReader.FileName.setValue(filePath)

            return ([mmfReader], mmfReader.Output)

            """
            # Cache the frames we read
            frameShape = mmfReader.Output.meta.ideal_blockshape

            mmfCache = OpBlockedArrayCache( parent=self )
            mmfCache.fixAtCurrent.setValue( False )
            mmfCache.BlockShape.setValue( frameShape )
            mmfCache.Input.connect( mmfReader.Output )

            return ([mmfReader, mmfCache], mmfCache.Output)
            """
        else:
            return ([], None)

    def _attemptOpenAsUfmf(self, filePath):
        if ".ufmf" in filePath:
            ufmfReader = OpStreamingUfmfReader(parent=self)
            ufmfReader.FileName.setValue(filePath)

            return ([ufmfReader], ufmfReader.Output)

            # Cache the frames we read
            """
            frameShape = ufmfReader.Output.meta.ideal_blockshape

            ufmfCache = OpBlockedArrayCache( parent=self )
            ufmfCache.fixAtCurrent.setValue( False )
            ufmfCache.BlockShape.setValue( frameShape )
            ufmfCache.Input.connect( ufmfReader.Output )

            return ([ufmfReader, ufmfCache], ufmfCache.Output)
            """
        else:
            return ([], None)

    def _attemptOpenAsRESTfulPrecomputedChunkedVolume(self, filePath):
        if not filePath.lower().startswith("precomputed://"):
            return ([], None)
        else:
            url = filePath.lstrip("precomputed://")
            reader = OpRESTfulPrecomputedChunkedVolumeReader(parent=self)
            reader.BaseUrl.setValue(url)
            return [reader], reader.Output

    def _attemptOpenAsH5N5Stack(self, filePath):
        if not ("*" in filePath or os.path.pathsep in filePath):
            return ([], None)

        # Now use the .checkGlobString method of the stack readers
        isSingleFile = True
        try:
            OpStreamingH5N5SequenceReaderS.checkGlobString(filePath)
        except OpStreamingH5N5SequenceReaderS.WrongFileTypeError:
            return ([], None)
        except (
            OpStreamingH5N5SequenceReaderS.NoInternalPlaceholderError,
            OpStreamingH5N5SequenceReaderS.NotTheSameFileError,
            OpStreamingH5N5SequenceReaderS.ExternalPlaceholderError,
        ):
            isSingleFile = False

        isMultiFile = True
        try:
            OpStreamingH5N5SequenceReaderM.checkGlobString(filePath)
        except (
            OpStreamingH5N5SequenceReaderM.NoExternalPlaceholderError,
            OpStreamingH5N5SequenceReaderM.SameFileError,
            OpStreamingH5N5SequenceReaderM.InternalPlaceholderError,
        ):
            isMultiFile = False

        assert not (isMultiFile and isSingleFile)

        if isSingleFile is True:
            opReader = OpStreamingH5N5SequenceReaderS(parent=self)
        elif isMultiFile is True:
            opReader = OpStreamingH5N5SequenceReaderM(parent=self)

        try:
            opReader.SequenceAxis.connect(self.SequenceAxis)
            opReader.GlobString.setValue(filePath)
            return ([opReader], opReader.OutputImage)
        except (OpStreamingH5N5SequenceReaderM.WrongFileTypeError, OpStreamingH5N5SequenceReaderS.WrongFileTypeError):
            return ([], None)

    def _attemptOpenAsTiffStack(self, filePath):
        if not ("*" in filePath or os.path.pathsep in filePath):
            return ([], None)

        try:
            opReader = OpTiffSequenceReader(parent=self)
            opReader.SequenceAxis.connect(self.SequenceAxis)
            opReader.GlobString.setValue(filePath)
            return ([opReader], opReader.Output)
        except OpTiffSequenceReader.WrongFileTypeError as ex:
            return ([], None)

    def _attemptOpenAsStack(self, filePath):
        if "*" in filePath or os.path.pathsep in filePath:
            stackReader = OpStackLoader(parent=self)
            stackReader.SequenceAxis.connect(self.SequenceAxis)
            stackReader.globstring.setValue(filePath)
            return ([stackReader], stackReader.stack)
        else:
            return ([], None)

    def _attemptOpenAsH5N5(self, filePath):
        # Check for an hdf5 or n5 extension
        pathComponents = PathComponents(filePath)
        ext = pathComponents.extension
        if ext[1:] not in OpInputDataReader.h5_n5_Exts:
            return [], None

        externalPath = pathComponents.externalPath
        internalPath = pathComponents.internalPath

        if not os.path.exists(externalPath):
            raise OpInputDataReader.DatasetReadError("Input file does not exist: " + externalPath)

        # Open the h5/n5 file in read-only mode
        try:
            h5N5File = OpStreamingH5N5Reader.get_h5_n5_file(externalPath, "r")
        except OpInputDataReader.DatasetReadError:
            raise
        except Exception as e:
            msg = "Unable to open H5/N5 File: {}\n{}".format(externalPath, str(e))
            raise OpInputDataReader.DatasetReadError(msg) from e
        else:
            if not internalPath:
                possible_internal_paths = lsH5N5(h5N5File)
                if len(possible_internal_paths) == 1:
                    internalPath = possible_internal_paths[0]["name"]
                elif len(possible_internal_paths) == 0:
                    h5N5File.close()
                    msg = "H5/N5 file contains no datasets: {}".format(externalPath)
                    raise OpInputDataReader.DatasetReadError(msg)
                else:
                    h5N5File.close()
                    msg = (
                        "When using hdf5/n5, you must append the hdf5 internal path to the "
                        "data set to your filename, e.g. myfile.h5/volume/data  "
                        "No internal path provided for dataset in file: {}".format(externalPath)
                    )
                    raise OpInputDataReader.DatasetReadError(msg)
            try:
                compression_setting = h5N5File[internalPath].compression
            except Exception as e:
                h5N5File.close()
                msg = "Error reading H5/N5 File: {}\n{}".format(externalPath, e)
                raise OpInputDataReader.DatasetReadError(msg) from e

            # If the h5 dataset is compressed, we'll have better performance
            #  with a multi-process hdf5 access object.
            # (Otherwise, single-process is faster.)
            allow_multiprocess_hdf5 = (
                "LAZYFLOW_MULTIPROCESS_HDF5" in os.environ and os.environ["LAZYFLOW_MULTIPROCESS_HDF5"] != ""
            )
            if compression_setting is not None and allow_multiprocess_hdf5 and isinstance(h5N5File, h5py.File):
                h5N5File.close()
                h5N5File = MultiProcessHdf5File(externalPath, "r")

        self._file = h5N5File

        h5N5Reader = OpStreamingH5N5Reader(parent=self)
        h5N5Reader.H5N5File.setValue(h5N5File)

        try:
            h5N5Reader.InternalPath.setValue(internalPath)
        except OpStreamingH5N5Reader.DatasetReadError as e:
            msg = "Error reading H5/N5 File: {}\n{}".format(externalPath, e.msg)
            raise OpInputDataReader.DatasetReadError(msg) from e

        return ([h5N5Reader], h5N5Reader.OutputImage)

    def _attemptOpenAsNpy(self, filePath):
        pathComponents = PathComponents(filePath)
        ext = pathComponents.extension
        npyzExts = OpInputDataReader.npyExts + OpInputDataReader.npzExts
        if ext not in (".%s" % x for x in npyzExts):
            return ([], None)

        externalPath = pathComponents.externalPath
        internalPath = pathComponents.internalPath
        # FIXME: check whether path is valid?!

        if not os.path.exists(externalPath):
            raise OpInputDataReader.DatasetReadError("Input file does not exist: " + externalPath)

        try:
            # Create an internal operator
            npyReader = OpNpyFileReader(parent=self)
            if internalPath is not None:
                internalPath = internalPath.replace("/", "")
            npyReader.InternalPath.setValue(internalPath)
            npyReader.FileName.setValue(externalPath)
            return ([npyReader], npyReader.Output)
        except OpNpyFileReader.DatasetReadError as e:
            raise OpInputDataReader.DatasetReadError(*e.args) from e

    def _attemptOpenAsRawBinary(self, filePath):
        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip(".")  # Remove leading dot

        # Check for numpy extension
        if fileExtension not in OpInputDataReader.rawExts:
            return ([], None)
        else:
            try:
                # Create an internal operator
                opReader = OpRawBinaryFileReader(parent=self)
                opReader.FilePath.setValue(filePath)
                return ([opReader], opReader.Output)
            except OpRawBinaryFileReader.DatasetReadError as e:
                raise OpInputDataReader.DatasetReadError(*e.args) from e

    def _attemptOpenAsH5BlockStore(self, filePath):
        if not os.path.splitext(filePath)[1] == ".json":
            return ([], None)

        op = OpH5BlockStoreReader(parent=self)
        try:
            # For now, there is no explicit schema validation for the json file,
            # but H5BlockStore constructor will fail to load the json.
            op.IndexFilepath.setValue(filePath)
            return [op], op.Output
        except:
            raise  # DELME
            op.cleanUp()
            return ([], None)

    def _attemptOpenAsDvidVolume(self, filePath):
        """
        Two ways to specify a dvid volume.
        1) via a file that contains the hostname, uuid, and dataset name (1 per line)
        2) as a url, e.g. http://localhost:8000/api/node/uuid/dataname
        """
        if os.path.splitext(filePath)[1] == ".dvidvol":
            with open(filePath) as f:
                filetext = f.read()
                hostname, uuid, dataname = filetext.splitlines()
            opDvidVolume = OpDvidVolume(hostname, uuid, dataname, parent=self)
            return [opDvidVolume], opDvidVolume.Output

        if "://" not in filePath:
            return ([], None)  # not a url

        url_format = "^protocol://hostname/api/node/uuid/dataname(\\?query_string)?"
        for field in ["protocol", "hostname", "uuid", "dataname", "query_string"]:
            url_format = url_format.replace(field, "(?P<" + field + ">[^?]+)")
        match = re.match(url_format, filePath)
        if not match:
            # DVID is the only url-based format we support right now.
            # So if it looks like the user gave a URL that isn't a valid DVID node, then error.
            raise OpInputDataReader.DatasetReadError("Invalid URL format for DVID: {}".format(filePath))

        fields = match.groupdict()
        try:
            query_string = fields["query_string"]
            query_args = {}
            if query_string:
                query_args = dict([s.split("=") for s in query_string.split("&")])
            try:
                opDvidVolume = OpDvidVolume(
                    fields["hostname"], fields["uuid"], fields["dataname"], query_args, parent=self
                )
                return [opDvidVolume], opDvidVolume.Output
            except:
                # Maybe this is actually a roi
                opDvidRoi = OpDvidRoi(fields["hostname"], fields["uuid"], fields["dataname"], parent=self)
                return [opDvidRoi], opDvidRoi.Output
        except OpDvidVolume.DatasetReadError as e:
            raise OpInputDataReader.DatasetReadError(*e.args) from e

    def _attemptOpenAsBlockwiseFileset(self, filePath):
        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip(".")  # Remove leading dot

        if fileExtension in OpInputDataReader.blockwiseExts:
            opReader = OpBlockwiseFilesetReader(parent=self)
            try:
                # This will raise a SchemaError if this is the wrong type of json config.
                opReader.DescriptionFilePath.setValue(filePath)
                return ([opReader], opReader.Output)
            except JsonConfigParser.SchemaError:
                opReader.cleanUp()
            except OpBlockwiseFilesetReader.MissingDatasetError as e:
                raise OpInputDataReader.DatasetReadError(*e.args) from e
        return ([], None)

    def _attemptOpenAsRESTfulBlockwiseFileset(self, filePath):
        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip(".")  # Remove leading dot

        if fileExtension in OpInputDataReader.blockwiseExts:
            opReader = OpRESTfulBlockwiseFilesetReader(parent=self)
            try:
                # This will raise a SchemaError if this is the wrong type of json config.
                opReader.DescriptionFilePath.setValue(filePath)
                return ([opReader], opReader.Output)
            except JsonConfigParser.SchemaError:
                opReader.cleanUp()
            except OpRESTfulBlockwiseFilesetReader.MissingDatasetError as e:
                raise OpInputDataReader.DatasetReadError(*e.args) from e
        return ([], None)

    def _attemptOpenAsTiledVolume(self, filePath):
        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip(".")  # Remove leading dot

        if fileExtension in OpInputDataReader.tiledExts:
            opReader = OpCachedTiledVolumeReader(parent=self)
            try:
                # This will raise a SchemaError if this is the wrong type of json config.
                opReader.DescriptionFilePath.setValue(filePath)
                return ([opReader], opReader.SpecifiedOutput)
            except JsonConfigParser.SchemaError:
                opReader.cleanUp()
        return ([], None)

    def _attemptOpenAsBigTiff(self, filePath):
        if not _supports_bigtiff:
            return ([], None)

        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip(".")  # Remove leading dot

        if fileExtension not in OpInputDataReader.tiffExts:
            return ([], None)

        if not os.path.exists(filePath):
            raise OpInputDataReader.DatasetReadError("Input file does not exist: " + filePath)

        opReader = OpBigTiffReader(parent=self)
        try:
            opReader.Filepath.setValue(filePath)
            return ([opReader], opReader.Output)
        except OpBigTiffReader.NotBigTiffError as ex:
            opReader.cleanUp()
        return ([], None)

    def _attemptOpenAsTiff(self, filePath):
        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip(".")  # Remove leading dot

        if fileExtension not in OpInputDataReader.tiffExts:
            return ([], None)

        if not os.path.exists(filePath):
            raise OpInputDataReader.DatasetReadError("Input file does not exist: " + filePath)

        opReader = OpTiffReader(parent=self)
        opReader.Filepath.setValue(filePath)

        page_shape = opReader.Output.meta.ideal_blockshape

        # Cache the pages we read
        opCache = OpBlockedArrayCache(parent=self)
        opCache.fixAtCurrent.setValue(False)
        opCache.BlockShape.setValue(page_shape)
        opCache.Input.connect(opReader.Output)

        return ([opReader, opCache], opCache.Output)

    def _attemptOpenWithVigraImpex(self, filePath):
        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip(".")  # Remove leading dot

        if fileExtension not in OpInputDataReader.vigraImpexExts:
            return ([], None)

        if not os.path.exists(filePath):
            raise OpInputDataReader.DatasetReadError("Input file does not exist: " + filePath)

        vigraReader = OpImageReader(parent=self)
        vigraReader.Filename.setValue(filePath)

        # Cache the image instead of reading the hard disk for every access.
        imageCache = OpBlockedArrayCache(parent=self)
        imageCache.Input.connect(vigraReader.Image)

        # 2D: Just one block for the whole image
        cacheBlockShape = vigraReader.Image.meta.shape

        taggedShape = vigraReader.Image.meta.getTaggedShape()
        if "z" in list(taggedShape.keys()):
            # 3D: blocksize is one slice.
            taggedShape["z"] = 1
            cacheBlockShape = tuple(taggedShape.values())

        imageCache.fixAtCurrent.setValue(False)
        imageCache.BlockShape.setValue(cacheBlockShape)
        assert imageCache.Output.ready()

        return ([vigraReader, imageCache], imageCache.Output)

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here because our output is directly connected..."

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly conncted to internal operators
        pass
