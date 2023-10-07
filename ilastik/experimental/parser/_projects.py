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
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type, TypeVar

import h5py

from . import types

T = TypeVar("T", bound="ILP")


class ILP(ABC):
    @classmethod
    @abstractmethod
    def from_ilp_file(cls: Type[T], h5file: h5py.File) -> T:
        ...


@dataclass(frozen=True)
class PixelClassificationProject(ILP):
    data_info: types.ProjectDataInfo
    feature_matrix: types.FeatureMatrix
    classifier: types.Classifier

    @classmethod
    def from_ilp_file(cls, h5file: h5py.File):
        ILP_WORKFLOW_NAME = b"Pixel Classification"

        class ILPkeys(types.StrEnum):
            WORKFLOW = "workflowName"
            INPUT_DATA = "Input Data/infos"
            FEATURES = "FeatureSelections"
            PIXEL_CLASSIFICATION = "PixelClassification"

        if any(key not in h5file for key in ILPkeys):
            raise types.IlastikAPIError(
                f"Not a valid ilastik project pixel classification project file with keys {h5file.keys()}"
            )

        type_: bytes = h5file[ILPkeys.WORKFLOW][()]
        if type_ != ILP_WORKFLOW_NAME:
            raise types.IlastikAPIError(f"Expected Pixel Classification Project, found {type_!r}")

        return cls(
            types.ProjectDataInfo.from_ilp_group(h5file[ILPkeys.INPUT_DATA]),
            types.FeatureMatrix.from_ilp_group(h5file[ILPkeys.FEATURES]),
            types.Classifier.from_ilp_group(h5file[ILPkeys.PIXEL_CLASSIFICATION]),
        )
