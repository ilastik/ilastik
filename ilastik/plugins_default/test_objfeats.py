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

class TestFeatures(ObjectFeaturesPlugin):

    all_features = {"with_nans" : {},
                    "with_nones" : {},
                    "fail_on_zero": {}}
    
    def availableFeatures(self, image, labels):
        return self.all_features
    
    def compute_global(self, image, labels, features, axes):
        lmax = numpy.max(labels)
        result = dict()
        result["with_nans"] = numpy.zeros((lmax, 1))
        result["with_nones"] = numpy.zeros((lmax, 1))
        result["fail_on_zero"] = numpy.zeros((lmax, 1))
        
        for i in range(lmax):
            if i%3==0:
                result["with_nans"][i]=numpy.NaN
                result["with_nones"][i]=None
            else:
                result["with_nans"][i]=21
                result["with_nones"][i]=42
                
        if numpy.sum(image)==0:
            raise RuntimeError("Features: should not get here!")
        
        return result
    
