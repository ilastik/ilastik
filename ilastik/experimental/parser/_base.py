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

import h5py

from . import types


class PixelClassificationProject:
    ILP_WORKFLOW_NAME = b"Pixel Classification"

    def __init__(self, hdf5_file: h5py.File) -> None:
        class ILPkeys(types.StrEnum):
            WORKFLOW = "workflowName"
            INPUT_DATA = "Input Data/infos"
            FEATURES = "FeatureSelections"
            PIXEL_CLASSIFICATION = "PixelClassification"

        if any(key not in hdf5_file for key in ILPkeys):
            raise types.IlastikAPIError(
                f"Not a valid ilastik project pixel classification project file with keys {hdf5_file.keys()}"
            )

        type_ = hdf5_file[ILPkeys.WORKFLOW][()]
        if type_ != self.ILP_WORKFLOW_NAME:
            raise types.IlastikAPIError(f"Expected Pixel Classification Project, found {type_}")

        self._data_info = types.ProjectDataInfo.from_ilp_group(hdf5_file[ILPkeys.INPUT_DATA.value])
        self._feature_matrix = types.FeatureMatrix.from_ilp_group(hdf5_file[ILPkeys.FEATURES.value])
        self._classifier = types.Classifier.from_ilp_group(hdf5_file[ILPkeys.PIXEL_CLASSIFICATION.value])

    @property
    def data_info(self) -> Optional[types.ProjectDataInfo]:
        return self._data_info

    @property
    def feature_matrix(self) -> types.FeatureMatrix:
        return self._feature_matrix

    @property
    def classifier(self) -> types.Classifier:
        return self._classifier
