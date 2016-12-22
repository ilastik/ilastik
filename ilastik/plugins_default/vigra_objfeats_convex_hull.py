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
#		   http://ilastik.org/license.html
###############################################################################
from ilastik.plugins import ObjectFeaturesPlugin
import vigra
import numpy
import logging
logger = logging.getLogger(__name__)

def cleanup_value(val, nObjects):
    """ensure that the value is a numpy array with the correct shape."""
    
    if type(val)==list:
        return val
    
    val = numpy.asarray(val)
    
    if val.ndim == 1:
        val = val.reshape(-1, 1)
    
    assert val.shape[0] == nObjects
    # remove background
    val = val[1:]
    return val

def cleanup(d, nObjects, features):
    result = dict((k, cleanup_value(v, nObjects)) for k, v in d.iteritems())
    newkeys = set(result.keys()) & set(features)
    return dict((k, result[k]) for k in newkeys)

class VigraConvexHullObjFeats(ObjectFeaturesPlugin):
    local_preffix = "Convex Hull " #note the space at the end, it's important
    
    ndim = None
    
    def availableFeatures(self, image, labels):
        names = vigra.analysis.extract2DConvexHullFeatures(labels, list_features_only=True)
        logger.debug('2D Convex Hull Features: Supported Convex Hull Features: done.')

        tooltips = {}
        result = dict((n, {}) for n in names)
        result = self.fill_properties(result)
        for f, v in result.iteritems():
            v['tooltip'] = self.local_preffix + f
        
        return result

    @staticmethod
    def fill_properties(features):
        # fill in the detailed information about the features.
        # features should be a dict with the feature_name as key.
        # NOTE, this function needs to be updated every time skeleton features change
        for feature in features.iterkeys():
            features[feature]["displaytext"] = feature
            features[feature]["detailtext"] = feature + ", stay tuned for more details"
            features[feature]["advanced"] = False
            features[feature]["group"] = "Shape"

            if feature == "InputVolume":
                features[feature]["displaytext"] = "Object Area"
                features[feature]["detailtext"] = "Area of this object, computed from the interpixel contour " \
                                                  " (can be slightly larger than simple size of the object in pixels). " \
                                                  "This feature is used to compute convexity."

            if feature == "HullVolume":
                features[feature]["displaytext"] = "Convex Hull Area"
                features[feature]["detailtext"] = "Area of the convex hull of this object"

            if feature == "Convexity":
                features[feature]["displaytext"] = "Convexity"
                features[feature]["detailtext"] = " The ratio between the areas of the object and its convex hull (<= 1)"

            if feature == "DefectVolumeMean":
                features[feature]["displaytext"] = "Mean Defect Area"
                features[feature]["detailtext"] = "Average of the areas of convexity defects. Defects are defined as connected components in the area of the " \
                                                  "convex hull, not covered by the original object."

            if feature == "DefectVolumeVariance":
                features[feature]["displaytext"] = "Variance of Defect Area"
                features[feature]["detailtext"] = "Variance of the distribution of areas of convexity defects. Defects are defined as connected components in the area of the " \
                                                  "convex hull, not covered by the original object."
            if feature == "DefectVolumeSkewness":
                features[feature]["displaytext"] = "Skewness of Defect Area"
                features[feature]["detailtext"] = "Skewness (3rd standardized moment, measure of asymmetry) of the distribution of the areas of convexity defects. " \
                                                  "Defects are defined as connected components in the area of the " \
                                                  "convex hull, not covered by the original object."

            if feature == "DefectVolumeKurtosis":
                features[feature]["displaytext"] = "Kurtosis of Defect Area"
                features[feature]["detailtext"] = "Kurtosis (4th standardized moment, measure of tails' heaviness) of the distribution of the areas of convexity defects. " \
                                                  "Defects are defined as connected components in the area of the " \
                                                  "convex hull, not covered by the original object."

            if feature == "DefectCount":
                features[feature]["displaytext"] = "Number of Defects"
                features[feature]["detailtext"] = "Total number of defects, i.e. number of connected components in the area of the " \
                                                  "convex hull, not covered by the original object"

            if feature == "DefectDisplacementMean":
                features[feature]["displaytext"] = "Mean Defect Displacement"
                features[feature]["detailtext"] = "Mean distance between the centroids of the original object and the centroids of the defects, weighted by defect area."

            if feature == "InputCenter":
                features[feature]["displaytext"] = "Object Center"
                features[feature]["detailtext"] = "Centroid of this object. The axes order is x, y, z"

            if feature == "HullCenter":
                features[feature]["displaytext"] = "Convex Hull Center"
                features[feature]["detailtext"] = "Centroid of the convex hull of this object. The axes order is x, y, z"

            if feature == "Defect Center":
                features[feature]["displaytext"] = "Defect Center"
                features[feature]["detailtext"] = "Combined centroid of convexity defects, which are defined as areas of the " \
                                                  "convex hull, not covered by the original object."

##
## OLD CONVEX HULL FEATURES, NO LONGER AVAILABLE IN VIGRA
##

#             if feature == "Perimeter":
#                 features[feature]["displaytext"] = "Convex Hull Perimeter"
#                 features[feature]["detailtext"] = "Perimeter of the convex hull of this object, computed from its interpixel contour."

#             if feature == "Rugosity":
#                 features[feature]["displaytext"] = "Rugosity"
#                 features[feature]["detailtext"] = "The ratio between the perimeters of the convex hull and this object object (>= 1)"

#             if feature == "Input Perimeter":
#                 features[feature]["displaytext"] = "Object Perimeter"
#                 features[feature]["detailtext"] = "Perimeter of the object, computed from the interpixel contour."

#             if feature == "Input Count":
#                 features[feature]["displaytext"] = "Object Size in Pixels"
#                 features[feature]["detailtext"] = "Size of this object in pixels."
#                 features[feature]["advanced"] = True #hide this feature, all it has to say is already contained in area

#             if feature == "Defect Area List":
#                 features[feature]["displaytext"] = "Largest Defect Area"
#                 features[feature]["detailtext"] = "Areas of the three largest defects. Defects are defined as connected components in the area of the " \
#                                                   "convex hull, not covered by the original object."

        return features

    def _do_4d(self, image, labels, features, axes):
        
        # ignoreLabel=None calculates background label parameters
        # ignoreLabel=0 ignores calculation of background label parameters
        result = vigra.analysis.extract2DConvexHullFeatures(labels.squeeze().astype(numpy.uint32), ignoreLabel=0)
        
        # find the number of objects
        try:
            nobj = result[features[0]].shape[0]
        except  Exception as e:
            logger.error("Feature name not found in computed features.\n"
                         "Your project file might be using obsolete features.\n"
                         "Please select new features, and re-train your classifier.\n"
                         "(Exception was: {})".format(e))
        
        #NOTE: this removes the background object!!!
        #The background object is always present (even if there is no 0 label) and is always removed here
        return cleanup(result, nobj, features)

    def compute_global(self, image, labels, features, axes):
        
        return self._do_4d(image, labels, features.keys(), axes)

