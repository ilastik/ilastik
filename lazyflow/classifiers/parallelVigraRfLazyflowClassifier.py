import os
import tempfile
from functools import partial
import cPickle as pickle

import numpy
import vigra
import h5py

from lazyflow.request import Request, RequestPool
from .lazyflowClassifier import LazyflowVectorwiseClassifierABC, LazyflowVectorwiseClassifierFactoryABC

import logging
logger = logging.getLogger(__name__)

class ParallelVigraRfLazyflowClassifierFactory(LazyflowVectorwiseClassifierFactoryABC):
    def __init__(self, num_forests, trees_per_forest, **kwargs):
        self._num_forests = num_forests
        self._trees_per_forest = trees_per_forest
        self._kwargs = kwargs
    
    def create_and_train(self, X, y):
        logger.debug( "Training parallel vigra RF" )
        # Save for future reference
        known_labels = numpy.unique(y)

        X = numpy.asarray(X, numpy.float32)
        y = numpy.asarray(y, numpy.uint32)
        if y.ndim == 1:
            y = y[:, numpy.newaxis]

        assert X.ndim == 2
        assert len(X) == len(y)

        # Create N forests
        forests = []
        for _ in range(self._num_forests):
            forest = vigra.learning.RandomForest(self._trees_per_forest, **self._kwargs)
            forests.append( forest )

        # Train them all in parallel
        oobs = [None] * len(forests)
        pool = RequestPool()
        for i, forest in enumerate(forests):
            req = Request( partial(forest.learnRF, X, y) )
            # save the oobs
            req.notify_finished( partial( oobs.__setitem__, i ) )
            pool.add( req )
        pool.wait()

        return ParallelVigraRfLazyflowClassifier( forests, oobs, known_labels )

    @property
    def description(self):
        temp_rf = vigra.learning.RandomForest( *self._args, **self._kwargs )
        return "Vigra Random Forest ({} trees)".format( temp_rf.treeCount() )

assert issubclass( ParallelVigraRfLazyflowClassifierFactory, LazyflowVectorwiseClassifierFactoryABC )

class ParallelVigraRfLazyflowClassifier(LazyflowVectorwiseClassifierABC):
    """
    Adapt the vigra RandomForest class to the interface lazyflow expects.
    """
    def __init__(self, forests, oobs, known_labels):
        self._known_labels = known_labels
        self._forests = forests
        
        # Note that oobs may not be in the same order as the forests.
        self._oobs = oobs
    
    def predict_probabilities(self, X):
        logger.debug( "Predicting with parallel vigra RF" )
        X = numpy.asarray(X, dtype=numpy.float32)

        # Create a request for each forest        
        reqs = []
        for forest in self._forests:
            req = Request( partial( forest.predictProbabilities, X ) )
            reqs.append( req )

        # Execute all requests in a pool        
        pool = RequestPool()
        for req in reqs:
            pool.add( req )
        pool.wait()

        # Aggregate the results
        predictions = reqs[0].result
        for req in reqs[1:]:
            predictions += req.result

        predictions /= len(reqs)
        return predictions
    
    @property
    def oobs(self):
        return self._oobs
    
    @property
    def known_classes(self):
        return self._known_labels

    def serialize_hdf5(self, h5py_group):
        for forest in self._forests:
            if forest is None:
                return

        name = h5py_group.name.split('/')[-1]
        # Due to non-shared hdf5 dlls, vigra can't write directly to
        # our open hdf5 group. Instead, we'll use vigra to write the
        # classifier to a temporary file.
        tmpDir = tempfile.mkdtemp()
        cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5').replace('\\', '/')
        for i, forest in enumerate(self._forests):
            targetname = '{0}/{1}'.format(name, "Forest{:04d}".format(i))
            forest.writeHDF5(cachePath, targetname)

        parent_group = h5py_group.parent
        del parent_group[name]
        # Open the temp file and copy to our project group
        with h5py.File(cachePath, 'r') as cacheFile:
            parent_group.copy(cacheFile[name], name)

        h5py_group['known_labels'] = self._known_labels
        
        # This field is required for all classifiers
        h5py_group['pickled_type'] = pickle.dumps( type(self) )

        os.remove(cachePath)
        os.rmdir(tmpDir)
    
    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        name = h5py_group.name.split('/')[-1]
        # Due to non-shared hdf5 dlls, vigra can't read directly
        # from our open hdf5 group. Instead, we'll copy the
        # classfier data to a temporary file and give it to vigra.
        tmpDir = tempfile.mkdtemp()
        cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5').replace('\\', '/')
        with h5py.File(cachePath, 'w') as cacheFile:
            cacheFile.copy(h5py_group, name)

        forests = []
        for dset_name, forestGroup in sorted(h5py_group.items()):
            if dset_name.startswith('Forest'):
                targetname = '{0}/{1}'.format(name, dset_name)
                forests.append(vigra.learning.RandomForest(cachePath, targetname))

        try:
            known_labels = list(h5py_group['known_labels'][:])
        except KeyError:
            # Older projects didn't store the labels explicitly.
            known_labels = range(1, forests[0].labelCount()+1 )

        try:
            oobs = list(h5py_group['oobs'][:])
        except KeyError:
            # Older projects didn't store the oobs.
            # Just provide something obviously invalid.
            oobs = [-1.0] * len(forests)

        os.remove(cachePath)
        os.rmdir(tmpDir)

        return ParallelVigraRfLazyflowClassifier( forests, oobs, known_labels )

assert issubclass( ParallelVigraRfLazyflowClassifier, LazyflowVectorwiseClassifierABC )
