import os
import string
import numpy
import vigra
import h5py

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiFromShape
from lazyflow.utility import OrderedSignal, getPathVariants
from lazyflow.operators import OpSubRegion, OpPixelOperator
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.ioOperators import OpH5WriterBigDataset

class OpDataExport(Operator):
    RawData = InputSlot(optional=True)
    Input = InputSlot()

    # Subregion params
    RegionStart = InputSlot(optional=True)
    RegionStop = OutputSlot(optional=True)

    # Normalization params    
    InputMin = InputSlot(optional=True)
    InputMax = InputSlot(optional=True)
    ExportMin = InputSlot(optional=True)
    ExportMax = InputSlot(optional=True)

    ExportDtype = InputSlot()
    OutputAxisOrder = InputSlot(optional=True) # If not provided, use input axistag order
    
    # File settings
    WorkingDirectory = InputSlot() # The project file directory
    OutputFilenameFormat = InputSlot(value='{dataset_dir}/{nickname}_RESULTS') # A format string allowing {dataset_dir} {nickname}, {roi}, {x_start}, {x_stop}, etc.
    OutputInternalPath = InputSlot(value='exported_data')
    OutputFormat = InputSlot(value='hdf5')

    # The dataset info for the original dataset (raw data)
    # If not provided, {nickname} and {dataset_dir} are not allowed in the filename format string
    RawDatasetInfo = InputSlot(optional=True)
    
    ImageToExport = OutputSlot()
    ExportPath = OutputSlot() # Location of the saved file after export is complete.
    
    # Input -> OpSubRegion -> OpNormalize -> ImageToExport
    
    def __init__(self, *args, **kwargs):
        super( OpDataExport, self ).__init__(*args, **kwargs)
        self._dirty = True
        
        opSubRegion = OpSubRegion( parent=self )
        opSubRegion.Input.connect( self.Input )
        opSubRegion.Start.connect( self.RegionStart )
        opSubRegion.Stop.connect( self.RegionStop )
        self._opSubRegion = opSubRegion
        
        opNormalizeAndConvert = OpPixelOperator( parent=self )
        opNormalizeAndConvert.Input.connect( opSubRegion.Output )
        self._opNormalizeAndConvert = opNormalizeAndConvert
        
        opReorderAxes = OpReorderAxes( parent=self )
        opReorderAxes.Input.connect( opNormalizeAndConvert.Output )
        self._opReorderAxes = opReorderAxes

        self.ImageToExport.connect( opReorderAxes.Output )
        
        self._opExportSlot = OpExportSlot( parent=self )
        self._opExportSlot.Input.connect( opReorderAxes.Output )
        self._opExportSlot.CoordinateOffset.connect( self.RegionStart )
        self._opExportSlot.OutputInternalPath.connect( self.OutputInternalPath )
        self._opExportSlot.OutputFormat.connect( self.OutputFormat )
        
        self.ExportPath.connect( self._opExportSlot.ExportPath )

    def setupOutputs(self):
        # Use user-provided axis order if specified
        if self.OutputAxisOrder.ready():
            self._opReorderAxes.AxisOrder.setValue( self.OutputAxisOrder.value )
        else:
            # Use original order, if present
            original_axistags = self.Input.meta.original_axistags or self.Input.meta.axistags
            self._opReorderAxes.AxisOrder.setValue( "".join( tag.key for tag in original_axistags ) )

        # Prepare subregion
        total_roi = roiFromShape( self.Input.meta.shape )
        if self.RegionStart.ready():
            self._opSubRegion.Start.connect( self.RegionStart )
        else:
            self._opSubRegion.Start.setValue( total_roi[0] )

        if self.RegionStop.ready():
            self._opSubRegion.Stop.connect( self.RegionStop )
        else:
            self._opSubRegion.Stop.setValue( total_roi[1] )
        
        # Set up normalization/dtype conversion
        export_dtype = self.ExportDtype.value
        need_normalize = ( self.InputMin.ready() and 
                           self.InputMax.ready() and 
                           self.ExportMin.ready() and 
                           self.ExportMax.ready() )
        if need_normalize:
            minVal, maxVal = self.InputMin.value, self.InputMax.value
            outputMinVal, outputMaxVal = self.ExportMin.value, self.ExportMax.value
            def normalize(a):
                frac = numpy.float32(outputMaxVal - outputMinVal) / numpy.float32(maxVal - minVal)
                return numpy.asarray(outputMinVal + (a - minVal) * frac, export_dtype)
            self._opNormalizeAndConvert.Function.setValue( normalize )
        else:
            # No normalization: just identity function with dtype conversion
            self._opNormalizeAndConvert.Function.setValue( lambda a: numpy.asarray(a, export_dtype) )

        # Obtain values for possible name fields
        roi = [ tuple(self._opSubRegion.Start.value), tuple(self._opSubRegion.Stop.value) ]
        known_keys = { 'roi' : roi }        
        if self.RawDatasetInfo.ready():
            rawInfo = self.RawDatasetInfo.value
            known_keys['nickname'] = rawInfo.nickname
            known_keys['dataset_dir'] = os.path.split(rawInfo.filePath)[0]

        # use partial formatting to fill in non-coordinate name fields
        name_format = self.OutputFilenameFormat.value
        partially_formatted_name = _format_known_keys( name_format, known_keys )
        
        # Convert to absolute path
        abs_path, _ = getPathVariants( partially_formatted_name, self.WorkingDirectory.value )
        self._opExportSlot.OutputFilenameFormat.setValue( abs_path )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here"
    
    def propagateDirty(self, slot, subindex, roi):
        self._dirty = True

    def run_export(self):
        self._opExportSlot.run_export()

class OpExportSlot(Operator):
    # TODO: Put this in lazyflow? (It intentionally avoids using ilastik-specific concepts like DatasetInfo)
    Input = InputSlot()
    
    OutputFormat = InputSlot() # string.  See formats, below
    OutputFilenameFormat = InputSlot() # A format string allowing {roi}, {t_start}, {t_stop}, etc (but not {nickname} or {dataset_dir})
    OutputInternalPath = InputSlot(value='exported_data')

    CoordinateOffset = InputSlot(optional=True) # Add an offset to the roi coordinates in the export path (useful if Input is a subregion of a larger dataset)

    ExportPath = OutputSlot()

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
        export_impls['tiff sequence'] = ('tiff', self._export_tiff_sequence)
        export_impls['multipage tiff'] = ('tiff', self._export_multipage_tiff)
        self._export_impls = export_impls
    
    def setupOutputs(self):
        self.ExportPath.meta.shape = (1,)
        self.ExportPath.meta.dtype = object
    
    def execute(self, slot, subindex, roi, result):
        assert slot == self.ExportPath, "Unknown output slot: {}".format( slot.name )
        path_format = self.OutputFilenameFormat.value
        file_extension = self._export_impls[ self.OutputFormat.value ][0]
        
        # Remove existing extension (if present) and add the correct extension
        path_format = os.path.splitext(path_format)[0]
        path_format += '.' + file_extension

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
        formatted_path = _format_known_keys( path_format, optional_replacements )
        result[0] = formatted_path
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
        export_path = self.ExportPath.value
        with h5py.File(export_path, 'w') as hdf5File:
            # Create a temporary operator to do the work for us
            opH5Writer = OpH5WriterBigDataset(parent=self)
            try:
                opH5Writer.hdf5File.setValue( hdf5File )
                opH5Writer.hdf5Path.setValue( self.OutputInternalPath.value )
                opH5Writer.Image.connect( self.Input )
        
                # The H5 Writer provides it's own progress signal, so just connect ours to it.
                opH5Writer.progressSignal.subscribe( self.progressSignal )

                # Perform the export and block for it in THIS THREAD.
                opH5Writer.WriteImage[:].wait()
            finally:
                opH5Writer.cleanUp()
                self.progressSignal(100)

    def _export_npy(self): pass
    def _export_tiff_sequence(self): pass
    def _export_multipage_tiff(self): pass

def _format_known_keys(s, entries):
    # Like str.format(), but 
    #  (1) accepts only a dict and 
    #  (2) allows the dict to be incomplete, 
    #      in which case those entries are left alone.
    fmt = string.Formatter()
    it = fmt.parse(s)
    s = ''
    for i in it:
        if i[1] in entries:
            val = entries[ i[1] ]
            s += i[0] + fmt.format_field( val, i[2] )
        else:
            # Replicate the original stub
            s += i[0]
            if i[1] or i[2]:
                s += '{'
            if i[1]:
                s += i[1]
            if i[2]:
                s += ':' + i[2]
            if i[1] or i[2]:
                s += '}'
    return s

if __name__ == "__main__":
    print _format_known_keys("Hello, {first_name}, my name is {my_name}", {'first_name' : 'Jim', 'my_name' : "Jon"})
    print _format_known_keys("Hello, {first_name:}, my name is {my_name}!", {"first_name" : [1,2,2]})
    