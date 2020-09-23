import vigra
import numpy

from lazyflow.graph import Graph
from lazyflow.operators.classifierOperators import OpClassifierPredict
from lazyflow.operators import OpReorderAxes
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.experimental import parser
from .types import Pipeline


def from_project_file(path) -> Pipeline:
    project: parser.PixelClassificationProject

    with parser.IlastikProject(path, "r") as project:
        if not all([project.data_info, project.features, project.classifier]):
            raise ValueError("not sufficient data in project file for predition")

        feature_matrix = project.features.as_matrix()
        classifer = project.classifier
        num_channels = project.data_info.num_channels
        axis_order = project.data_info.axis_order
        num_spatial_dims = len(project.data_info.spatial_axes)


    class _PipelineImpl(Pipeline):
        def __init__(self):
            graph = Graph()
            self._reorder_op = OpReorderAxes(graph=graph, AxisOrder=axis_order)

            self._feature_sel_op = OpFeatureSelection(graph=graph)
            self._feature_sel_op.InputImage.connect(self._reorder_op.Output)
            self._feature_sel_op.FeatureIds.setValue(feature_matrix.names)
            self._feature_sel_op.Scales.setValue(feature_matrix.scales)
            self._feature_sel_op.SelectionMatrix.setValue(feature_matrix.selections)

            self._predict_op = OpClassifierPredict(graph=graph)
            self._predict_op.Classifier.setValue(classifer.instance)
            self._predict_op.Classifier.meta.classifier_factory = classifer.factory
            self._predict_op.Image.connect(self._feature_sel_op.OutputImage)
            self._predict_op.LabelsCount.setValue(classifer.label_count)

        def predict(self, data):
            data = _make_vigra_with_cannel_axis(data)
            num_channels_in_data = data.shape[data.axistags.index("c")]
            if num_channels_in_data != num_channels:
                raise ValueError(f"Number of channels mismatch. Classifier trained for {num_channels} but input has {num_channels_in_data}")

            num_spatial_in_data = sum(a.isSpatial() for a in data.axistags)
            if num_spatial_in_data != num_spatial_dims:
                raise ValueError(
                    "Number of spatial dims doesn't match. "
                    f"Classifier trained for {num_spatial_dims} but input has {num_spatial_in_data}"
                )

            self._reorder_op.Input.setValue(data)

            return self._predict_op.PMaps.value[...]

    return _PipelineImpl()


def _guess_channel_axis_idx(shape):
    for idx, val in enumerate(shape):
        if val < 4:
            return idx
    return None


def _guess_axistags(shape):
    if len(shape) > 5 or len(shape) < 2:
        raise NotImplementedError(f"Got shape {shape}")

    ch_idx = _guess_channel_axis_idx(shape)
    spatial = ["z", "y", "x"]

    guessed_tags = ""

    for idx, size in enumerate(shape):
        if idx != ch_idx:
            guessed_tags = spatial.pop() + guessed_tags

    if ch_idx is not None:
        guessed_tags = guessed_tags[:ch_idx] + "c" + guessed_tags[ch_idx:]

    return guessed_tags


def _make_vigra_with_cannel_axis(data):
    axes = _guess_axistags(data.shape)
    if "c" not in axes:
        result = data.reshape(*data.shape, 1)
        return vigra.taggedView(result, axes + "c")
    else:
        return vigra.taggedView(data, axes)
