from typing import Union
import warnings

import h5py
import vigra
import xarray

from ilastik.experimental import parser
from lazyflow.graph import Graph
from lazyflow.operators.classifierOperators import OpClassifierPredict
from lazyflow.operators import OpReorderAxes
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection


class PixelClassificationPipeline:
    @staticmethod
    def from_project_file(path) -> "PixelClassificationPipeline":
        with h5py.File(path, "r") as f:
            project = parser.PixelClassificationProject(f)
            if not all([project.data_info, project.feature_matrix, project.classifier]):
                raise ValueError("not sufficient data in project file for predition")

        return PixelClassificationPipeline(project)

    def __init__(self, project: parser.PixelClassificationProject):
        self._num_spatial_dims = len(project.data_info.spatial_axes)
        self._num_channels = project.data_info.num_channels

        graph = Graph()
        self._reorder_op = OpReorderAxes(graph=graph, AxisOrder=ensure_channel_axis(project.data_info.axis_order))

        self._feature_sel_op = OpFeatureSelection(graph=graph)
        self._feature_sel_op.InputImage.connect(self._reorder_op.Output)
        self._feature_sel_op.FeatureIds.setValue(project.feature_matrix.names)
        self._feature_sel_op.Scales.setValue(project.feature_matrix.scales)
        self._feature_sel_op.SelectionMatrix.setValue(project.feature_matrix.selections)
        self._feature_sel_op.ComputeIn2d.setValue(project.feature_matrix.compute_in_2d.tolist())

        self._predict_op = OpClassifierPredict(graph=graph)
        self._predict_op.Classifier.setValue(project.classifier.instance)
        self._predict_op.Classifier.meta.classifier_factory = project.classifier.factory
        self._predict_op.Image.connect(self._feature_sel_op.OutputImage)
        self._predict_op.LabelsCount.setValue(project.classifier.label_count)

    def predict(self, data: Union[vigra.VigraArray, xarray.DataArray]) -> xarray.DataArray:
        warnings.warn(
            "The predict method will disappear in future versions, please use get_probabilities()",
            DeprecationWarning,
        )
        return self.get_probabilities(raw_data=data)

    def get_probabilities(self, raw_data: Union[vigra.VigraArray, xarray.DataArray]) -> xarray.DataArray:
        raw_data = as_vigra_array(raw_data)
        num_channels_in_data = raw_data.channels
        if num_channels_in_data != self._num_channels:
            raise ValueError(
                f"Number of channels mismatch. Classifier trained for {self._num_channels} but input has {num_channels_in_data}"
            )

        num_spatial_in_data = sum(a.isSpatial() for a in raw_data.axistags)
        if num_spatial_in_data != self._num_spatial_dims:
            raise ValueError(
                "Number of spatial dims doesn't match. "
                f"Classifier trained for {self._num_spatial_dims} but input has {num_spatial_in_data}"
            )

        self._reorder_op.Input.setValue(raw_data)

        probabilities = self._predict_op.PMaps.value[...]
        return xarray.DataArray(probabilities, dims=tuple(self._predict_op.PMaps.meta.axistags.keys()))


def ensure_channel_axis(axis_order):
    if "c" not in axis_order:
        return axis_order + "c"
    return axis_order


def from_project_file(path) -> PixelClassificationPipeline:
    warnings.warn(
        "The `from_project_file` function will disappear in future versions.",
        DeprecationWarning,
    )

    return PixelClassificationPipeline.from_project_file(path)


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
