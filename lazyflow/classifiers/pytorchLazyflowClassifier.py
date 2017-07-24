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
import numpy as np
import vigra
import h5py

from .lazyflowClassifier import LazyflowPixelwiseClassifierABC, LazyflowPixelwiseClassifierFactoryABC
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.graph import Graph

import logging
logger = logging.getLogger(__name__)

try:
    from tiktorch.wrapper import TikTorch
except ImportError as e:
    print(e)


# FIXME: hard coded file path to a trained and pickled pytorch network!
# PYTORCH_MODEL_FILE_PATH = '/Users/chaubold/opt/miniconda/envs/ilastik-py3/src/tiktorch/test3.nn'
PYTORCH_MODEL_FILE_PATH = '/Users/chaubold/opt/miniconda/envs/ilastik-py3/src/tiktorch/dunet-cpu.nn'

class PyTorchLazyflowClassifierFactory(LazyflowPixelwiseClassifierFactoryABC):
    VERSION = 1 # This is used to determine compatibility of pickled classifier factories.
                # You must bump this if any instance members are added/removed/renamed.
    
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

        # FIXME: hard coded file path to a trained and pickled pytorch network!
        self._filename = PYTORCH_MODEL_FILE_PATH
        self._loaded_pytorch_net = None
    
    def create_and_train_pixelwise(self, feature_images, label_images, axistags=None, feature_names=None):
        self._filename = PYTORCH_MODEL_FILE_PATH
        logger.debug('Loading pytorch network from {}'.format(self._filename))

        # Save for future reference
        # known_labels = numpy.sort(vigra.analysis.unique(y))

        # TODO: check whether loaded network has the same number of classes as specified in ilastik!
        self._loaded_pytorch_net = TikTorch.unserialize(self._filename)
        logger.info(self.description)

        # logger.info("OOB during training: {}".format( oob ))
        return PyTorchLazyflowClassifier(self._loaded_pytorch_net, self._filename)

    def get_halo_shape(self, data_axes='zyxc'):
        # return (z_halo, y_halo, x_halo, 0)
        if len(data_axes) == 4:
            return (0, 32, 32, 0)
        # FIXME: assuming 'yxc' !
        elif len(data_axes) == 3:
            return (32, 32, 0)

    @property
    def description(self):
        if self._loaded_pytorch_net:
            return "pytorch network loaded from {} with expected input shape {} and output shape {}".format(
                self._filename,
                self._loaded_pytorch_net.expected_input_shape,
                self._loaded_pytorch_net.expected_output_shape)
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
    HALO_SIZE = 32

    """
    Adapt the vigra RandomForest class to the interface lazyflow expects.
    """
    def __init__(self, pytorch_net, filename):
        self._pytorch_net = pytorch_net
        self._filename = filename
        self._opReorderAxes = OpReorderAxes(graph=Graph())
        self._opReorderAxes.AxisOrder.setValue('zcyx')
    
    def predict_probabilities_pixelwise(self, feature_image, roi, axistags=None):
        logger.info('predicting using pytorch network for image of shape {} and roi {}'.format(feature_image.shape, roi))
        logger.info("Stats of input: min={}, max={}, mean={}".format(feature_image.min(), feature_image.max(), feature_image.mean()))
        logger.info('expected pytorch input shape is {} '.format(self._pytorch_net.expected_input_shape))
        logger.info('expected pytorch output shape is {} '.format(self._pytorch_net.expected_output_shape))

        # num_channels = len(self.known_classes)
        num_channels = 2
        expected_shape = [stop - start for start, stop in zip(roi[0], roi[1])] + [num_channels]

        self._opReorderAxes.Input.setValue(vigra.VigraArray(feature_image, axistags=axistags))
        self._opReorderAxes.AxisOrder.setValue('zcyx')
        reordered_feature_image = self._opReorderAxes.Output([]).wait()

        # normalizing patch
        # reordered_feature_image = (reordered_feature_image - reordered_feature_image.mean()) / (reordered_feature_image.std() + 0.000001)

        logger.info(
            'Shape after reordering input is {}, axistags are {}'.format(
                reordered_feature_image.shape, 
                self._opReorderAxes.Output.meta.axistags))
         
        slice_shape = list(reordered_feature_image.shape[:]) # ignore z axis
        slice_shape[0] = 1

        if slice_shape != list(self._pytorch_net.expected_input_shape):
            logger.info("Expected input shape is {}, but got {}, returning zeros".format(self._pytorch_net.expected_input_shape, slice_shape))
            return np.zeros(expected_shape)
        else:
            result = np.zeros([reordered_feature_image.shape[0], num_channels] + list(reordered_feature_image.shape[2:]))

            # we always predict in 2D, per z-slice, so we loop over z
            for z in range(reordered_feature_image.shape[0]):
                # logger.warning("Dumping to {}".format('"/Users/chaubold/Desktop/dump.h5"'))
                # vigra.impex.writeHDF5(reordered_feature_image[z,...], "data", "/Users/chaubold/Desktop/dump.h5")
                result_slice = self._pytorch_net.forward([reordered_feature_image[z:z+1,...]])[0]
                logger.info("Resulting slice {} has shape {}".format(z, result_slice.shape))
                result[z, 0, ...] = result_slice

            logger.info("Obtained a predicted block of shape {}".format(result.shape))
            
            # crop away halo and reorder axes to match "axistags"
            cropped_result = result[..., self.HALO_SIZE:-self.HALO_SIZE, self.HALO_SIZE:-self.HALO_SIZE] # crop in X and Y
            logger.info("cropped the predicted block to shape {}".format(cropped_result.shape))

            self._opReorderAxes.Input.setValue(vigra.VigraArray(cropped_result, axistags=vigra.makeAxistags('zcyx')))
            self._opReorderAxes.AxisOrder.setValue(''.join(axistags.keys())) # axistags is vigra.AxisTags, but opReorderAxes expects a string
            result = self._opReorderAxes.Output([]).wait()
            logger.info("Reordered result to shape {}".format(result.shape))

            # FIXME: not needed for real neural net results:
            logger.info("Stats of result: min={}, max={}, mean={}".format(result.min(), result.max(), result.mean()))

            return result

    
    @property
    def known_classes(self):
        return list(range(self._pytorch_net.expected_output_shape[0]))

    @property
    def feature_count(self):
        return self._pytorch_net.expected_input_shape[0]

    def get_halo_shape(self, data_axes='zyxc'):
        if len(data_axes) == 4:
            return (0, self.HALO_SIZE, self.HALO_SIZE, 0)
        # FIXME: assuming 'yxc' !
        elif len(data_axes) == 3:
            return (self.HALO_SIZE, self.HALO_SIZE, 0)

    def serialize_hdf5(self, h5py_group):
        # TODO: serialize network directly to HDF5!
        h5py_group[self.HDF5_GROUP_FILENAME] = self._filename

    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        # TODO: load from HDF5 instead of hard coded path!

        filename = PYTORCH_MODEL_FILE_PATH
        #filename = h5py_group[cls.HDF5_GROUP_FILENAME]
        logger.warning("Deserializing from {}".format(filename))
        loaded_pytorch_net = TikTorch.unserialize(filename)
        loaded_pytorch_net.set('window_size', [512, 512])

        return PyTorchLazyflowClassifier(loaded_pytorch_net, filename)

assert issubclass( PyTorchLazyflowClassifier, LazyflowPixelwiseClassifierABC )
