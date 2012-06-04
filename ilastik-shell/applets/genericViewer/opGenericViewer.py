from lazyflow.graph import Graph, Operator, OperatorWrapper, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot
import copy
from lazyflow.operators import Op5ToMulti, OpMultiInputConcatenater, OpMultiArrayStacker, OpMultiArraySlicer2

class OpGenericViewer(Operator):
    """
    Accepts a couple lists of input images and merges them into an output list of layers for display.
    """
    name = "OpGenericViewer"
    category = "Top-level"

    # We have three different inputs.
    # Which slot you add to determines how the image will be displayed.

    # Base layer image: Always goes on the bottom
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
        # self.BaseLayer(level=0) -> opBasePromoter.Output(level=1) -> ---------------------------------------------------------
        #                                                                                                                       \
        # self.AtomicLayers(level=1) -> ----------------------------------------------------------------------------------------->> opLayerListConcatenater.Output(level=1) --> self.OutputLayers(level=1)
        #                                                                                                                       /
        # self.ChannelwiseLayers(level=1) -> opWrappedChannelSlicer.Slices(level=2) -> opSliceListConcatenater.Output(level=1)--
        
        # TODO: Inject metadata...
        
        self.opBasePromoter = Op5ToMulti( graph=self.graph, parent=self )
        self.opBasePromoter.Input0.connect( self.BaseLayer )

        self.opWrappedChannelSlicer = OperatorWrapper( OpMultiArraySlicer2( graph=self.graph, parent=self ) )
        self.opWrappedChannelSlicer.Input.connect( self.ChannelwiseLayers )
        self.opWrappedChannelSlicer.AxisFlag.setValue('c')

        self.opSliceListConcatenater = OpMultiInputConcatenater( graph=self.graph, parent=self )
        self.opSliceListConcatenater.Inputs.connect( self.opWrappedChannelSlicer.Slices )
        
        self.opLayerListConcatenater = OpMultiInputConcatenater( graph=self.graph, parent=self )
        self.opLayerListConcatenater.Inputs.resize(3) # 3 lists to concatenate        
        self.opLayerListConcatenater.Inputs[0].connect(self.AtomicLayers)
        self.opLayerListConcatenater.Inputs[1].connect(self.opSliceListConcatenater.Output)
        self.opLayerListConcatenater.Inputs[2].connect(self.opBasePromoter.Outputs)

        self.OutputLayers.connect( self.opLayerListConcatenater.Output )

    def setupOutputs(self):
        # Nothing to set up (Output is directly connected to our internal operators).
        # But this is a convenient place to check for errors.
        shape = None
        for index, slot in enumerate(self.OutputLayers):
            if slot.configured():
                if shape == None:
                    shape = slot.meta.shape
                    channelPosition = slot.meta.axistags.index('c')
                    shapeNoChannel = list(shape)
                    shapeNoChannel.pop(channelPosition)
                else:
                    assert slot.meta.axistags.index('c') == channelPosition
                    imageShapeNoChannel = list(slot.meta.shape)
                    imageShapeNoChannel.pop(channelPosition)
                    assert shapeNoChannel == imageShapeNoChannel, "All layers should have the same shape."
        
    def getSubOutSlot(self, slots, indexes, key, result):
        # Should never get here because our output is directly connected to an internal operator
        assert False
        
    def propagateDirty(self, inputSlot, roi):
        # Nothing to do here because our output is directly connected to an internal operator.
        # The internal operators will automatically propagate dirtyness to the output.
        pass

if __name__ == "__main__":
    from lazyflow.operators import *
    from lazyflow.operators.ioOperators import *
    graph = Graph()

    # Give the same image to all three inputs
    opInputProvider = OpNpyFileReader(graph=graph)
    opInputProvider.FileName.setValue( '/home/bergs/5d.npy' )
    
    opGenericViewer = OpGenericViewer(graph=graph)        
    opGenericViewer.BaseLayer.connect( opInputProvider.Output )
    
    opGenericViewer.AtomicLayers.resize(1)
    opGenericViewer.AtomicLayers[0].connect( opInputProvider.Output )

    opGenericViewer.ChannelwiseLayers.resize(1)
    opGenericViewer.ChannelwiseLayers[0].connect( opInputProvider.Output )
    
    assert opGenericViewer.opWrappedChannelSlicer.Slices.level == 2
    assert len( opGenericViewer.OutputLayers ) == 1 + 1 + 2
    
    # Atomic images are not split up
    assert opGenericViewer.OutputLayers[0].meta.shape == opInputProvider.Output.meta.shape
    
    # Channelwise layers are divided into a separate layer for each channel.
    # Each layer's shape should match the input except for the channel
    assert opGenericViewer.OutputLayers[1].meta.shape == opInputProvider.Output.meta.shape[:-1] + (1,)
    assert opGenericViewer.OutputLayers[2].meta.shape == opInputProvider.Output.meta.shape[:-1] + (1,)

    assert numpy.all( opGenericViewer.OutputLayers[0][:].wait() == opInputProvider.Output[:].wait() )
    assert numpy.all( opGenericViewer.OutputLayers[1][:].wait() == opInputProvider.Output[:,:,:,:,0].wait() )
    assert numpy.all( opGenericViewer.OutputLayers[2][:].wait() == opInputProvider.Output[:,:,:,:,1].wait() )
    assert numpy.all( opGenericViewer.OutputLayers[3][:].wait() == opInputProvider.Output[:].wait() )

    # Base image is not split up: shape should match input
    assert opGenericViewer.OutputLayers[3].meta.shape == opInputProvider.Output.meta.shape
    







