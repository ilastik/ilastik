###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2017, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#          http://ilastik.org/license/
###############################################################################
"""
TODOs TikTorchflowClassifier:
"""
from builtins import range
import pickle as pickle
import tempfile

import numpy
import vigra

from .lazyflowClassifier import LazyflowPixelwiseClassifierABC, LazyflowPixelwiseClassifierFactoryABC
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.graph import Graph
from lazyflow.roi import roiToSlice
from inferno.io.transform import Compose
from inferno.io.transform.generic import Normalize, Cast, AsTorchBatch

import logging
logger = logging.getLogger(__name__)

from tiktorch.wrapper import TikTorch


class TikTorchLazyflowClassifierFactory(LazyflowPixelwiseClassifierFactoryABC):
    # The version is used to determine compatibility of pickled classifier factories.
    # You must bump this if any instance members are added/removed/renamed.
    VERSION = 1

    def __init__(self, tiktorch_config_path, hyperparameter_config_path=None):
        self._filename = tiktorch_config_path
        self._loaded_pytorch_net = None

        self.train_model = True

        if tiktorch_net is None:
            # tiktorch_net = TikTorch.unserialize(self._filename)
            tiktorch_net = TikTorch(filename)

        self._loaded_pytorch_net = tiktorch_net

        self._opReorderAxes = OpReorderAxes(graph=Graph())
        self._opReorderAxes.AxisOrder.setValue('zcyx')

    def create_and_train_pixelwise(self, feature_images, label_images, axistags=None, feature_names=None):
        logger.debug('Loading pytorch network from {}'.format(self._filename))

        if self.train_model:
            reordered_feature_images = []
            reordered_labels = []
            for i in range(len(feature_images)):
                self._opReorderAxes.Input.setValue(vigra.VigraArray(feature_images[i], axistags=axistags))
                self._opReorderAxes.AxisOrder.setValue('zcyx')
                reordered_feature_images.append(self._opReorderAxes.Output([]).wait())

                self._opReorderAxes.Input.setValue(vigra.VigraArray(label_images[i], axistags=axistags))
                self._opReorderAxes.AxisOrder.setValue('zcyx')
                reordered_labels.append(self._opReorderAxes.Output([]).wait())


            # TODO: check whether loaded network has the same number of classes as specified in ilastik!
            # self._loaded_pytorch_net = TikTorch.unserialize(self._filename)
            self._loaded_pytorch_net.train(reordered_feature_images, reordered_labels)
            logger.info(self.description)

        return TikTorchLazyflowClassifier(self._loaded_pytorch_net, self._filename)

    def determineBlockShape(self, max_shape, train=True):
        return TikTorch(self._filename).dry_run(max_shape, train)

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
            return (
                f"pytorch network loaded from {self._filename} with "
                #f"expected input shape {self._loaded_pytorch_net.expected_input_shape} and "
                #f"output shape {self._loaded_pytorch_net.expected_output_shape}"
            )
        else:
            return f"pytorch network loading from {self._filename} failed"

    def estimated_ram_usage_per_requested_predictionchannel(self):
        # FIXME: compute from model size somehow??
        return numpy.inf

    def __eq__(self, other):
        return (isinstance(other, type(self)))

    def __ne__(self, other):
        return not self.__eq__(other)


assert issubclass(TikTorchLazyflowClassifierFactory, LazyflowPixelwiseClassifierFactoryABC)


class TikTorchLazyflowClassifier(LazyflowPixelwiseClassifierABC):
    HDF5_GROUP_FILENAME = 'pytorch_network_path'

    def __init__(self, tiktorch_net, filename=None):
        """
        Args:
            tiktorch_net (tiktorch): tiktorch object to be loaded into this
              classifier object
            filename (None, optional): Save file name for future reference
        """
        self._filename = filename
        if self._filename is None:
            self._filename = ""

        self.HALO_SIZE = None

        if tiktorch_net is None:
            print (self._filename)
            # tiktorch_net = TikTorch.unserialize(self._filename)
            tiktorch_net = TikTorch(filename)

        self._tiktorch_net = tiktorch_net
        self.exp_input_shape = exp_input_shape 

        self._opReorderAxes = OpReorderAxes(graph=Graph())
        self._opReorderAxes.AxisOrder.setValue('zcyx')

    def predict_probabilities_pixelwise(self, feature_image, roi, axistags=None):
        """
        forward function for tiktorch, roi handling happens in tiktorch
        so its set to 0
        """
        assert isinstance(roi, numpy.ndarray)
        print('tiktorchLazyflowClassifier.predict tile shape:', feature_image.shape)
        self._opReorderAxes.Input.setValue(vigra.VigraArray(feature_image, axistags=axistags))
        self._opReorderAxes.AxisOrder.setValue('zcyx')
        reordered_feature_image = self._opReorderAxes.Output([]).wait()

        transform = Compose(Normalize())
        reordered_feature_image = transform(reordered_feature_image)

        input_tensor = [reordered_feature_image[z] for z in range(reordered_feature_image.shape[0])]
        result = self._tiktorch_net.forward(input_tensor)
        logger.info(f"Obtained a predicted block of shape {result.shape}")
        self._opReorderAxes.Input.setValue(vigra.VigraArray(result, axistags=vigra.makeAxistags('zcyx')))
        # axistags is vigra.AxisTags, but opReorderAxes expects a string
        self._opReorderAxes.AxisOrder.setValue(''.join(axistags.keys()))
        result = self._opReorderAxes.Output([]).wait()
        result = numpy.concatenate((1 - result, result), axis=3)

        return result

    @property
    def known_classes(self):
        return list(range(self._tiktorch_net.output_shape[0]))

    @property
    def feature_count(self):
        return self._tiktorch_net.expected_input_shape[0]

    def get_halo_shape(self, data_axes='zyxc'):
        if len(data_axes) == 4:
            return (0, self.HALO_SIZE, self.HALO_SIZE, 0)
        # FIXME: assuming 'yxc' !
        elif len(data_axes) == 3:
            return (self.HALO_SIZE, self.HALO_SIZE, 0)

    def serialize_hdf5(self, h5py_group):
        logger.debug('Serializing')
        h5py_group[self.HDF5_GROUP_FILENAME] = self._filename
        h5py_group['pickled_type'] = pickle.dumps(type(self), 0)

        # HACK: can this be done more elegantly?
        with tempfile.TemporaryFile() as f:
            self._tiktorch_net.serialize(f)
            f.seek(0)
            h5py_group['classifier'] = numpy.void(f.read())

    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        # TODO: load from HDF5 instead of hard coded path!
        logger.debug('Deserializing')
        # HACK:
        # filename = PYTORCH_MODEL_FILE_PATH
        filename = h5py_group[cls.HDF5_GROUP_FILENAME]
        logger.debug("Deserializing from {}".format(filename))

        with tempfile.TemporaryFile() as f:
            f.write(h5py_group['classifier'].value)
            f.seek(0)
            loaded_pytorch_net = TikTorch.unserialize(f)

        return TikTorchLazyflowClassifier(loaded_pytorch_net, filename)


assert issubclass(TikTorchLazyflowClassifier, LazyflowPixelwiseClassifierABC)
