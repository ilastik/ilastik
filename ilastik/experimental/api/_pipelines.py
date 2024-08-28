###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
# pyright: strict
import warnings
from typing import Literal, Union

import h5py
import vigra
import xarray

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.experimental import parser
from ilastik.utility.slottools import DtypeConvertFunction
from lazyflow.graph import Graph
from lazyflow.operators import OpReorderAxes
from lazyflow.operators.classifierOperators import OpClassifierPredict
from lazyflow.operators.generic import OpMultiArrayStacker, OpPixelOperator


class PixelClassificationPipeline:
    """
    Pipeline for accessing trained Pixel Classification classifiers from Python

    Example usage:

    ```Python
    import imageio.v3 as iio
    import xarray
    from ilastik.experimental.api import PixelClassificationPipeline

    img = xarray.DataArray(iio.imread("<path/to/image-file.tif>"), dims=("y", "x"))
    pipeline = PixelClassificationPipeline.from_ilp_file("<path/to/project.ilp>")

    prob_maps = pipeline.get_probabilities(img)
    ```

    Example using an OME-Zarr dataset stored remotely:
    ```Python
    import xarray
    from ilastik.experimental.api import PixelClassificationPipeline
    from lazyflow.utility.io_util.OMEZarrStore import OMEZarrStore

    store = OMEZarrStore("<https://example.com/data.zarr>")
    zarray = store.get_zarr_array("<scale name>")
    dims = tuple(store.axistags.keys())

    img = xarray.DataArray(zarray, dims=dims)  # downloads the entire image
    pipeline = PixelClassificationPipeline.from_ilp_file("<path/to/project.ilp>")

    prob_maps = pipeline.get_probabilities(img)
    ```
    """

    @classmethod
    def from_ilp_file(cls, path: str) -> "PixelClassificationPipeline":
        """
        Create a Pixel Classification Pipeline instance from a trained project.ilp file

        Args:
            path: Path to the ilp file

        Returns:
            PixelClassificationPipeline instance configured with trained classifier
        """
        with h5py.File(path, "r") as f:
            project = parser.PixelClassificationProject.model_validate(f)

        return cls(project)

    def __init__(self, project: parser.PixelClassificationProject):
        self._num_spatial_dims = len(project.input_data.spatial_axes)
        self._num_channels = project.input_data.num_channels

        graph = Graph()
        self._reorder_op = OpReorderAxes(graph=graph, AxisOrder=ensure_channel_axis(project.input_data.axis_order))

        self._feature_sel_op = OpFeatureSelection(graph=graph)
        self._feature_sel_op.InputImage.connect(self._reorder_op.Output)
        self._feature_sel_op.FeatureIds.setValue(project.feature_matrix.names)
        self._feature_sel_op.Scales.setValue(project.feature_matrix.scales)
        self._feature_sel_op.SelectionMatrix.setValue(project.feature_matrix.selections)
        self._feature_sel_op.ComputeIn2d.setValue(project.feature_matrix.compute_in_2d.tolist())

        self._predict_op = OpClassifierPredict(graph=graph)
        self._predict_op.Classifier.setValue(project.classifier.classifier)
        self._predict_op.Classifier.meta.classifier_factory = project.classifier.classifier_factory
        self._predict_op.Image.connect(self._feature_sel_op.OutputImage)
        self._predict_op.LabelsCount.setValue(project.classifier.label_count)

    def predict(self, data: Union[vigra.VigraArray, xarray.DataArray]) -> xarray.DataArray:
        warnings.warn(
            "The predict method will disappear in future versions, please use get_probabilities()",
            DeprecationWarning,
        )
        return self.get_probabilities(raw_data=data)

    def get_probabilities(self, raw_data: Union[vigra.VigraArray, xarray.DataArray]) -> xarray.DataArray:
        """
        Get pixel probability map from pipeline.

        Args:
            raw_data: image with same dimensionality as in the trained project file
        """
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


class AutocontextPipeline:
    """
    Pipeline for accessing trained Autocontext classifiers from Python

    Example usage:

    ```Python
    from ilastik.experimental.api import AutocontextPipeline
    import imageio.v3 as iio
    import xarray

    img = xarray.DataArray(iio.imread("<path/to/image-file.tif>"), dims=("y", "x"))
    pipeline = AutocontextPipeline.from_ilp_file("<path/to/project.ilp>")

    prob_maps = pipeline.get_probabilities_stage_2(img)
    ```

    """

    @classmethod
    def from_ilp_file(cls, path: str) -> "AutocontextPipeline":
        """
        Create an Autocontext Pipeline instance from a trained project.ilp file

        Args:
            path: Path to the ilp file

        Returns:
            AutocontextPipeline instance configured with trained classifier
        """
        with h5py.File(path, "r") as f:
            project = parser.AutocontextProject.model_validate(f)

        return cls(project)

    def __init__(self, project: parser.AutocontextProject):
        self._num_spatial_dims = len(project.input_data.spatial_axes)
        self._num_channels = project.input_data.num_channels

        graph = Graph()
        self._reorder_op = OpReorderAxes(graph=graph, AxisOrder=ensure_channel_axis(project.input_data.axis_order))

        self._feature_sel_op_stage1 = OpFeatureSelection(graph=graph)
        self._feature_sel_op_stage1.InputImage.connect(self._reorder_op.Output)
        self._feature_sel_op_stage1.FeatureIds.setValue(project.feature_matrix_stage1.names)
        self._feature_sel_op_stage1.Scales.setValue(project.feature_matrix_stage1.scales)
        self._feature_sel_op_stage1.SelectionMatrix.setValue(project.feature_matrix_stage1.selections)
        self._feature_sel_op_stage1.ComputeIn2d.setValue(project.feature_matrix_stage1.compute_in_2d.tolist())

        self._predict_op_stage1 = OpClassifierPredict(graph=graph)
        self._predict_op_stage1.Classifier.setValue(project.classifier_stage1.classifier)
        self._predict_op_stage1.Classifier.meta.classifier_factory = project.classifier_stage1.classifier_factory
        self._predict_op_stage1.Image.connect(self._feature_sel_op_stage1.OutputImage)
        self._predict_op_stage1.LabelsCount.setValue(project.classifier_stage1.label_count)

        # add stacking
        self._opConvertPMapsToInputPixelType = OpPixelOperator(graph=graph)
        self._opConvertPMapsToInputPixelType.Input.connect(self._predict_op_stage1.PMaps)
        self._opConvertPMapsToInputPixelType.Function.setValue(lambda x: x)

        self._opStacker = OpMultiArrayStacker(graph=graph)
        self._opStacker.Images.resize(2)
        self._opStacker.Images[0].connect(self._reorder_op.Output)
        self._opStacker.Images[1].connect(self._opConvertPMapsToInputPixelType.Output)
        self._opStacker.AxisFlag.setValue("c")

        self._feature_sel_op_stage2 = OpFeatureSelection(graph=graph)
        self._feature_sel_op_stage2.InputImage.connect(self._opStacker.Output)
        self._feature_sel_op_stage2.FeatureIds.setValue(project.feature_matrix_stage2.names)
        self._feature_sel_op_stage2.Scales.setValue(project.feature_matrix_stage2.scales)
        self._feature_sel_op_stage2.SelectionMatrix.setValue(project.feature_matrix_stage2.selections)
        self._feature_sel_op_stage2.ComputeIn2d.setValue(project.feature_matrix_stage2.compute_in_2d.tolist())

        self._predict_op_stage2 = OpClassifierPredict(graph=graph)
        self._predict_op_stage2.Classifier.setValue(project.classifier_stage2.classifier)
        self._predict_op_stage2.Classifier.meta.classifier_factory = project.classifier_stage2.classifier_factory
        self._predict_op_stage2.Image.connect(self._feature_sel_op_stage2.OutputImage)
        self._predict_op_stage2.LabelsCount.setValue(project.classifier_stage2.label_count)

    def _get_probabilities(self, raw_data: Union[vigra.VigraArray, xarray.DataArray], stage: Literal[1, 2]):
        raw_data = as_vigra_array(raw_data)
        num_channels_in_data = raw_data.channels

        fun_convert = DtypeConvertFunction(raw_data.dtype)

        if self._opConvertPMapsToInputPixelType.Function.value != fun_convert:
            self._opConvertPMapsToInputPixelType.Function.setValue(fun_convert)

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

        if stage == 1:
            predict_op = self._predict_op_stage1
        elif stage == 2:
            predict_op = self._predict_op_stage2
        else:
            raise ValueError(f"Invalid argument {stage=}. There are only stage 1 and 2.")

        probabilities = predict_op.PMaps.value[...]
        return xarray.DataArray(probabilities, dims=tuple(predict_op.PMaps.meta.axistags.keys()))

    def get_probabilities_stage_1(self, raw_data: Union[vigra.VigraArray, xarray.DataArray]) -> xarray.DataArray:
        """
        Get pixel probability map from pipeline.

        Args:
            raw_data: image with same dimensionality as in the trained project file
        """
        return self._get_probabilities(raw_data, stage=1)

    def get_probabilities_stage_2(self, raw_data: Union[vigra.VigraArray, xarray.DataArray]) -> xarray.DataArray:
        """
        Get pixel probability map from pipeline.

        Args:
            raw_data: image with same dimensionality as in the trained project file
        """
        return self._get_probabilities(raw_data, stage=2)


def ensure_channel_axis(axis_order):
    if "c" not in axis_order:
        return axis_order + "c"
    return axis_order


def from_project_file(path) -> PixelClassificationPipeline:
    """
    create a PixelClassificationPipeline

    deprecated: please use `experimental.api.PixelClassificationPipeline.from_ilp_file`
    """
    warnings.warn(
        "The `from_project_file` function will disappear in future versions. Please use `PixelClassificationPipeline.from_ilp_file(path)`",
        DeprecationWarning,
    )

    return PixelClassificationPipeline.from_ilp_file(path)


def as_vigra_array(data: Union[vigra.VigraArray, xarray.DataArray]) -> vigra.VigraArray:
    if isinstance(data, vigra.VigraArray):
        return data

    if isinstance(data, xarray.DataArray):
        return vigra.taggedView(data.values, data.dims)

    raise NotImplementedError(f"Data type '{type(data)}' not supported, use `vigra.VigraArray` or `xarray.DataArray`.")
