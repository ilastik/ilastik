import os
import numpy
import vigra
import h5py
from functools import partial

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import TinyVector, roiFromShape
from lazyflow.utility import OrderedSignal, format_known_keys, PathComponents
from lazyflow.operators.ioOperators import OpH5WriterBigDataset, OpNpyWriter, OpExport2DImage, OpStackWriter

class OpExportSlot(Operator):
    """
    Export a slot 'as-is', i.e. no subregion, no dtype conversion, no normalization, no axis re-ordering, etc.
    For sequence export formats, the sequence is indexed by the axistags' FIRST axis.
    For example, txyzc produces a sequence of xyzc volumes.
    """
    # TODO: Put this in lazyflow? (It intentionally avoids using ilastik-specific concepts like DatasetInfo)
    Input = InputSlot()
    
    OutputFormat = InputSlot(value='hdf5') # string.  See formats, below
    OutputFilenameFormat = InputSlot() # A format string allowing {roi}, {t_start}, {t_stop}, etc (but not {nickname} or {dataset_dir})
    OutputInternalPath = InputSlot(value='exported_data')

    CoordinateOffset = InputSlot(optional=True) # Add an offset to the roi coordinates in the export path (useful if Input is a subregion of a larger dataset)

    ExportPath = OutputSlot()
    SupportedFormats = OutputSlot()

    _2d_formats = vigra.impex.listExtensions().split()
    _3d_sequence_formats = map( lambda s: s + ' sequence', _2d_formats )
    FORMATS = [ 'hdf5', 'npy' ] + _2d_formats + _3d_sequence_formats + ['multipage tiff', 'multipage tiff sequence']

    def __init__(self, *args, **kwargs):
        super( OpExportSlot, self ).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()

        # Set up the impl function lookup dict
        export_impls = {}
        export_impls['hdf5'] = ('h5', self._export_hdf5)
        export_impls['npy'] = ('npy', self._export_npy)
        
        for fmt in self._2d_formats:
            export_impls[fmt] = (fmt, partial(self._export_2d, fmt) )
            export_impls[fmt + ' sequence'] = (fmt, partial(self._export_2d_sequence, fmt) )
        export_impls['multipage tiff'] = ('tiff', self._export_multipage_tiff)
        export_impls['multipage tiff sequence'] = ('tiff', self._export_multipage_tiff_sequence)
        self._export_impls = export_impls
    
    def setupOutputs(self):
        self.ExportPath.meta.shape = (1,)
        self.ExportPath.meta.dtype = object
        
        if self.OutputFormat.value == 'hdf5' and self.OutputInternalPath.value == "":
            self.ExportPath.meta.NOTREADY = True
    
    def execute(self, slot, subindex, roi, result):
        if slot == self.ExportPath:
            return self._executeExportPath(result)
        if slot == self.SupportedFormats:
            return self._executeSupportedFormats(result)
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

    def _executeSupportedFormats(self, result):
        # Start with hdf5 and npy, because they support everything
        supported_formats = ['hdf5', 'npy']

        # Count the number of non-singleton axes
        dimensionality = sum( TinyVector(self.Input.meta.shape) > 1 )

        if dimensionality <= 2:
            supported_formats += OpExportSlot._2d_formats
        if dimensionality == 3:
            supported_formats += OpExportSlot._3d_sequence_formats
            supported_formats += ['multipage tiff']
        if dimensionality == 4:
            supported_formats += ['multipage tiff sequence']

        result[0] = supported_formats
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.OutputFormat or slot == self.OutputFilenameFormat:
            self.ExportPath.setDirty()

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
            assert "Unknown export format: {}".format( output_format )

        export_func()
    
    def _export_hdf5(self):
        self.progressSignal( 0 )

        # Create and open the hdf5 file
        export_components = PathComponents(self.ExportPath.value)
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
    
    def _export_2d_sequence(self, fmt):
        self.progressSignal(0)
        export_path_pattern = self.ExportPath.value
        directory, filename = os.path.split(export_path_pattern)
        
        try:
            # Find the non-singleton axes (not counting channel).
            # Choose last 2 non-singleton axes as the axes of the slices.
            tagged_items = self.ImageToExport.getTaggedShape().items()
            filtered_items = filter( lambda (k, v): k != 'c' and v > 1, tagged_items )
            filtered_axes = zip( *filtered_items )[0]
            assert len(filtered_axes) <= 3
            
            opWriter = OpStackWriter( parent=self )
            opWriter.ImageAxesNames.setValue( filtered_axes[-2:] )
            opWriter.Filepath.setValue( directory )
            opWriter.Filepath.setValue( filename )
            opWriter.Filetype.setValue( fmt )
            opWriter.Image.connect( self.Input )
            
            # Run the export
            opWriter.run_export()
        finally:
            opWriter.cleanUp()
            self.progressSignal(100)
    
    def _export_multipage_tiff(self): pass
    def _export_multipage_tiff_sequence(self): pass
































