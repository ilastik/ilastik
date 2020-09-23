import vigra
import numpy

from lazyflow.graph import Graph
from lazyflow.operators.classifierOperators import OpClassifierPredict
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

    class _PipelineImpl(Pipeline):
        def __init__(self):
            graph = Graph()
            self._feature_sel_op = OpFeatureSelection(graph=graph)
            self._feature_sel_op.FeatureIds.setValue(feature_matrix.names)
            self._feature_sel_op.Scales.setValue(feature_matrix.scales)
            self._feature_sel_op.SelectionMatrix.setValue(feature_matrix.selections)

            self._predict_op = OpClassifierPredict(graph=graph)
            self._predict_op.Classifier.setValue(classifer.instance)
            self._predict_op.Classifier.meta.classifier_factory = classifer.factory
            self._predict_op.Image.connect(self._feature_sel_op.OutputImage)
            self._predict_op.LabelsCount.setValue(classifer.label_count)

        def predict(self, data):
            axes = _guess_axistags(data.shape)
            data = _make_vigra_with_cannel_axis(data, axes)
            num_channels_in_data = data.shape[data.axistags.index("c")]
            if num_channels_in_data != num_channels:
                raise ValueError(f"Number of channels mismatch. Classifier trained for {num_channels} but input has {num_channels_in_data}")

            self._feature_sel_op.InputImage.setValue(data)

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


def _make_vigra_with_cannel_axis(data, axes):
    if "c" not in axes:
        result = data.reshape(*data.shape, 1)
        return vigra.taggedView(result, axes + "c")
    else:
        return vigra.taggedView(data, axes)
