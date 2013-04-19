from ilastik.plugins import ObjectFeaturesPlugin
from ilastik.applets.objectExtraction.opObjectExtraction import make_bboxes, max_margin
import vigra
import numpy as np
from lazyflow.request import Request, RequestPool

def cleanup_key(k):
    return k.replace(' ', '')

def cleanup_value(val, hasZero, isGlobal):
    """ensure that the value is a numpy array with the correct shape."""
    val = np.asarray(val)

    if val.ndim == 0:
        val = val.reshape(1, 1)

    if val.ndim == 1:
        if isGlobal:
            val = val.reshape(-1, 1)
        else:
            if hasZero:
                val = val.reshape(-1, 1)
                assert val.shape == (2, 1)
            else:
                val = val.reshape(1, -1)

    if val.ndim > 2:
        val = val.reshape(val.shape[0], -1)

    if hasZero and val.shape[0] > 1:
        val = val[1:]
    return val

def cleanup(d, hasZero, isGlobal, features):
    result = dict((cleanup_key(k), cleanup_value(v, hasZero, isGlobal)) for k, v in d.iteritems())
    newkeys = set(result.keys()) & set(features)
    return dict((k, result[k]) for k in newkeys)

class VigraObjFeats(ObjectFeaturesPlugin):
    # features not in this list are assumed to be local.
    local_features = set(["Mean", "Variance", "Skewness", \
                          "Kurtosis", "Histogram", \
                          "Covariance", "Minimum", "Maximum"])
    suffix = " in neighborhood" #note the space in front, it's important

    def availableFeatures(self, image, labels):
        names = vigra.analysis.supportedRegionFeatures(image, labels)
        names = list(f.replace(' ', '') for f in names)
        local = set(names) & self.local_features
        names.extend([x+self.suffix for x in local])
        result = dict((n, {}) for n in names)
        for f, v in result.iteritems():
            if self.suffix in f:
                v['margin'] = 0
        return result

    def _do_4d(self, image, labels, features, axes):
        image = np.asarray(image, dtype=np.float32)
        labels = np.asarray(labels, dtype=np.uint32)
        result = vigra.analysis.extractRegionFeatures(image, labels, features, ignoreLabel=0)
        return cleanup(result, 0 in labels, True, features)

    def compute_global(self, image, labels, features, axes):
        features = features.keys()
        local = [x+self.suffix for x in self.local_features]
        features = list(set(features) - set(local))
        return self._do_4d(image, labels, features, axes)

    def compute_local(self, image, binary_bbox, features, axes):
        """helper that deals with individual objects"""
        margin = max_margin({'': features})
        features = features.keys()
        local = [x+self.suffix for x in self.local_features]
        features = list(set(features) & set(local))
        features = [x.split(' ')[0] for x in features]
        results = []
        #FIXME: this is done globally as if all the features have the same margin
        #we should group features by their margins
        passed, excl = make_bboxes(binary_bbox, margin)
        for label, suffix in zip([passed, excl],
                                 ['_incl', '_excl']):
            result = self._do_4d(image, label, features, axes)
            results.append(self.update_keys(result, suffix=suffix))
        return self.combine_dicts(results)
