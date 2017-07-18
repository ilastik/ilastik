from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import map
from builtins import zip
from builtins import range
import os
import tempfile
import pickle as pickle
import collections

import numpy
import vigra
import h5py

from .lazyflowClassifier import LazyflowPixelwiseClassifierABC, LazyflowPixelwiseClassifierFactoryABC

import logging
logger = logging.getLogger(__name__)

from tiktorch import TikTorch

class PyTorchLazyflowClassifierFactory(LazyflowPixelwiseClassifierFactoryABC):
    VERSION = 1 # This is used to determine compatibility of pickled classifier factories.
                # You must bump this if any instance members are added/removed/renamed.
    
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

        # FIXME: hard coded file path to a trained and pickled pytorch network!
        self._filename = 'blabla'
        self._loaded_pytorch_net = None
    
    def create_and_train_pixelwise(self, feature_images, label_images, axistags=None, feature_names=None):
        logger.debug('Loading pytorch network from {}'.format(self._filename))

        # Save for future reference
        # known_labels = numpy.sort(vigra.analysis.unique(y))

        # TODO: check whether loaded network has the same number of classes as specified in ilastik!

        self._loaded_pytorch_net = TikTorch.unserialize(self._filename)

        # logger.info("OOB during training: {}".format( oob ))
        return PyTorchLazyflowClassifier(self._loaded_pytorch_net, self._filename)

    def get_halo_shape(self, data_axes='zyxc'):
        # return (z_halo, y_halo, x_halo, 0)
        return (0,0,0,0)

    @property
    def description(self):
        if self._loaded_pytorch_net:
            return "pytorch network loaded from {} with expected input shape {} and output shape {}".format(
                self._filename,
                self._loaded_pytorch_net.expected_input_shape(),
                self._loaded_pytorch_net.expected_output_shape())
        else:
            return "pytorch network loading from {} failed".format(self._filename)

    def estimated_ram_usage_per_requested_predictionchannel(self):
        # FIXME: compute from model size somehow??
        return numpy.inf

    def __eq__(self, other):
        return (    isinstance(other, type(self))
                and self._args == other._args
                and self._kwargs == other._kwargs )
    def __ne__(self, other):
        return not self.__eq__(other)

assert issubclass(PyTorchLazyflowClassifierFactory, LazyflowPixelwiseClassifierFactoryABC)

class PyTorchLazyflowClassifier(LazyflowPixelwiseClassifierABC):
    HDF5_GROUP_FILENAME = 'pytorch_network_path'

    """
    Adapt the vigra RandomForest class to the interface lazyflow expects.
    """
    def __init__(self, pytorch_net, filename):
        self._pytorch_net = pytorch_net
        self._filename = filename
    
    def predict_probabilities_pixelwise(self, feature_image, roi, axistags=None):
        logger.debug('predicting using pytorch network')
        return self._pytorch_net.forward(feature_image)
    
    @property
    def known_classes(self):
        return self._pytorch_net.expected_output_shape()[1]

    @property
    def feature_count(self):
        return self._pytorch_net.expected_input_shape()[1]

    def get_halo_shape(self, data_axes='zyxc'):
        return (0,0,0,0)

    def serialize_hdf5(self, h5py_group):
        # TODO: serialize network directly to HDF5!
        h5py_group[self.HDF5_GROUP_FILENAME] = self._filename

    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        # TODO: load from HDF5 instead of hard coded path!
        filename = h5py_group[cls.HDF5_GROUP_FILENAME]
        loaded_pytorch_net = TikTorch.unserialize(filename)

        return PyTorchLazyflowClassifier(loaded_pytorch_net, filename)

assert issubclass( PyTorchLazyflowClassifier, LazyflowPixelwiseClassifierABC )
