###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################
from typing import TYPE_CHECKING
from ilastik.plugins import ObjectFeaturesPlugin
import numpy

from ilastik.plugins.types import PluginInfo

if TYPE_CHECKING:
    from ilastik.plugins.types import FeatureDescription, FloatArray
    import vigra


class TestFeatures(ObjectFeaturesPlugin):
    plugin_info = PluginInfo(
        name="TestFeatures", author="Anna Kreshuk", version="0.1", description="Dummy features for testing the pipeline"
    )

    all_features: dict[str, dict[str, str]] = {"with_nans": {}, "with_nones": {}, "fail_on_zero": {}}

    def availableFeatures(self, image: "vigra.VigraArray", labels: "vigra.VigraArray") -> dict[str, dict[str, str]]:
        return self.all_features

    def fill_properties(self, features: dict[str, dict[str, str]]) -> dict[str, "FeatureDescription"]:
        return {
            "with_nans": {
                "displaytext": "with_nans",
                "detailtext": "with_nans details",
                "tooltip": "with_nans tooltip",
                "advanced": False,
            },
            "with_nones": {
                "displaytext": "with_nones",
                "detailtext": "with_nones details",
                "tooltip": "with_nones tooltip",
                "advanced": False,
            },
            "fail_on_zero": {
                "displaytext": "fail_on_zero",
                "detailtext": "fail_on_zero details",
                "tooltip": "fail_on_zero tooltip",
                "advanced": False,
            },
        }

    def compute_global(
        self, image: "vigra.VigraArray", labels: "vigra.VigraArray", features: dict[str, dict[str, str]], axes: str
    ) -> dict[str, "FloatArray"]:

        lmax = int(numpy.max(labels))
        result = dict(
            with_nans=numpy.zeros((lmax, 1)), with_nones=numpy.zeros((lmax, 1)), fail_on_zero=numpy.zeros((lmax, 1))
        )

        for i in range(lmax):
            if i % 3 == 0:
                result["with_nans"][i] = numpy.nan
                result["with_nones"][i] = None
            else:
                result["with_nans"][i] = 21
                result["with_nones"][i] = 42

        if numpy.sum(image) == 0:
            raise RuntimeError("Features: should not get here!")

        return result
