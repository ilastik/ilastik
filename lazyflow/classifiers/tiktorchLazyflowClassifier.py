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
from tiktorch.types import NDArray, LabeledNDArray, NDArrayBatch, LabeledNDArrayBatch, SetDeviceReturnType
from tiktorch.rpc_interface import INeuralNetworkAPI
from tiktorch.rpc import Client, TCPConnConf

from .lazyflowClassifier import LazyflowOnlineClassifier


logger = logging.getLogger(__name__)


class ReorderAxes:
    def __init__(self, axes_order: str) -> None:
        self.axes_order = axes_order
        self._op = OpReorderAxes(graph=Graph())
        self._op.AxisOrder.setValue(axes_order)

    def reorder(self, input_arr: numpy.ndarray, axes_tags: str):
        tagged_arr = vigra.VigraArray(input_arr, axistags=axes_tags)
        self._op.Input.setValue(tagged_arr)
        return self._op.Output([]).wait()


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
        self._our_reorderer = ReorderAxes(self.input_axis_order)
        self._opReorderAxesInImg = OpReorderAxes(graph=Graph())
        self._opReorderAxesInLabel = OpReorderAxes(graph=Graph())
        self._opReorderAxesInImg.AxisOrder.setValue(self.input_axis_order)
        self._opReorderAxesInLabel.AxisOrder.setValue(self.input_axis_order)
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

        if len(self.input_axis_order) != len(ret.training_shape):
            raise ValueError(
                f"input axis order {self.input_axis_order} incompatible with determined training shape {ret.training_shape}"
            )
        if any([len(self.input_axis_order) != len(vs) for vs in ret.valid_shapes]):
            raise ValueError(
                f"input axis order {self.input_axis_order} incompatible with determined valid shapes {ret.valid_shapes}"
            )
        if len(self.input_axis_order) != len(ret.shrinkage):
            raise ValueError(
                f"input axis order {self.input_axis_order} incompatible with determined shrinkage {ret.shrinkage}"
            )

        self.training_shape = tuple([dict(zip(self.input_axis_order, ret.training_shape)).get(a, 1) for a in "tczyx"])
        self.valid_shapes = [
            tuple([dict(zip(self.input_axis_order, vs)).get(a, 1) for a in "tczyx"]) for vs in ret.valid_shapes
        ]
        self.shrinkage = tuple([dict(zip(self.input_axis_order, ret.shrinkage)).get(a, 0) for a in "tczyx"])

    def _reorder_out(self, arr, axes_tags):
        return self._our_reorderer.reorder(arr, axes_tags)

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

    def pause_training(self):
        self.tikTorchClient.pause_training()

    def resume_training(self):
        self.tikTorchClient.resume_training()

    def send_hparams(self, hparams):
        self.tikTorchClient.set_hparams(hparams)

    def create_and_train_pixelwise(
        self, feature_images, label_images, axistags=None, feature_names=None, image_ids=None
    ):
        logger.debug("Loading pytorch network")
        assert self.tikTorchClient is not None, "TikTorchLazyflowClassifierFactory not properly initialized."

        if self.train_model:
            self.update(feature_images, label_images, axistags, image_ids)
            self.resume_training()

        logger.info(self.description)

        return self

    def update(self, feature_images: Iterable, label_images: Iterable, axistags, image_ids: Iterable):
        # TODO: check whether loaded network has the same number of classes as specified in ilastik!
        images = []
        labels = []

        for img, label, id_ in zip(feature_images, label_images, image_ids):
            out_img = self._reorder_out(img, axistags)
            out_label = self._reorder_out(label, axistags)
            images.append(NDArray(out_img, id_))
            labels.append(NDArray(out_label, id_))

        self.tikTorchClient.update_training_data(NDArrayBatch(images), NDArrayBatch(labels))

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
        logger.info("predict tile shape: %s (axistags: %r)", feature_image.shape, axistags)

        # translate roi axes todo: remove with tczyx standard
        output_axis_order = self.output_axis_order
        if "c" not in output_axis_order:
            output_axis_order = "c" + output_axis_order
            c_was_not_in_output_axis_order = True
        else:
            c_was_not_in_output_axis_order = False

        roi = roi[:, [axistags.index(a) for a in output_axis_order]]

        self._opReorderAxesInImg.Input.setValue(vigra.VigraArray(feature_image, axistags=axistags))
        reordered_feature_image = self._opReorderAxesInImg.Output([]).wait()
        # todo: do transforms in tiktorch
        transform = Compose(Normalize())
        reordered_feature_image = transform(reordered_feature_image)

        result = self.tikTorchClient.forward(NDArray(reordered_feature_image)).result().as_numpy()[0]
        logger.info(f"Obtained a predicted block of shape {result.shape}")
        if c_was_not_in_output_axis_order:
            result = result[None, ...]

        halo = numpy.array(self.get_halo(output_axis_order))
        shrink = numpy.array(self.get_shrinkage(output_axis_order))
        # remove halo from result todo: do not send tensor with halo back, but remove halo in tiktorch instead
        assert len(result.shape) == len(halo), (result.shape, halo)
        result = result[[slice(h, -h) if h else slice(None) for h in halo]]

        # make two channels out of single channel predictions
        channel_axis = output_axis_order.find("c")
        if result.shape[channel_axis] == 1:
            result = numpy.concatenate((result, 1 - result), axis=channel_axis)
            logger.info(f"Changed shape of predicted block to {result.shape} by adding '1-p' channel")

        # remove shrinkage and halo from roi
        logger.debug('roi %s\nhalo %s\nshrink %s', roi, halo, shrink)
        roi -= halo + shrink
        assert all(a >= 0 for a in roi[0]), roi[0]
        assert all(a <= s for a, s in zip(roi[1], result.shape)), (roi[1], result.shape)

        # select roi from result
        shape_wo_halo = result.shape
        result = result[roiToSlice(*roi)]
        logger.info(
            f"Selected roi (start: {roi[0]}, stop: {roi[1]}) from result without halo {shape_wo_halo}. Now"
            f" result has shape: ({result.shape})."
        )

        self._opReorderAxesOut.AxisOrder.setValue("".join(axistags.keys()))
        self._opReorderAxesOut.Input.setValue(vigra.VigraArray(result, axistags=vigra.defaultAxistags(output_axis_order)))
        return self._opReorderAxesOut.Output[:].wait()

    @property
    def known_classes(self):
        nclasses = self.training_shape[1] - self.shrinkage[1]
        if nclasses == 1:
            nclasses += 1
        return list(range(1, 1 + nclasses))

    @property
    def feature_count(self):
        return self.input_channels

    def set_halo(self, halo: Tuple[int, ...]) -> None:
        in_order = self.input_axis_order.replace("b", "")
        if len(in_order) == len(halo) + 1:
            # assume channel axis to be left out in halo
            in_order = in_order.replace("c", "")

        if len(in_order) != len(halo):
            raise ValueError(f"Input axis order {self.input_axis_order} incompatible with halo {halo}")

        halo_dims = dict(zip(in_order, halo))
        if "c" in halo_dims and halo_dims["c"] != 0:
            raise ValueError(
                f"Expected halo for channel axis to be zero, but found halo {halo} with input axis order "
                f"{self.input_axis_order} => {halo_dims}"
            )

        self.halo = tuple([halo_dims.get(a, 0) for a in "tczyx"])

    def get_halo(self, data_axes: str = "zyx") -> Tuple[int, ...]:
        """
        :return: required halo for data axes
        """
        assert "b" not in data_axes, "batch dimension cannot be halo dimension"
        assert all([a in "tczyx" for a in data_axes])
        halo = [self.halo["tczyx".index(a)] for a in data_axes]
        # todo: remove data_axes for all classifiers and set it implicitly to tczyx

        return tuple(halo)

    def get_shrinkage(self, data_axes: str = "zyx"):
        assert all([a in "tczyx" for a in data_axes])
        shrink = [self.shrinkage["tczyx".index(a)] for a in data_axes]
        assert all([s % 2 == 0 for s in shrink]), shrink
        return tuple(s // 2 for s in shrink)

    @property
    def output_channels(self):
        return self.input_channels - self.shrinkage[1]

    def get_valid_shapes(self, data_axes: str = "zyx"):
        assert all([a in "tczyx" for a in data_axes])
        return [tuple(vs["tczyx".index(a)] for a in data_axes) for vs in self.valid_shapes]

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
