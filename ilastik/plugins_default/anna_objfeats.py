from ilastik.plugins import ObjectFeaturesPlugin
from ilastik.applets.objectExtraction.opObjectExtraction import make_bboxes, max_margin
import vigra
import numpy as np

class AnnaObjFeats(ObjectFeaturesPlugin):
    all_features = ['bad_slices', 'lbp', 'lapl']

    def availableFeatures(self, image, labels):
        return dict((f, {'margin' : 0}) for f in self.all_features)

    def badslices(self, image, label_bboxes, axes):
        rawbbox = image

        #compute the quality score of an object -
        #count the number of fully black slices inside its bbox
        #FIXME: the interpolation part is not tested at all...
        nbadslices = 0
        badslices = []
        area = rawbbox.shape[axes.x] * rawbbox.shape[axes.y]
        bboxkey = [slice(None)] * 3
        for iz in range(image.shape[axes.z]):
            bboxkey[axes.z] = iz
            nblack = np.sum(rawbbox[tuple(bboxkey)]==0)
            if nblack>0.5*area:
                nbadslices = nbadslices + 1
                badslices.append(iz)

        result = {}
        result["bad_slices"] = np.array([nbadslices])
        return result

    def lbp(self, image, label_bboxes, axes):
        rawbbox = image
        ccbboxobject, passed, ccbboxexcl = label_bboxes

        #FIXME: there is a mess about which of the lbp features are computed (obj, excl or incl)
        import skimage.feature as ft
        P=8
        R=1
        lbp_total = np.zeros(passed.shape)
        for iz in range(image.shape[axes.z]):
            #an lbp image
            bboxkey = [slice(None)] * 3
            bboxkey[axes.z] = iz
            bboxkey = tuple(bboxkey)
            lbp_total[bboxkey] = ft.local_binary_pattern(rawbbox[bboxkey], P, R, "uniform")
        #extract relevant parts
        lbp_incl = lbp_total[passed]
        lbp_excl = lbp_total[ccbboxexcl.astype(bool)]
        lbp_obj = lbp_total[ccbboxobject.astype(bool)]
        lbp_hist_incl, _ = np.histogram(lbp_incl, normed=True, bins=(P + 2), range=(0, P + 2))
        lbp_hist_excl, _ = np.histogram(lbp_excl, normed=True, bins=(P + 2), range=(0, P + 2))
        lbp_hist_obj, _ = np.histogram(lbp_obj, normed=True, bins=(P + 2), range=(0, P + 2))

        result = {}
        result["lbp_incl"] = lbp_hist_incl
        result["lbp_excl"] = lbp_hist_excl
        result["lbp"] = lbp_hist_obj
        return result

    def lapl(self, image, label_bboxes, axes):
        rawbbox = image
        ccbboxobject, passed, ccbboxexcl = label_bboxes

        #compute mean and variance of laplacian in the object and its neighborhood
        lapl = None
        result = {}
        try:
            lapl = vigra.filters.laplacianOfGaussian(rawbbox)
        except RuntimeError:
            #kernel longer than line. who cares?
            result["lapl_incl"] = None
            result["lapl_excl"] = None
            result["lapl"] = None
        else:
            lapl_incl = lapl[passed]
            lapl_excl = lapl[ccbboxexcl.astype(bool)]
            lapl_obj = lapl[ccbboxobject.astype(bool)]
            lapl_mean_incl = np.mean(lapl_incl)
            lapl_var_incl = np.var(lapl_incl)
            lapl_mean_excl = np.mean(lapl_excl)
            lapl_var_excl = np.var(lapl_excl)
            lapl_mean_obj = np.mean(lapl_obj)
            lapl_var_obj = np.var(lapl_obj)
            result["lapl_incl"] = np.array([lapl_mean_incl, lapl_var_incl])
            result["lapl_excl"] = np.array([lapl_mean_excl, lapl_var_excl])
            result["lapl"] = np.array([lapl_mean_obj, lapl_var_obj])
        return result

    def _do_3d(self, image, label_bboxes, features, axes):
        kwargs = locals()
        del kwargs['self']
        del kwargs['features']
        kwargs['label_bboxes'] = kwargs.pop('label_bboxes')
        results = []
        features = features.keys()
        if 'bad_slices' in features:
            results.append(self.badslices(**kwargs))
        if 'lbp' in features:
            results.append(self.lbp(**kwargs))
        if 'lapl' in features:
            results.append(self.lapl(**kwargs))
        return self.combine_dicts(results)

    def compute_local(self, image, binary_bbox, features, axes):
        margin = max_margin({'': features})
        passed, excl = make_bboxes(binary_bbox, margin)
        return self.do_channels(self._do_3d, image,
                                label_bboxes=[binary_bbox, passed, excl],
                                features=features, axes=axes)