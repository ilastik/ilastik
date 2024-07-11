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

# Plugin written by Oane Gros.
# Does feature extraction by spherical projection texture
# Does a user-settable projection along rays from the centroid in gauss-legendre quadrature
# Mapping the data to a 2D sphericall surface
# This is decomposed into a spherical harmonics power spectrum
# The resulting feature is an undersampled (for feature reduction) spectrum
###############################################################################

# core ilastik
from ilastik.plugins import ObjectFeaturesPlugin
import ilastik.applets.objectExtraction.opObjectExtraction

# core
import vigra
import numpy as np

from sphericaltexture import SphericalTextureGenerator


class SphericalProjection(ObjectFeaturesPlugin):
    def __init__(self):
        self.margin = 0  # necessary for calling compute_local
        self.stg = None

    def availableFeatures(self, image, labels):
        self.stg = None
        result = {}
        if labels.ndim == 2:
            result[f"{labels.ndim}D Circular Texture"] = {}
        elif labels.ndim == 3:
            result[f"{labels.ndim}D Spherical Texture"] = {}
        result[f"{labels.ndim}D Polarization Direction"] = {}
        result = self.fill_properties(result)
        for f, v in result.items():
            v["tooltip"] = f
        return result

    @staticmethod
    def fill_properties(features):
        # fill in the detailed information about the features.
        # features should be a dict with the feature_name as key.
        # NOTE, this function needs to be updated every time skeleton features change
        for name, feature in features.items():
            feature["margin"] = 0
            feature["displaytext"] = name
            if "Texture" in name:
                feature["detailtext"] = (
                    "Maps each object to a sphere/circle by mean intensity projection,"
                    "and quantifies the distribution of the intensity signal in the projection "
                    "through Spherical Harmonics/Fourier decomposition. "
                    "It thus gives a quantification of variance per angular wavelength in 20 values."
                )
            else:
                feature["detailtext"] = (
                    "Maps each object to a sphere/circle by mean intensity projection, and returns "
                    "the angle in rad with the max intensity in the angular projection."
                )
        return features

    def _do_3d(self, image, binary_bbox, stg_to_feat, axes):
        if self.stg is None:
            raise Exception("SphericalTextureGenerator was not initialized")
        stg_results = self.stg.process_image(image, binary_bbox)
        for key in list(stg_results.keys()):  # rename keys to ilastik feature names
            stg_results[key] = np.nan_to_num(stg_results[key])
            stg_results[stg_to_feat[key]] = stg_results.pop(key)

        print(stg_results)
        return stg_results

    def compute_local(self, image, binary_bbox, features, axes):
        output_types = []
        stg_to_feat = {}
        ndim = None
        for feature in features:
            if "Spherical Texture" in feature:
                output_types.append("Condensed Spectrum")
                ndim = int(feature[0])
                stg_to_feat["Intensity Condensed Spectrum"] = feature
            if "Polarization Direction" in feature:
                output_types.append("Polarization Direction")
                ndim = int(feature[0])
                stg_to_feat["Intensity Polarization Direction"] = feature

        if self.stg == None:
            self.stg = SphericalTextureGenerator(projections=["Intensity"], output_types=output_types)

        # slice off neighborhood
        margin = [(np.min(dim), np.max(dim) + 1) for dim in np.nonzero(binary_bbox)]
        image = image[margin[0][0] : margin[0][1], margin[1][0] : margin[1][1], margin[2][0] : margin[2][1]]
        binary_bbox = binary_bbox[margin[0][0] : margin[0][1], margin[1][0] : margin[1][1], margin[2][0] : margin[2][1]]

        return self.do_channels(self._do_3d, image, binary_bbox=binary_bbox, stg_to_feat=stg_to_feat, axes=axes)
