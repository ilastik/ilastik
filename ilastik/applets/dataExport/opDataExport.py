import collections
import numpy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility import PathComponents, getPathVariants, format_known_keys
from lazyflow.operators.ioOperators import OpInputDataReader, OpFormattedDataExport
from lazyflow.operators.generic import OpSubRegion

class OpDataExport(Operator):
    """
    Top-level operator for the export applet.
    Mostly a simple wrapper for OpProcessedDataExport, but with extra formatting of the export path based on lane attributes.
    """
    TransactionSlot = InputSlot()   # To apply all settings in one 'transaction', 
                                    # disconnect this slot and reconnect it when all slots are ready

    RawData = InputSlot(optional=True) # Display only
    FormattedRawData = OutputSlot() # OUTPUT - for overlaying the transformed raw data with the export data.

    # The dataset info for the original dataset (raw data)
    RawDatasetInfo = InputSlot()
    WorkingDirectory = InputSlot() # Non-absolute paths are relative to this directory.  If not provided, paths must be absolute.
    
    Input = InputSlot() # The results slot we want to export

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
    OutputFilenameFormat = InputSlot(value='{dataset_dir}/{nickname}_export') # A format string allowing {dataset_dir} {nickname}, {roi}, {x_start}, {x_stop}, etc.
    OutputInternalPath = InputSlot(value='exported_data')
    OutputFormat = InputSlot(value='hdf5')
    
    ExportPath = OutputSlot() # Location of the saved file after export is complete.
    
    ConvertedImage = OutputSlot() # Cropped image, not yet re-ordered (useful for guis)
    ImageToExport = OutputSlot() # The image that will be exported

    ImageOnDisk = OutputSlot() # This slot reads the exported image from disk (after the export is complete)
    Dirty = OutputSlot() # Whether or not the result currently matches what's on disk
    FormatSelectionIsValid = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpDataExport, self ).__init__(*args, **kwargs)
        
        self._opFormattedExport = OpFormattedDataExport( parent=self )
        opFormattedExport = self._opFormattedExport

        # Forward almost all inputs to the 'real' exporter
        opFormattedExport.TransactionSlot.connect( self.TransactionSlot )
        opFormattedExport.Input.connect( self.Input )
        opFormattedExport.RegionStart.connect( self.RegionStart )
        opFormattedExport.RegionStop.connect( self.RegionStop )
        opFormattedExport.InputMin.connect( self.InputMin )
        opFormattedExport.InputMax.connect( self.InputMax )
        opFormattedExport.ExportMin.connect( self.ExportMin )
        opFormattedExport.ExportMax.connect( self.ExportMax )
        opFormattedExport.ExportDtype.connect( self.ExportDtype )
        opFormattedExport.OutputAxisOrder.connect( self.OutputAxisOrder )
        opFormattedExport.OutputFormat.connect( self.OutputFormat )
        
        self.ConvertedImage.connect( opFormattedExport.ConvertedImage )
        self.ImageToExport.connect( opFormattedExport.ImageToExport )
        self.ExportPath.connect( opFormattedExport.ExportPath )
        self.FormatSelectionIsValid.connect( opFormattedExport.FormatSelectionIsValid )
        self.progressSignal = opFormattedExport.progressSignal

        self.Dirty.setValue(True) # Default to Dirty

        self._opImageOnDiskProvider = None

        # We don't export the raw data, but we connect it to it's own op 
        #  so it can be displayed alongside the data to export in the same viewer.  
        # This keeps axis order, shape, etc. in sync with the displayed export data.
        # Note that we must not modify the channels of the raw data, so it gets passed throught a helper.
        opHelper = OpRawSubRegionHelper( parent=self )
        opHelper.RawImage.connect( self.RawData )
        opHelper.ExportStop.connect( self.RegionStart )        
        opHelper.ExportStop.connect( self.RegionStop )

        opFormatRaw = OpFormattedDataExport( parent=self )
        opFormatRaw.TransactionSlot.connect( self.TransactionSlot )
        opFormatRaw.Input.connect( self.RawData )
        opFormatRaw.RegionStart.connect( opHelper.RawStart )
        opFormatRaw.RegionStop.connect( opHelper.RawStop )
        opFormatRaw.InputMin.connect( self.InputMin )
        opFormatRaw.InputMax.connect( self.InputMax )
        opFormatRaw.ExportMin.connect( self.ExportMin )
        opFormatRaw.ExportMax.connect( self.ExportMax )
        opFormatRaw.ExportDtype.connect( self.ExportDtype )
        opFormatRaw.OutputAxisOrder.connect( self.OutputAxisOrder )
        opFormatRaw.OutputFormat.connect( self.OutputFormat )
        self._opFormatRaw = opFormatRaw
        self.FormattedRawData.connect( opFormatRaw.ImageToExport )

    def cleanupOnDiskView(self):
        if self._opImageOnDiskProvider is not None:
            self.ImageOnDisk.disconnect()
            self._opImageOnDiskProvider.cleanUp()
            self._opImageOnDiskProvider = None

    def setupOnDiskView(self):
        # Set up the output that let's us view the exported file
        self._opImageOnDiskProvider = OpImageOnDiskProvider( parent=self )
        self._opImageOnDiskProvider.TransactionSlot.connect( self.TransactionSlot )
        self._opImageOnDiskProvider.Input.connect( self.ImageToExport )
        self._opImageOnDiskProvider.WorkingDirectory.connect( self.WorkingDirectory )
        self._opImageOnDiskProvider.DatasetPath.connect( self._opFormattedExport.ExportPath )
        self._opImageOnDiskProvider.Dirty.connect( self.Dirty )
        self.ImageOnDisk.connect( self._opImageOnDiskProvider.Output )
        
    def setupOutputs(self):
        self.cleanupOnDiskView()        

        rawInfo = self.RawDatasetInfo.value
        dataset_dir = PathComponents(rawInfo.filePath).externalDirectory
        abs_dataset_dir, _ = getPathVariants(dataset_dir, self.WorkingDirectory.value)
        known_keys = {}        
        known_keys['dataset_dir'] = abs_dataset_dir
        known_keys['nickname'] = rawInfo.nickname

        # Disconnect to open the 'transaction'
        if self._opImageOnDiskProvider is not None:
            self._opImageOnDiskProvider.TransactionSlot.disconnect()
        self._opFormattedExport.TransactionSlot.disconnect()

        # Blank the internal path while we manipulate the external path
        #  to avoid invalid intermediate states of ExportPath
        self._opFormattedExport.OutputInternalPath.setValue( "" )

        # use partial formatting to fill in non-coordinate name fields
        name_format = self.OutputFilenameFormat.value
        partially_formatted_name = format_known_keys( name_format, known_keys )
        
        # Convert to absolute path before configuring the internal op
        abs_path, _ = getPathVariants( partially_formatted_name, self.WorkingDirectory.value )
        self._opFormattedExport.OutputFilenameFormat.setValue( abs_path )

        # use partial formatting on the internal dataset name, too
        internal_dataset_format = self.OutputInternalPath.value 
        partially_formatted_dataset_name = format_known_keys( internal_dataset_format, known_keys )
        self._opFormattedExport.OutputInternalPath.setValue( partially_formatted_dataset_name )

        # Re-connect to finish the 'transaction'
        self._opFormattedExport.TransactionSlot.connect( self.TransactionSlot )
        if self._opImageOnDiskProvider is not None:
            self._opImageOnDiskProvider.TransactionSlot.connect( self.TransactionSlot )
        
        self.setupOnDiskView()

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here"
    
    def propagateDirty(self, slot, subindex, roi):
        # Out input data changed, so we have work to do when we get executed.
        self.Dirty.setValue(True)

    def run_export(self):
        # If we're not dirty, we don't have to do anything.
        if self.Dirty.value:
            self.cleanupOnDiskView()
            self._opFormattedExport.run_export()
            self.Dirty.setValue( False )
            self.setupOnDiskView()

class OpRawSubRegionHelper(Operator):
    RawImage = InputSlot()
    ExportStart = InputSlot(optional=True)
    ExportStop = InputSlot(optional=True)
    
    RawStart = OutputSlot()
    RawStop = OutputSlot()
    
    def setupOutputs(self):
        tagged_shape = self.RawImage.meta.getTaggedShape()
        if self.ExportStart.ready():
            tagged_start = collections.OrderedDict( zip( self.RawImage.meta.getAxisKeys(), self.ExportStart.value ) )
            tagged_start['c'] = tagged_shape['c']
            self.RawStart.setValue( tagged_start.values() )
        else:
            self.RawStart.meta.NOTREADY = True
            
        if self.ExportStop.ready():
            tagged_stop = collections.OrderedDict( zip( self.RawImage.meta.getAxisKeys(), self.ExportStop.value ) )
            tagged_stop['c'] = tagged_shape['c']
            self.RawStop.setValue( tagged_stop.values() )
        else:
            self.RawStop.meta.NOTREADY = True

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here"
    
    def propagateDirty(self, slot, subindex, roi):
        pass # No need to do anything here.

class OpImageOnDiskProvider(Operator):
    """
    This simply wraps a lazyflow OpInputDataReader, but provides a default output if the file doesn't exist yet.
    """
    TransactionSlot = InputSlot()
    Input = InputSlot() # Used for dtype and shape only. Data is always provided directly from the file.

    WorkingDirectory = InputSlot()
    DatasetPath = InputSlot() # A TOTAL path (possibly including a dataset name, e.g. myfile.h5/volume/data
    Dirty = InputSlot()
    
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpImageOnDiskProvider, self ).__init__(*args, **kwargs)
        self._opReader = None
    
    def setupOutputs( self ):
        if self._opReader is not None:
            self.Output.disconnect()
            self._opReader.cleanUp()
            self._opReader = None

        try:
            # Configure the reader
            dataReady = True
            self._opReader = OpInputDataReader( parent=self )
            self._opReader.WorkingDirectory.setValue( self.WorkingDirectory.value )
            self._opReader.FilePath.setValue( self.DatasetPath.value )

            dataReady &= self._opReader.Output.meta.shape == self.Input.meta.shape
            dataReady &= self._opReader.Output.meta.dtype == self.Input.meta.dtype
            if dataReady:
                self.Output.connect( self._opReader.Output )
            else:
                self._opReader.cleanUp()
                self._opReader = None
                self.Output.meta.NOTREADY = True

        except OpInputDataReader.DatasetReadError:
            # Note: If the data is exported as a 'sequence', then this will always be NOTREADY
            #       because the 'path' (e.g. 'myfile_{slice_index}.png' will be nonexistent.
            #       That's okay because a stack is probably too slow to be of use for a preview anyway.
            self._opReader.cleanUp()
            self._opReader = None
            # The dataset doesn't exist yet.
            self.Output.meta.NOTREADY = True

    def execute(self, slot, subindex, roi, result):
        assert False, "Output is supposed to be directly connected to an internal operator."

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            self.Output.setDirty( roi )
        else:
            self.Output.setDirty( slice(None) )

def get_model_op(wrappedOp):
    """
    Create a "model operator" that the gui can use.  
    The model op is a single (non-wrapped) export operator that the 
    gui will manipulate while the user plays around with the export 
    settings.  When the user is finished, the model op slot settings can 
    be copied over to the 'real' (wrapped) operator slots. 
    """
    if len( wrappedOp ) == 0:
        return

    # These are the slots the export settings gui will manipulate.
    setting_slots = [ wrappedOp.RegionStart,
                      wrappedOp.RegionStop,
                      wrappedOp.InputMin,
                      wrappedOp.InputMax,
                      wrappedOp.ExportMin,
                      wrappedOp.ExportMax,
                      wrappedOp.ExportDtype,
                      wrappedOp.OutputAxisOrder,
                      wrappedOp.OutputFilenameFormat,
                      wrappedOp.OutputInternalPath,
                      wrappedOp.OutputFormat ]

    # Use an instance of OpFormattedDataExport, since has the important slots and no others.
    model_op = OpFormattedDataExport( parent=wrappedOp.parent )
    for slot in setting_slots:
        model_inslot = getattr(model_op, slot.name)
        if slot.ready():
            model_inslot.setValue( slot.value )

    # Choose a roi that can apply to all images in the original operator
    shape = None
    axes = None
    for slot in wrappedOp.Input:
        assert slot.ready()
        if shape is None:
            shape = slot.meta.shape
            axes = slot.meta.getAxisKeys()
            dtype = slot.meta.dtype
        else:
            assert slot.meta.getAxisKeys() == axes, "Can't export multiple slots with different axes."
            assert slot.meta.dtype == dtype
            shape = numpy.minimum( slot.meta.shape, shape )

    # Must provide a 'ready' slot for the gui
    # Use a subregion operator to provide a slot with the meta data we chose.
    opSubRegion = OpSubRegion( parent=wrappedOp.parent )
    opSubRegion.Start.setValue( (0,)*len(shape) )
    opSubRegion.Stop.setValue( tuple(shape) )
    opSubRegion.Input.connect( slot )
    
    # (The actual contents of this slot are not important to the settings gui.
    #  It only cares about the metadata.)
    model_op.Input.connect( opSubRegion.Output )

    return model_op








