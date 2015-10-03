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
import os
import collections
from functools import partial

import numpy
import vigra
import h5py

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiFromShape
from lazyflow.utility import OrderedSignal, format_known_keys, PathComponents
from lazyflow.operators.ioOperators import OpH5WriterBigDataset, OpNpyWriter, OpExport2DImage, OpStackWriter, \
                                           OpExportMultipageTiff, OpExportMultipageTiffSequence, OpExportToArray

try:
    from lazyflow.operators.ioOperators import OpExportDvidVolume
    _supports_dvid = True
except ImportError as ex:
    if 'OpDvidVolume' not in ex.args[0] and 'OpExportDvidVolume' not in ex.args[0]:
        raise
    _supports_dvid = False

FormatInfo = collections.namedtuple('FormatInfo', ('name', 'extension', 'min_dim', 'max_dim'))
class OpExportSlot(Operator):
    """
    Export a slot 'as-is', i.e. no subregion, no dtype conversion, no normalization, no axis re-ordering, etc.
    For sequence export formats, the sequence is indexed by the axistags' FIRST axis.
    For example, txyzc produces a sequence of xyzc volumes.
    """
    Input = InputSlot()
    
    OutputFormat = InputSlot(value='hdf5') # string.  See formats, below
    OutputFilenameFormat = InputSlot() # A format string allowing {roi}, {t_start}, {t_stop}, etc (but not {nickname} or {dataset_dir})
    OutputInternalPath = InputSlot(value='exported_data')

    CoordinateOffset = InputSlot(optional=True) # Add an offset to the roi coordinates in the export path (useful if Input is a subregion of a larger dataset)

    ExportPath = OutputSlot()
    FormatSelectionErrorMsg = OutputSlot()

    _2d_exts = vigra.impex.listExtensions().split()    

    # List all supported formats
    _2d_formats = map( lambda ext: FormatInfo(ext, ext, 2, 2), _2d_exts)
    _3d_sequence_formats = map( lambda ext: FormatInfo(ext + ' sequence', ext, 3, 3), _2d_exts)
    _3d_volume_formats = [ FormatInfo('multipage tiff', 'tiff', 3, 3) ]
    _4d_sequence_formats = [ FormatInfo('multipage tiff sequence', 'tiff', 4, 4) ]
    nd_format_formats = [ FormatInfo('hdf5', 'h5', 0, 5),
                          FormatInfo('numpy', 'npy', 0, 5),
                          FormatInfo('dvid', '', 2, 5),
                          FormatInfo('blockwise hdf5', 'json', 0, 5) ]
    
    ALL_FORMATS = _2d_formats + _3d_sequence_formats + _3d_volume_formats\
                + _4d_sequence_formats + nd_format_formats

    def __init__(self, *args, **kwargs):
        super( OpExportSlot, self ).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()

        # Set up the impl function lookup dict
        export_impls = {}
        export_impls['hdf5'] = ('h5', self._export_hdf5)
        export_impls['npy'] = ('npy', self._export_npy)
        export_impls['dvid'] = ('', self._export_dvid)
        export_impls['blockwise hdf5'] = ('json', self._export_blockwise_hdf5)
        
        for fmt in self._2d_formats:
            export_impls[fmt.name] = (fmt.extension, partial(self._export_2d, fmt.extension) )

        for fmt in self._3d_sequence_formats:
            export_impls[fmt.name] = (fmt.extension, partial(self._export_3d_sequence, fmt.extension) )

        export_impls['multipage tiff'] = ('tiff', self._export_multipage_tiff)
        export_impls['multipage tiff sequence'] = ('tiff', self._export_multipage_tiff_sequence)
        self._export_impls = export_impls

        self.Input.notifyMetaChanged( self._updateFormatSelectionErrorMsg )
    
    def setupOutputs(self):
        self.ExportPath.meta.shape = (1,)
        self.ExportPath.meta.dtype = object
        self.FormatSelectionErrorMsg.meta.shape = (1,)
        self.FormatSelectionErrorMsg.meta.dtype = object
        
        if self.OutputFormat.value == 'hdf5' and self.OutputInternalPath.value == "":
            self.ExportPath.meta.NOTREADY = True
    
    def execute(self, slot, subindex, roi, result):
        if slot == self.ExportPath:
            return self._executeExportPath(result)
        else:
            assert False, "Unknown output slot: {}".format( slot.name )

    def _executeExportPath(self, result):
        path_format = self.OutputFilenameFormat.value
        file_extension = self._export_impls[ self.OutputFormat.value ][0]
        
        # Remove existing extension (if present) and add the correct extension (if any)
        if file_extension:
            path_format = os.path.splitext(path_format)[0]
            path_format += '.' + file_extension

        # Provide the TOTAL path (including dataset name)
        if self.OutputFormat.value == 'hdf5':
            path_format += '/' + self.OutputInternalPath.value

        roi = numpy.array( roiFromShape(self.Input.meta.shape) )
        
        # Intermediate state can cause coordinate offset and input shape to be mismatched.
        # Just don't use the offset if it looks wrong.
        # (The client will provide a valid offset later on.)
        if self.CoordinateOffset.ready() and len(self.CoordinateOffset.value) == len(roi[0]):
            offset = self.CoordinateOffset.value
            assert len(roi[0] == len(offset))
            roi += offset
        optional_replacements = {}
        optional_replacements['roi'] = map(tuple, roi)
        for key, (start, stop) in zip( self.Input.meta.getAxisKeys(), roi.transpose() ):
            optional_replacements[key + '_start'] = start
            optional_replacements[key + '_stop'] = stop
        formatted_path = format_known_keys( path_format, optional_replacements )
        result[0] = formatted_path
        return result

    def _updateFormatSelectionErrorMsg(self, *args):
        error_msg = self._get_format_selection_error_msg()
        self.FormatSelectionErrorMsg.setValue( error_msg )

    def _get_format_selection_error_msg(self, *args):
        """
        If the currently selected format does not support the input image format, 
        return an error message stating why. Otherwise, return an empty string.
        """
        if not self.Input.ready():
            return "Input not ready"
        output_format = self.OutputFormat.value

        # These cases support all combinations
        if output_format in ('hdf5', 'npy', 'blockwise hdf5'):
            return ""
        
        tagged_shape = self.Input.meta.getTaggedShape()
        axes = OpStackWriter.get_nonsingleton_axes_for_tagged_shape( tagged_shape )
        output_dtype = self.Input.meta.dtype

        if output_format == 'dvid':
            # dvid requires a channel axis, which must come last.
            # Internally, we transpose it before sending it over the wire
            if tagged_shape.keys()[-1] != 'c':
                return "DVID requires the last axis to be channel."

            # Make sure DVID supports this dtype/channel combo.
            from libdvid.voxels import VoxelsMetadata
            axiskeys = self.Input.meta.getAxisKeys()
            # We reverse the axiskeys because the export operator (see below) uses transpose_axes=True
            reverse_axiskeys = "".join(reversed( axiskeys ))
            reverse_shape = tuple(reversed(self.Input.meta.shape))
            metainfo = VoxelsMetadata.create_default_metadata( reverse_shape,
                                                               output_dtype,
                                                               reverse_axiskeys,
                                                               0.0,
                                                               'nanometers' )
            try:
                metainfo.determine_dvid_typename()
            except Exception as ex:
                return str(ex)
            else:
                return ""

        return FormatValidity.check(self.Input.meta.getTaggedShape(),
                                    self.Input.meta.dtype,
                                    output_format)

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.OutputFormat or slot == self.OutputFilenameFormat:
            self.ExportPath.setDirty()
        if slot == self.OutputFormat:
            self._updateFormatSelectionErrorMsg()

    def run_export_to_array(self):
        """
        Export the slot data to an array, instead of to disk.
        The data is computed blockwise, as necessary.
        The result is returned.
        """
        self.progressSignal(0)
        opExport = OpExportToArray(parent=self)
        try:
            opExport.progressSignal.subscribe(self.progressSignal)
            opExport.Input.connect(self.Input)
            return opExport.run_export_to_array()
        finally:
            opExport.cleanUp()
            self.progressSignal(100)                
    
    def run_export(self):
        """
        Perform the export and WAIT for it to complete.
        If you want asynchronous execution, run this function in a request:
        
            req = Request( opExport.run_export )
            req.submit()
        """
        output_format = self.OutputFormat.value
        try:
            export_func = self._export_impls[output_format][1]
        except KeyError:
            raise Exception( "Unknown export format: {}".format( output_format ) )
        else:
            export_func()
    
    def _export_hdf5(self):
        self.progressSignal( 0 )

        # Create and open the hdf5 file
        export_components = PathComponents(self.ExportPath.value)
        try:
            os.remove(export_components.externalPath)
        except OSError as ex:
            # It's okay if the file isn't there.
            if ex.errno != 2:
                raise
        try:
            with h5py.File(export_components.externalPath, 'w') as hdf5File:
                # Create a temporary operator to do the work for us
                opH5Writer = OpH5WriterBigDataset(parent=self)
                try:
                    opH5Writer.hdf5File.setValue( hdf5File )
                    opH5Writer.hdf5Path.setValue( export_components.internalPath )
                    opH5Writer.Image.connect( self.Input )
            
                    # The H5 Writer provides it's own progress signal, so just connect ours to it.
                    opH5Writer.progressSignal.subscribe( self.progressSignal )
    
                    # Perform the export and block for it in THIS THREAD.
                    opH5Writer.WriteImage[:].wait()
                finally:
                    opH5Writer.cleanUp()
                    self.progressSignal(100)
        except IOError as ex:
            import sys
            msg = "\nException raised when attempting to export to {}: {}\n"\
                  .format( export_components.externalPath, str(ex) )
            sys.stderr.write(msg)
            raise

    def _export_npy(self):
        self.progressSignal(0)
        export_path = self.ExportPath.value
        try:
            opWriter = OpNpyWriter( parent=self )
            opWriter.Filepath.setValue( export_path )
            opWriter.Input.connect( self.Input )
            
            # Run the export in this thread
            opWriter.write()
        finally:
            opWriter.cleanUp()
            self.progressSignal(100)
    
    def _export_dvid(self):
        self.progressSignal(0)
        export_path = self.ExportPath.value
        
        opExport = OpExportDvidVolume( transpose_axes=True, parent=self )
        try:
            opExport.Input.connect( self.Input )
            opExport.NodeDataUrl.setValue( export_path )
            
            # Run the export in this thread
            opExport.run_export()
        finally:
            opExport.cleanUp()
            self.progressSignal(100)
    
    def _export_blockwise_hdf5(self):
        raise NotImplementedError
    
    def _export_2d(self, fmt):
        self.progressSignal(0)
        export_path = self.ExportPath.value
        try:
            opExport = OpExport2DImage( parent=self )
            opExport.Filepath.setValue( export_path )
            opExport.Input.connect( self.Input )
            
            # Run the export
            opExport.run_export()
        finally:
            opExport.cleanUp()
            self.progressSignal(100)
    
    def _export_3d_sequence(self, extension):
        self.progressSignal(0)
        export_path_base, export_path_ext = os.path.splitext( self.ExportPath.value )
        export_path_pattern = export_path_base + "." + extension
        
        try:
            opWriter = OpStackWriter( parent=self )
            opWriter.FilepathPattern.setValue( export_path_pattern )
            opWriter.Input.connect( self.Input )
            opWriter.progressSignal.subscribe( self.progressSignal )
            
            if self.CoordinateOffset.ready():
                step_axis = opWriter.get_nonsingleton_axes()[0]
                step_axis_index = self.Input.meta.getAxisKeys().index(step_axis)
                step_axis_offset = self.CoordinateOffset.value[step_axis_index]
                opWriter.SliceIndexOffset.setValue( step_axis_offset )

            # Run the export
            opWriter.run_export()
        finally:
            opWriter.cleanUp()
            self.progressSignal(100)
    
    def _export_multipage_tiff(self):
        self.progressSignal(0)
        export_path = self.ExportPath.value
        try:
            opExport = OpExportMultipageTiff( parent=self )
            opExport.Filepath.setValue( export_path )
            opExport.Input.connect( self.Input )
            opExport.progressSignal.subscribe( self.progressSignal )
            
            # Run the export
            opExport.run_export()
        finally:
            opExport.cleanUp()
            self.progressSignal(100)
        
    def _export_multipage_tiff_sequence(self):
        self.progressSignal(0)
        export_path_base, export_path_ext = os.path.splitext( self.ExportPath.value )
        export_path_pattern = export_path_base + ".tiff"
        
        try:
            opExport = OpExportMultipageTiffSequence( parent=self )
            opExport.FilepathPattern.setValue( export_path_pattern )
            opExport.Input.connect( self.Input )
            opExport.progressSignal.subscribe( self.progressSignal )
            
            if self.CoordinateOffset.ready():
                step_axis = opExport.get_nonsingleton_axes()[0]
                step_axis_index = self.Input.meta.getAxisKeys().index(step_axis)
                step_axis_offset = self.CoordinateOffset.value[step_axis_index]
                opExport.SliceIndexOffset.setValue( step_axis_offset )

            # Run the export
            opExport.run_export()
        finally:
            opExport.cleanUp()
            self.progressSignal(100)


np = numpy
class FormatValidity(object):

    # { extension : [permitted formats] }
    dtypes = {'jpg': (np.uint8,),
              'png': (np.uint8, np.uint16,),
              'gif': (np.uint8,),
              'hdr': (np.float32,),
              'bmp': (np.uint8,),
              'tiff': (np.uint8, np.uint16, np.uint32, np.uint64,),  # https://partners.adobe.com/public/developer/en/tiff/TIFF6.pdf
              'ras': (np.uint8,),  # citation needed
              'pnm': (np.uint8, np.uint16,),  # see http://netpbm.sourceforge.net/doc/
              'ppm': (np.uint8, np.uint16,),
              'pgm': (np.uint8, np.uint16,),
              'pbm': (np.uint8, np.uint16,),  # vigra outputs p[gn]m
              'npy': (np.uint8, np.uint16, np.uint32, np.uint64,
                      np.int8, np.int16, np.int32, np.int64,
                      np.float32, np.float64,),
              'hdf5': (np.uint8, np.uint16, np.uint32, np.uint64,
                       np.int8, np.int16, np.int32, np.int64,
                       np.float32, np.float64,),
              }

    # { extension : (min_ndim, max_ndim) } 
    axes = {'jpg': (2, 2),
            'png': (2, 2),
            'gif': (2, 2),
            'hdr': (2, 2),
            'bmp': (2, 2),
            'tiff': (2, 5),
            'ras': (2, 2),
            'pnm': (2, 2),
            'ppm': (2, 2),
            'pgm': (2, 2),
            'pbm': (2, 2),
            'npy': (0, 5),
            'hdf5': (0, 5),
            }

    # { extension : [allowed_num_channels] }
    colors = {'jpg': (1,),
              'png': (1, 3,),
              'gif': (1, 3,),
              'hdr': (3,),
              'bmp': (1, 3,),
              'tiff': (),
              'ras': (1, 3,),
              'pnm': (1, 3,),
              'ppm': (1, 3,),
              'pgm': (1,),
              'pbm': (1,),  # vigra outputs p[gn]m
              'npy': (),  # empty means "no restriction on number of channels"
              'hdf5': (), # ditto
              }

    @classmethod
    def check(cls, taggedShape, dtype, fmt):
        # get number of channels
        c = 1
        if 'c' in taggedShape:
            c = taggedShape['c']

        s = np.sum([1 for k in taggedShape if taggedShape[k] > 1 and k in 'txyz'])

        fmtparts = fmt.split()
        ind = -1 # where to find the 'real' format name within the format name string.

        # If exporting a sequence/multipage format, the "real" dimensionality is 
        #  reduced because one spatial axis is consumed as the "step" axis.
        if 'sequence' in fmt:
            s -= 1
            ind -= 1
        if 'multipage' in fmt:
            s -= 1

        if 'sequence' in fmt and 'multipage' in fmt:
            # For sequences of multipage tiffs, any number of channels is permitted as long 
            #   as it is one of the leading axes (i.e. the files or pages are split across channels).
            # In that case, each page will have a single 'channel' in the exported data,
            #  but we have to "undo" the "s -= 1" step from above.
            if 'c' in taggedShape.keys()[0:2]:
                c = 1
                s += 1
        elif 'sequence' in fmt or 'multipage' in fmt:
            # Similarly, for any sequence or multipage tiff, any number of channels is 
            #  permitted as long as it is the first axis (the axis we step across).
            # (See comment above)
            if 'c' == taggedShape.keys()[0]:
                c = 1
                s += 1

        msgs = []
        realfmt = fmtparts[ind]

        # map format to canonical version
        if realfmt == 'jpeg':
            realfmt = 'jpg'
        if realfmt == 'tif':
            realfmt = 'tiff'

        if not realfmt in cls.axes:
            return "Unknown format {}".format(realfmt)

        if dtype not in cls.dtypes[realfmt]:
            msgs.append("data type {} not supported by format {}".format(dtype, realfmt))

        if s < cls.axes[realfmt][0] or s > cls.axes[realfmt][1]:
            msgs.append("wrong number of non-channel axes for format {}".format(realfmt))

        if len(cls.colors[realfmt]) > 0 and c not in cls.colors[realfmt]:
            msgs.append("wrong number of channels for format {}".format(realfmt))

        return "; ".join(msgs)

