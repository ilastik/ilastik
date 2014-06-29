from ilastik.plugins import ObjectFeaturesPlugin
import ilastik.applets.objectExtraction.opObjectExtraction
import vigra
import numpy
from lazyflow.operators.opInterpMissingData import OpDetectMissing
from lazyflow.graph import Graph

class ExampleObjFeats(ObjectFeaturesPlugin):
    all_features = ['lbp', 'radii_ratio']
    local_features = ['lbp', 'radii_ratio']
    local_suffix = " in neighborhood" #note the space in front, it's important
    local_out_suffixes = [local_suffix, " in object and neighborhood"]

    def availableFeatures(self, image, labels):
        names = self.all_features
        #names.extend([x+self.local_suffix for x in self.local_features])
        
        # we can compute LBPs in the object, in the neighborhood, and in both
        names.extend(["lbp"+x for x in self.local_out_suffixes])
        return dict((f, {'margin' : 0}) for f in names)


    def lbp(self, image, label_bboxes, axes):
        ''' This function computes local binary pattern histograms
            for the object, the neighborhood of the object (without 
            the object itself), and both the object and the neighborhood)
            
            The LBPs are computed via the scikit.image package
        '''
        rawbbox = image
        mask_object, mask_both, mask_neigh = label_bboxes

        import skimage.feature as ft
        P=8
        R=1
        lbp_total = numpy.zeros(mask_both.shape)
        
        #LBPs are inherently 2D. For 3D data, loop over the z slices
        #This function always gets a 3D bounding box, for 2D data
        #the box will have a singleton dimension
        for iz in range(image.shape[axes.z]):
            #an lbp image
            bboxkey = [slice(None)] * 3
            bboxkey[axes.z] = iz
            bboxkey = tuple(bboxkey)
            lbp_total[bboxkey] = ft.local_binary_pattern(rawbbox[bboxkey], P, R, "uniform")
        #extract relevant parts
        lbp_incl = lbp_total[mask_both]
        lbp_excl = lbp_total[mask_neigh.astype(bool)]
        lbp_obj = lbp_total[mask_object.astype(bool)]
        lbp_hist_incl, _ = numpy.histogram(lbp_incl, normed=True, bins=(P + 2), range=(0, P + 2))
        lbp_hist_excl, _ = numpy.histogram(lbp_excl, normed=True, bins=(P + 2), range=(0, P + 2))
        lbp_hist_obj, _ = numpy.histogram(lbp_obj, normed=True, bins=(P + 2), range=(0, P + 2))

        result = {}
        result["lbp"+self.local_out_suffixes[1]] = lbp_hist_incl
        result["lbp"+self.local_out_suffixes[0]] = lbp_hist_excl
        result["lbp"] = lbp_hist_obj
        return result

    def radii_ratio(self, image, label_bboxes, axes):
        ''' This function computes the ratio of the first and last principal radii
            of the object '''
        
        mask_object, mask_both, mask_neigh = label_bboxes
        feats = vigra.analysis.extractRegionFeatures(mask_object.astype(numpy.float32), \
                                                     mask_object.astype(numpy.uint32), \
                                                     features=["RegionAxes", "RegionRadii"])
        rr = feats["RegionRadii"][1]
        result = {}
        result["radii_ratio"]=float(rr[0])/rr[-1]
        return result

    def _do_3d(self, image, label_bboxes, features, axes):
        kwargs = locals()
        del kwargs['self']
        del kwargs['features']
        kwargs['label_bboxes'] = kwargs.pop('label_bboxes')
        results = []
        features = features.keys()
        if 'lbp' in features:
            results.append(self.lbp(**kwargs))
        if 'radii_ratio' in features:
            results.append(self.radii_ratio(**kwargs))
        return self.combine_dicts(results)

    def compute_local(self, image, binary_bbox, features, axes):
        margin = ilastik.applets.objectExtraction.opObjectExtraction.max_margin({'': features})
        passed, excl = ilastik.applets.objectExtraction.opObjectExtraction.make_bboxes(binary_bbox, margin)
        return self.do_channels(self._do_3d, image,
                                label_bboxes=[binary_bbox, passed, excl],
                                features=features, axes=axes)