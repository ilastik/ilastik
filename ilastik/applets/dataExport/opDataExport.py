import os

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility import OrderedSignal, getPathVariants, format_known_keys
from lazyflow.operators.ioOperators import OpFormattedDataExport

class OpExportLaneResult(Operator):
    """
    Top-level operator for the export applet.
    Mostly a simple wrapper for OpProcessedDataExport, but with extra formatting of the export path based on lane attributes.
    """
    RawData = InputSlot(optional=True) # Display only

    # The dataset info for the original dataset (raw data)
    # If not provided, {nickname} and {dataset_dir} are not allowed in the filename format string
    RawDatasetInfo = InputSlot()
    WorkingDirectory = InputSlot() # Non-absolute paths are relative to this directory.  If not provided, paths must be absolute.
    
    Input = InputSlot()

    # Subregion params
    RegionStart = InputSlot(optional=True)
    RegionStop = InputSlot(optional=True)

    # Normalization params    
    InputMin = InputSlot(optional=True)
    InputMax = InputSlot(optional=True)
    ExportMin = InputSlot(optional=True)
    ExportMax = InputSlot(optional=True)

    ExportDtype = InputSlot(optional=True)
    OutputAxisOrder = InputSlot(optional=True)
    
    # File settings
    OutputFilenameFormat = InputSlot(value='{dataset_dir}/{nickname}_RESULTS') # A format string allowing {dataset_dir} {nickname}, {roi}, {x_start}, {x_stop}, etc.
    OutputInternalPath = InputSlot(value='exported_data')
    OutputFormat = InputSlot(value='hdf5')

    ConvertedImage = OutputSlot() # Not yet re-ordered
    ImageToExport = OutputSlot()
    ExportPath = OutputSlot() # Location of the saved file after export is complete.

    def __init__(self, *args, **kwargs):
        super( OpExportLaneResult, self ).__init__(*args, **kwargs)
        
        self._opFormattedExport = OpFormattedDataExport( parent=self )
        opFormattedExport = self._opFormattedExport

        # Forward almost all inputs to the 'real' exporter
        opFormattedExport.Input.connect( self.Input )
        opFormattedExport.RegionStart.connect( self.RegionStart )
        opFormattedExport.RegionStop.connect( self.RegionStop )
        opFormattedExport.InputMin.connect( self.InputMin )
        opFormattedExport.InputMax.connect( self.InputMax )
        opFormattedExport.ExportMin.connect( self.ExportMin )
        opFormattedExport.ExportMax.connect( self.ExportMax )
        opFormattedExport.ExportDtype.connect( self.ExportDtype )
        opFormattedExport.OutputAxisOrder.connect( self.OutputAxisOrder )
        opFormattedExport.OutputInternalPath.connect( self.OutputInternalPath )
        opFormattedExport.OutputFormat.connect( self.OutputFormat )        
        
        self.ConvertedImage.connect( opFormattedExport.ConvertedImage )
        self.ImageToExport.connect( opFormattedExport.ImageToExport )
        self.ExportPath.connect( opFormattedExport.ExportPath )
        
    def setupOutputs(self):
        rawInfo = self.RawDatasetInfo.value
        known_keys = {}        
        known_keys['nickname'] = rawInfo.nickname
        known_keys['dataset_dir'] = os.path.split(rawInfo.filePath)[0]

        # use partial formatting to fill in non-coordinate name fields
        name_format = self.OutputFilenameFormat.value
        partially_formatted_name = format_known_keys( name_format, known_keys )
        
        # Convert to absolute path
        abs_path, _ = getPathVariants( partially_formatted_name, self.WorkingDirectory.value )
        self._opFormattedExport.OutputFilenameFormat.setValue( abs_path )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here"
    
    def propagateDirty(self, slot, subindex, roi):
        print "TODO"

    def run_export(self):
        self._opFormattedExport.run_export()

