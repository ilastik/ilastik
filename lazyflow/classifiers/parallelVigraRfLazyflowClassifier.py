import os
import tempfile
from functools import partial
import cPickle as pickle

import numpy
import vigra
import h5py

from lazyflow.request import Request, RequestPool
from lazyflowClassifier import LazyflowVectorwiseClassifierABC, LazyflowVectorwiseClassifierFactoryABC

import logging
logger = logging.getLogger(__name__)

class ParallelVigraRfLazyflowClassifierFactory(LazyflowVectorwiseClassifierFactoryABC):
    VERSION = 1 # This is used to determine compatibility of pickled classifier factories.
                # You must bump this if any instance members are added/removed/renamed.
    
    def __init__(self, num_trees_total=100, num_forests=None, **kwargs):
        """
        num_trees_total: The number of trees to train
        num_forests: How many forests in which to distribute the trees (forests can train and predict in parallel)
                     If not provided, the number of forests is automatically determined 
                     to match the number of available lazyflow worker threads.
        kwargs: Additional keyword args, passed directly to the vigra.RandomForest constructor.
        """
        self._num_trees = num_trees_total
        self._kwargs = kwargs

        # By default, num_forests matches the number of lazyflow worker threads
        self._num_forests = num_forests or Request.global_thread_pool.num_workers
        self._num_forests = max(1, self._num_forests)
    
    def create_and_train(self, X, y):
        # Distribute trees as evenly as possible
        tree_counts = numpy.array( [self._num_trees // self._num_forests] * self._num_forests )
        tree_counts[:self._num_trees % self._num_forests] += 1
        assert tree_counts.sum() == self._num_trees
        tree_counts = map(int, tree_counts)
        
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
        for tree_count in tree_counts:
            forests.append( vigra.learning.RandomForest(tree_count, **self._kwargs) )

        # Train them all in parallel
        oobs = [None] * len(forests)
        pool = RequestPool()
        for i, forest in enumerate(forests):
            req = Request( partial(forest.learnRF, X, y) )
            # save the oobs
            req.notify_finished( partial( oobs.__setitem__, i ) )
            pool.add( req )
        pool.wait()

        logger.info( "Training complete. Average OOB: {}".format( numpy.average(oobs) ) )
        return ParallelVigraRfLazyflowClassifier( forests, oobs, known_labels )

    @property
    def description(self):
        return "Parallel Vigra Random Forest Factory ({} trees total)"\
               .format( self._num_trees )

    def __eq__(self, other):
        return (    isinstance(other, type(self))
                and self._num_trees == other._num_trees
                and self._kwargs == other._kwargs )
    def __ne__(self, other):
        return not self.__eq__(other)

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
        
        self._num_trees = sum( forest.treeCount() for forest in self._forests )
    
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
        predictions = self._forests[0].treeCount() * reqs[0].result
        for forest, req in zip(self._forests[1:], reqs[1:]):
            predictions += forest.treeCount() * req.result

        predictions /= self._num_trees
        return predictions
    
    @property
    def oobs(self):
        return self._oobs
    
    @property
    def known_classes(self):
        return self._known_labels

    @property
    def feature_count(self):
        return self._forests[0].featureCount()

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

        h5py_group = parent_group[name]
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
