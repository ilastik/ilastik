import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.opFeatureMatrixCache import OpFeatureMatrixCache
from lazyflow.operators.classifierOperators import OpTrainRandomForestFromFeatures

class TestOpTrainRandomForestFromFeatures(object):
    
    def testBasic(self):
        features = numpy.indices( (100,100) ).astype(numpy.float) + 0.5
        features = numpy.rollaxis(features, 0, 3)
        features = vigra.taggedView(features, 'xyc')
        labels = numpy.zeros( (100,100,1), dtype=numpy.uint8 )
        labels = vigra.taggedView(labels, 'xyc')
        
        labels[10,10] = 1
        labels[10,11] = 1
        labels[20,20] = 2
        labels[20,21] = 2
        
        graph = Graph()
        opFeatureMatrixCache = OpFeatureMatrixCache(graph=graph)
        opFeatureMatrixCache.FeatureImage.setValue(features)
        opFeatureMatrixCache.LabelImage.setValue(labels)
        opFeatureMatrixCache.NonZeroLabelBlocks.setValue(0)
        
        opFeatureMatrixCache.LabelImage.setDirty( numpy.s_[10:11, 10:12] )
        opFeatureMatrixCache.LabelImage.setDirty( numpy.s_[20:21, 20:22] )
        opFeatureMatrixCache.LabelImage.setDirty( numpy.s_[30:31, 30:32] )

        opTrain = OpTrainRandomForestFromFeatures( graph=graph )
        opTrain.MaxLabel.setValue(2)
        opTrain.LabelAndFeatureMatrix.connect( opFeatureMatrixCache.LabelAndFeatureMatrix )
        
        trained_forest_list = opTrain.Classifier.value
        
        # This isn't much of a test at the moment...
        for forest in trained_forest_list:
            assert isinstance( forest, vigra.learning.RandomForest )


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
