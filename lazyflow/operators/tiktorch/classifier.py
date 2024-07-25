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
from typing import Callable, Dict, Iterable, Sequence, Tuple, Union

import xarray
import grpc

from lazyflow.request import Request
from lazyflow.roi import roiToSlice
from lazyflow.futures_utils import MappableFuture, map_future

from tiktorch import converters
from tiktorch.proto import data_store_pb2, data_store_pb2_grpc, inference_pb2, inference_pb2_grpc

from vigra import AxisTags

from . import _base

logger = logging.getLogger(__name__)


def enforce_min_shape(min_shape, step, axes) -> Tuple[int, ...]:
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
    return tuple([int(s + i * m) for s, i in zip(min_shape, step)])


class ModelSession:
    def __init__(self, session, factory):
        self.__session = session
        self.__factory = factory

        assert (
            len(self.__session.inputNames) == 1 and len(self.__session.inputShapes) == 1
        ), "Currently operators can handle only a single input tensor."
        assert (
            len(self.__session.outputNames) == 1 and len(self.__session.outputShapes) == 1
        ), "Currently operators can handle only a single output tensor"

        self._implicit_input_shape = self.__session.inputShapes[0]
        self._implicit_output_shape = self.__session.outputShapes[0]

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
    def input_name(self) -> str:
        return self.__session.inputNames[0]

    @property
    def output_name(self) -> str:
        return self.__session.outputNames[0]

    @property
    def input_axes(self) -> Sequence[str]:
        """Get axes for model input"""
        return self.__session.inputAxes

    @property
    def output_axes(self) -> Sequence[str]:
        """Get axes for model output"""
        return self.__session.outputAxes

    def get_output_shape(self) -> Dict[str, int]:
        """Get shape for model output

        shape = shape(reference_input_tensor) * scale + 2 * offset
        """
        # get input shapes for all possible axes that ilastik can understand
        input_shape = {name: size for name, size in zip("itzyxc", self.get_input_shape("itzyxc"))}

        input_name = self.input_name
        output_name = self.output_name
        shape = self._implicit_output_shape

        if shape.shapeType == 0:
            # explicit shape
            output_shape_by_name = {d.name: d.size for d in shape.shape.namedInts}
            result = output_shape_by_name
        elif shape.shapeType == 1:
            # parametrized shape
            # HACK: need to determine min shape same way as prediction_pipeline
            reference_tensor = shape.referenceTensor
            assert (
                reference_tensor == input_name
            ), f"Reference tensor {reference_tensor} for output {output_name} not found in input shape {input_name}."
            offset_size_by_name = defaultdict(lambda: 0, {d.name: d.size for d in shape.offset.namedFloats})
            scale_size_by_name = defaultdict(lambda: 1.0, {d.name: d.size for d in shape.scale.namedFloats})
            output_shape_by_name = {}
            for dim in shape.scale.namedFloats:
                if dim.name == "b":
                    continue
                output_shape_by_name[dim.name] = int(
                    input_shape[dim.name] * scale_size_by_name[dim.name] + 2 * offset_size_by_name[dim.name]
                )
            result = output_shape_by_name
        else:
            raise ValueError(f"Cannot work with shapes of shapeType {shape.shapeType}.")

        # sanity check:
        axes = "".join(result.keys())
        halo = self.get_halo(axes=axes)
        shape_after_halo = [result[axkey] - 2 * axhalo for axkey, axhalo in zip(axes, halo)]
        if not all(x > 0 for x in shape_after_halo):
            logger.warning(
                f"Network configuration problem detected - output {output_name} shape - 2*halo invalid:{shape_after_halo}."
            )

        return result

    @property
    def has_training(self) -> bool:
        return self.__session.hasTraining

    def get_halo(self, axes: Union[str, AxisTags] = "zyx") -> Tuple[int, ...]:
        """Get halo sizes for model output

        Returns:
          models can take multiple images as outputs. For each such input, a
            list of shapes is returned. Linked to `input_names` via keys in
            returned dict.
        """
        if isinstance(axes, AxisTags):
            axes = "".join(axes.keys())
        halo_size_by_name = {d.name: d.size for d in self._implicit_output_shape.halo.namedInts}
        return tuple([halo_size_by_name.get(axis, 0) for axis in axes])

    def get_input_shape(self, axes: Union[str, AxisTags] = "itzyxc") -> Tuple[int, ...]:
        """Get input shape for model input

        Note: for parametrized input shapes we try to do something sensible with
          the shape, and not just return the minimum shape. See also
          `enforce_min_shape`.

        Returns:
          models can take multiple images as inputs. For each such input, a list
            of shapes is returned. Linked to `input_names` via keys in returned
            dict.
        """
        if isinstance(axes, AxisTags):
            axes = "".join(axes.keys())

        shape = self._implicit_input_shape
        dim_size_by_name = defaultdict(lambda: 1, {d.name: d.size for d in shape.shape.namedInts})

        if shape.shapeType == 0:
            # explicit shape
            result = tuple([dim_size_by_name[axis] for axis in axes])
        elif shape.shapeType == 1:
            # parametrized shape
            # HACK: need to determine min shape same way as prediction_pipeline
            dim_step_by_name = defaultdict(lambda: 0, {d.name: d.size for d in shape.stepShape.namedInts})
            shape_dims = "".join(d.name for d in shape.shape.namedInts)
            min_shape = enforce_min_shape(
                [dim_size_by_name[x] for x in shape_dims], [dim_step_by_name[x] for x in shape_dims], shape_dims
            )
            min_shape_by_name = defaultdict(lambda: 1, {name: size for name, size in zip(shape_dims, min_shape)})
            result = tuple(min_shape_by_name[axis] for axis in axes)
        else:
            raise ValueError(f"Cannot work with shapes of shapeType {shape.shapeType}.")

        return result

    @property
    def training_shape(self) -> Tuple[int, ...]:
        warnings.warn("HARDCODED training shape, this might not do what you want.")
        return (0, 0, 0, 128, 128)

    @property
    def known_classes(self) -> Sequence[int]:
        """
        FIXME: assumes first output is the segmentation output
        """
        output_shape = self.get_output_shape()
        assert "c" in output_shape, "Channel Axis needed in output shape."
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

    def predict(
        self, tensors: Sequence[numpy.ndarray], rois: Sequence[numpy.ndarray], axistags: Sequence[AxisTags]
    ) -> Sequence[numpy.ndarray]:
        """
        Args:
            tensors: classifier inputs
            roi: ROI
            axistags: axistags of input tensors
        Returns:
            result tensors
        """
        assert all(isinstance(r, numpy.ndarray) for r in rois)
        logger.debug("predict tile shape: %s (axistags: %r)", [t.shape for t in tensors], axistags)

        # translate roi axes todo: remove with tczyx standard
        # output_axis_order = self._model_conf.output_axis_order
        output_axes = self.output_axes

        # Assuming images with only spacial axes to be images
        # -> if there is no `c` axis, we'll append it in the result
        def needs_c(axistags: Union[str, AxisTags]) -> bool:
            if isinstance(axistags, AxisTags):
                axistags = "".join(axistags.keys())
            if any(ax in axistags for ax in "ci"):
                return False

            return True

        needs_c_axis = [needs_c(at) for at in output_axes]

        input_axes = self.input_axes
        assert (
            len(tensors) == len(input_axes) == len(axistags)
        ), f"Number of input tensors ({len(tensors)}) must match number of input axes ({len(input_axes)}) and axistags ({len(axistags)})"

        def ensure_float32(tensor: numpy.ndarray) -> numpy.ndarray:
            if tensor.dtype == "float32":
                return tensor
            else:
                return tensor.astype("float32")

        reordered_tensors = [
            ensure_float32(reorder_axes(t, from_axes_tags=at, to_axes_tags=ati))
            for t, at, ati in zip(tensors, axistags, input_axes)
        ]

        try:
            current_rq = Request._current_request()
            resp = self.tiktorchClient.Predict.future(
                inference_pb2.PredictRequest(
                    tensors=[
                        converters.numpy_to_pb_tensor(t, axistags=at) for t, at in zip(reordered_tensors, input_axes)
                    ],
                    modelSessionId=self.__session.id,
                )
            )
            resp.add_done_callback(lambda o: current_rq._wake_up())
            current_rq._suspend()
            resp = resp.result()
            assert len(resp.tensors) == len(output_axes)
            results = [converters.pb_tensor_to_numpy(t) for t in resp.tensors]
        except Exception:
            logger.exception(f"Predict call failed with exception.")
            return 0

        logger.debug(f"Obtained a predicted block of shape {[r.shape for r in results]}.")
        # add c axis if needed
        for i, (tensor, n) in enumerate(zip(results, needs_c_axis)):
            if n:
                results[i] = tensor[None, ...]

        shapes_wo_halo = [r.shape for r in results]

        results = [
            reorder_axes(r, from_axes_tags=ot, to_axes_tags=at) for r, ot, at in zip(results, output_axes, axistags)
        ]
        results = [r[roiToSlice(*roi)] for r, roi in zip(results, rois)]

        logger.debug(f"result without halo {shapes_wo_halo}. Now result has shape: ({[r.shape for r in results]}).")
        return results


def reorder_axes(
    input_arr: numpy.ndarray, *, from_axes_tags: Union[str, AxisTags], to_axes_tags: Union[str, AxisTags]
) -> numpy.ndarray:
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

    def create_model_session(self, upload_id: str, devices: Sequence[str]):
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
