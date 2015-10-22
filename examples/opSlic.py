"""
This file defines a simple operator for computing SLIC superpixels using scikit-image.

This example demonstrates how blockwise access to a 'global' operation
(such as superpixel generation) can cause undesirable results, and how
a cache can be used to force every request to be taken from a global result.

See the __main__ section, below.
It also includes a brief demonstration of lazyflow's OperatorWrapper mechanism.
"""
import skimage.segmentation
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpBlockedArrayCache

class OpSlic(Operator):
    """
    Computes SLIC superpixels for any requested region of the image.
    Every request is considered independently, so it isn't desirable to
    concatenate the results of several requests into one large image.
    (If you do, the final image will appear 'quilted'.)
    """
    Input = InputSlot()
    
    # These are the slic parameters.
    # Here we give default values, but they can be changed.
    NumSegments = InputSlot(value=100)
    Compactness = InputSlot(value=10.0)
    MaxIter = InputSlot(value=10)
    
    Output = OutputSlot()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

        tagged_shape = self.Input.meta.getTaggedShape()
        assert 'c' in tagged_shape, "We assume the image has an explicit channel axis."
        assert tagged_shape.keys()[-1] == 'c', "This code assumes that channel is the LAST axis."
        
        # Output will have exactly one channel, regardless of input channels
        tagged_shape['c'] = 1
        self.Output.meta.shape = tuple(tagged_shape.values())
    
    def execute(self, slot, subindex, roi, result):
        input_data = self.Input(roi.start, roi.stop).wait()
        slic_sp = skimage.segmentation.slic(input_data,
                                            n_segments=self.NumSegments.value,
                                            compactness=self.Compactness.value,
                                            max_iter=self.MaxIter.value,
                                            multichannel=True,
                                            enforce_connectivity=True,
                                            convert2lab=False) # Use with caution.
                                                               # This would cause slic() to have special behavior for 3-channel data,
                                                               # in which case we better really be dealing with RGB channels
                                                               # (not, say 3 unrelated image features).
        
        # slic_sp has no channel axis, so insert that axis before copying to 'result'
        result[:] = slic_sp[...,None]
    
    def propagateDirty(self, slot, subindex, roi):
        # For some operators, a dirty in one part of the image only causes changes in nearby regions.
        # But for superpixel operators, changes in one corner can affect results in the opposite corner.
        # Therefore, everything is dirty.
        self.Output.setDirty()

class OpSlicCached(Operator):
    """
    Computes SLIC superpixels and cache the result for the entire image.
    """
    # Same slots as OpSlic
    Input = InputSlot()
    NumSegments = InputSlot(value=100)
    Compactness = InputSlot(value=10.0)
    MaxIter = InputSlot(value=10)
    
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpSlicCached, self).__init__(*args, **kwargs)
        # This operator does no computation on its own.
        # Instead, it owns a little internal pipeline:
        # 
        # Input --> OpSlic --> OpCache --> Output
        #
        
        # Feed all inputs directly into the operator that actually computes the slic superpixels
        self.opSlic = OpSlic( parent=self )
        self.opSlic.NumSegments.connect( self.NumSegments )
        self.opSlic.Compactness.connect( self.Compactness )
        self.opSlic.MaxIter.connect( self.MaxIter )
        self.opSlic.Input.connect( self.Input )
        
        self.opCache = OpBlockedArrayCache( parent=self )
        self.opCache.Input.connect( self.opSlic.Output )
        self.Output.connect( self.opCache.Output )
    
    def setupOutputs(self):
        # The cache is capable of requesting and storing results in small blocks,
        # but we want to force the entire image to be handled and stored at once.
        # Therefore, we set the 'block shape' to be the entire image -- there will only be one block stored in the cache.
        # (Note: The OpBlockedArrayCache.innerBlockshape slot is deprecated and ignored.)
        self.opCache.outerBlockShape.setValue( self.Input.meta.shape )
    
    def execute(self, slot, subindex, roi, result):
        # When an output slot is accessed, it asks for data from it's upstream connection (if any)
        # If it has no upstream connection, then it will call it's own operator's execute() function.
        # In this case, there is only one output slot, and it already has an upstream connection.
        # Therefore, this execute() function will never be accessed -- no slots would ever call it.
        assert False, "This function will never be called."

    def propagateDirty(self, slot, subindex, roi):
        # There's nothing to do here -- our Input slot is already directly connected to a 
        # little pipeline that will propagate 'dirty notifications' all the way to the output.
        pass

if __name__ == "__main__":
    # Let's try a quick test of the above operators
    import numpy
    import vigra
    import skimage.measure
    from lazyflow.graph import Graph
    
    test_image = numpy.zeros( (100,100,1), dtype=numpy.uint8 )
    # Test data should be a tagged vigra array, so the operator can read the axistags
    test_image = vigra.taggedView(test_image, 'yxc')
    
    # Try the uncached operator
    opSlic = OpSlic(graph=Graph())
    opSlic.Input.setValue( test_image )
    
    # Request a 20x20 region of the output
    slic_output = opSlic.Output[0:20, 0:20, 0:1].wait()
    assert slic_output.shape == (20,20,1)
    connected_components = skimage.measure.label( slic_output )
    num_sp = connected_components.max()
    print "The uncached operator produced {} superpixels".format(num_sp)
    
    # Now try the cached version
    opSlicCached = OpSlicCached(graph=Graph())
    opSlicCached.Input.setValue( test_image )
    slic_output = opSlicCached.Output[0:20, 0:20, 0:1].wait()
    assert slic_output.shape == (20,20,1)
    connected_components = skimage.measure.label( slic_output )
    num_sp = connected_components.max()
    print "The CACHED operator produced {} superpixels".format(num_sp)

    # Now let's make it possible for the operator to handle multiple images.
    # The parameters like Compactness, etc. should be shared across all "lanes",
    # so we'll 'broadcast' those slots.
    # But the Input slot is, of course, unique to each input image. It is not broadcasted.
    from lazyflow.graph import OperatorWrapper
    opMultiImageSlicCached = OperatorWrapper( OpSlicCached, broadcastingSlotNames=['NumSegments', 'Compactness', 'MaxIter'], graph=Graph())
    assert opMultiImageSlicCached.Input.level == 1
    assert opMultiImageSlicCached.Output.level == 1
    assert opMultiImageSlicCached.NumSegments.level == 0
    assert opMultiImageSlicCached.Compactness.level == 0
    assert opMultiImageSlicCached.MaxIter.level == 0
    
    # Let's try it on 2 images
    opMultiImageSlicCached.Input.resize(2)
    opMultiImageSlicCached.Input[0].setValue( test_image+42 )
    opMultiImageSlicCached.Input[1].setValue( test_image+7 )
    
    slic_sp_0 = opMultiImageSlicCached.Output[0][:].wait()
    slic_sp_1 = opMultiImageSlicCached.Output[1][:].wait()
    
    # OK, we chose silly test data, so the results should be identical, right?
    assert (slic_sp_0 == slic_sp_1).all()
    print "Both outputs of opMultiImageSlicCached had {} superpixels".format( slic_sp_0.max() )
