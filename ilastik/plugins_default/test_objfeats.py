# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

from ilastik.plugins import ObjectFeaturesPlugin
import vigra
import numpy

class TestFeatures(ObjectFeaturesPlugin):

    all_features = {"with_nans" : {},
                    "with_nones" : {}}
    
    def availableFeatures(self, image, labels):
        return self.all_features
    
    def compute_global(self, image, labels, features, axes):
        lmax = numpy.max(labels)
        result = dict()
        result["with_nans"] = numpy.zeros((lmax, 1))
        result["with_nones"] = numpy.zeros((lmax, 1))
        for i in range(lmax):
            if i%3==0:
                result["with_nans"][i]=numpy.NaN
                result["with_nones"][i]=None
            else:
                result["with_nans"][i]=21
                result["with_nones"][i]=42
                
        return result
    
