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

#from tiktorch.client import TikTorchClient
from tiktorch.wrapper import TikTorch as TikTorchClient

import logging

logger = logging.getLogger(__name__)


class TikTorchLazyflowClassifierFactory(LazyflowPixelwiseClassifierFactoryABC):
    # The version is used to determine compatibility of pickled classifier factories.
    # You must bump this if any instance members are added/removed/renamed.
    VERSION = 1

    def __init__(self, tiktorch_config_path, hyperparameter_config_path=None):
        self._filename = tiktorch_config_path  # DELETE this attribute
        # Privates
        self._tikTorchClient = None
        self._train_model = None
        self._opReorderAxes = OpReorderAxes(graph=Graph())
        self._opReorderAxes.AxisOrder.setValue('zcyx')

        # Publics
        self.tikTorchClient = TikTorchClient(tiktorch_config_path)

    @property
    def tikTorchClient(self):
        return self._tikTorchClient

    @tikTorchClient.setter
    def tikTorchClient(self, value):
        if isinstance(value, TikTorchClient):
            self._tikTorchClient = value
        else:
            raise ValueError

    @property
    def train_model(self):
        return self._train_model

    @train_model.setter
    def train_model(self, value):
        if isinstance(value, bool):
            self._train_model = value
        else:
            ValueError

    def create_and_train_pixelwise(self, feature_images, label_images, axistags=None, feature_names=None):
        logger.debug('Loading pytorch network from {}'.format(self._filename))

        if self.train_model:
            reordered_feature_images = []
            reordered_labels = []
            for i in range(len(feature_images)):
                self._opReorderAxes.Input.setValue(vigra.VigraArray(feature_images[i], axistags=axistags))
                self._opReorderAxes.AxisOrder.setValue('czyx')
                reordered_feature_images.append(self._opReorderAxes.Output([]).wait())

                self._opReorderAxes.Input.setValue(vigra.VigraArray(label_images[i], axistags=axistags))
                self._opReorderAxes.AxisOrder.setValue('czyx')
                reordered_labels.append(self._opReorderAxes.Output([]).wait())

            # TODO: check whether loaded network has the same number of classes as specified in ilastik!
            self._tikTorchClient.train(reordered_feature_images, reordered_labels)
            logger.info(self.description)

        return TikTorchLazyflowClassifier(self.tikTorchClient, self._filename)

    def determineBlockShape(self, max_shape, train=True):
        return self.tikTorchClient.dry_run(max_shape, train)

    def get_halo_shape(self, data_axes='zyxc'):
        halo = self.tikTorchClient.get('halo')
        if len(data_axes) == 4:
            return (0, 32, 32, 0)
        # FIXME: assuming 'yxc' !
        elif len(data_axes) == 3:
            return (32, 32, 0)

    @property
    def description(self):
        if self._tikTorchClient:
            return (
                f'pytorch network loaded from {self._filename} with '
                # f'expected input shape {self._loaded_pytorch_net.expected_input_shape} and "
                # f'output shape {self._loaded_pytorch_net.expected_output_shape}'
            )
        else:
            return f'pytorch network loading from {self._filename} failed'

    def estimated_ram_usage_per_requested_predictionchannel(self):
        # FIXME: compute from model size somehow??
        return numpy.inf

    def __eq__(self, other):
        return isinstance(other, type(self))

    def __ne__(self, other):
        return not self.__eq__(other)


assert issubclass(TikTorchLazyflowClassifierFactory, LazyflowPixelwiseClassifierFactoryABC)


class TikTorchLazyflowClassifier(LazyflowPixelwiseClassifierABC):
    HDF5_GROUP_FILENAME = 'pytorch_network_path'

    def __init__(self, client, filename=''):
        """
        Args:
            tiktorch_net (tiktorch): tiktorch object to be loaded into this
              classifier object
            filename (None, optional): Save file name for future reference
        """
        # Privates
        self._tikTorchClient = None
        self._opReorderAxes = OpReorderAxes(graph=Graph())
        self._filename = filename
        self._halo = None

        # Publics
        self.HALO_SIZE = 0
        self.tikTorchClient = client

    @property
    def tikTorchClient(self):
        return self._tikTorchClient

    @tikTorchClient.setter
    def tikTorchClient(self, value):
        if isinstance(value, TikTorchClient):
            self._tikTorchClient = value
        else:
            raise ValueError

    @property
    def halo(self):
        if self._halo is None:
            self.compute_halo()
        return self._halo

    def compute_halo(self):
        self._halo = self.tikTorchClient.get('halo')

    def predict_probabilities_pixelwise(self, feature_image, roi, axistags=None):
        """
        forward function for tiktorch, roi handling happens in tiktorch
        so its set to 0
        """
        assert isinstance(roi, numpy.ndarray)
        logger.info(f'tiktorchLazyflowClassifier.predict tile shape: {feature_image.shape}')
        self._opReorderAxes.Input.setValue(vigra.VigraArray(feature_image, axistags=axistags))
        self._opReorderAxes.AxisOrder.setValue('czyx')
        reordered_feature_image = self._opReorderAxes.Output([]).wait()

        transform = Compose(Normalize())
        reordered_feature_image = transform(reordered_feature_image)

        input_tensor = [reordered_feature_image[z] for z in range(reordered_feature_image.shape[0])]

        if len(self.halo) == 2:
            result = None
            for i in range(feature_image.shape[0]):
                input_ = [input_tensor[0][i: i+1]]
                out = self.tikTorchClient.forward(input_)
                if result is None:
                    result = out
                else:
                    result = numpy.concatenate((result, out), axis=1)
        else:
            result = self.tikTorchClient.forward(input_tensor)
        logger.info(f'Obtained a predicted block of shape {result.shape}')
        self._opReorderAxes.Input.setValue(vigra.VigraArray(result, axistags=vigra.defaultAxistags('czyx')))
        # axistags is vigra.AxisTags, but opReorderAxes expects a string
        self._opReorderAxes.AxisOrder.setValue(''.join(axistags.keys()))
        result = self._opReorderAxes.Output([]).wait()
        result = self.remove_halo(result)
        result = numpy.concatenate((result, 1-result), axis=3)

        return result

    def remove_halo(self, tensor):
        halo = self.tikTorchClient.get('halo')
        minimalIncrement = 32  # TODO: hardcoded for now. Better: include in TikTorch config file
        haloBlocked = tuple(int(numpy.ceil(x / minimalIncrement) * minimalIncrement - x) if x > 0 else minimalIncrement for x in halo)
        if len(halo) == 2:
            haloSlice = [slice(None), *[slice(x, -x) for x in haloBlocked], slice(None)]
        elif len(halo) == 3:
            haloSlice = [*[slice(x, -x) for x in haloBlocked], slice(None)]
        return tensor[haloSlice]

    @property
    def known_classes(self):
        return list(range(self.tikTorchClient.output_shape[0]))

    @property
    def feature_count(self):
        return self.tikTorchClient.expected_input_shape[0]

    def get_halo_shape(self, data_axes='zyxc'):
        halo = self.tikTorchClient.get('halo')
        minimalIncrement = 32 # TODO: hardcoded for now. Better: include in TikTorch config file
        haloBlocked = tuple(int(numpy.ceil(x / minimalIncrement) * minimalIncrement) if x > 0 else minimalIncrement for x in halo)
        if len(halo) == 2:
            return (0, *haloBlocked, 0)
        # FIXME: assuming 'yxc' !
        elif len(halo) == 3:
            return (*haloBlocked, 0)

    def serialize_hdf5(self, h5py_group):
        logger.debug('Serializing')
        h5py_group[self.HDF5_GROUP_FILENAME] = self._filename
        h5py_group['pickled_type'] = pickle.dumps(type(self), 0)

        # HACK: can this be done more elegantly?
        with tempfile.TemporaryFile() as f:
            self.tikTorchClient.serialize(f)
            f.seek(0)
            h5py_group['classifier'] = numpy.void(f.read())

    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        # TODO: load from HDF5 instead of hard coded path!
        logger.debug('Deserializing')
        # HACK:
        # filename = PYTORCH_MODEL_FILE_PATH
        filename = h5py_group[cls.HDF5_GROUP_FILENAME]
        logger.debug('Deserializing from {}'.format(filename))

        with tempfile.TemporaryFile() as f:
            f.write(h5py_group['classifier'].value)
            f.seek(0)
            loaded_pytorch_net = TikTorchClient.unserialize(f)

        return TikTorchLazyflowClassifier(loaded_pytorch_net, filename)


assert issubclass(TikTorchLazyflowClassifier, LazyflowPixelwiseClassifierABC)