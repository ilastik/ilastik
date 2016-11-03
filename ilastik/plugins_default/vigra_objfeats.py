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
import ilastik.applets.objectExtraction.opObjectExtraction
#from ilastik.applets.objectExtraction.opObjectExtraction import make_bboxes, max_margin
import vigra
import numpy as np
from lazyflow.request import Request, RequestPool

def cleanup_key(k):
    return k.replace(' ', '')

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
    result = dict((cleanup_key(k), cleanup_value(v, nObjects, "Global" in k)) for k, v in d.iteritems())
    newkeys = set(result.keys()) & set(features)
    return dict((k, result[k]) for k in newkeys)

class VigraObjFeats(ObjectFeaturesPlugin):
    # features not in this list are assumed to be local.
    local_features = set(["Mean", "Variance", "Skewness", \
                          "Kurtosis", "Histogram", \
                          "Covariance", "Minimum", "Maximum"])
    local_suffix = " in neighborhood" #note the space in front, it's important
    local_out_suffixes = [local_suffix, " in object and neighborhood"]

    ndim = None
    
    def availableFeatures(self, image, labels):
        names = vigra.analysis.supportedRegionFeatures(image, labels)
        names = list(f.replace(' ', '') for f in names)
        local = set(names) & self.local_features
        tooltips = {}
        names.extend([x+self.local_suffix for x in local])
        result = dict((n, {}) for n in names)  
        for f, v in result.iteritems():
            if self.local_suffix in f:
                v['margin'] = 0
            #build human readable names from vigra names
            #TODO: many cases are not covered
            props = self.find_properties(f)
            for prop_name, prop_value in props.iteritems():
                v[prop_name] = prop_value
        
        return result

    def find_properties(self, feature_name):

        tooltip = feature_name
        advanced = False
        displaytext = feature_name
        detailtext = feature_name
        # NOTE: it's important to have the "inside the object" phrase in the description of features, that can also
        # be computed in the object neighborhood
        if feature_name == "Count":
            displaytext = "Size in pixels"
            detailtext = "Total size of the object in pixels. No correction for anisotropic resolution or anything else."

        if feature_name == "Maximum":
            displaytext = "Maximum intensity"
            detailtext = "Maximum intensity value inside the object. For multi-channel data, this feature is computed channel-wise."

        if feature_name == "Minimum":
            displaytext = "Minimum intensity"
            detailtext = "Minimum intensity value inside the object. For multi-channel data, this feature is computed channel-wise."

        if feature_name == "Coord<Minimum>":
            displaytext = "Bounding Box Minimum"
            detailtext = "The coordinates of the lower left corner of the object's bounding box. The first axis is x, then y, then z (if available)."

        if feature_name == "Coord<Maximum>":
            displaytext = "Bounding Box Maximum"
            detailtext = "The coordinates of the upper right corner of the object's bounding box. The first axis is x, then y, then z (if available)."

        if feature_name == "Mean":
            displaytext = "Mean Intensity"
            detailtext = "Mean intensity inside the object. For multi-channel data, this feature is computed channel-wise."

        if feature_name == "Variance":
            displaytext = "Variance of Intensity"
            detailtext = "Variance of the intensity distribution inside the object. For multi-channel data, this feature is computed channel-wise."

        if feature_name == "Skewness":
            displaytext = "Skewness of Intensity"
            detailtext = "Skewness of the intensity distribution inside the object, also known as the third standardized moment. This feature measures the asymmetry of the"  \
                         "intensity distribution inside the object. For multi-channel data, this feature is computed channel-wise. "

        if feature_name == "Kurtosis":
            displaytext = "Kurtosis of Intensity"
            detailtext = "Kurtosis of the intensity distribution inside the object, also known as the fourth standardized moment. This feature measures the heaviness of the" \
                         "tails for the distribution of intensity over the object's pixels. For multi-channel data, this feature is computed channel-wise. "

        if feature_name == "RegionCenter":
            displaytext = "Center of the object"
            detailtext = "Average of the coordinates of this object's pixels."

        if feature_name == "RegionRadii":
            displaytext = "Radii of the object"
            detailtext = "Eigenvalues of the PCA on the coordinates of the object's pixels. Very roughly, this corresponds to the radii of an ellipse fit to the object." \
                        " The radii are ordered, with the largest value as first."

        if feature_name == "RegionAxes":
            displaytext = "Principal components of the object"
            detailtext = "Eigenvectors of the PCA on the coordinates of the object's pixels. Very roughly, this corresponds to the axes of an ellipse fit to the object." \
                        " The axes are ordered starting from the one with the largest eigenvalue."

        if feature_name == "Quantiles":
            displaytext = "Quantiles of Intensity"
            detailtext = "Quantiles of the intensity distribution inside the object, in the following order: 0%, 10%, 25%, 50%, 75%, 90%, 100%. "

        if feature_name == "Histogram":
            displaytext = "Histogram of Intensity"
            detailtext = "Histogram of the intensity distribution inside the object. The histogram has 64 bins and its range is computed from the global minimum" \
                         "and maximum intensity values in the whole image."

        if feature_name == "Covariance":
            displaytext = "Covariance of Channel Intensity"
            detailtext = "For multi-channel images this feature computes the covariance between the channels inside the object."

        if feature_name == "Sum":
            displaytext = "Total Intensity"
            detailtext = "Sum of intensity values for all the pixels inside the object. For multi-channel images, computed channel-wise."

        if "<" in feature_name and feature_name!="Coord<Minimum>" and feature_name!="Coord<Maximum>":
            advanced = True

        if self.local_suffix in feature_name:
            stripped_name = feature_name.replace(self.local_suffix, "")
            # we have detailed info for this feature, let's apply it to the
            texts = self.find_properties(stripped_name)
            displaytext = texts["displaytext"] + " in neighborhood"
            detailtext = texts["detailtext"].replace("inside the object", "in the object neighborhood")
            detailtext = detailtext + " The size of the neighborhood is determined from the controls in the lower part of the dialogue."
            tooltip = tooltip + ", as defined by neighborhood size below"

        props = {}
        props["tooltip"] = tooltip
        props["advanced"] = advanced
        props["displaytext"] = displaytext
        props["detailtext"] = detailtext
        return props

    def _do_4d(self, image, labels, features, axes):
        if self.ndim==2:
            result = vigra.analysis.extractRegionFeatures(image.squeeze().astype(np.float32), labels.squeeze().astype(np.uint32), features, ignoreLabel=0)
        else:
            result = vigra.analysis.extractRegionFeatures(image.astype(np.float32), labels.astype(np.uint32), features, ignoreLabel=0)
            
        #take a non-global feature
        local_features = [x for x in features if "Global<" not in x]
        #find the number of objects
        nobj = result[local_features[0]].shape[0]
        
        #NOTE: this removes the background object!!!
        #The background object is always present (even if there is no 0 label) and is always removed here
        return cleanup(result, nobj, features)

    def compute_global(self, image, labels, features, axes):
        features = features.keys()
        local = [x+self.local_suffix for x in self.local_features]
        features = list(set(features) - set(local))
        
        #the image parameter passed here is the whole dataset. 
        #We can use it estimate if the data is 2D or 3D and then apply 
        #this knowledge in compute_local
        nZ = image.shape[axes.z]
        if nZ>1:
            self.ndim = 3
        else:
            self.ndim = 2
            
        return self._do_4d(image, labels, features, axes)

    def compute_local(self, image, binary_bbox, feature_dict, axes):
        """helper that deals with individual objects"""
        
        featurenames = feature_dict.keys()
        local = [x+self.local_suffix for x in self.local_features]
        featurenames = list(set(featurenames) & set(local))
        featurenames = [x.split(' ')[0] for x in featurenames]
        results = []
        margin = ilastik.applets.objectExtraction.opObjectExtraction.max_margin({'': feature_dict})
        #FIXME: this is done globally as if all the features have the same margin
        #we should group features by their margins
        passed, excl = ilastik.applets.objectExtraction.opObjectExtraction.make_bboxes(binary_bbox, margin)
        #assert np.all(passed==excl)==False
        #assert np.all(binary_bbox+excl==passed)
        for label, suffix in zip([excl, passed],
                                 self.local_out_suffixes):
            result = self._do_4d(image, label, featurenames, axes)
            results.append(self.update_keys(result, suffix=suffix))
        return self.combine_dicts(results)
