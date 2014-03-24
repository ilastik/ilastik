import warnings

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OperatorWrapper, OpSingleChannelSelector, \
    OpMultiArraySlicer, OpCompressedCache

# OpMultiArraySlicer2, OpPixelOperator, OpVigraLabelVolume, OpFilterLabels, \
# OpCompressedCache, OpColorizeLabels, , \
# OpMultiArrayStacker, 

# import numpy as np
import vigra

class OpMriVolPreproc( Operator ):
    name = "opMriVolPrepoc5d"
    
    # RawInput = InputSlot(optional=True) # Display only
    PredImage = InputSlot() # Prediction image
    Sigma = InputSlot(stype='float', value=1.0)

    Output = OutputSlot()
    # CachedOutput = OutputSlot() # For the GUI (blockwise-access)

    # For serialization
    # InputHdf5 = InputSlot(optional=True)
    # OutputHdf5 = OutputSlot()
    # CleanBlocks = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpMriVolPreproc, self).__init__(*args, **kwargs)

        '''
        self._opTimeSlicer = OpMultiArraySlicer(parent=self)
        self._opTimeSlicer.AxisFlag.setValue('t')
        self._opTimeSlicer.Input.connect( self.PredImage )
        assert self._opTimeSlicer.Slices.level == 1
        self._opChannelSelector = OperatorWrapper(OpSingleChannelSelector, 
                                                  parent = self )
        self._opChannelSelector.Input.connect( self._opTimeSlicer.Slices )
        '''

        #cache our own output, don't propagate from internal operator
        # self._opCache = OpCompressedCache( parent=self )
        # self._opCache.name = "OpMriVolPreproc._opCache"
        # self._opCache.InputHdf5.connect( self.InputHdf5 )
        
        # self.CachedOutput.connect(self._opCache.Output)
        
        # Serialization outputs
        # self.CleanBlocks.connect( self._opCache.CleanBlocks )
        # self.OutputHdf5.connect( self._opCache.OutputHdf5 )

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."
        
    def propagateDirty(self, slot, subindex, roi):
        print 'dirty'
        pass # Nothing to do...
