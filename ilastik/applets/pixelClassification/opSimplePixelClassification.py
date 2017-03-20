from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.opCompressedUserLabelArray import OpCompressedUserLabelArray
from lazyflow.operators.classifierOperators import OpTrainClassifierBlocked, OpClassifierPredict
from lazyflow.operators.valueProviders import OpValueCache

class OpSimplePixelClassification(Operator):
    """
    This example operator performs pixel classification on sparsely labeled data.
    It is similar to ilastik's OpPixelClassification operator, but simpler (with less functionality).
    """
    ClassifierFactory = InputSlot()
    Labels = InputSlot(level=1)
    Features = InputSlot(level=1)
    
    Predictions = OutputSlot(level=1)
    
    def __init__(self, *args, **kwargs):
        """
        Instantiate the pipeline of internal operators and connect them together.
        
        Most of the the operators we use here are designed to handle a single 
        input image and produce a single output image (slot level=0).
        In those cases, we use the OperatorWrapper mechanism to dynamically manage 
        a list of these operators.  (When wrapped, the operators have slots with level=1.)
        
        (In ilastik, we use OpMultiLaneWrapper, which extends OperatorWrapper with extra functionality.)
        """
        super(OpSimplePixelClassification, self).__init__(*args, **kwargs)

        # SUMMARY SCHEMATIC:
        #
        #  ClassifierFactory ---------------------------------
        #                                                     \
        #  Labels ---> Wrapped(OpCompressedUserLabelArray) --> OpTrainClassifierBlocked --> OpValueCache -->
        #             /                                       /                                             \
        #  Features --                                       /                                               Wrapped(OpClassifierPredict) --> Predictions
        #             \                                     /                                               /
        #              Wrapped(OpBlockedArrayCache) --------------------------------------------------------        

        # LABEL CACHE(S)
        # We are really just using this as a cache for label data, which is loaded 'manually' in ingest_labels (below).
        # Therefore, none of these input slots is going to be used, but we need to configure them anyway,
        # or else the operator won't be 'ready'.
        self.opAllLabelCaches = OperatorWrapper( OpCompressedUserLabelArray, parent=self,
                                                 broadcastingSlotNames=['eraser', 'deleteLabel'] )
        self.opAllLabelCaches.Input.connect( self.Labels )
        self.opAllLabelCaches.deleteLabel.setValue( -1 )
        self.opAllLabelCaches.eraser.setValue( 255 )

        # FEATURE CACHE(S)
        self.opAllFeatureCaches = OperatorWrapper( OpBlockedArrayCache, parent=self,
                                                   broadcastingSlotNames=['fixAtCurrent'] )
        self.opAllFeatureCaches.fixAtCurrent.setValue(False) # Do not freeze caches
        self.opAllFeatureCaches.Input.connect( self.Features )

        # TRAINING OPERATOR
        self.opTrain = OpTrainClassifierBlocked( parent=self )
        self.opTrain.ClassifierFactory.connect( self.ClassifierFactory )
        self.opTrain.Labels.connect( self.opAllLabelCaches.Output )
        self.opTrain.Images.connect( self.opAllFeatureCaches.Output )
        self.opTrain.nonzeroLabelBlocks.connect( self.opAllLabelCaches.nonzeroBlocks )

        # CLASSIFIER CACHE
        # This cache stores exactly one object: the classifier itself.
        self.opClassifierCache = OpValueCache(parent=self)
        self.opClassifierCache.Input.connect( self.opTrain.Classifier )
        self.opClassifierCache.fixAtCurrent.setValue(False)

        # PREDICTION OPERATOR(S)
        self.opAllPredictors = OperatorWrapper( OpClassifierPredict, parent=self,
                                                broadcastingSlotNames=['Classifier', 'LabelsCount'] )
        self.opAllPredictors.Classifier.connect( self.opTrain.Classifier )
        self.opAllPredictors.LabelsCount.connect( self.opTrain.MaxLabel )
        self.opAllPredictors.Image.connect( self.opAllFeatureCaches.Output )
        self.Predictions.connect( self.opAllPredictors.PMaps )

    def setupOutputs(self):
        """
        There are no OutputSlots that need setup, (our only OutputSlot will be implictly
        configured because it is directly connected to one of our internal operators).
        But there is still a little work to do: choose block shapes for our internal caches.
        """
        # Configure the cache block shapes
        # We couldn't do this in __init__ because our input slots weren't 'ready' yet,
        #  so we do this in setupOutputs(), since all the input slots are ready by now.
        for lane_index in range(len(self.Features)):
            tagged_shape = self.Features[lane_index].meta.getTaggedShape()
    
            # Feature cache blocks
            # Here, we choose a block shape of only a single slice, but the full span of XY
            tagged_feature_blockshape = tagged_shape.copy()
            if 'z' in tagged_feature_blockshape:
                tagged_feature_blockshape['z'] = 1
            if 't' in tagged_feature_blockshape:
                tagged_feature_blockshape['t'] = 1
    
            self.opAllFeatureCaches[lane_index].BlockShape.setValue( tuple( tagged_feature_blockshape.values() ) )
    
            # Label cache blockshape
            # (this choice has some effect on performance, but is not critical.)
            label_blockshape = (256,) * (len(tagged_shape)-1) + (1,)
            self.opAllLabelCaches[lane_index].blockShape.setValue(label_blockshape)

    def ingest_labels(self):
        """
        Once this operator is configured and ready-to-go, call this function to
        load our internal label cache with the label data from upstream.
        
        Unlike ilastik's OpPixelClassification, this simple operator
        is not written to handle on-the-fly updates to the label data.
        Hence, this function is here to load the data.
        """
        global_max_label = 0
        for opSingleLabelCache, input_label_slot in zip(self.opAllLabelCaches, self.Labels):
            lane_max = opSingleLabelCache.ingestData( input_label_slot )
            global_max_label = max(global_max_label, lane_max)
        self.opTrain.MaxLabel.setValue(global_max_label)
    
    def execute(self, slot, subindex, roi, result):
        # Since this operator doesn't produce data on it's own 
        # (all of its output slots are connected directly to other operators),
        # there's nothing to do here, and this function will never be called.
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        # Since this operator doesn't produce data on it's own 
        # (all of its output slots are connected directly to other operators),
        # we can rely on 'dirty' events to be propagated from input to output on their own.
        # There's nothing to do here.
        pass
    
# Example usage.
if __name__ == "__main__":
    import sys
    import numpy
    import vigra
    from lazyflow.graph import Graph
    from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory

    ## These lines can be used to disable parallelism in lazyflow entirely
    ## (useful for debugging)
    #from lazyflow.request import Request
    #Request.reset_thread_pool(0)
    
    # Let's configure the logging module to show us debugging log messages from modules of interest.
    import logging
    formatter = logging.Formatter("%(name)s: %(message)s")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter( formatter )
    
    logging.getLogger().addHandler(handler) # root logger
    logging.getLogger("lazyflow.operators.opFeatureMatrixCache").setLevel(logging.DEBUG)
    logging.getLogger("lazyflow.operators.classifierOperators").setLevel(logging.DEBUG)
    logging.getLogger("lazyflow.classifiers").setLevel(logging.DEBUG)
    
    def test():
        # Make up some garbage features for this test
        features = numpy.indices( (100,100) ).astype(numpy.float32) + 0.5
        features = numpy.rollaxis(features, 0, 3)
        features = vigra.taggedView(features, 'yxc')
        assert features.shape == (100,100,2)

        # Define a couple arbitrary labels.
        labels = numpy.zeros( (100,100,1), dtype=numpy.uint8 )
        labels = vigra.taggedView(labels, 'yxc')
        
        labels[10,10] = 1
        labels[10,11] = 1
        labels[20,20] = 2
        labels[20,21] = 2

        graph = Graph()
        opPixelClassification = OpSimplePixelClassification(graph=Graph())
        
        # Specify the classifier type: A random forest with just 10 trees.
        opPixelClassification.ClassifierFactory.setValue( ParallelVigraRfLazyflowClassifierFactory(10) )

        # In a typical use-case, the inputs to our operator would be connected to some upstream pipeline via Slot.connect().
        # But for this test, we will provide the data as raw VigraArrays via the special Slot.setValue() function.
        # Also, we have to manually resize() the level-1 slots.
        opPixelClassification.Features.resize(1)
        opPixelClassification.Features[0].setValue( features )

        opPixelClassification.Labels.resize(1)
        opPixelClassification.Labels.setValue(labels)

        # Load the label cache, which will pull from the Labels slot...
        print "Ingesting labels..."
        opPixelClassification.ingest_labels()

        print "Initiating prediction..."
        predictions = opPixelClassification.Predictions[0][:].wait()
        assert predictions.shape == (100,100,2)
        assert predictions.dtype == numpy.float32
        assert 0.0 <= predictions.min() <= predictions.max() <= 1.0
        print "Done predicting."
    
    # Run the test.
    test()
