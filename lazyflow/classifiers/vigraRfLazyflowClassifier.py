import os
import tempfile
import cPickle as pickle
import collections

import numpy
import vigra
import h5py

from lazyflowClassifier import LazyflowVectorwiseClassifierABC, LazyflowVectorwiseClassifierFactoryABC

import logging
logger = logging.getLogger(__name__)

class VigraRfLazyflowClassifierFactory(LazyflowVectorwiseClassifierFactoryABC):
    VERSION = 1 # This is used to determine compatibility of pickled classifier factories.
                # You must bump this if any instance members are added/removed/renamed.
    
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
    
    def create_and_train(self, X, y, feature_names=None):
        logger.debug( 'Training single-threaded vigra RF with feature importance' )

        # Save for future reference
        known_labels = numpy.unique(y)

        X = numpy.asarray(X, numpy.float32)
        y = numpy.asarray(y, numpy.uint32)
        if y.ndim == 1:
            y = y[:, numpy.newaxis]

        assert X.ndim == 2
        assert len(X) == len(y)
        classifier = vigra.learning.RandomForest(*self._args, **self._kwargs)
        
        if feature_names is None:
            oob = classifier.learnRF(X, y)
            named_importances = None
        else:
            assert len(feature_names) == X.shape[-1], \
                "Training data has {} features, but you gave {} feature names" \
                .format( X.shape[-1], len(feature_names) )
            
            oob, importances = classifier.learnRFWithFeatureSelection(X, y)
            named_importances = collections.OrderedDict( zip( feature_names, importances ) )

            importance_table = self.generate_importance_table( named_importances, sort=True )
            logger.info("Feature Importance measurements during training:\n" + importance_table)

        logger.info("OOB during training: {}".format( oob ))
        return VigraRfLazyflowClassifier( classifier, known_labels, feature_names, oob, named_importances )

    @classmethod
    def generate_importance_table(cls, named_importances_dict, sort=True):
        """
        Return a string of the given importances dict, in csv format, 
        but also with extra spaces for pretty-printing.
        """
        import csv
        from StringIO import StringIO
        CSV_FORMAT = { 'delimiter' : '\t', 'lineterminator' : '\n' }

        feature_name_length = max( map(len, named_importances_dict.keys()) )

        # See vigra/random_forest/rf_visitors.hxx, class VariableImportanceVisitor
        n_classes = len(named_importances_dict.values()[0]) - 2
        columns = [ "{: <{width}}".format("Feature Name", width=feature_name_length) ]
        columns += [ "  Class #{}".format(i) for i in range(n_classes)]
        columns += [ "   Overall" ]
        columns += [ "      Gini" ]
        
        output = StringIO()
        csv_writer = csv.writer(output, **CSV_FORMAT)
        csv_writer.writerow( columns )

        if sort:
            # Sort by "overall" importance (column -2)
            sorted_importances = sorted( named_importances_dict.items(),
                                         key=lambda (k,v): v[-2] )
            named_importances_dict = collections.OrderedDict( sorted_importances )

        for feature_name, importances in named_importances_dict.items():
            feature_name = "{: <{width}}".format(feature_name, width=feature_name_length)
            importance_strings = map( lambda x: "{: .03f}".format(x), importances )
            importance_strings = map( lambda s: "{: >10}".format(s), importance_strings )
            csv_writer.writerow( [feature_name] + importance_strings )
        return output.getvalue()

    @property
    def description(self):
        temp_rf = vigra.learning.RandomForest( *self._args, **self._kwargs )
        return "Vigra Random Forest ({} trees)".format( temp_rf.treeCount() )

    def estimated_ram_usage_per_requested_predictionchannel(self):
        return 4

    def __eq__(self, other):
        return (    isinstance(other, type(self))
                and self._args == other._args
                and self._kwargs == other._kwargs )
    def __ne__(self, other):
        return not self.__eq__(other)

assert issubclass( VigraRfLazyflowClassifierFactory, LazyflowVectorwiseClassifierFactoryABC )

class VigraRfLazyflowClassifier(LazyflowVectorwiseClassifierABC):
    """
    Adapt the vigra RandomForest class to the interface lazyflow expects.
    """
    def __init__(self, vigra_rf, known_labels, feature_names, oob, importances=None):
        self._known_labels = known_labels
        self._vigra_rf = vigra_rf
        self._feature_names = feature_names
        self.oob = oob
        self.importances = importances
    
    def predict_probabilities(self, X):
        logger.debug( 'predicting single-threaded vigra RF' )
        return self._vigra_rf.predictProbabilities( numpy.asarray(X, dtype=numpy.float32) )
    
    @property
    def known_classes(self):
        return self._known_labels

    @property
    def feature_count(self):
        return self._vigra_rf.featureCount()

    @property
    def feature_names(self):
        return self._feature_names

    def serialize_hdf5(self, h5py_group):
        # Due to non-shared hdf5 dlls, vigra can't write directly to
        # our open hdf5 group. Instead, we'll use vigra to write the
        # classifier to a temporary file.
        tmpDir = tempfile.mkdtemp()
        cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5').replace('\\', '/')
        self._vigra_rf.writeHDF5(cachePath, 'forest')

        # Open the temp file and copy to our project group
        with h5py.File(cachePath, 'r') as cacheFile:
            h5py_group.copy(cacheFile['forest'], 'forest')

        h5py_group['known_labels'] = self._known_labels
        h5py_group['feature_names'] = self._feature_names
        
        # This field is required for all classifiers
        h5py_group['pickled_type'] = pickle.dumps( type(self) )

    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        # Due to non-shared hdf5 dlls, vigra can't read directly
        # from our open hdf5 group. Instead, we'll copy the
        # classfier data to a temporary file and give it to vigra.
        tmpDir = tempfile.mkdtemp()
        cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5').replace('\\', '/')
        with h5py.File(cachePath, 'w') as cacheFile:
            cacheFile.copy(h5py_group['forest'], 'forest')

        forest = vigra.learning.RandomForest(cachePath, 'forest')
        known_labels = list(h5py_group['known_labels'][:])
        feature_names = list(h5py_group['feature_names'][:])

        os.remove(cachePath)
        os.rmdir(tmpDir)

        return VigraRfLazyflowClassifier( forest, known_labels, feature_names, None, None )

assert issubclass( VigraRfLazyflowClassifier, LazyflowVectorwiseClassifierABC )
