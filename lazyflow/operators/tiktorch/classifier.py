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
from typing import Iterable, List, Callable, Tuple, Dict

import xarray
import vigra
import grpc


from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.graph import Graph
from lazyflow.request import Request
from lazyflow.roi import roiToSlice
from lazyflow.futures_utils import MappableFuture, map_future

from tiktorch import converters
from tiktorch.proto import data_store_pb2, data_store_pb2_grpc, inference_pb2, inference_pb2_grpc

# HACK: prediction_pipeline uses this heuristic to guess a sensible shape
# we need to do the same on the ilastik side, as the correct model info is sent
# over.
# from bioimageio.core.prediction_pipeline._prediction_pipeline import enforce_min_shape

from vigra import AxisTags

from . import _base

logger = logging.getLogger(__name__)


def enforce_min_shape(min_shape, step, axes):
    """Hack: pick a bigger shape than min shape

    Some models come with super tiny minimal shapes, that make the processing
    too slow. While dryrun is not implemented, we'll "guess" a sensible shape
    and hope it will fit into memory.
    """
    MIN_SIZE_2D = 512
    MIN_SIZE_3D = 64

    assert len(min_shape) == len(step) == len(axes)

    spacial_increments = sum(i != 0 for i, a in zip(step, axes) if a in "xyz")
    if spacial_increments > 2:
        target_size = MIN_SIZE_3D
    else:
        target_size = MIN_SIZE_2D

    factors = [
        int(numpy.ceil((target_size - s) / i)) for s, i, a in zip(min_shape, step, axes) if (a in "xyz") and (i != 0)
    ]
    # we assume shape is "large" enough if one of the axes is larger than min_size
    if any(f <= 0 for f in factors):
        return min_shape

    # choose the smallest increment to make at least one size >= target_size
    m = min([x for x in factors])
    return [s + i * m for s, i in zip(min_shape, step)]


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
    def name(self) -> str:
        return self.__session.name

    @property
    def input_axes(self) -> List[str]:
        return self.__session.inputAxes

    @property
    def output_axes(self) -> List[str]:
        return self.__session.outputAxes

    def get_output_shapes(self) -> List[List[Dict[str, int]]]:
        """Get output shapes for all model output
        shape = shape(reference_input_tensor) * scale + 2 * offset
        """
        # FIXME: we don't really send over reference tensor ids yet.
        # so for now,
        output_axes = self.output_axes[0]
        input_shapes = self.get_input_shapes(axes="".join(output_axes))
        assert (
            len(input_shapes) == 1
        ), "Currently referencing input tensors by name not supported. Fail if more than one input"
        input_shape = input_shapes[0][0]
        input_shape_by_name = {name: size for name, size in zip(output_axes, input_shape)}
        result = []
        output_shapes = self.__session.outputShapes
        assert len(output_shapes) == 1, "Currently only single output shapes are supported"
        for shape in self.__session.outputShapes:
            if shape.shapeType == 0:
                # explicit shape
                output_shape_by_name = {d.name: d.size for d in shape.shape.namedInts}
                result.append([output_shape_by_name])
            elif shape.shapeType == 1:
                # parametrized shape
                # HACK: need to determine min shape same way as prediction_pipeline
                # HACK: assume input tensor at index 0 of input shapes
                offset_size_by_name = defaultdict(lambda: 0, {d.name: d.size for d in shape.offset.namedFloats})
                scale_size_by_name = defaultdict(lambda: 1.0, {d.name: d.size for d in shape.scale.namedFloats})
                output_shape_by_name = {}
                for dim in input_shape_by_name:
                    output_shape_by_name[dim] = int(
                        input_shape_by_name[dim] * scale_size_by_name[dim] + 2 * offset_size_by_name[dim]
                    )
                result.append([output_shape_by_name])
            else:
                raise ValueError(f"Cannot work with shapes of shapeType {shape.shapeType}")

        # sanity check:
        assert len(result) == 1
        res = result[0][0]
        axes = "".join(res.keys())
        halo = self.get_halos(axes=axes)
        assert len(halo) == 1
        halo = halo[0]
        shape_after_halo = [res[axkey] - 2 * axhalo for axkey, axhalo in zip(axes, halo)]
        if not all(x > 0 for x in shape_after_halo):
            logger.warning(f"Network configuration problem detected - output shape - 2*halo invalid:{shape_after_halo}")

        return result

    @property
    def has_training(self) -> bool:
        return self.__session.hasTraining

    def get_halos(self, axes: str = "zyx") -> List[Tuple[int]]:
        if isinstance(axes, AxisTags):
            axes = "".join(axes.keys())
        halos = []
        for output_shape in self.__session.outputShapes:
            halo_size_by_name = {d.name: d.size for d in output_shape.halo.namedInts}
            halos.append(tuple([halo_size_by_name.get(axis, 0) for axis in axes]))

        return halos

    def get_input_shapes(self, axes: str = "zyx") -> List[List[Tuple[int]]]:
        """Get input shapes for all model inputs

        Returns:
          models can take multiple images as inputs. For each such input, a list
            of shapes is returned.
        """
        if isinstance(axes, AxisTags):
            axes = "".join(axes.keys())
        result = []
        for shape in self.__session.inputShapes:
            if shape.shapeType == 0:
                # explicit shape
                dim_size_by_name = defaultdict(lambda: 1, {d.name: d.size for d in shape.shape.namedInts})
                result.append([tuple([dim_size_by_name[axis] for axis in axes])])
            elif shape.shapeType == 1:
                # parametrized shape
                # HACK: need to determine min shape same way as prediction_pipeline
                dim_size_by_name = defaultdict(lambda: 1, {d.name: d.size for d in shape.shape.namedInts})
                dim_step_by_name = defaultdict(lambda: 0, {d.name: d.size for d in shape.stepShape.namedInts})
                shape_dims = "".join(d.name for d in shape.shape.namedInts)
                min_shape = enforce_min_shape(
                    [dim_size_by_name[x] for x in shape_dims], [dim_step_by_name[x] for x in shape_dims], shape_dims
                )
                min_shape_by_name = defaultdict(lambda: 1, {name: size for name, size in zip(shape_dims, min_shape)})
                result.append([tuple(min_shape_by_name[axis] for axis in axes)])
            else:
                raise ValueError(f"Cannot work with shapes of shapeType {shape.shapeType}")

        return result

    @property
    def training_shape(self) -> Tuple[int]:
        warnings.warn("HARDCODED training shape, this might not do what you want.")
        return (0, 0, 0, 128, 128)

    @property
    def known_classes(self) -> List[int]:
        """
        FIXME: assumes a single output!
        """
        output_shapes = self.get_output_shapes()
        assert len(output_shapes) == 1, "Currenlty only a single output is supported"
        # there could be multiple output shapes per output in the future (with implicit output shapes)
        output_shape = output_shapes[0][0]
        assert "c" in output_shape, "Channel Axis needed in output shape"
        return list(range(1, int(output_shape["c"]) + 1))

    @property
    def num_classes(self) -> int:
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
        output_axes = self.output_axes
        assert len(output_axes) == 1
        output_axis_order = output_axes[0]
        # need to handle batch dimension :/
        if "c" not in output_axis_order:
            output_axis_order = "c" + output_axis_order
            c_was_not_in_output_axis_order = True
        else:
            c_was_not_in_output_axis_order = False

        input_axes = self.input_axes
        assert len(input_axes) == 1
        input_axis_order = input_axes[0]
        reordered_feature_image = reorder_axes(feature_image, from_axes_tags=axistags, to_axes_tags=input_axis_order)
        try:
            current_rq = Request._current_request()
            resp = self.tiktorchClient.Predict.future(
                inference_pb2.PredictRequest(
                    tensors=[converters.numpy_to_pb_tensor(reordered_feature_image, axistags=input_axis_order)],
                    modelSessionId=self.__session.id,
                )
            )
            resp.add_done_callback(lambda o: current_rq._wake_up())
            current_rq._suspend()
            resp = resp.result()
            assert len(resp.tensors) == 1
            result = converters.pb_tensor_to_numpy(resp.tensors[0])
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
        halos = self.get_halos(axes=axistags)
        assert len(halos) == 1

        result = reorder_axes(result, from_axes_tags=output_axis_order, to_axes_tags=axistags)
        result = result[roiToSlice(*roi)]

        logger.debug(f"result without halo {shape_wo_halo}. Now" f" result has shape: ({result.shape}).")
        return result


def reorder_axes(input_arr: numpy.ndarray, *, from_axes_tags: str, to_axes_tags: str) -> numpy.ndarray:
    if isinstance(from_axes_tags, AxisTags):
        from_axes_tags = "".join(from_axes_tags.keys())

    if isinstance(to_axes_tags, AxisTags):
        to_axes_tags = "".join(to_axes_tags.keys())

    tagged_input = xarray.DataArray(input_arr, dims=tuple(from_axes_tags))

    axes_removed = set(from_axes_tags).difference(to_axes_tags)
    axes_added = set(to_axes_tags).difference(from_axes_tags)

    output = tagged_input.squeeze(tuple(axes_removed)).expand_dims(tuple(axes_added)).transpose(*tuple(to_axes_tags))
    assert len(output.shape) == len(to_axes_tags)
    return output.data


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
