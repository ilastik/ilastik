import vigra
import numpy
import xarray

from functools import singledispatch
from lazyflow.graph import Graph
from lazyflow.utility.helpers import get_default_axisordering
from lazyflow.operators.classifierOperators import OpClassifierPredict
from lazyflow.operators import OpReorderAxes
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.experimental import parser
from .types import Pipeline


def _ensure_channel_axis(axis_order):
    if "c" not in axis_order:
        return axis_order + "c"
    return axis_order


def from_project_file(path) -> Pipeline:
    project: parser.PixelClassificationProject

    with parser.IlastikProject(path, "r") as project:
        if not project.ready_for_prediction:
            raise ValueError("not sufficient data in project file for prediction")

        feature_matrix = project.feature_matrix
        classifer = project.classifier
        num_channels = project.data_info.num_channels
        axis_order = project.data_info.axis_order
        num_spatial_dims = len(project.data_info.spatial_axes)

    class _PipelineImpl(Pipeline):
        def __init__(self):
            graph = Graph()
            self._reorder_op = OpReorderAxes(graph=graph, AxisOrder=_ensure_channel_axis(axis_order))

            self._feature_sel_op = OpFeatureSelection(graph=graph)
            self._feature_sel_op.InputImage.connect(self._reorder_op.Output)
            self._feature_sel_op.FeatureIds.setValue(feature_matrix.names)
            self._feature_sel_op.Scales.setValue(feature_matrix.scales)
            self._feature_sel_op.SelectionMatrix.setValue(feature_matrix.selections)
            self._feature_sel_op.ComputeIn2d.setValue(feature_matrix.compute_in_2d.tolist())

            self._predict_op = OpClassifierPredict(graph=graph)
            self._predict_op.Classifier.setValue(classifer.instance)
            self._predict_op.Classifier.meta.classifier_factory = classifer.factory
            self._predict_op.Image.connect(self._feature_sel_op.OutputImage)
            self._predict_op.LabelsCount.setValue(classifer.label_count)

        def predict(self, data):
            data = convert_to_vigra(data)
            num_channels_in_data = data.channels
            if num_channels_in_data != num_channels:
                raise ValueError(
                    f"Number of channels mismatch. Classifier trained for {num_channels} but input has {num_channels_in_data}"
                )

            num_spatial_in_data = sum(a.isSpatial() for a in data.axistags)
            if num_spatial_in_data != num_spatial_dims:
                raise ValueError(
                    "Number of spatial dims doesn't match. "
                    f"Classifier trained for {num_spatial_dims} but input has {num_spatial_in_data}"
                )

            self._reorder_op.Input.setValue(data)

            data = self._predict_op.PMaps.value[...]
            return xarray.DataArray(data, dims=tuple(self._predict_op.PMaps.meta.axistags.keys()))

    return _PipelineImpl()


@singledispatch
def convert_to_vigra(data):
    raise NotImplementedError(f"{type(data)}")


@convert_to_vigra.register
def _(data: vigra.VigraArray):
    return data


@convert_to_vigra.register
def _(data: numpy.ndarray):
    raise ValueError("numpy arrays don't provide information about axistags expecting xarray")


@convert_to_vigra.register
def _(data: xarray.DataArray):
    axistags = "".join(data.dims)
    return vigra.taggedView(data.values, axistags)
