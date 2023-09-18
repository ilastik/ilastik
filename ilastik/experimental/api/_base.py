from typing import Union
import warnings

import vigra
import xarray

from lazyflow.graph import Graph
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
        if not all([project.data_info, project.feature_matrix, project.classifier]):
            raise ValueError("not sufficient data in project file for predition")

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

        def predict(self, data: Union[vigra.VigraArray, xarray.DataArray]) -> xarray.DataArray:
            warnings.warn(
                "The predict method will disappear in future versions, please use get_probabilities()",
                DeprecationWarning,
            )
            return self.get_probabilities(raw_data=data)

        def get_probabilities(self, raw_data: Union[vigra.VigraArray, xarray.DataArray]) -> xarray.DataArray:

            raw_data = as_vigra_array(raw_data)
            num_channels_in_data = raw_data.channels
            if num_channels_in_data != num_channels:
                raise ValueError(
                    f"Number of channels mismatch. Classifier trained for {num_channels} but input has {num_channels_in_data}"
                )

            num_spatial_in_data = sum(a.isSpatial() for a in raw_data.axistags)
            if num_spatial_in_data != num_spatial_dims:
                raise ValueError(
                    "Number of spatial dims doesn't match. "
                    f"Classifier trained for {num_spatial_dims} but input has {num_spatial_in_data}"
                )

            self._reorder_op.Input.setValue(raw_data)

            probabilities = self._predict_op.PMaps.value[...]
            return xarray.DataArray(probabilities, dims=tuple(self._predict_op.PMaps.meta.axistags.keys()))

    return _PipelineImpl()


def as_vigra_array(data: Union[vigra.VigraArray, xarray.DataArray]) -> vigra.VigraArray:
    if isinstance(data, vigra.VigraArray):
        return data
    elif isinstance(data, xarray.DataArray):
        axistags = "".join(data.dims)
        return vigra.taggedView(data.values, axistags)
    else:
        raise NotImplementedError(
            f"Data type '{type(data)}' not supported, use `vigra.VigraArray` or `xarray.DataArray`."
        )
