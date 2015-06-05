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
#		   http://ilastik.org/license/
###############################################################################
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpImageReader, OpBlockedArrayCache, OpMetadataInjector, OpSubRegion
from opStreamingHdf5Reader import OpStreamingHdf5Reader
from opNpyFileReader import OpNpyFileReader
from opTiffReader import OpTiffReader
from opTiffSequenceReader import OpTiffSequenceReader
from lazyflow.operators.ioOperators import OpStackLoader, OpBlockwiseFilesetReader, OpRESTfulBlockwiseFilesetReader, OpCachedTiledVolumeReader
from lazyflow.utility.jsonConfig import JsonConfigParser
from lazyflow.utility.pathHelpers import isUrl

try:
    from lazyflow.operators.ioOperators import OpDvidVolume
    _supports_dvid = True
except ImportError as ex:
    if 'OpDvidVolume' not in ex.args[0]:
        raise
    _supports_dvid = False

import h5py
import vigra
import os
import re
import logging

from lazyflow.utility.io.multiprocessHdf5File import MultiProcessHdf5File

class OpInputDataReader(Operator):
    """
    This operator can read input data of any supported type.
    The data format is determined from the file extension.
    """
    name = "OpInputDataReader"
    category = "Input"

    h5Exts = ['h5', 'hdf5', 'ilp']
    npyExts = ['npy']
    blockwiseExts = ['json']
    tiledExts = ['json']
    tiffExts = ['tif', 'tiff']
    vigraImpexExts = vigra.impex.listExtensions().split()
    SupportedExtensions = h5Exts + npyExts + vigraImpexExts + blockwiseExts
    if _supports_dvid:
        dvidExts = ['dvidvol']
        SupportedExtensions += dvidExts

    # FilePath is inspected to determine data type.
    # For hdf5 files, append the internal path to the filepath,
    #  e.g. /mydir/myfile.h5/internal/path/to/dataset
    # For stacks, provide a globstring, e.g. /mydir/input*.png
    # Other types are determined via file extension
    WorkingDirectory = InputSlot(stype='filestring', optional=True)
    FilePath = InputSlot(stype='filestring')

    # FIXME: Document this.
    SubVolumeRoi = InputSlot(optional=True) # (start, stop)

    Output = OutputSlot()
    
    loggingName = __name__ + ".OpInputDataReader"
    logger = logging.getLogger(loggingName)

    class DatasetReadError(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super(OpInputDataReader, self).__init__(*args, **kwargs)
        self.internalOperators = []
        self.internalOutput = None
        self._file = None

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
        filePath = self.FilePath.value
        assert isinstance(filePath, (str,unicode)), "Error: filePath is not of type str.  It's of type {}".format(type(filePath))

        # Does this look like a relative path?
        useRelativePath = not isUrl(filePath) and not os.path.isabs(filePath)

        if useRelativePath:
            # If using a relative path, we need both inputs before proceeding
            if not self.WorkingDirectory.ready():
                return
            else:
                # Convert this relative path into an absolute path
                filePath = os.path.normpath(os.path.join(self.WorkingDirectory.value, filePath)).replace('\\','/')

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

        openFuncs = [ self._attemptOpenAsDvidVolume,
                      self._attemptOpenAsTiffStack,
                      self._attemptOpenAsStack,
                      self._attemptOpenAsHdf5,
                      self._attemptOpenAsNpy,
                      self._attemptOpenAsBlockwiseFileset,
                      self._attemptOpenAsRESTfulBlockwiseFileset,
                      self._attemptOpenAsTiledVolume,
                      self._attemptOpenAsTiff,
                      self._attemptOpenWithVigraImpex ]

        # Try every method of opening the file until one works.
        iterFunc = openFuncs.__iter__()
        while not self.internalOperators:
            try:
                openFunc = iterFunc.next()
            except StopIteration:
                break
            self.internalOperators, self.internalOutput = openFunc(filePath)

        if self.internalOutput is None:
            raise RuntimeError("Can't read " + filePath + " because it has an unrecognized format.")

        # If we've got a ROI, append a subregion operator.
        if self.SubVolumeRoi.ready():
            self._opSubRegion = OpSubRegion( parent=self )
            self._opSubRegion.Roi.setValue( self.SubVolumeRoi.value )
            self._opSubRegion.Input.connect( self.internalOutput )
            self.internalOutput = self._opSubRegion.Output
        
        self.opInjector = OpMetadataInjector( parent=self )
        self.opInjector.Input.connect( self.internalOutput )
        
        # Add metadata for estimated RAM usage if the internal operator didn't already provide it.
        if self.internalOutput.meta.ram_per_pixelram_usage_per_requested_pixel is None:
            ram_per_pixel = self.internalOutput.meta.dtype().nbytes
            if 'c' in self.internalOutput.meta.getTaggedShape():
                ram_per_pixel *= self.internalOutput.meta.getTaggedShape()['c']
            self.opInjector.Metadata.setValue( {'ram_per_pixelram_usage_per_requested_pixel' : ram_per_pixel} )
        else:
            # Nothing to add
            self.opInjector.Metadata.setValue( {} )            

        # Directly connect our own output to the internal output
        self.Output.connect( self.opInjector.Output )
    
    def _attemptOpenAsTiffStack(self, filePath):
        if not ('*' in filePath or os.path.pathsep in filePath):
            return ([], None)
        
        try:
            opReader = OpTiffSequenceReader(parent=self)
            opReader.GlobString.setValue(filePath)
            return (opReader, opReader.Output)
        except OpTiffSequenceReader.WrongFileTypeError as ex:
            return ([], None)
        
    
    def _attemptOpenAsStack(self, filePath):
        if '*' in filePath or os.path.pathsep in filePath:
            stackReader = OpStackLoader(parent=self)
            stackReader.globstring.setValue(filePath)
            return ([stackReader], stackReader.stack)
        else:
            return ([], None)

    def _attemptOpenAsHdf5(self, filePath):
        # Check for an hdf5 extension
        h5Exts = OpInputDataReader.h5Exts + ['ilp']
        h5Exts = ['.' + ex for ex in h5Exts]
        ext = None
        for x in h5Exts:
            if x in filePath:
                ext = x

        if ext is None:
            return ([], None)

        externalPath = filePath.split(ext)[0] + ext
        internalPath = filePath.split(ext)[1]

        if not os.path.exists(externalPath):
            raise OpInputDataReader.DatasetReadError("Input file does not exist: " + externalPath)

        # Can't set the internal path yet if we don't have one
        assert internalPath != '', \
            "When using hdf5, you must append the hdf5 internal path to the "\
            "data set to your filename, e.g. myfile.h5/volume/data  "\
            "No internal path provided for dataset in file: {}".format( externalPath )

        # Open the h5 file in read-only mode
        try:
            h5File = h5py.File(externalPath, 'r')
            try:
                compression_setting = h5File[internalPath].compression
            except Exception as e:
                h5File.close()
                msg = "Error reading HDF5 File: {}\n{}".format(externalPath, e.msg)
                raise OpInputDataReader.DatasetReadError( msg )
 
            # If the h5 dataset is compressed, we'll have better performance 
            #  with a multi-process hdf5 access object.
            # (Otherwise, single-process is faster.)
            allow_multiprocess_hdf5 = "LAZYFLOW_MULTIPROCESS_HDF5" in os.environ and os.environ["LAZYFLOW_MULTIPROCESS_HDF5"] != ""
            if compression_setting is not None and allow_multiprocess_hdf5:
                h5File.close()                
                h5File = MultiProcessHdf5File(externalPath, 'r')
        except OpInputDataReader.DatasetReadError:
            raise
        except Exception as e:
            msg = "Unable to open HDF5 File: {}\n{}".format( externalPath, str(e) )
            raise OpInputDataReader.DatasetReadError( msg )
        self._file = h5File

        h5Reader = OpStreamingHdf5Reader(parent=self)
        h5Reader.Hdf5File.setValue(h5File)

        try:
            h5Reader.InternalPath.setValue(internalPath)
        except OpStreamingHdf5Reader.DatasetReadError as e:
            msg = "Error reading HDF5 File: {}\n{}".format(externalPath, e.msg)
            raise OpInputDataReader.DatasetReadError( msg )

        return ([h5Reader], h5Reader.OutputImage)

    def _attemptOpenAsNpy(self, filePath):
        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip('.') # Remove leading dot

        # Check for numpy extension
        if fileExtension not in OpInputDataReader.npyExts:
            return ([], None)
        else:
            try:
                # Create an internal operator
                npyReader = OpNpyFileReader(parent=self)
                npyReader.FileName.setValue(filePath)
                return ([npyReader], npyReader.Output)
            except OpNpyFileReader.DatasetReadError as e:
                raise OpInputDataReader.DatasetReadError( *e.args )

    def _attemptOpenAsDvidVolume(self, filePath):
        """
        Two ways to specify a dvid volume.
        1) via a file that contains the hostname, uuid, and dataset name (1 per line)
        2) as a url, e.g. http://localhost:8000/api/node/uuid/dataname
        """
        if os.path.splitext(filePath)[1] == '.dvidvol':
            with open(filePath) as f:
                filetext = f.read()
                hostname, uuid, dataname = filetext.splitlines()
            opDvidVolume = OpDvidVolume( hostname, uuid, dataname, transpose_axes=True, parent=self )
            return [opDvidVolume], opDvidVolume.Output
        if '://' in filePath:
            url_format = "^protocol://hostname/api/node/uuid/dataname(\\?query_string)?"
            for field in ['protocol', 'hostname', 'uuid', 'dataname', 'query_string']:
                url_format = url_format.replace( field, '(?P<' + field + '>[^?]+)' )
            match = re.match( url_format, filePath )
            if match:
                fields = match.groupdict()
                try:
                    query_string = fields['query_string']
                    query_args = {}
                    if query_string:
                        query_args = dict( map(lambda s: s.split('='), query_string.split('&')) )
                    opDvidVolume = OpDvidVolume( fields['hostname'], fields['uuid'], fields['dataname'], query_args,
                                                 transpose_axes=True, parent=self )
                    return [opDvidVolume], opDvidVolume.Output
                except OpDvidVolume.DatasetReadError as e:
                    raise OpInputDataReader.DatasetReadError( *e.args )
        return ([], None)

    def _attemptOpenAsBlockwiseFileset(self, filePath):
        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip('.') # Remove leading dot

        if fileExtension in OpInputDataReader.blockwiseExts:
            opReader = OpBlockwiseFilesetReader(parent=self)
            try:
                # This will raise a SchemaError if this is the wrong type of json config.
                opReader.DescriptionFilePath.setValue( filePath )
                return ([opReader], opReader.Output)
            except JsonConfigParser.SchemaError:
                opReader.cleanUp()
            except OpBlockwiseFilesetReader.MissingDatasetError as e:
                raise OpInputDataReader.DatasetReadError(*e.args)
        return ([], None)

    def _attemptOpenAsRESTfulBlockwiseFileset(self, filePath):
        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip('.') # Remove leading dot

        if fileExtension in OpInputDataReader.blockwiseExts:
            opReader = OpRESTfulBlockwiseFilesetReader(parent=self)
            try:
                # This will raise a SchemaError if this is the wrong type of json config.
                opReader.DescriptionFilePath.setValue( filePath )
                return ([opReader], opReader.Output)
            except JsonConfigParser.SchemaError:
                opReader.cleanUp()
            except OpRESTfulBlockwiseFilesetReader.MissingDatasetError as e:
                raise OpInputDataReader.DatasetReadError(*e.args)
        return ([], None)

    def _attemptOpenAsTiledVolume(self, filePath):
        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip('.') # Remove leading dot

        if fileExtension in OpInputDataReader.tiledExts:
            opReader = OpCachedTiledVolumeReader(parent=self)
            try:
                # This will raise a SchemaError if this is the wrong type of json config.
                opReader.DescriptionFilePath.setValue( filePath )
                return ([opReader], opReader.SpecifiedOutput)
            except JsonConfigParser.SchemaError:
                opReader.cleanUp()
        return ([], None)

    def _attemptOpenAsTiff(self, filePath):
        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip('.') # Remove leading dot

        if fileExtension not in OpInputDataReader.tiffExts:
            return ([], None)

        if not os.path.exists(filePath):
            raise OpInputDataReader.DatasetReadError("Input file does not exist: " + filePath)

        opReader = OpTiffReader( parent=self )
        opReader.Filepath.setValue(filePath)

        page_shape = opReader.Output.meta.ideal_blockshape

        # Cache the pages we read
        opCache = OpBlockedArrayCache( parent=self )
        opCache.fixAtCurrent.setValue( False )
        opCache.innerBlockShape.setValue( page_shape )
        opCache.outerBlockShape.setValue( page_shape )
        opCache.Input.connect( opReader.Output )
        
        return ([opReader, opCache], opCache.Output)
    
    def _attemptOpenWithVigraImpex(self, filePath):
        fileExtension = os.path.splitext(filePath)[1].lower()
        fileExtension = fileExtension.lstrip('.') # Remove leading dot

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
        if 'z' in taggedShape.keys():
            # 3D: blocksize is one slice.
            taggedShape['z'] = 1
            cacheBlockShape = tuple(taggedShape.values())
        
        imageCache.fixAtCurrent.setValue( False ) 
        imageCache.innerBlockShape.setValue( cacheBlockShape ) 
        imageCache.outerBlockShape.setValue( cacheBlockShape ) 
        assert imageCache.Output.ready()
        
        return ([vigraReader, imageCache], imageCache.Output)

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here because our output is directly connected..."

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly conncted to internal operators
        pass

    @classmethod
    def getInternalDatasets(cls, filePath):
        """
        Search the given file for internal datasets, and return their internal paths as a list.
        For now, it is assumed that the file is an hdf5 file.
        
        Returns: A list of the internal datasets in the file, or None if the format doesn't support internal datasets.
        """
        datasetNames = None
        ext = os.path.splitext(filePath)[1][1:]
        
        # HDF5. Other formats don't contain more than one dataset (as far as we're concerned).
        if ext in OpInputDataReader.h5Exts:
            datasetNames = []
            # Open the file as a read-only so we can get a list of the internal paths
            with h5py.File(filePath, 'r') as f:
                # Define a closure to collect all of the dataset names in the file.
                def accumulateDatasetPaths(name, val):
                    if type(val) == h5py._hl.dataset.Dataset and 3 <= len(val.shape) <= 5:
                        datasetNames.append( '/' + name )    
                # Visit every group/dataset in the file            
                f.visititems(accumulateDatasetPaths)        

        return datasetNames



















