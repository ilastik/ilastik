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
from ilastik.plugins import ObjectFeaturesPlugin
import ilastik.applets.objectExtraction.opObjectExtraction

# from ilastik.applets.objectExtraction.opObjectExtraction import make_bboxes, max_margin
import vigra
import numpy as np
from lazyflow.request import Request, RequestPool


def cleanup_key(k):
    return k.replace(" ", "")


def cleanup_value(val, nObjects, isGlobal):
    """ensure that the value is a numpy array with the correct shape."""
    val = np.asarray(val)

    if val.ndim == 0 or isGlobal:
        # repeat the global values for all the objects
        scalar = val.reshape((1,))[0]
        val = np.zeros((nObjects, 1), dtype=val.dtype)
        val[:, 0] = scalar

    if val.ndim == 1:
        val = val.reshape(-1, 1)

    if val.ndim > 2:
        val = val.reshape(val.shape[0], -1)

    assert val.shape[0] == nObjects
    # remove background
    val = val[1:]
    return val


def cleanup(d, nObjects, features):
    result = dict((cleanup_key(k), cleanup_value(v, nObjects, "Global" in k)) for k, v in d.items())
    newkeys = set(result.keys()) & set(features)
    return dict((k, result[k]) for k in newkeys)


class VigraObjFeats(ObjectFeaturesPlugin):
    # features not in this list are assumed to be local.
    local_features = set(
        ["Mean", "Variance", "Skewness", "Kurtosis", "Histogram", "Covariance", "Minimum", "Maximum", "Sum"]
    )
    local_suffix = " in neighborhood"  # note the space in front, it's important
    local_out_suffixes = [local_suffix, " in object and neighborhood"]

    ndim = None

    def availableFeatures(self, image, labels):
        names = vigra.analysis.supportedRegionFeatures(image, labels)
        names = list(f.replace(" ", "") for f in names)
        local = set(names) & self.local_features
        tooltips = {}
        names.extend([x + self.local_suffix for x in local])
        result = dict((n, {}) for n in names)
        result = self.fill_properties(result)

        return result

    def fill_properties(self, features):
        # fills properties into the dictionary of features

        for feature_name in features.keys():
            features[feature_name]["displaytext"] = feature_name
            features[feature_name]["detailtext"] = feature_name + ", stay tuned for more details"
            features[feature_name]["advanced"] = False

            features[feature_name]["tooltip"] = feature_name

            # NOTE: it's important to have the "inside the object" phrase in the description of features, that can also
            # be computed in the object neighborhood

            if feature_name == "Count":
                features[feature_name]["displaytext"] = "Size in pixels"
                features[feature_name][
                    "detailtext"
                ] = "Total size of the object in pixels. No correction for anisotropic resolution or anything else."
                features[feature_name]["group"] = "Shape"

            if feature_name == "Maximum":
                features[feature_name]["displaytext"] = "Maximum intensity"
                features[feature_name][
                    "detailtext"
                ] = "Maximum intensity value inside the object. For multi-channel data, this feature is computed channel-wise."
                features[feature_name]["group"] = "Intensity Distribution"

            if feature_name == "Minimum":
                features[feature_name]["displaytext"] = "Minimum intensity"
                features[feature_name][
                    "detailtext"
                ] = "Minimum intensity value inside the object. For multi-channel data, this feature is computed channel-wise."
                features[feature_name]["group"] = "Intensity Distribution"

            if feature_name == "Coord<Minimum>":
                features[feature_name]["displaytext"] = "Bounding Box Minimum"
                features[feature_name][
                    "detailtext"
                ] = "The coordinates of the lower left corner of the object's bounding box. The first axis is x, then y, then z (if available)."
                features[feature_name]["group"] = "Location"

            if feature_name == "Coord<Maximum>":
                features[feature_name]["displaytext"] = "Bounding Box Maximum"
                features[feature_name][
                    "detailtext"
                ] = "The coordinates of the upper right corner of the object's bounding box. The first axis is x, then y, then z (if available)."
                features[feature_name]["group"] = "Location"

            if feature_name == "Mean":
                features[feature_name]["displaytext"] = "Mean Intensity"
                features[feature_name][
                    "detailtext"
                ] = "Mean intensity inside the object. For multi-channel data, this feature is computed channel-wise."
                features[feature_name]["group"] = "Intensity Distribution"

            if feature_name == "Variance":
                features[feature_name]["displaytext"] = "Variance of Intensity"
                features[feature_name][
                    "detailtext"
                ] = "Variance of the intensity distribution inside the object. For multi-channel data, this feature is computed channel-wise."
                features[feature_name]["group"] = "Intensity Distribution"

            if feature_name == "Skewness":
                features[feature_name]["displaytext"] = "Skewness of Intensity"
                features[feature_name]["detailtext"] = (
                    "Skewness of the intensity distribution inside the object, also known as the third standardized moment. This feature measures the asymmetry of the "
                    "intensity distribution inside the object. For multi-channel data, this feature is computed channel-wise. "
                )
                features[feature_name]["group"] = "Intensity Distribution"

            if feature_name == "Kurtosis":
                features[feature_name]["displaytext"] = "Kurtosis of Intensity"
                features[feature_name]["detailtext"] = (
                    "Kurtosis of the intensity distribution inside the object, also known as the fourth standardized moment. This feature measures the heaviness of the "
                    "tails for the distribution of intensity over the object's pixels. For multi-channel data, this feature is computed channel-wise. "
                )
                features[feature_name]["group"] = "Intensity Distribution"

            if feature_name == "RegionCenter":
                features[feature_name]["displaytext"] = "Center of the object"
                features[feature_name]["detailtext"] = "Average of the coordinates of this object's pixels."
                features[feature_name]["group"] = "Location"

            if feature_name == "RegionRadii":
                features[feature_name]["displaytext"] = "Radii of the object"
                features[feature_name]["detailtext"] = (
                    "Eigenvalues of the PCA on the coordinates of the object's pixels. Very roughly, this corresponds to the radii of an ellipse fit to the object. "
                    " The radii are ordered, with the largest value as first."
                )
                features[feature_name]["group"] = "Shape"

            if feature_name == "RegionAxes":
                features[feature_name]["displaytext"] = "Principal components of the object"
                features[feature_name]["detailtext"] = (
                    "Eigenvectors of the PCA on the coordinates of the object's pixels. Very roughly, this corresponds to the axes of an ellipse fit to the object. "
                    " The axes are ordered starting from the one with the largest eigenvalue."
                )
                features[feature_name]["group"] = "Shape"

            if feature_name == "Quantiles":
                features[feature_name]["displaytext"] = "Quantiles of Intensity"
                features[feature_name][
                    "detailtext"
                ] = "Quantiles of the intensity distribution inside the object, in the following order: 0%, 10%, 25%, 50%, 75%, 90%, 100%. "
                features[feature_name]["group"] = "Intensity Distribution"

            if feature_name == "Histogram":
                features[feature_name]["displaytext"] = "Histogram of Intensity"
                features[feature_name]["detailtext"] = (
                    "Histogram of the intensity distribution inside the object. The histogram has 64 bins and its range is computed from the global minimum "
                    "and maximum intensity values in the whole image."
                )
                features[feature_name]["group"] = "Intensity Distribution"

            if feature_name == "Covariance":
                features[feature_name]["displaytext"] = "Covariance of Channel Intensity"
                features[feature_name][
                    "detailtext"
                ] = "For multi-channel images this feature computes the covariance between the channels inside the object."
                features[feature_name]["group"] = "Intensity Distribution"

            if feature_name == "Sum":
                features[feature_name]["displaytext"] = "Total Intensity"
                features[feature_name][
                    "detailtext"
                ] = "Sum of intensity values for all the pixels inside the object. For multi-channel images, computed channel-wise."
                features[feature_name]["group"] = "Intensity Distribution"

            if "<" in feature_name and feature_name != "Coord<Minimum>" and feature_name != "Coord<Maximum>":
                features[feature_name]["advanced"] = True

            if self.local_suffix in feature_name:
                stripped_name = feature_name.replace(self.local_suffix, "")
                # we have detailed info for this feature, let's apply it to the
                fake_dict = {stripped_name: {}}
                texts = self.fill_properties(fake_dict)
                features[feature_name]["displaytext"] = texts[stripped_name]["displaytext"] + " in neighborhood"
                features[feature_name]["detailtext"] = texts[stripped_name]["detailtext"].replace(
                    "inside the object", "in the object neighborhood"
                )
                features[feature_name]["detailtext"] = (
                    features[feature_name]["detailtext"]
                    + " The size of the neighborhood is determined from the controls in the lower part of the dialogue."
                )
                features[feature_name]["tooltip"] = (
                    features[feature_name]["tooltip"] + ", as defined by neighborhood size below"
                )
                features[feature_name]["margin"] = 0
                features[feature_name]["group"] = "Intensity Distribution"

        return features

    def _do_4d(self, image, labels, features, axes):
        if self.ndim == 2:
            result = vigra.analysis.extractRegionFeatures(
                image.squeeze().astype(np.float32), labels.squeeze().astype(np.uint32), features, ignoreLabel=0
            )
        else:
            result = vigra.analysis.extractRegionFeatures(
                image.astype(np.float32), labels.astype(np.uint32), features, ignoreLabel=0
            )

        # take a non-global feature
        local_features = [x for x in features if "Global<" not in x]
        # find the number of objects
        nobj = result[local_features[0]].shape[0]

        # NOTE: this removes the background object!!!
        # The background object is always present (even if there is no 0 label) and is always removed here
        cleaned = cleanup(result, nobj, features)

        if "Coord<Maximum>" in cleaned:
            # Coord<min>, Coord<max> yield end inclusive bounds
            # This leads to bounding boxes that are always one pixel too small
            cleaned["Coord<Maximum>"] += 1
        return cleaned

    def compute_global(self, image, labels, features, axes):
        features = list(features.keys())
        local = [x + self.local_suffix for x in self.local_features]
        features = list(set(features) - set(local))

        # the image parameter passed here is the whole dataset.
        # We can use it estimate if the data is 2D or 3D and then apply
        # this knowledge in compute_local
        nZ = image.shape[axes.z]
        if nZ > 1:
            self.ndim = 3
        else:
            self.ndim = 2

        return self._do_4d(image, labels, features, axes)

    def compute_local(self, image, binary_bbox, feature_dict, axes):
        """helper that deals with individual objects"""

        featurenames = list(feature_dict.keys())
        local = [x + self.local_suffix for x in self.local_features]
        featurenames = list(set(featurenames) & set(local))
        featurenames = [x.split(" ")[0] for x in featurenames]
        results = []
        margin = ilastik.applets.objectExtraction.opObjectExtraction.max_margin({"": feature_dict})
        # FIXME: this is done globally as if all the features have the same margin
        # we should group features by their margins
        passed, excl = ilastik.applets.objectExtraction.opObjectExtraction.make_bboxes(binary_bbox, margin)
        # assert np.all(passed==excl)==False
        # assert np.all(binary_bbox+excl==passed)
        for label, suffix in zip([excl, passed], self.local_out_suffixes):
            result = self._do_4d(image, label, featurenames, axes)
            results.append(self.update_keys(result, suffix=suffix))
        return self.combine_dicts(results)
