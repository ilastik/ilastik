import numpy

from lazyflow.utility import format_known_keys
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiFromShape
from lazyflow.operators import OpSubRegion, OpPixelOperator
from lazyflow.operators.opReorderAxes import OpReorderAxes

from .opExportSlot import OpExportSlot

class OpFormattedDataExport(Operator):
    """
    Wraps OpExportSlot, but with optional preprocessing:
    - cut out a subregion
    - renormalize the data
    - convert to a different dtype
    - transpose axis order
    """
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
    OutputFilenameFormat = InputSlot(value='RESULTS_{roi}') # A format string allowing {roi}, {x_start}, {x_stop}, etc.
    OutputInternalPath = InputSlot(value='exported_data')
    OutputFormat = InputSlot(value='hdf5')

    ImageToExport = OutputSlot() # Preview of the pre-processed image that will be exported
    ExportPath = OutputSlot() # Location of the saved file after export is complete.
    
    # Simplified block diagram:
    #
    # Input -> opSubRegion -> opNormalizeAndConvert -> opReorderAxes -> opExportSlot
    #                                                               \
    #                                                                -> ImageToExport
    
    def __init__(self, *args, **kwargs):
        super( OpFormattedDataExport, self ).__init__(*args, **kwargs)
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
            # FIXME: If the original_axistags have no channel axis but the new image has multiple channels,
            #        append a channel axis.  Potentially an issue for 't' as well.
            original_axistags = self.Input.meta.original_axistags or self.Input.meta.axistags
            self._opReorderAxes.AxisOrder.setValue( "".join( tag.key for tag in original_axistags ) )

        # Prepare subregion operator
        total_roi = roiFromShape( self.Input.meta.shape )
        total_roi = map( tuple, total_roi )
        if self.RegionStart.ready():
            self._opSubRegion.Start.connect( self.RegionStart )
        else:
            self._opSubRegion.Start.disconnect()
            self._opSubRegion.Start.setValue( total_roi[0] )

        if self.RegionStop.ready():
            self._opSubRegion.Stop.connect( self.RegionStop )
        else:
            self._opSubRegion.Stop.disconnect()
            self._opSubRegion.Stop.setValue( total_roi[1] )
        
        # Set up normalization and dtype conversion
        export_dtype = self.Input.meta.dtype
        if self.ExportDtype.ready():
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

        # use partial formatting to fill in non-coordinate name fields
        name_format = self.OutputFilenameFormat.value
        partially_formatted_path = format_known_keys( name_format, known_keys )
        self._opExportSlot.OutputFilenameFormat.setValue( partially_formatted_path )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here"
    
    def propagateDirty(self, slot, subindex, roi):
        self._dirty = True

    def run_export(self):
        self._opExportSlot.run_export()
