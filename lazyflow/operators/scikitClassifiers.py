import abc
import copy

import numpy
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.utility import OrderedSignal

from opFeatureMatrixCache import OpFeatureMatrixCache
from opConcatenateFeatureMatrices import OpConcatenateFeatureMatrices

def _has_attribute( cls, attr ):
    return any(attr in B.__dict__ for B in cls.__mro__)

def _has_attributes( cls, attrs ):
    return all(_has_attribute(cls, a) for a in attrs)

class ClassifierABC(object):
    """
    Defines an interface for classifier objects.
    All scikit-learn classifiers already satisfy this interface.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def fit(self, X, y):
        raise NotImplementedError
    
    @abc.abstractmethod
    def predict_proba(self, X):
        raise NotImplementedError

    @abc.abstractproperty
    def classes_(self):
        raise NotImplementedError
    
    @classmethod
    def __subclasshook__(cls, C):
        if cls is ClassifierABC:
            return _has_attributes(C, ['fit', 'predict_proba'])
        return NotImplemented
    
    def check_instance(self, inst):
        return hasattr('classes_')

class VigraRandomForest(object):
    """
    Make the vigra random forest look like a scikit classifier.
    """
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._classifier = vigra.learning.RandomForest(*args, **kwargs)
        self._known_labels = []
    
    def fit(self, X, y):
        # Save for future reference
        self._known_labels = numpy.unique(y)

        X = numpy.asarray(X, numpy.float32)
        y = numpy.asarray(y, numpy.uint32)
        if y.ndim == 1:
            y = y[:, numpy.newaxis]

        assert X.ndim == 2
        assert len(X) == len(y)
        self._classifier.learnRF(X, y)

        return self
    
    def predict_proba(self, X):
        return self._classifier.predictProbabilities( numpy.asarray(X, dtype=numpy.float32) )
    
    @property
    def classes_(self):
        return self._known_labels
    
    @property
    def n_classes_(self):
        return len(self._known_labels)
    
class OpScikitClassifierPredict(Operator):
    Image = InputSlot()
    LabelsCount = InputSlot()
    Classifier = InputSlot()
    
    PMaps = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpScikitClassifierPredict, self ).__init__(*args, **kwargs)

    def setupOutputs(self):
        assert self.Image.meta.getAxisKeys()[-1] == 'c'
        
        nlabels = max(self.LabelsCount.value, 1) #we'll have at least 2 labels once we actually predict something
                                                #not setting it to 0 here is friendlier to possible downstream
                                                #ilastik operators, setting it to 2 causes errors in pixel classification
                                                #(live prediction doesn't work when only two labels are present)
        
        self.PMaps.meta.dtype = numpy.float32
        self.PMaps.meta.axistags = copy.copy(self.Image.meta.axistags)
        self.PMaps.meta.shape = self.Image.meta.shape[:-1]+(nlabels,) # FIXME: This assumes that channel is the last axis
        self.PMaps.meta.drange = (0.0, 1.0)

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()

        classifier = self.Classifier.value
        if classifier is None:
            # Training operator may return 'None' if there was no data to train with
            return numpy.zeros(numpy.subtract(roi.stop, roi.start), dtype=numpy.float32)[...]

        newKey = key[:-1]
        newKey += (slice(0,self.Image.meta.shape[-1],None),)

        input_data = self.Image[newKey].wait()

        shape=input_data.shape
        prod = numpy.prod(shape[:-1])
        features = input_data.reshape((prod, shape[-1]))

        probabilities = classifier.predict_proba( features )
        
        # We're expecting a channel for each label class.
        # If we didn't provide at least one sample for each label,
        #  we may get back fewer channels.
        if probabilities.shape[1] != self.PMaps.meta.shape[-1]:
            # Copy to an array of the correct shape
            # This is slow, but it's an unusual case
            assert probabilities.shape[-1] == len(classifier.classes_)
            full_probabilities = numpy.zeros( probabilities.shape[:-1] + (self.PMaps.meta.shape[-1],), dtype=numpy.float32 )
            for i, label in enumerate(classifier.classes_):
                full_probabilities[:, label-1] = probabilities[:, i]
            
            probabilities = full_probabilities
        
        # Reshape to image
        probabilities.shape = shape[:-1] + (self.PMaps.meta.shape[-1],)

        # Copy only the prediction channels the client requested.
        result[...] = probabilities[...,roi.start[-1]:roi.stop[-1]]
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Classifier:
            self.logger.debug("classifier changed, setting dirty")
            self.PMaps.setDirty()
        elif slot == self.Image:
            self.PMaps.setDirty()


class OpTrainScikitClassifierBlocked(Operator):
    Images = InputSlot(level=1)
    Labels = InputSlot(level=1)
    nonzeroLabelBlocks = InputSlot(level=1) # TODO: Eliminate this slot. It isn't used any more...
    MaxLabel = InputSlot()
    
    Classifier = OutputSlot()
    
    # Images[N] ---                                                                                    MaxLabel ------
    #              \                                                                                                  \
    # Labels[N] --> opFeatureMatrixCaches ---(FeatureImage[N])---> opConcatenateFeatureImages ---(FeatureMatrices)---> OpTrainFromFeatures ---(Classifier)--->

    def __init__(self, classifier_factory, *args, **kwargs):
        super(OpTrainScikitClassifierBlocked, self).__init__(*args, **kwargs)        
        self.progressSignal = OrderedSignal()
        
        self._opFeatureMatrixCaches = OperatorWrapper( OpFeatureMatrixCache, parent=self )
        self._opFeatureMatrixCaches.LabelImage.connect( self.Labels )
        self._opFeatureMatrixCaches.FeatureImage.connect( self.Images )
        self._opFeatureMatrixCaches.NonZeroLabelBlocks.connect( self.nonzeroLabelBlocks )
        
        self._opConcatenateFeatureMatrices = OpConcatenateFeatureMatrices( parent=self )
        self._opConcatenateFeatureMatrices.FeatureMatrices.connect( self._opFeatureMatrixCaches.LabelAndFeatureMatrix )
        self._opConcatenateFeatureMatrices.ProgressSignals.connect( self._opFeatureMatrixCaches.ProgressSignal )
        
        self._opTrainFromFeatures = OpTrainScikitClassifierFromFeatures( classifier_factory, parent=self )
        self._opTrainFromFeatures.LabelAndFeatureMatrix.connect( self._opConcatenateFeatureMatrices.ConcatenatedOutput )
        self._opTrainFromFeatures.MaxLabel.connect( self.MaxLabel )
        
        self.Classifier.connect( self._opTrainFromFeatures.Classifier )

        # Progress reporting
        def _handleFeatureProgress( progress ):
            self.progressSignal( 0.8*progress )
        self._opConcatenateFeatureMatrices.progressSignal.subscribe( _handleFeatureProgress )
        
        def _handleTrainingComplete():
            self.progressSignal( 100.0 )
        self._opTrainFromFeatures.trainingCompleteSignal.subscribe( _handleTrainingComplete )

    def setupOutputs(self):
        pass # Nothing to do; our output is connected to an internal operator.

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here..."

    def propagateDirty(self, slot, subindex, roi):
        pass

class OpTrainScikitClassifierFromFeatures(Operator):
    LabelAndFeatureMatrix = InputSlot()
    
    MaxLabel = InputSlot()
    Classifier = OutputSlot()
    
    def __init__(self, classifer_factory, *args, **kwargs):
        """
        classifier_factory: A callable that creates a classifier instance.
                            Examples: 
                                - sklearn.naive_bayes.GaussianNB
                                - partial(sklearn.ensemble.RandomForestClassifier, 10)
        """
        super(OpTrainScikitClassifierFromFeatures, self).__init__(*args, **kwargs)
        self._classifer_factory = classifer_factory
        self.trainingCompleteSignal = OrderedSignal()

        # TODO: Progress...
        #self.progressSignal = OrderedSignal()

    def setupOutputs(self):
        self.Classifier.meta.dtype = object
        self.Classifier.meta.shape = (1,)

    def execute(self, slot, subindex, roi, result):
        labels_and_features = self.LabelAndFeatureMatrix.value
        featMatrix = labels_and_features[:,1:]
        labelsMatrix = labels_and_features[:,0:1].astype(numpy.uint32)
        
        maxLabel = self.MaxLabel.value

        if featMatrix.shape[0] < maxLabel:
            # If there isn't enough data for the random forest to train with, return None
            result[:] = None
            self.trainingCompleteSignal()
            return

        classifier = self._classifer_factory()
        #assert isinstance(classifier, ClassifierABC), \
        #    "Classifier is of type {}, which does not satisfy the ClassifierABC interface."\
        #    "".format( type(classifier) )
        classifier.fit( featMatrix, labelsMatrix[:,0] )
        result[0] = classifier
        
        self.trainingCompleteSignal()
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Classifier.setDirty()        


