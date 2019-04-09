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
import logging
import socket
import numpy

from typing import Iterable, Tuple

import vigra

from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.graph import Graph
from lazyflow.roi import roiToSlice
from inferno.io.transform import Compose
from inferno.io.transform.generic import Normalize

from tiktorch import serializers  # noqa
from tiktorch.launcher import LocalServerLauncher, RemoteSSHServerLauncher, SSHCred
from tiktorch.types import (
    NDArray,
    LabeledNDArray,
    NDArrayBatch,
    LabeledNDArrayBatch,
    Point2D,
    Point3D,
    Point4D,
    SetDeviceReturnType,
)
from tiktorch.rpc_interface import INeuralNetworkAPI
from tiktorch.rpc import Client, TCPConnConf

from .lazyflowClassifier import LazyflowOnlineClassifier


logger = logging.getLogger(__name__)


class TikTorchLazyflowClassifierFactory(LazyflowOnlineClassifier):
    # The version is used to determine compatibility of pickled classifier factories.
    # You must bump this if any instance members are added/removed/renamed.
    VERSION = 1
    halo: Tuple[int, int, int, int, int]

    def __init__(
        self, config: dict, binary_model: bytes, binary_state: bytes, binary_optimizer_state: bytes, server_config: dict
    ) -> None:
        # default values for config:
        self._config = {"name": "tiktorch model"}
        self._config.update(config)
        self.set_halo(config["halo"])

        # assert all(key not in self._config for key in self.__dict__.keys())
        # self.__dict__.update(self._config)
        # print('shrinkage:', self.shrinkage)

        # Privates
        self._tikTorchClassifier = None
        self._train_model = None
        self._opReorderAxesInImg = OpReorderAxes(graph=Graph())
        self._opReorderAxesInLabel = OpReorderAxes(graph=Graph())
        self._opReorderAxesInImg.AxisOrder.setValue("czyx")
        self._opReorderAxesInLabel.AxisOrder.setValue("czyx")
        self._opReorderAxesOut = OpReorderAxes(graph=Graph())

        addr, port1, port2 = (
            socket.gethostbyname(server_config["address"]),
            server_config["port1"],
            server_config["port2"],
        )
        conn_conf = TCPConnConf(addr, port1, port2)

        if addr == "127.0.0.1":
            self.launcher = LocalServerLauncher(conn_conf)
        else:
            self.launcher = RemoteSSHServerLauncher(
                conn_conf, cred=SSHCred(server_config["username"], server_config["password"])
            )

        self.launcher.start()
        self._shutdown_sent = False

        self._tikTorchClient = Client(INeuralNetworkAPI(), conn_conf)
        selected_devices = [d[0] for d in server_config["devices"] if d[2]]
        logger.debug("loading tiktorch model with config: %s", config)
        fut = self._tikTorchClient.load_model(
            config, binary_model, binary_state, binary_optimizer_state, selected_devices
        )
        try:
            ret: SetDeviceReturnType = fut.result(timeout=60)
        except Exception as e:
            logger.warning(e)
            logger.warning("Could not load tiktorch model within 60 seconds. Trying again for another 360s ...")
            ret: SetDeviceReturnType = fut.result(timeout=360)  # todo: except timeout

        self.training_shape = ret.training_shape
        self.valid_shapes = ret.valid_shapes
        self.shrinkage = ret.shrinkage

    def __getattr__(self, item):
        if item != "_config":
            try:
                return self._config[item]
            except (AttributeError, KeyError):
                pass

        raise AttributeError(item)

    def shutdown(self):
        self._shutdown_sent = True
        self.launcher.stop()

    @property
    def tikTorchClient(self):
        return self._tikTorchClient

    @property
    def train_model(self):
        return self._train_model

    @train_model.setter
    def train_model(self, value):
        if isinstance(value, bool):
            self._train_model = value
        else:
            raise ValueError(f"expected boolean, got {value}")

    def pause_training_process(self):
        if self.tikTorchClient.training_process_is_running():
            self.tikTorchClient.pause()
        else:
            logger.debug("tikTorchClient cannot be paused. (training process not running)")

    def resume_training_process(self):
        if self.tikTorchClient.training_process_is_running():
            self.tikTorchClient.resume()
        else:
            logger.debug("tikTorchClient cannot be resumed. (training process not running)")

    def send_hparams(self, hparams):
        self.tikTorchClient.set_hparams(hparams)

    def create_and_train_pixelwise(
        self, feature_images, label_images, axistags=None, feature_names=None, image_ids=None
    ):
        logger.debug("Loading pytorch network")
        assert self.tikTorchClient is not None, "TikTorchLazyflowClassifierFactory not properly initialized."

        if self.train_model:
            self.update(feature_images, label_images, axistags, image_ids)
            self.tikTorchClient.resume()

        logger.info(self.description)

        return self

    def update(self, feature_images: Iterable, label_images: Iterable, axistags, image_ids: Iterable):
        # TODO: check whether loaded network has the same number of classes as specified in ilastik!
        data = []
        reordered_labels = []
        for img, label, id in zip(feature_images, label_images, image_ids):
            self._opReorderAxesInImg.Input.setValue(vigra.VigraArray(img, axistags=axistags))
            self._opReorderAxesInLabel.Input.setValue(vigra.VigraArray(label, axistags=axistags))
            data.append(
                LabeledNDArray(
                    array=self._opReorderAxesInImg.Output([]).wait(),
                    label=self._opReorderAxesInLabel.Output([]).wait(),
                    id_=id,
                )
            )

        data = LabeledNDArrayBatch(data)

        self.tikTorchClient.train(data)

    def get_model_state(self):
        return self.tikTorchClient.get_model_state()

    def get_optimizer_state(self):
        return self.tikTorchClient.get_optimizer_state()

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

    @property
    def description(self):
        if self.tikTorchClient:
            return "pytorch network loaded."
        else:
            return "pytorch network loading failed."

    def estimated_ram_usage_per_requested_predictionchannel(self):
        # FIXME: compute from model size somehow??
        return numpy.inf

    def __eq__(self, other):
        return isinstance(other, type(self))

    def __ne__(self, other):
        return not self.__eq__(other)

    def predict_probabilities_pixelwise(self, feature_image, roi, axistags=None):
        """
        :param numpy.ndarray feature_image: classifier input
        :param numpy.ndarray roi: ROI within feature_image
        :param vigra.AxisTags axistags: axistags of feature_image
        :return: probabilities
        """
        assert isinstance(roi, numpy.ndarray)
        logger.info(f"tiktorchLazyflowClassifier.predict tile shape: {feature_image.shape}")

        # translate roi axes todo: remove with tczyx standard
        roi = roi[:, [axistags.index(a) for a in "czyx"]]

        self._opReorderAxesIn.Input.setValue(vigra.VigraArray(feature_image, axistags=axistags))
        reordered_feature_image = self._opReorderAxesIn.Output([]).wait()
        assert reordered_feature_image.shape in self.valid_shapes, (reordered_feature_image.shape, self.valid_shapes)
        transform = Compose(Normalize())
        reordered_feature_image = transform(reordered_feature_image)

        result = self.tikTorchClient.forward(NDArrayBatch([NDArray(reordered_feature_image)])).as_numpy()[0]
        logger.info(f"Obtained a predicted block of shape {result.shape}")
        halo = numpy.array(self.get_halo("zyx"))
        shrink = numpy.array(self.get_shrinkage("zyx"))
        # remove halo from result todo: do not send tensor with halo back, but remove halo in tiktorch instead
        assert len(result.shape) == len(halo), (result.shape, halo)
        result = result[[slice(h, -h) if h else slice(None) for h in halo]]

        # make two channels out of single channel predictions
        if result.shape[0] == 1:
            result = numpy.concatenate((result, 1 - result), axis=0)
            logger.info(f"Changed shape of predicted block to {result.shape} by adding '1-p' channel")

        # remove shrinkage and halo from roi
        roi -= halo + shrink
        assert all(a >= 0 for a in roi[0]), roi[0]
        assert all(a <= s for a, s in zip(roi[1], result.shape)), (roi[1], result.shape)

        # select roi from result
        shape_wo_halo = result.shape
        result = result[roiToSlice(*roi)]
        logger.info(
            f"Selected roi (start: {roi[0]}, stop: {roi[1]}) from result without halo ({shape_wo_halo}). Now"
            f" result has shape: ({result.shape})."
        )

        self._opReorderAxesOut.AxisOrder.setValue("".join(axistags.keys()))
        self._opReorderAxesOut.Input.setValue(vigra.VigraArray(result, axistags=vigra.defaultAxistags("czyx")))
        return self._opReorderAxesOut.Output[:].wait()

    @property
    def known_classes(self):
        nr_classes = self.output_shape[0]
        if nr_classes == 1:
            nr_classes = 2
        return list(range(nr_classes))

    @property
    def feature_count(self):
        return self.input_channels

    def set_halo(self, halo: Tuple[int, ...]) -> None:
        in_order = self.input_axis_order.replace("b", "").replace("c", "")
        if len(in_order) != len(halo):
            raise ValueError(
                "Input order (optionally including batch dimension 'b' and channel dimension 'c') incompatible with halo (always excluding 'b' and 'c'"
            )
        halo_dims = {a: h for a, h in zip(in_order, halo)}
        self.halo = tuple([halo_dims.get(a, 0) for a in "tczyx"])

    def get_halo(self, data_axes="zyx") -> Tuple[int, ...]:
        """
        :return: required halo for data axes
        """
        assert "b" not in data_axes, "batch dimension cannot be halo dimension"
        assert all([a in "tczyx" for a in data_axes])
        halo = [self.halo["tczyx".index(a)] for a in data_axes]
        # todo: remove data_axes for all classifiers and set it implicitly to tczyx

        return tuple(halo)

    def get_shrinkage(self, data_axes="zyx"):
        assert all([a in "tczyx" for a in data_axes])
        shrink = [self.shrinkage.get(a, 0) for a in "zyx"]
        assert all([s % 2 == 0 for s in shrink])
        return tuple(s // 2 for s in shrink)

    @property
    def output_channels(self):
        return self.input_channels - self.shrinkage[1]

    def get_valid_shapes(self, data_axes="zyx"):
        assert all([a in data_axes for a in "czyx"])
        return [tuple(vs[a] for a in data_axes) for vs in self.valid_shapes]

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

    def __del__(self):
        if not self._shutdown_sent:
            try:
                self.launcher.stop()
            except AttributeError:
                pass
