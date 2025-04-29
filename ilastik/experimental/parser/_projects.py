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

from pydantic import BaseModel, Field

from . import types


class PixelClassificationProject(BaseModel):
    input_data: types.InputData = Field(alias="Input Data")
    feature_matrix: types.FeatureMatrix = Field(alias="FeatureSelections")
    classifier: types.Classifier = Field(alias="PixelClassification")


class AutocontextProject(BaseModel):
    input_data: types.InputData = Field(alias="Input Data")
    feature_matrix_stage1: types.FeatureMatrix = Field(alias="FeatureSelections")
    classifier_stage1: types.Classifier = Field(alias="PixelClassification")
    feature_matrix_stage2: types.FeatureMatrix = Field(alias="FeatureSelections01")
    classifier_stage2: types.Classifier = Field(alias="PixelClassification01")


class _ObjectClassificationProjectBase(BaseModel):
    input_data: types.InputData = Field(alias="Input Data")
    classifier: types.ObjectClassificationClassifier = Field(alias="ObjectClassification")


class ObjectClassificationFromSegmentationProject(_ObjectClassificationProjectBase):
    pass


class ObjectClassificationFromProbabilitiesProject(_ObjectClassificationProjectBase):
    threshdolding: types.ThresholdTwoLevels = Field(alias="ThresholdTwoLevels")
