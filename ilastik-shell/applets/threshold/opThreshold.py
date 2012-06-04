from lazyflow.graph import Graph, Operator, OperatorWrapper, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot

from applets.genericViewer.opGenericViewer import OpGenericViewer
import numpy

# TODO: This class doesn't belong here.  Move it to lazyflow.
class OpThreshold(Operator):
    InputImage = InputSlot()
    MinValue = InputSlot(stype='int')
    MaxValue = InputSlot(stype='int')
    
    Output = OutputSlot()
    
    def setupOutputs(self):
        # Copy the input metadata
        self.Output.meta.assignFrom( self.InputImage.meta )
    
    def execute(self, slot, roi, result):
        key = roi.toSlice()
        raw = self.InputImage[key].wait()
        mask = numpy.logical_and(self.MinValue.value <= raw, raw <= self.MaxValue.value)
        result[...] = mask * raw
    
    def propagateDirty(self, inputSlot, roi):
        if inputSlot.name == "InputImage":
            self.Output.setDirty(roi)
        if inputSlot.name == "MinValue" or inputSlot.name == "MaxValue":
            self.Output.setDirty( slice(None) )

class OpThresholdViewer(Operator):
    name = "OpThresholdViewer"
    category = "Top-level"
    
    InputImage = InputSlot()
    MinValue = InputSlot(stype='int')
    MaxValue = InputSlot(stype='int')
    
    OutputLayers = MultiOutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpThresholdViewer, self ).__init__(*args, **kwargs)
        
        self.opGenericViewer = OpGenericViewer(graph=self.graph, parent=self)
        self.opThreshold = OpThreshold(graph=self.graph, parent=self)
        
        self.opThreshold.InputImage.connect( self.InputImage )
        self.opThreshold.MinValue.connect( self.MinValue )
        self.opThreshold.MaxValue.connect( self.MaxValue )
        
        self.opGenericViewer.BaseLayer.connect( self.InputImage )
        self.opGenericViewer.ChannelwiseLayers.resize(1)
        self.opGenericViewer.ChannelwiseLayers[0].connect( self.opThreshold.Output )
        
        self.OutputLayers.connect( self.opGenericViewer.OutputLayers )
        

if __name__ == "__main__":
    g = Graph()
    op = OpThreshold(graph=g)
    
    # Data is the sum of the indices
    data = numpy.indices((10,10)).sum(0)
    
    op.MinValue.setValue(2)
    op.MaxValue.setValue(5)
    op.InputImage.setValue(data)
    
    assert numpy.all(op.Output.value <= 5)
    assert numpy.logical_or(op.Output.value >= 2, op.Output.value == 0).all()


