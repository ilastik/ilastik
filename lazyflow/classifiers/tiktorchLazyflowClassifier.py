###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2019, the ilastik team
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
import os
import pickle as pickle
import logging
import tempfile
import yaml

import numpy
import vigra

from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.graph import Graph
from lazyflow.roi import roiToSlice
from inferno.io.transform import Compose
from inferno.io.transform.generic import Normalize

from tiktorch.client import TikTorchClient
from tiktorch.blockinator import np_pad

from .lazyflowClassifier import LazyflowPixelwiseClassifierABC, \
                                LazyflowPixelwiseClassifierFactoryABC

logger = logging.getLogger(__name__)

class TikTorchLazyflowClassifierFactory(LazyflowPixelwiseClassifierFactoryABC):
    # The version is used to determine compatibility of pickled classifier factories.
    # You must bump this if any instance members are added/removed/renamed.
    VERSION = 1

    def __init__(self, *args, server_config: dict, start_server=True):
        # Privates
        self._tikTorchClient = None
        self._tikTorchClassifier = None
        self._train_model = None
        self._opReorderAxes = OpReorderAxes(graph=Graph())
        self._opReorderAxes.AxisOrder.setValue('zcyx')

        # Publics
        self.tikTorchClient = TikTorchClient(*args, **server_config, start_server=start_server)

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

    def pause_training_process(self):
        if self.tikTorchClient.training_process_is_running():
            self.tikTorchClient.pause()
        else:
            logger.debug('tikTorchClient cannot be paused. (training process not running)')

    def resume_training_process(self):
        if self.tikTorchClient.training_process_is_running():
            self.tikTorchClient.resume()
        else:
            logger.debug('tikTorchClient cannot be resumed. (training process not running)')

    def send_hparams(self, hparams):
        self.tikTorchClient.set_hparams(hparams)

    def create_and_train_pixelwise(self, feature_images, label_images, axistags=None,
                                   feature_names=None, image_ids=None):
        logger.debug('Loading pytorch network')
        assert self.tikTorchClient is not None, \
               "TikTorchLazyflowClassifierFactory not properly initialized."

        if self.train_model:
            self.update(feature_images, label_images, axistags, image_ids)
            self._tikTorchClient.resume()
        else:
            self.update([], [], None, [])

        logger.info(self.description)

        if self._tikTorchClassifier is None:
            self._tikTorchClassifier = TikTorchLazyflowClassifier(self.tikTorchClient)

        return self._tikTorchClassifier

    def update(self, feature_images, label_images, axistags=None, image_ids=None):
        reordered_feature_images = []
        reordered_labels = []
        for i in range(len(feature_images)):
            self._opReorderAxes.Input.setValue(
                vigra.VigraArray(feature_images[i], axistags=axistags)
            )
            self._opReorderAxes.AxisOrder.setValue('czyx')
            reordered_feature_images.append(self._opReorderAxes.Output([]).wait())

            self._opReorderAxes.Input.setValue(
                vigra.VigraArray(label_images[i], axistags=axistags)
            )
            self._opReorderAxes.AxisOrder.setValue('czyx')
            reordered_labels.append(self._opReorderAxes.Output([]).wait())

        # TODO: check whether loaded network has the same number of classes as specified in ilastik!
        self._tikTorchClient.train(reordered_feature_images, reordered_labels, image_ids)

    def get_model_state(self):
        return self._tikTorchClient.get_model_state()

    def get_optimizer_state(self):
        return self._tikTorchClient.get_optimizer_state()

    @staticmethod
    def get_view_with_axes(in_array: numpy.ndarray, in_axiskeys: str, out_axiskeys: str) -> vigra.VigraArray:
        """
        Args:
            in_array: numpy array
            in_axiskeys: string specifying the input axisorder
            out_axiskeys: string specifying the output axisorder

        Returns:
            returns a view in the output axisorder

        """
        assert len(in_array.shape) == len(in_axiskeys)
        tagged_array = in_array.view(vigra.VigraArray)
        tagged_array.axistags = vigra.defaultAxistags(in_axiskeys)
        reordered_view = tagged_array.withAxes(*out_axiskeys)
        return reordered_view

    def determineBlockShape(self, max_shape, train=True):
        # determine blockshape with e.g. binary dry run
        pass

    def get_halo_shape(self, data_axes='zyxc'):
        # halo = self.tikTorchClient.get('halo')
        logger.warning('Using hardcoded halo')
        halo = {'t': 0, 'c': 0, 'z': 0, 'y': 32, 'x': 32}
        return tuple(halo[axis] for axis in data_axes)

    @property
    def description(self):
        if self._tikTorchClient:
            return 'pytorch network loaded.'
        else:
            return 'pytorch network loading failed.'

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

    def __init__(self, client):
        """
        Args:
            tiktorch_net (tiktorch): tiktorch object to be loaded into this
              classifier object
            filename (None, optional): Save file name for future reference
        """
        # Privates
        self._tikTorchClient = None
        self._opReorderAxesIn = OpReorderAxes(graph=Graph())
        self._opReorderAxesIn.AxisOrder.setValue('czyx')
        self._opReorderAxesOut = OpReorderAxes(graph=Graph())
        self._halo = None
        self._shrinkage = None
        self._valid_shapes = []

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
        return self.tikTorchClient.get('halo', assert_exist=True)

    @property
    def shrinkage(self):
        """
        Similar to a halo, the shrinkage describes the loss of image size in each dimension
        (for one border => half of the total size loss)
        :return: loss of image size per border in each dimension
        """
        return self.tikTorchClient.get('shrinkage', default=(0, 0, 0, 0))

    @property
    def valid_shapes(self):
        # All input data shapes the network can handle in ascending order.
        if not self._valid_shapes:
            self.compute_valid_shapes()
        return self._valid_shapes

    def compute_valid_shapes(self):
        """Computes all valid shapes in ascending order"""
        assert not self._valid_shapes, 'trying to recompute valid shapes'
        self._valid_shapes = []
        candidates = []
        candidates.append(self.tikTorchClient.get('min_input_shape'))  # todo: add more valid shapes

        for shape in candidates:
            if len(shape) == 2:  # assume yx
                new_shape = (1, 1, *shape)
            elif len(shape) == 3:  # assume cyx
                logger.warning(f'Ambiguous interpretation of shape {shape} as cyx')
                new_shape = (shape[0], 1, shape[1], shape[2])
            elif len(shape) == 4:  # assume czyx
                new_shape = tuple(shape)
            else:
                raise ValueError(f'Could not interpret shape: {shape}')

            self._valid_shapes.append(new_shape)
            if new_shape[0] == 1:
                # A single channel gives rise to two channels: (p, 1-p)
                self._valid_shapes.append((2, *new_shape[1:]))

    def predict_probabilities_pixelwise(self, feature_image, roi, axistags=None):
        """
        :param numpy.ndarray feature_image: classifier input
        :param numpy.ndarray roi: ROI within feature_image
        :param vigra.AxisTags axistags: axistags of feature_image
        :return: probabilities
        """
        assert isinstance(roi, numpy.ndarray)
        logger.info(f'tiktorchLazyflowClassifier.predict tile shape: {feature_image.shape}')

        # translate roi axes todo: remove with tczyx standard
        roi = roi[:, [axistags.index(a) for a in 'czyx']]

        self._opReorderAxesIn.Input.setValue(vigra.VigraArray(feature_image, axistags=axistags))
        reordered_feature_image = self._opReorderAxesIn.Output([]).wait()
        assert reordered_feature_image.shape in self.valid_shapes, (reordered_feature_image.shape, self.valid_shapes)
        transform = Compose(Normalize())
        reordered_feature_image = transform(reordered_feature_image)

        result = self.tikTorchClient.forward(reordered_feature_image)
        logger.info(f'Obtained a predicted block of shape {result.shape}')
        halo = numpy.array(self.get_halo_shape('czyx'))
        shrink = numpy.array(self.get_shrinkage('czyx'))
        # remove halo from result todo: do not send tensor with halo back, but remove halo in tiktorch instead
        assert len(result.shape) == len(halo), (result.shape, halo)
        result = result[[slice(h, -h) if h else slice(None) for h in halo]]

        # make two channels out of single channel predictions
        if result.shape[0] == 1:
            result = numpy.concatenate((result, 1-result), axis=0)
            logger.info(f'Changed shape of predicted block to {result.shape} by adding \'1-p\' channel')

        # remove shrinkage and halo from roi
        roi -= halo + shrink
        assert all(a >= 0 for a in roi[0]), roi[0]
        assert all(a <= s for a, s in zip(roi[1], result.shape)), (roi[1], result.shape)

        # select roi from result
        shape_wo_halo = result.shape
        result = result[roiToSlice(*roi)]
        logger.info(f'Selected roi (start: {roi[0]}, stop: {roi[1]}) from result without halo ({shape_wo_halo}). Now'
                    f' result has shape: ({result.shape}).')


        self._opReorderAxesOut.AxisOrder.setValue(''.join(axistags.keys()))
        self._opReorderAxesOut.Input.setValue(vigra.VigraArray(result, axistags=vigra.defaultAxistags('czyx')))
        return self._opReorderAxesOut.Output[:].wait()

    @property
    def known_classes(self):
        nr_classes = self.tikTorchClient.get('output_shape')[0]
        if nr_classes == 1:
            nr_classes = 2
        return list(range(nr_classes))

    @property
    def feature_count(self):
        return self.tikTorchClient.expected_input_shape[0]

    def get_halo_shape(self, data_axes='zyxc'):
        """
        :return: required halo for data axes
        """
        # todo: remove data_axes for all classifiers and set it implicitly to tczyx
        halo = self.halo

        if len(halo) == 2:
            tczyx_halo =  (0, 0, 0, *halo)
        elif len(halo) == 3:
            tczyx_halo =  (0, 0, *halo)
        else:
            raise NotImplementedError('Unknown halo length: {len(halo)}. How to interpret this halo: {halo}?')

        return tuple(tczyx_halo['tczyx'.index(axis)] for axis in data_axes)

    def get_shrinkage(self, data_axes='zyxc'):
        assert all([a in data_axes for a in 'czyx'])
        return tuple(self.shrinkage['czyx'.index(a)] for a in data_axes)

    def get_valid_shapes(self, data_axes='zyxc'):
        assert all([a in data_axes for a in 'czyx'])
        return [tuple(vs['czyx'.index(a)] for a in data_axes) for vs in self.valid_shapes]

    def serialize_hdf5(self, h5py_group):
        pass  # nothing to serialize here
    #     logger.debug('Serializing')
    #     h5py_group[self.HDF5_GROUP_FILENAME] = self._filename
    #     h5py_group['pickled_type'] = pickle.dumps(type(self), 0)
    #
    #     # HACK: can this be done more elegantly?
    #     with tempfile.TemporaryFile() as f:
    #         self.tikTorchClient.serialize(f)
    #         f.seek(0)
    #         h5py_group['classifier'] = numpy.void(f.read())

    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        pass  # nothing to deserialize here
    #     # TODO: load from HDF5 instead of hard coded path!
    #     logger.debug('Deserializing')
    #     # HACK:
    #     # filename = PYTORCH_MODEL_FILE_PATH
    #     filename = h5py_group[cls.HDF5_GROUP_FILENAME]
    #     logger.debug('Deserializing from {}'.format(filename))
    #
    #     with tempfile.TemporaryFile() as f:
    #         f.write(h5py_group['classifier'].value)
    #         f.seek(0)
    #         loaded_pytorch_net = TikTorchClient.unserialize(f)
    #
    #     return TikTorchLazyflowClassifier(loaded_pytorch_net, filename)

assert issubclass(TikTorchLazyflowClassifier, LazyflowPixelwiseClassifierABC)
