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
import logging
logger = logging.getLogger(__name__)

def cleanup_value(val, nObjects):
    """ensure that the value is a numpy array with the correct shape."""
    val = np.asarray(val)
    
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

class VigraSkeletonObjFeats(ObjectFeaturesPlugin):
    
    local_preffix = "Skeleton " #note the space at the end, it's important
    
    ndim = None
    
    def availableFeatures(self, image, labels):
        
        try:
            names = vigra.analysis.supportedSkeletonFeatures(labels)
            logger.info('2D Skeleton Features: Supported Skeleton Features: done.')
        except:
            logger.error('2D Skeleton Features: Supported Skeleton Features: failed (Vigra commit must be f8e48031abb1158ea804ca3cbfe781ccc62d09a2 or newer).')
            names = []
        
        tooltips = {}
        result = dict((n, {}) for n in names)  
        for f, v in result.iteritems():
            v['tooltip'] = self.local_preffix + f
        
        return result

    def _do_4d(self, image, labels, features, axes):
        
        result = vigra.analysis.extractSkeletonFeatures(labels.squeeze().astype(np.uint32))
        
        # find the number of objects
        nobj = result[features[0]].shape[0]
        
        #NOTE: this removes the background object!!!
        #The background object is always present (even if there is no 0 label) and is always removed here
        return cleanup(result, nobj, features)

    def compute_global(self, image, labels, features, axes):
        
        return self._do_4d(image, labels, features.keys(), axes)

