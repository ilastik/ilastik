from lazyflow.graph import Graph, Operator, OperatorWrapper, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot
import copy
from lazyflow.operators import Op5ToMulti, OpMultiInputConcatenater, OpMultiArrayStacker, OpMultiArraySlicer2

class OpGenericViewer(Operator):
    """
    """
    name = "OpGenericViewer"
    category = "Top-level"

    # We have three different inputs.
    # All are optional, and each is treated differently before it is appended to the 

    # Base layer image: Always goes on the bottom with no alpha channel
    BaseLayer = InputSlot()

    # Atomic layer inputs: Displayed as-is (multiple channels, if any, will be displayed in the same layer)
    AtomicLayers = MultiInputSlot( optional=True )
    
    # ChannelSliced inputs: Each channel is sliced out into its own layer
    ChannelwiseLayers = MultiInputSlot( optional=True )

    # Output: The list of layers to be displayed by the applet viewer
    OutputLayers = MultiOutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpGenericViewer, self).__init__(*args, **kwargs)

        # CONNECTION DIAGRAM:
        #
        # self.BaseLayer(level=0) -> opBasePromoter.Output(level=1) -> -----------------------------------------------
        #                                                                                                             \
        # self.AtomicLayers(level=1) -> ------------------------------------------------------------------------------->> opConcatenator.Output(level=1) --> self.OutputLayers(level=1)
        #                                                                                                             /
        # self.ChannelwiseLayers(level=1) -> opChannelStacker.Output(level=0) -> opChannelSlicer.Slices(level=1) -> --
        
        # TODO: Inject metadata...
        
        self.opBasePromoter = Op5ToMulti( graph=self.graph, parent=self )
        self.opBasePromoter.name = 'opBasePromoter'
        self.opBasePromoter.Input0.connect( self.BaseLayer )

        self.opChannelStacker = OpMultiArrayStacker( graph=self.graph, parent=self )
        self.opChannelStacker.Images.connect( self.ChannelwiseLayers )
        self.opChannelStacker.AxisFlag.setValue('c')
        
        self.opChannelSlicer = OpMultiArraySlicer2( graph=self.graph, parent=self )
        self.opChannelSlicer.Input.connect( self.opChannelStacker.Output )
        self.opChannelSlicer.AxisFlag.setValue('c')

        self.opConcatenator = OpMultiInputConcatenater( graph=self.graph, parent=self )
        self.opConcatenator.Inputs.resize(3) # 3 lists to concatenate        
        self.opConcatenator.Inputs[0].connect(self.opBasePromoter.Outputs)
        self.opConcatenator.Inputs[1].connect(self.AtomicLayers)
        self.opConcatenator.Inputs[2].connect(self.opChannelSlicer.Slices)

        self.OutputLayers.connect( self.opConcatenator.Output )

    def setupOutputs(self):
        # All inputs must have the same shape (except for channels)
        multiInputs = []
        if self.BaseLayer.configured():
            multiInputs.append( self.opBasePromoter.Outputs )
        if self.AtomicLayers.configured():
            multiInputs.append( self.AtomicLayers )
        if self.ChannelwiseLayers.configured():
            multiInputs.append( self.ChannelwiseLayers )
        
        checkShape = None
        channelAxisPosition = None
        for multislot in multiInputs:
            for index, imageSlot in enumerate( multislot ):
                if not imageSlot.configured():
                    continue
                
                imageShape = imageSlot.meta.shape
                if checkShape == None:
                    channelAxisPosition = imageSlot.meta.axistags.index('c') # Assumes that the channel axis tag is actually present
                    checkShape = imageShape
                else:
                    # We assume that the channel axis is in the same position for every image
                    assert channelAxisPosition == imageSlot.meta.axistags.index('c'), "All results images must have the same channel axis position"

                    # Remove channel dimension
                    checkShapeNoChannel = list(imageShape).pop(channelAxisPosition)
                    imageShapeNoChannel = list(imageShape).pop(channelAxisPosition)
                    assert imageShapeNoChannel == checkShapeNoChannel, "All results images must have the same shape (except for num channels)"

        if channelAxisPosition is not None:
            # Now that we know where to find the channel, tell our internal stacker operator
            # TODO: Why does the stacker need to know the axis position in advance?
            #       Could this be an optional input slot for it?
            self.opChannelStacker.AxisIndex.setValue(channelAxisPosition)
        
    def getSubOutSlot(self, slots, indexes, key, result):
        # Should never get here because our output is directly connected to an internal operator
        assert False
        
    def propagateDirty(self, inputSlot, roi):
        # Nothing to do here because our output is directly connected to an internal operator.
        # The internal operators will automatically propagate dirtyness to the output.
        pass




















