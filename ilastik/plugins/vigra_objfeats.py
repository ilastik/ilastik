from ilastik.plugins import ObjectFeaturesPlugin
import vigra
import numpy as np
from lazyflow.request import Request, RequestPool
from functools import partial

def update_keys(d, prefix=None, suffix=None):
    if prefix is None:
        prefix = ''
    if suffix is None:
        suffix = ''
    return dict((prefix + k + suffix, v) for k, v in d.items())

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

    def execute(self, image, labels, features):
        features = list(set(features).intersection(self.global_features))
        result = vigra.analysis.extractRegionFeatures(image, labels, features, ignoreLabel=0)
        return cleanup(result, 0 in labels, True, features)

    def execute_local(self, image, features, axes, min_xyz, max_xyz,
                      rawbbox, passed, ccbboxexcl, ccbboxobject):
        features = list(set(features).difference(self.global_features))
        labeled_bboxes = [passed, ccbboxexcl, ccbboxobject]
        feats = [None, None, None]
        pool = RequestPool()
        rawbbox = np.asarray(rawbbox, dtype=np.float32)
        labeled_bboxes = list(np.asarray(bbox, dtype=np.uint32) for bbox in labeled_bboxes)
        for ibox, bbox in enumerate(labeled_bboxes):
            def extractObjectFeatures(ibox):
                feats[ibox] = vigra.analysis.extractRegionFeatures(rawbbox,
                                                                   bbox,
                                                                   features,
                                                                   histogramRange=[0, 255],
                                                                   binCount = 10,
                                                                   ignoreLabel=0)
            req = pool.request(partial(extractObjectFeatures, ibox))
        pool.wait()

        result = {}
        feats[0] = update_keys(feats[0], suffix='_incl')
        feats[1] = update_keys(feats[1], suffix='_excl')

        feats = list(cleanup(f, 0 in labels, False, features) for f, labels in zip(feats, labeled_bboxes))
        return dict(sum((d.items() for d in feats), []))
