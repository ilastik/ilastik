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
                                           OpExportMultipageTiff, OpExportMultipageTiffSequence

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
    FormatSelectionIsValid = OutputSlot()

    _2d_exts = vigra.impex.listExtensions().split()    

    # List all supported formats
    _2d_formats = map( lambda ext: FormatInfo(ext, ext, 2, 2), _2d_exts)
    _3d_sequence_formats = map( lambda ext: FormatInfo(ext + ' sequence', ext, 3, 3), _2d_exts)
    _3d_volume_formats = [ FormatInfo('multipage tiff', 'tiff', 3, 3) ]
    _4d_sequence_formats = [ FormatInfo('multipage tiff sequence', 'tiff', 4, 4) ]
    nd_format_formats = [ FormatInfo('hdf5', 'h5', 0, 5),
                        FormatInfo('numpy', 'npy', 0, 5)]
    
    ALL_FORMATS = _2d_formats + _3d_sequence_formats + _3d_volume_formats\
                + _4d_sequence_formats + nd_format_formats

    def __init__(self, *args, **kwargs):
        super( OpExportSlot, self ).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()

        # Set up the impl function lookup dict
        export_impls = {}
        export_impls['hdf5'] = ('h5', self._export_hdf5)
        export_impls['npy'] = ('npy', self._export_npy)
        
        for fmt in self._2d_formats:
            export_impls[fmt.name] = (fmt.extension, partial(self._export_2d, fmt.extension) )

        for fmt in self._3d_sequence_formats:
            export_impls[fmt.name] = (fmt.extension, partial(self._export_3d_sequence, fmt.extension) )

        export_impls['multipage tiff'] = ('tiff', self._export_multipage_tiff)
        export_impls['multipage tiff sequence'] = ('tiff', self._export_multipage_tiff_sequence)
        self._export_impls = export_impls

        self.Input.notifyMetaChanged( self._updateFormatSelectionIsValid )
    
    def setupOutputs(self):
        self.ExportPath.meta.shape = (1,)
        self.ExportPath.meta.dtype = object
        self.FormatSelectionIsValid.meta.shape = (1,)
        self.FormatSelectionIsValid.meta.dtype = object
        
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
        
        # Remove existing extension (if present) and add the correct extension
        path_format = os.path.splitext(path_format)[0]
        path_format += '.' + file_extension

        # Provide the TOTAL path (including dataset name)
        if self.OutputFormat.value == 'hdf5':
            path_format += '/' + self.OutputInternalPath.value

        roi = numpy.array( roiFromShape(self.Input.meta.shape) )
        if self.CoordinateOffset.ready():
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

    def _updateFormatSelectionIsValid(self, *args):
        valid = self._is_format_selection_valid()
        self.FormatSelectionIsValid.setValue( valid )

    def _is_format_selection_valid(self, *args):
        """
        Return True if the currently selected format is valid to export the current input dataset
        """
        if not self.Input.ready():
            return False
        output_format = self.OutputFormat.value

        # hdf5 and npy support all combinations
        if output_format == 'hdf5' or output_format == 'npy':
            return True
        
        tagged_shape = self.Input.meta.getTaggedShape()
        axes = OpStackWriter.get_nonsingleton_axes_for_tagged_shape( tagged_shape )
        output_dtype = self.Input.meta.dtype

        # None of the remaining formats support more than 4 channels.
        if 'c' in tagged_shape and tagged_shape['c'] > 4:
            return False

        # HDR format supports float32 only, and must have exactly 3 channels
        if output_format == 'hdr' or output_format == 'hdr sequence':
            return output_dtype == numpy.float32 and \
                   'c' in tagged_shape and tagged_shape['c'] == 3

        # Apparently, TIFF supports everything but signed byte
        if 'tif' in output_format and output_dtype == numpy.int8:
            return False

        # Apparently, these formats support everything except uint32
        # See http://github.com/ukoethe/vigra/issues/153
        if output_dtype == numpy.uint32 and \
           ( 'pbm' in output_format or \
             'pgm' in output_format or \
             'pnm' in output_format or \
             'ppm' in output_format ):
            return False

        # These formats don't support 2 channels (must be either 1 or 3)
        non_dualband_formats = ['bmp', 'gif', 'jpg', 'jpeg', 'ras']
        for fmt in non_dualband_formats:
            if fmt in output_format and axes[0] != 'c' and 'c' in tagged_shape:
                if 'c' in tagged_shape and tagged_shape['c'] != 1 and tagged_shape['c'] != 3:
                    return False

        # 2D formats only support 2D images (singleton/channel axes excepted)
        if filter(lambda fmt: fmt.name == output_format, self._2d_formats):
            # Examples:
            # OK: 'xy', 'xyc'
            # NOT OK: 'xc', 'xyz'
            nonchannel_axes = filter(lambda a: a != 'c', axes)
            return len(nonchannel_axes) == 2

        nonstep_axes = axes[1:]
        nonchannel_axes = filter( lambda a: a != 'c', nonstep_axes )

        # 3D sequences of 2D images require a 3D image
        # (singleton/channel axes excepted, unless channel is the 'step' axis)
        if filter(lambda fmt: fmt.name == output_format, self._3d_sequence_formats)\
           or output_format == 'multipage tiff':
            # Examples:
            # OK: 'xyz', 'xyzc', 'cxy'
            # NOT OK: 'cxyz'
            return len(nonchannel_axes) == 2

        # 4D sequences of 3D images require a 4D image
        # (singleton/channel axes excepted, unless channel is the 'step' axis)
        if output_format == 'multipage tiff sequence':
            # Examples:
            # OK: 'txyz', 'txyzc', 'cxyz'
            # NOT OK: 'xyzc', 'xyz', 'xyc'
            return len(nonchannel_axes) == 3

        assert False, "Unknown format case: {}".format( output_format )

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.OutputFormat or slot == self.OutputFilenameFormat:
            self.ExportPath.setDirty()
        if slot == self.OutputFormat:
            self._updateFormatSelectionIsValid()

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
    
































