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
import warnings
from collections import defaultdict
from typing import Iterable, List, Callable

import vigra
import grpc


from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.graph import Graph
from lazyflow.request import Request
from lazyflow.roi import roiToSlice
from lazyflow.futures_utils import MappableFuture, map_future

from tiktorch import converters
from tiktorch.proto import data_store_pb2, data_store_pb2_grpc, inference_pb2, inference_pb2_grpc

from vigra import AxisTags

from . import _base

logger = logging.getLogger(__name__)


class ModelSession:
    def __init__(self, session, factory):
        self.__session = session
        self.__factory = factory

    @property
    def tiktorchClient(self):
        return self.__factory._client

    def create_and_train_pixelwise(self, *args, **kwargs):
        self.__factory.create_and_train_pixelwise(*args, **kwargs)
        return self

    @property
    def name(self):
        return self.__session.name

    @property
    def input_axes(self):
        return self.__session.inputAxes

    @property
    def output_axes(self):
        return self.__session.outputAxes

    @property
    def offset(self):
        return self.__session.offset

    @property
    def scale(self):
        return self.__session.scale

    def get_output_shape(self):
        """
        shape = shape(input_tensor) * scale + 2 * offset
        """
        offsets = defaultdict(lambda: 0, {d.name: d.size for d in self.offset})
        scales = defaultdict(lambda: 1.0, {d.name: d.size for d in self.scale})

        result = []
        # FIXME: currently we don't make use of having potentially multiple valid
        # output shapes. It can make sense, to choose it dynamically, e.g.
        # a smaller one for "live" prediction, a larger one for batch
        for shape in self.__session.validShapes:
            dim_size_by_name = {d.name: d.size for d in shape.dims}
            valid_shape = {}
            for dim in dim_size_by_name:
                valid_shape[dim] = int(dim_size_by_name[dim] * scales[dim] + 2 * offsets[dim])

            result.append(valid_shape)
        return result[0]

    @property
    def has_training(self):
        return self.__session.hasTraining

    def get_halo(self, axes: str = "zyx"):
        dim_size_by_name = {d.name: d.size for d in self.__session.halo}
        return [dim_size_by_name.get(axis, 0) for axis in axes]

    def get_valid_shapes(self, axes: str = "zyx"):
        result = []
        for shape in self.__session.validShapes:
            dim_size_by_name = {d.name: d.size for d in shape.dims}

            valid_shape = []
            for axis in axes:
                size = dim_size_by_name.get(axis, 1)
                valid_shape.append(size)

            result.append(valid_shape)

        return result

    @property
    def training_shape(self):
        warnings.warn("HARDCODED training shape, this might not do what you want.")
        return [0, 0, 0, 128, 128]

    @property
    def known_classes(self):
        output_shape = self.get_output_shape()
        return list(range(1, int(output_shape["c"]) + 1))

    @property
    def num_classes(self):
        return len(self.known_classes)

    def update(self, feature_images: Iterable, label_images: Iterable, axistags, image_ids: Iterable):
        # TODO: check whether loaded network has the same number of classes as specified in ilastik!
        return
        images = []
        labels = []
        to_remove = []

        for img, label, id_ in zip(feature_images, label_images, image_ids):
            id_str = ",".join(str(v) for v in id_)
            if not label.any():
                to_remove.append(id_str)
                continue

            out_img = self._reorder_out(img, axistags)
            out_label = self._reorder_out(label, axistags)
            out_label = out_label.astype(numpy.uint8)

            images.append(NDArray(out_img, id_str))
            labels.append(NDArray(out_label, id_str))

        self.tikTorchClient.update_training_data(NDArrayBatch(images), NDArrayBatch(labels))
        self.tikTorchClient.remove_data("training", to_remove)

    def close(self):
        self.tiktorchClient.CloseModelSession(self.__session)

    def predict(self, feature_image, roi, axistags=None):
        """
        :param numpy.ndarray feature_image: classifier input
        :param numpy.ndarray roi: ROI within feature_image
        :param vigra.AxisTags axistags: axistags of feature_image
        :return: probabilities
        """
        assert isinstance(roi, numpy.ndarray)
        logger.debug("predict tile shape: %s (axistags: %r)", feature_image.shape, axistags)

        # translate roi axes todo: remove with tczyx standard
        # output_axis_order = self._model_conf.output_axis_order
        output_axis_order = self.output_axes
        if "c" not in output_axis_order:
            output_axis_order = "c" + output_axis_order
            c_was_not_in_output_axis_order = True
        else:
            c_was_not_in_output_axis_order = False
        roi = roi[:, [axistags.index(a) for a in output_axis_order]]

        reordered_feature_image = reorder_axes(feature_image, from_axes_tags=axistags, to_axes_tags=self.input_axes)

        try:
            current_rq = Request._current_request()
            resp = self.tiktorchClient.Predict.future(
                inference_pb2.PredictRequest(
                    tensor=converters.numpy_to_pb_tensor(reordered_feature_image, axistags=self.input_axes),
                    modelSessionId=self.__session.id,
                )
            )
            resp.add_done_callback(lambda o: current_rq._wake_up())
            current_rq._suspend()
            resp = resp.result()
            result = converters.pb_tensor_to_numpy(resp.tensor)
        except Exception:
            logger.exception("Predict call failed")
            return 0

        logger.debug(f"Obtained a predicted block of shape {result.shape}")
        if c_was_not_in_output_axis_order:
            result = result[None, ...]

        # make two channels out of single channel predictions
        channel_axis = output_axis_order.find("c")
        if result.shape[channel_axis] == 1:
            result = numpy.concatenate((result, 1 - result), axis=channel_axis)
            logger.debug(f"Changed shape of predicted block to {result.shape} by adding '1-p' channel")

        shape_wo_halo = result.shape
        result = result[roiToSlice(*roi)]
        logger.debug(
            f"Selected roi (start: {roi[0]}, stop: {roi[1]}) from result without halo {shape_wo_halo}. Now"
            f" result has shape: ({result.shape})."
        )

        return reorder_axes(result, from_axes_tags=output_axis_order, to_axes_tags=axistags)


def reorder_axes(input_arr: numpy.ndarray, *, from_axes_tags: str, to_axes_tags: str):
    if isinstance(from_axes_tags, AxisTags):
        from_axes_tags = "".join(from_axes_tags.keys())

    if isinstance(to_axes_tags, AxisTags):
        to_axes_tags = "".join(to_axes_tags.keys())

    op = OpReorderAxes(graph=Graph())

    tagged_arr = vigra.VigraArray(input_arr, axistags=vigra.defaultAxistags(from_axes_tags))
    op.Input.setValue(tagged_arr)
    op.AxisOrder.setValue(to_axes_tags)

    return op.Output([]).wait()


class _NullLauncher:
    def start(self):
        pass

    def stop(self):
        pass


class Progress:
    def __init__(self):
        self.__cancelled = False

    def cancel(self):
        self.__cancelled = True

    def canceled(self):
        return self.__cancelled

    def report(self, percent: int) -> None:
        raise NotImplementedError


class Connection(_base.IConnection):
    UPLOAD_CHUNK_SIZE = 1 * 1024 * 1024  # 1mb

    def __init__(self, client, upload_client):
        self._client = client
        self._upload_client = upload_client

    def get_devices(self):
        resp = self._client.ListDevices(inference_pb2.Empty())
        return [(d.id, d.id) for d in resp.devices]

    def upload(self, content: bytes, *, progress_cb: Callable[[int], None], cancel_token=None) -> MappableFuture[str]:
        def _content_iter():
            total_size = len(content)

            yield data_store_pb2.UploadRequest(info=data_store_pb2.UploadInfo(size=total_size))

            for i in range(0, total_size, self.UPLOAD_CHUNK_SIZE):
                yield data_store_pb2.UploadRequest(content=content[i : i + self.UPLOAD_CHUNK_SIZE])
                progress_cb(int(min(i + self.UPLOAD_CHUNK_SIZE, total_size) * 100 / total_size))

            progress_cb(100)

        result = self._upload_client.Upload.future(_content_iter())
        cancel_token.add_callback(result.cancel)

        return map_future(result, lambda res: res.id)

    def create_model_session(self, upload_id: str, devices: List[str]):
        session = self._client.CreateModelSession(
            inference_pb2.CreateModelSessionRequest(model_uri=f"upload://{upload_id}", deviceIds=devices)
        )
        return ModelSession(session, self)


class TiktorchConnectionFactory(_base.IConnectionFactory):
    def ensure_connection(self, config):
        if self._connection:
            return self._connection

        _100_MB = 100 * 1024 * 1024
        server_config = config
        host, port = server_config.address.split(":")
        addr = socket.gethostbyname(host)
        logger.debug("Trying to connect to tiktorch server using %s(%s):%s", host, addr, port),
        self._chan = grpc.insecure_channel(
            f"{addr}:{port}",
            options=[("grpc.max_send_message_length", _100_MB), ("grpc.max_receive_message_length", _100_MB)],
        )
        client = inference_pb2_grpc.InferenceStub(self._chan)
        upload_client = data_store_pb2_grpc.DataStoreStub(self._chan)
        self._devices = [d.id for d in server_config.devices if d.enabled]
        self._connection = Connection(client, upload_client)
        return self._connection

    def __init__(self) -> None:
        self._tikTorchClassifier = None
        self._train_model = None
        self._shutdown_sent = False
        self._connection = None

    def shutdown(self):
        self._shutdown_sent = True
        self.launcher.stop()

    @property
    def tikTorchClient(self):
        return self._tikTorchClient

    @property
    def description(self):
        if self.tikTorchClient:
            return "TikTorch classifier (client available)"
        else:
            return "TikTorch classifier (client missing)"

    def __eq__(self, other):
        return isinstance(other, type(self))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __del__(self):
        if not self._shutdown_sent:
            try:
                self.launcher.stop()
            except AttributeError:
                pass
