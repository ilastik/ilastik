from ilastik.plugins import ObjectFeaturesPlugin
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
    newkeys = set(result.keys()).intersection(set(features))
    return dict((k, result[k]) for k in newkeys)

class VigraObjFeats(ObjectFeaturesPlugin):
    # features not in this list are assumed to be local.
    global_features = set(["RegionAxes",
                           "RegionRadii",
                           "Coord<ArgMaxWeight>",
                           "Coord<ArgMinWeight>"])

    # these features should not be presented to the user, since they
    # are not useful for prediction.
    # FIXME: add others to this list.
    excluded_features = set(['RegionCenter',
                             'Coord<Minimum>',
                             'Coord<Maximum>',
                             ])

    def availableFeatures(self):
        names = vigra.analysis.supportedRegionFeatures(np.zeros((3, 3), dtype=np.float32),
                                                       np.zeros((3, 3), dtype=np.uint32))
        names = list(f.replace(' ', '') for f in names)
        names = set(names).difference(self.excluded_features)
        return names

    def _do_3d(self, image, labels, features, axes, *args, **kwargs):
        image = np.asarray(image, dtype=np.float32)
        labels = np.asarray(labels, dtype=np.uint32)
        result = vigra.analysis.extractRegionFeatures(image, labels, features, ignoreLabel=0,
                                                      histogramRange=[0, 255], binCount=10)
        return cleanup(result, 0 in labels, True, features)

    def compute_global(self, image, labels, features, axes):
        features = list(set(features).intersection(self.global_features))
        return self.do_channels(image, labels, features, axes, self._do_3d)

    def compute_local(self, image, label_bboxes, features, axes, mins, maxs):
        features = list(set(features).difference(self.global_features))
        return self.do_channels_local(image, label_bboxes, features, axes,
                                      mins, maxs, self._do_3d)
