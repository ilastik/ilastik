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
    
