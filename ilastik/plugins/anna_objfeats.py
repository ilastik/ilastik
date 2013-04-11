from ilastik.plugins import ObjectFeaturesPlugin
import vigra
import numpy as np

class AnnaObjFeats(ObjectFeaturesPlugin):
    all_features = ['bad_slices', 'lbp', 'lapl']

    def availableFeatures(self, image, labels):
        return self.all_features

    def badslices(self, image, label_bboxes, axes, mins, maxs):
        rawbbox = image

        #compute the quality score of an object -
        #count the number of fully black slices inside its bbox
        #FIXME: the interpolation part is not tested at all...
        nbadslices = 0
        badslices = []
        area = rawbbox.shape[axes.x] * rawbbox.shape[axes.y]
        bboxkey = [slice(None)] * 3
        for iz in range(maxs.z - mins.z):
            bboxkey[axes.z] = iz
            nblack = np.sum(rawbbox[tuple(bboxkey)]==0)
            if nblack>0.5*area:
                nbadslices = nbadslices + 1
                badslices.append(iz)

        #interpolate the raw data
        imagekey = [slice(None)] * 3
        imagekey[axes.x] = slice(mins.x, maxs.x, None)
        imagekey[axes.y] = slice(mins.y, maxs.y, None)
        try:
            for sl in badslices:
                if sl==0:
                    if mins.z==0:
                        continue
                    slprev=mins.z
                    slprevsum = area
                    while slprevsum>0.5*area and slprev>0:
                        slprev = slprev - 1
                        imagekey[axes.z]=slprev
                        slprevsum = np.sum(image[tuple(imagekey)])
                else:
                    slprev = sl + mins.z
                    while slprev - mins.z in badslices and slprev>=0:
                        slprev = slprev - 1

                if sl == maxs.z - 1:
                    if sl==image.shape[axes.z]-1:
                        continue
                    slnext = maxs.z - 1
                    slnextsum = area
                    while slnextsum>0.5*area and slnext<image.shape[axes.z]-1:
                        slnext = slnext + 1
                        imagekey[axes.z] = slnext
                        slnextsum = np.sum(image[tuple(imagekey)])
                else:
                    slnext = sl + mins.z
                    while slnext - mins.z in badslices and slnext<maxs.z:
                        slnext = slnext + 1

                interval = slnext - slprev

                weightnext = float(slnext - sl) / interval
                weightprev = float(sl - slprev) / interval
                bboxkey[axes.z] = sl
                keycurrent = tuple(bboxkey)
                imagekey[axes.z] = slprev
                keyprev = tuple(imagekey)
                imagekey[axes.z] = slnext
                keynext = tuple(imagekey)
                rawbbox[keycurrent] = weightnext * image[keynext] + weightprev * image[keyprev]
        except:
            #interpolation didn't work. just go on.
            print "interpolation failed"
        result = {}
        result["bad_slices"] = np.array([nbadslices])
        return result

    def lbp(self, image, label_bboxes, axes, mins, maxs):
        rawbbox = image
        ccbboxobject, passed, ccbboxexcl = label_bboxes

        #FIXME: there is a mess about which of the lbp features are computed (obj, excl or incl)
        import skimage.feature as ft
        P=8
        R=1
        lbp_total = np.zeros(passed.shape)
        for iz in range(maxs.z - mins.z):
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

    def lapl(self, image, label_bboxes, axes, mins, maxs):
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

    def _do_3d(self, image, label_bboxes, features, axes, mins, maxs):
        kwargs = locals()
        del kwargs['self']
        del kwargs['features']
        results = []
        if 'bad_slices' in features:
            results.append(self.badslices(**kwargs))
        if 'lbp' in features:
            results.append(self.lbp(**kwargs))
        if 'lapl' in features:
            results.append(self.lapl(**kwargs))

        return self.combine_dicts(results)

    def compute_local(self, image, label_bboxes, features, axes, mins, maxs):
        return self.do_channels(image, label_bboxes, features, axes, self._do_3d, mins=mins, maxs=maxs)