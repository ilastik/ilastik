from ilastik.plugins import ObjectFeaturesPlugin
import vigra
import numpy as np

class AnnaObjFeats(ObjectFeaturesPlugin):
    all_features = ['bad_slices', 'lbp', 'lapl']

    def availableFeatures(self):
        return self.all_features

    def badslices(self, image, axes, min_xyz, max_xyz, rawbbox,
                  passed, ccbboxexcl, ccbboxobject):
        #compute the quality score of an object -
        #count the number of fully black slices inside its bbox
        #FIXME: the interpolation part is not tested at all...
        xAxis, yAxis, zAxis = axes
        minx, miny, minz = min_xyz
        maxx, maxy, maxz = max_xyz
        nbadslices = 0
        badslices = []
        area = rawbbox.shape[xAxis] * rawbbox.shape[yAxis]
        bboxkey = 3 * [None]
        bboxkey[xAxis] = slice(None, None, None)
        bboxkey[yAxis] = slice(None, None, None)
        for iz in range(maxz - minz):
            bboxkey[zAxis] = iz
            nblack = np.sum(rawbbox[tuple(bboxkey)]==0)
            if nblack>0.5*area:
                nbadslices = nbadslices + 1
                badslices.append(iz)

        #interpolate the raw data
        imagekey = 3*[None]
        imagekey[xAxis] = slice(minx, maxx, None)
        imagekey[yAxis] = slice(miny, maxy, None)
        try:
            for sl in badslices:
                if sl==0:
                    if minz==0:
                        continue
                    slprev=minz
                    slprevsum = area
                    while slprevsum>0.5*area and slprev>0:
                        slprev = slprev - 1
                        imagekey[zAxis]=slprev
                        slprevsum = np.sum(image[tuple(imagekey)])
                else:
                    slprev = sl + minz
                    while slprev - minz in badslices and slprev>=0:
                        slprev = slprev - 1

                if sl == maxz - 1:
                    if sl==image.shape[zAxis]-1:
                        continue
                    slnext = maxz - 1
                    slnextsum = area
                    while slnextsum>0.5*area and slnext<image.shape[zAxis]-1:
                        slnext = slnext + 1
                        imagekey[zAxis] = slnext
                        slnextsum = np.sum(image[tuple(imagekey)])
                else:
                    slnext = sl + minz
                    while slnext - minz in badslices and slnext<maxz:
                        slnext = slnext + 1

                interval = slnext - slprev

                weightnext = float(slnext - sl) / interval
                weightprev = float(sl - slprev) / interval
                bboxkey[zAxis] = sl
                keycurrent = tuple(bboxkey)
                imagekey[zAxis] = slprev
                keyprev = tuple(imagekey)
                imagekey[zAxis] = slnext
                keynext = tuple(imagekey)
                rawbbox[keycurrent] = weightnext * image[keynext] + weightprev * image[keyprev]
        except:
            #interpolation didn't work. just go on.
            print "interpolation failed"
        result = {}
        result["bad_slices"] = np.array([nbadslices])
        return result

    def lbp(self, image, axes, min_xyz, max_xyz, rawbbox, passed,
            ccbboxexcl, ccbboxobject):
        #FIXME: there is a mess about which of the lbp features are computed (obj, excl or incl)
        xAxis, yAxis, zAxis = axes
        minx, miny, minz = min_xyz
        maxx, maxy, maxz = max_xyz
        import skimage.feature as ft
        P=8
        R=1
        lbp_total = np.zeros(passed.shape)
        for iz in range(maxz - minz):
            #an lbp image
            bboxkey = 3 * [None]
            bboxkey[xAxis] = slice(None, None, None)
            bboxkey[yAxis] = slice(None, None, None)
            bboxkey[zAxis] = iz
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

    def lapl(self, image, axes, min_xyz, max_xyz, rawbbox, passed,
             ccbboxexcl, ccbboxobject):
        xAxis, yAxis, zAxis = axes
        minx, miny, minz = min_xyz
        maxx, maxy, maxz = max_xyz
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

    def execute_local(self, image, features, axes, min_xyz, max_xyz,
                      rawbbox, passed, ccbboxexcl, ccbboxobject):
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

        return dict(sum((a.items() for a in results), []))
