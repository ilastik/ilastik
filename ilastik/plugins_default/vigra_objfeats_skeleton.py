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
    val = numpy.asarray(val)
    
    if val.ndim == 1:
        val = val.reshape(-1, 1)
    assert val.shape[0] == nObjects
    
    # remove background
    val = val[1:]
    return val

def cleanup(d, nObjects, features):
    
    result = dict((k, cleanup_value(v, nObjects)) for k, v in d.items())
    newkeys = set(result.keys()) & set(features)
    return dict((k, result[k]) for k in newkeys)

class VigraSkeletonObjFeats(ObjectFeaturesPlugin):
    
    local_preffix = "Skeleton " #note the space at the end, it's important
    
    ndim = None
    
    def availableFeatures(self, image, labels):
        names = vigra.analysis.supportedSkeletonFeatures(labels)
        logger.debug('2D Skeleton Features: Supported Skeleton Features: done.')

        tooltips = {}
        result = dict((n, {}) for n in names)
        result = self.fill_properties(result)
        for f, v in result.items():
            v['tooltip'] = self.local_preffix + f
        
        return result

    @staticmethod
    def fill_properties(features):
        # fill in the detailed information about the features.
        # features should be a dict with the feature_name as key.
        # NOTE, this function needs to be updated every time skeleton features change
        for feature in features.keys():
            features[feature]["displaytext"] = feature
            features[feature]["detailtext"] = feature + ", stay tuned for more details"
            features[feature]["advanced"] = False
            features[feature]["group"] = "Shape"
            if feature == "Branch Count":
                features[feature]["displaytext"] = "Number of Branches"
                features[feature]["detailtext"] = "Total number of branches in the skeleton of this object."
            if feature == "Hole Count":
                features[feature]["displaytext"] = "Number of Holes"
                features[feature]["detailtext"] = "The number of cycles in the skeleton (i.e. the number of cavities in the region)"
            if feature == "Diameter":
                features[feature]["displaytext"] = "Diameter"
                features[feature]["detailtext"] = "The longest path between two endpoints on the skeleton."
            if feature == "Euclidean Diameter":
                features[feature]["displaytext"] = "Euclidean Diameter"
                features[feature]["detailtext"] = "The Euclidean distance between the endpoints (terminals) of the longest path " \
                                                  "on the skeleton"
            if feature == "Skeleton Center":
                features[feature]["displaytext"] = "Center of the Skeleton"
                features[feature]["detailtext"] = "The coordinates of the midpoint on the longest path between the endpoints of the skeleton."
                features[feature]["group"] = "Location"
            if feature == "Total Length":
                features[feature]["displaytext"] = "Length of the Skeleton"
                features[feature]["detailtext"] = "Total length of the skeleton in pixels"
            if feature == "Average Length":
                features[feature]["displaytext"] = "Average Branch Length"
                features[feature]["detailtext"] = "Average length of a branch in the skeleton"
            if feature == "Terminal 1":
                features[feature]["displaytext"] = "Terminal 1"
                features[feature]["detailtext"] = "First endpoint of the longest path between the skeleton's endpoints"
                features[feature]["group"] = "Location"
                features[feature]["advanced"] = True
            if feature == "Terminal 2":
                features[feature]["displaytext"] = "Terminal 2"
                features[feature]["detailtext"] = "Second endpoint of the longest path between the skeleton's endpoints"
                features[feature]["group"] = "Location"
                features[feature]["advanced"] = True

        return features

    def _do_4d(self, image, labels, features, axes):
        result = vigra.analysis.extractSkeletonFeatures(labels.squeeze().astype(numpy.uint32))

        # find the number of objects
        nobj = result[features[0]].shape[0]
        
        #NOTE: this removes the background object!!!
        #The background object is always present (even if there is no 0 label) and is always removed here
        return cleanup(result, nobj, features)

    def compute_global(self, image, labels, features, axes):
        
        return self._do_4d(image, labels, list(features.keys()), axes)

