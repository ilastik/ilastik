import warnings
from functools import singledispatch

import numpy
import vigra
import xarray

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.applets.objectClassification.opObjectClassification import OpMultiRelabelSegmentation, OpObjectPredict
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction
from ilastik.applets.thresholdTwoLevels.opThresholdTwoLevels import OpThresholdTwoLevels
from ilastik.experimental import parser
from lazyflow.graph import Graph
from lazyflow.operators import OpMultiArrayStacker, OpReorderAxes, OpPixelOperator
from lazyflow.operators.classifierOperators import OpClassifierPredict

from .types import (
    ObjectClassificationFromSegmentationPipeline,
    ObjectClassificationFromPredictionPipeline,
    PixelClassificationPipeline,
)


def _reorder_output(output: numpy.ndarray, output_axisorder: vigra.AxisTags, input_axisorder: str):
    assert len(output.shape) == len(output_axisorder)
    if "c" in output_axisorder and "c" not in input_axisorder:
        # if input data was supplied without channel axes, put channel last
        input_axisorder = input_axisorder + "c"

    drop_axes = []
    for axis, size in zip(output_axisorder, output.shape):
        if axis not in input_axisorder:
            assert size == 1
            drop_axes.append(axis)

    output_array = xarray.DataArray(output, dims=tuple(output_axisorder))
    return output_array.squeeze(drop_axes).transpose(*tuple(input_axisorder))


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


class _PixelClassificationPipelineImpl(PixelClassificationPipeline):
    def __init__(self, project: parser.PixelClassificationProject):
        feature_matrix = project.feature_matrix
        classifer = project.classifier
        self._num_channels = project.data_info.num_channels
        self._axis_order = project.data_info.axis_order
        self._num_spatial_dims = len(project.data_info.spatial_axes)

        graph = Graph()
        self._reorder_op = OpReorderAxes(graph=graph, AxisOrder="tzyxc")

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
        warnings.warn(
            "The predict method will disappear in future versions, please use get_probabilities()",
            DeprecationWarning,
        )
        return self.get_probabilities(raw_data=data)

    def _check_data(self, data):
        num_channels_in_data = data.channels
        if num_channels_in_data != self._num_channels:
            raise ValueError(
                f"Number of channels mismatch. Classifier trained for {self._num_channels} but input has {num_channels_in_data}"
            )

        num_spatial_in_data = sum(a.isSpatial() for a in data.axistags)
        if num_spatial_in_data != self._num_spatial_dims:
            raise ValueError(
                "Number of spatial dims doesn't match. "
                f"Classifier trained for {self._num_spatial_dims} but input has {num_spatial_in_data}"
            )

    def get_probabilities(self, raw_data):
        return self._process(raw_data, output_slot=self._predict_op.PMaps)

    def _process(self, raw_data, output_slot):
        raw_data = convert_to_vigra(raw_data)
        input_axistags = "".join(ax.key for ax in raw_data.axistags)
        self._check_data(raw_data)
        self._reorder_op.Input.setValue(raw_data)
        processed_data = output_slot.value[...]
        return _reorder_output(processed_data, "".join(output_slot.meta.axistags.keys()), input_axistags)


class _ObjectClassificationPipelineBase:
    def __init__(self, project: parser.ObjectClassificationProjectBase):
        super().__init__()
        self._graph = Graph()

        classifer = project.classifier
        selected_object_features = project.selected_object_features
        self._num_channels = project.data_info.num_channels
        self._axis_order = project.data_info.axis_order
        self._num_spatial_dims = len(project.data_info.spatial_axes)
        self._obj_extraction_op = OpObjectExtraction(graph=self._graph)
        self._obj_extraction_op.Features.setValue(selected_object_features.selected_features)
        self._predict_op = OpObjectPredict(graph=self._graph)
        self._predict_op.Classifier.setValue(classifer.instance)
        self._predict_op.Features.connect(self._obj_extraction_op.RegionFeatures)
        self._predict_op.SelectedFeatures.setValue(selected_object_features.selected_features)
        self._predict_op.LabelsCount.setValue(classifer.label_count)

        self._relabel_to_obj_probs = OpMultiRelabelSegmentation(graph=self._graph)
        self._relabel_to_obj_probs.Image.connect(self._obj_extraction_op.LabelImage)
        self._relabel_to_obj_probs.ObjectMaps.connect(self._predict_op.ProbabilityChannels)
        self._relabel_to_obj_probs.Features.connect(self._obj_extraction_op.RegionFeatures)

        self._stack_prob_channels = OpMultiArrayStacker(graph=self._graph)
        self._stack_prob_channels.Images.connect(self._relabel_to_obj_probs.Output)
        self._stack_prob_channels.AxisFlag.setValue("c")

    def _check_data(self, data):
        num_channels_in_data = data.channels
        if num_channels_in_data != self._num_channels:
            raise ValueError(
                f"Number of channels mismatch. Classifier trained for {self._num_channels} but input has {num_channels_in_data}"
            )

        num_spatial_in_data = sum(a.isSpatial() for a in data.axistags)
        if num_spatial_in_data != self._num_spatial_dims:
            raise ValueError(
                "Number of spatial dims doesn't match. "
                f"Classifier trained for {self._num_spatial_dims} but input has {num_spatial_in_data}"
            )


class _ObjectClassificationFromSegmentationPipelineImpl(
    _ObjectClassificationPipelineBase, ObjectClassificationFromSegmentationPipeline
):
    def __init__(self, project: parser.ObjectClassificationProjectBase):
        super().__init__(project)
        self._reorder_raw_op = OpReorderAxes(graph=self._graph, AxisOrder="txyzc")
        self._reorder_seg_op = OpReorderAxes(graph=self._graph, AxisOrder="txyzc")
        self._obj_extraction_op.RawImage.connect(self._reorder_raw_op.Output)
        self._obj_extraction_op.BinaryImage.connect(self._reorder_seg_op.Output)

    def get_object_probabilities(self, raw_data, segmentation_image):
        return self._process(raw_data, segmentation_image, output_slot=self._stack_prob_channels.Output)

    def _process(self, raw_data, segmentation_image, output_slot):
        raw_data = convert_to_vigra(raw_data)
        input_axistags = "".join(ax.key for ax in raw_data.axistags)
        segmentation_image = convert_to_vigra(segmentation_image)
        self._check_data(raw_data)
        self._reorder_raw_op.Input.setValue(raw_data)
        self._reorder_seg_op.Input.setValue(segmentation_image)
        processed_data = output_slot.value[...]
        return _reorder_output(processed_data, "".join(output_slot.meta.axistags.keys()), input_axistags)


class _ObjectClassificationFromPredictionPipelineImpl(
    _ObjectClassificationPipelineBase, ObjectClassificationFromPredictionPipeline
):
    def __init__(self, project: parser.ObjectClassificationProjectBase):
        super().__init__(project)
        self._reorder_raw_op = OpReorderAxes(graph=self._graph, AxisOrder="txyzc")
        self._reorder_pred_op = OpReorderAxes(graph=self._graph, AxisOrder="txyzc")

        self._normalize_probmaps = OpPixelOperator(graph=self._graph)
        self._normalize_probmaps.Input.connect(self._reorder_pred_op.Output)

        thresh_settings = project.thresholding_settings
        self._thresholding_op = OpThresholdTwoLevels(graph=self._graph)
        self._thresholding_op.RawInput.connect(self._reorder_raw_op.Output)
        self._thresholding_op.MinSize.setValue(thresh_settings.min_size)
        self._thresholding_op.MaxSize.setValue(thresh_settings.max_size)
        self._thresholding_op.HighThreshold.setValue(thresh_settings.high_threshold)
        self._thresholding_op.LowThreshold.setValue(thresh_settings.low_threshold)
        self._thresholding_op.SmootherSigma.setValue(thresh_settings.smoother_sigmas)
        self._thresholding_op.Channel.setValue(thresh_settings.channel)
        self._thresholding_op.CoreChannel.setValue(thresh_settings.core_channel)
        self._thresholding_op.CurOperator.setValue(thresh_settings.method)
        self._thresholding_op.InputImage.connect(self._normalize_probmaps.Output)

        self._obj_extraction_op.RawImage.connect(self._reorder_raw_op.Output)
        self._obj_extraction_op.BinaryImage.connect(self._thresholding_op.Output)

    def get_object_probabilities(self, raw_data, prediction_maps):
        return self._process(raw_data, prediction_maps, output_slot=self._stack_prob_channels.Output)

    def _setup_normalization_function(self, prediction_maps: numpy.ndarray):
        """Configure normalizing op according to prediction dtype"""
        if numpy.issubdtype(prediction_maps.dtype, numpy.floating):
            self._normalize_probmaps.Function.setValue(lambda x: x.astype(numpy.float32))
        elif numpy.issubdtype(prediction_maps.dtype, numpy.integer):
            # assuming full range for normalization
            drange_info = numpy.iinfo(prediction_maps.dtype)
            min_, max_ = drange_info.min, drange_info.max
            self._normalize_probmaps.Function.setValue(lambda x: (x.astype(numpy.float32) - min_) / (max_ - min_))
        else:
            raise ValueError(f"Array of dtype {prediction_maps.dtype} not supported")

    def _process(self, raw_data, prediction_maps, output_slot):
        raw_data = convert_to_vigra(raw_data)
        input_axistags = "".join(ax.key for ax in raw_data.axistags)
        prediction_maps = convert_to_vigra(prediction_maps)
        self._check_data(raw_data)
        self._reorder_raw_op.Input.setValue(raw_data)
        self._setup_normalization_function(prediction_maps)
        self._reorder_pred_op.Input.setValue(prediction_maps)
        thresholded = self._thresholding_op.Output[()].wait()
        processed_data = output_slot.value[...]
        return _reorder_output(processed_data, "".join(output_slot.meta.axistags.keys()), input_axistags)


@singledispatch
def get_pipeline_for_project(project):
    raise NotImplementedError(f"{type(project)}")


@get_pipeline_for_project.register
def _(project: parser.PixelClassificationProject):
    return _PixelClassificationPipelineImpl(project=project)


@get_pipeline_for_project.register
def _(project: parser.ObjectClassificationProjectBase):
    return _ObjectClassificationFromSegmentationPipelineImpl(project=project)


@get_pipeline_for_project.register
def _(project: parser.ObjectClassificationFromPredictionProject):
    return _ObjectClassificationFromPredictionPipelineImpl(project=project)
