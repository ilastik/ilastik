###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2023, the ilastik developers
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
from typing import Union

import h5py
import vigra
import xarray

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.experimental import parser
from lazyflow.graph import Graph
from lazyflow.operators import OpReorderAxes
from lazyflow.operators.classifierOperators import OpClassifierPredict


class PixelClassificationPipeline:
    """
    Pipeline for accessing trained Pixel Classification classifiers from Python

    Example usage:

    ```Python
    from ilastik.experimental.api import PixelClassificationPipeline
    import imageio.v3 as iio

    img = iio.imread("<path/to/image-file.tif>")
    pipeline = PixelClassificationPipeline.from_ilp_file("<path/to/project.ilp>")

    prob_maps = pipeline.get_probabilities(img)
    ```

    """

    @classmethod
    def from_ilp_file(cls, path: str) -> "PixelClassificationPipeline":
        """
        Create a Pixel Classification Pipeline instance from a traine project.ilp file

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
