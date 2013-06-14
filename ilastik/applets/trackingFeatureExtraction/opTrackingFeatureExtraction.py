import numpy
import h5py
import vigra.analysis
import math
import pgmlink

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import SubRegion, List
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction    ,\
    default_features_key
from ilastik.applets.objectExtraction import config, opObjectExtraction



class OpTrackingFeatureExtraction(OpObjectExtraction):
    name = "Tracking Feature Extraction"

    TranslationVectors = InputSlot(optional=True)
    
    RegionFeaturesVigra = OutputSlot()
        
    def __init__(self, parent):
        super(OpTrackingFeatureExtraction, self).__init__(parent)
                
#        vigra_features = ['Count', 'RegionCenter', 'Mean', 'Variance' ] #, 'Coord<ValueList>', 'RegionRadii']
#        for name in vigra_features:
#            if name not in opObjectExtraction.default_features:
#                opObjectExtraction.default_features.append(name)        
            
        self.RegionFeaturesVigra.connect(self._opRegFeats.Output)
        
#        self.RegionFeatures.disconnect()
        self._opRegFeatsAdaptOutput.Input.disconnect()
        self.BlockwiseRegionFeatures.disconnect()
        self.ComputedFeatureNames.disconnect()
        
        self._opCellFeats = OpCellFeatures(parent=self)
        self._opCellFeats.LabelImage.connect(self.LabelImage)
        self._opCellFeats.RawImage.connect(self.RawImage)
        self._opCellFeats.TranslationVectors.connect(self.TranslationVectors)
        self._opCellFeats.RegionFeaturesVigra.connect(self.RegionFeaturesVigra)
        self._opCellFeats.Features.connect(self.Features)
        
#        self.RegionFeatures.connect(self._opCellFeats.RegionFeaturesExtended)
        self._opRegFeatsAdaptOutput.Input.connect(self._opCellFeats.RegionFeaturesExtended)
        self.BlockwiseRegionFeatures.connect(self._opCellFeats.RegionFeaturesExtended)
        self.ComputedFeatureNames.connect(self._opCellFeats.ComputedFeatureNames)        
        
    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here."

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.TranslationVectors:
            self.RegionFeatures.setDirty(slice(None))        



class OpCellFeatures(Operator):
    name = "Cell Features"
    
    LabelImage = InputSlot()
    RawImage = InputSlot()    
    RegionFeaturesVigra = InputSlot()
    TranslationVectors = InputSlot(optional=True)
    Features = InputSlot(rtype=List, stype=Opaque, value={})
        
    RegionFeaturesExtended = OutputSlot()
    ComputedFeatureNames =  OutputSlot(rtype=List, stype=Opaque)
    
    divisionFeatures = ['SquaredDistance%02d', 'AngleDaughters', 'ChildrenSizeRatio',\
                         'SquaredDistanceRatio', 'ParentChildrenSizeRatio', \
                         'ChildrenMeanRatio', 'ParentChildrenMeanRatio']
    cellClassificationFeatures = ['GMM_BIC']
    
    ndim = None
    numNeighbors = 2
    templateSize = 30  # window in which we look for neighboring labels in the next time steps
    size_filter_from_divfeat = 5
    with_uncorrected_features = True # plain features
    with_corrected_features = True  # the region centers are corrected by translation vector
    with_cell_classification_features = False # features for cell classification
    defaultSquaredDistance = 1000
    size_filter_from_cellfeat = 20
    bic_regularization = 0.05   
    
    transl_corr_suffix = "_corr"    
    
    def __init__(self, parent):
        super(OpCellFeatures,self).__init__(parent=parent)
        self._cache = {}
        self.fixed = False
        
    def setupOutputs(self):
        self.RegionFeaturesExtended.meta.assignFrom(self.RegionFeaturesVigra.meta)        
        if self.with_corrected_features and not self.TranslationVectors.ready():
            raise Exception("TranslationVectors slot is not ready, cannot compute translation corrected features")        

        
    def propagateDirty(self, slot, subindex, roi):
        if slot is self.TranslationVectors:
            self.RegionFeaturesExtended.setDirty([])
                        
    def execute(self, slot, subindex, roi, result):
        if slot == self.ComputedFeatureNames:
            computed_features = {}
            if self.Features.ready():
                computed_features = self.Features.get([]).wait()
            computed_features[config.features_division_detection_name] = { name: {} for name in config.selected_features_division_detection[config.features_division_detection_name] }
            computed_features[config.features_cell_classification_name] = { name: {} for name in config.selected_features_cell_classification[config.features_cell_classification_name] }
            return computed_features                    

        if slot == self.RegionFeaturesExtended:                
            assert roi.stop[0] - roi.start[0] == 1, "this operator is only implemented for singleton rois, roi = " + str(roi)
            
            t = roi.start[0]
            
            if t in self._cache:
                # FIXME: if features have changed, they may not be in the cache.
                feats_at = self._cache[t]
            elif self.fixed:
                feats_at = dict((f, numpy.asarray([[]])) for f in self.features)
            else:
                print 'Extracting Division Features at t=%d' % t
                
                feats_at = {}
                lshape = self.LabelImage.meta.shape                
                
                roi_cur = SubRegion(roi.slot, [t], [t+1])                
                region_feats_cur = self.RegionFeaturesVigra.get(roi_cur).wait()[0]
                
#                for plugin_name in region_feats_cur.keys():
#                    if plugin_name != self.vigra_feature_plugin_name:
#                        feats_at[plugin_name] = region_feats_cur[plugin_name]
#                        continue
                                        
#                    feats_at_plugin = {}
                
#                for name in region_feats_cur[plugin_name].keys():                        
#                    feats_at_plugin[name] = region_feats_cur[plugin_name][name]
                
                feats_vigra_cur = region_feats_cur[config.features_vigra_name]
                feats_cell_class = {}
                feats_cell_div = {}
                                
                if self.with_corrected_features:
                    name = 'RegionCenter'+self.transl_corr_suffix
                    feats_vigra_cur[name] = numpy.zeros(feats_vigra_cur['RegionCenter'].shape)
                    
                    for label in range(1,feats_vigra_cur['RegionCenter'].shape[0]):
                        coord = feats_vigra_cur['RegionCenter'][label]
                        coord_rounded = [int(round(x)) for x in coord]
                        coord_rounded_end = [x+1 for x in coord_rounded]
                        coord_roi = SubRegion(self.TranslationVectors, 
                                             start=[t,] + coord_rounded + [0,],
                                             stop=[t+1,] + coord_rounded_end + [3,])
                        translation = self.TranslationVectors.get(coord_roi).wait().flatten() 
                        feats_vigra_cur[name][label] = coord + translation
                    
                num = feats_vigra_cur['RegionCenter'].shape[0]
                
                for n in range(self.numNeighbors):
                    if 'SquaredDistance%02d' in self.divisionFeatures:                            
                        name = 'SquaredDistance%02d' % n   
                        self.divisionFeatures.append(name)
                        if n == self.numNeighbors - 1:
                            self.divisionFeatures.remove('SquaredDistance%02d')
                    name = 'SquaredDistance%02d' % n
                    if self.with_uncorrected_features:
                        feats_cell_div[name] = numpy.ones([num,1]) * self.defaultSquaredDistance
                    if self.with_corrected_features:
                        feats_cell_div[name+self.transl_corr_suffix] = numpy.ones([num,1]) * self.defaultSquaredDistance
                
                for name in self.divisionFeatures:
                    if self.with_uncorrected_features:
                        feats_cell_div[name] = numpy.zeros([num,1])
                    if self.with_corrected_features:     
                        feats_cell_div[name+self.transl_corr_suffix] = numpy.zeros([num,1])
                
                if self.with_cell_classification_features:
                    if self.ndim is None:
                        ndim = 2
                        for rc in feats_vigra_cur['RegionCenter']:
                            if rc[2] != 0:
                                ndim = 3
                                break
                        self.ndim = ndim
                    for name in self.cellClassificationFeatures:
                        feats_cell_class[name] = numpy.zeros([num,config.num_max_objects])
                    
                if t < self.LabelImage.meta.shape[0] - 1:
                    roi_next = SubRegion(roi.slot, [t+1], [t+2])
                    feats_vigra_next = self.RegionFeaturesVigra.get(roi_next).wait()[0][config.features_vigra_name]

                    tcroi_next = SubRegion(self.LabelImage,
                                      start = [t+1,] + (len(lshape) - 1) * [0,],
                                      stop = [t+2,] + list(lshape[1:]))

                    image_next = self.RawImage.get(tcroi_next).wait()
                    axiskeys = self.RawImage.meta.getTaggedShape().keys()
                    assert axiskeys == list('txyzc'), "FIXME: OpRegionFeatures requires txyzc input data."
                    image_next = image_next[0,...,0] # assumes t,x,y,z,c

                    labels_next = self.LabelImage.get(tcroi_next).wait()
                    axiskeys = self.LabelImage.meta.getTaggedShape().keys()
                    assert axiskeys == list('txyzc'), "FIXME: OpRegionFeatures requires txyzc input data."
                    labels_next = labels_next[0,...,0] # assumes t,x,y,z,c
                else:
                    feats_vigra_next = None
                    labels_next = None
                    
                                     
                if self.with_uncorrected_features:
                    self.extractDivisionFeatures(feats_cell_div, feats_vigra_cur, feats_vigra_next, labels_next, self.divisionFeatures, 
                                                 numNeighbors=self.numNeighbors, size_filter_from=self.size_filter_from_divfeat,
                                                 suffix='')
                
                if self.with_corrected_features:
                    self.extractDivisionFeatures(feats_cell_div, feats_vigra_cur, feats_vigra_next, labels_next, self.divisionFeatures, 
                                                 numNeighbors=self.numNeighbors, size_filter_from=self.size_filter_from_divfeat,                                                         
                                                 suffix=self.transl_corr_suffix)
                
                if self.with_cell_classification_features:
                    self.extractCellClassificationFeatures(feats_cell_class, feats_vigra_cur, self.cellClassificationFeatures, self.ndim, 
                                                           size_filter_from=self.size_filter_from_cellfeat, regularization_parameter=self.bic_regularization)
                        
                feats_at[config.features_cell_classification_name] = feats_cell_class    
                feats_at[config.features_division_detection_name] = feats_cell_div
                feats_at[config.features_vigra_name] = feats_vigra_cur
                feats_at[default_features_key] = region_feats_cur[default_features_key]
    
                self._cache[t] = feats_at                
                self.RegionFeaturesExtended._sig_value_changed()
                
                
            result[0] = feats_at
        
        self.ComputedFeatureNames.setDirty([])
        
        return result     
    
    @staticmethod
    def gmm_num_parameters(gmm):
        """Return the number of free parameters in the gmm model."""
        ndim = gmm.means.shape[1]
        if gmm.cvtype == 'full':
            cov_params = gmm.n_components * ndim * (ndim + 1) / 2.
        elif gmm.cvtype == 'diag':
            cov_params = gmm.n_components * ndim
        elif gmm.cvtype == 'tied':
            cov_params = ndim * (ndim + 1) / 2.
        elif gmm.cvtype == 'spherical':
            cov_params = gmm.n_components
        mean_params = ndim * gmm.n_components
        return int(cov_params + mean_params + gmm.n_components - 1)
        
    def gmm_bic(self, gmm, data):
        return (-2 * gmm.score(data).sum() + self.gmm_num_parameters(gmm) * numpy.log(data.shape[0]))
    
    def gmm_bic_mod(self, gmm, data, reg_par, k):
        return (gmm.score(data).sum() - reg_par * k)
    
    def gmm_aic(self, gmm, data):
        return - 2 * gmm.score(data).sum() + 2 * self.gmm_num_parameters(gmm) 
    
    def extractCellClassificationFeatures(self, feats_cell_class_cur, feats_vigra_cur, featurenames, ndim, size_filter_from=4,regularization_parameter = 0.1):
        ''' adds cell classification features to feats_at_cur '''
        
        from sklearn import mixture, cluster

        for label_cur, vals in enumerate(feats_vigra_cur['Coord<ValueList >']):
            if label_cur == 0:
                continue
            
            if 'GMM_BIC' in featurenames: 
                size = feats_vigra_cur['Count'][label_cur]
                
                if size <= size_filter_from:
                    bic_score_list = [0 for ii in range(ndim)]
                else:
                    #### PGMLINK implementation
#                    data = pgmlink.feature_array()
#                    for el in vals:
#                        for i in range(ndim):                         
#                            data.push_back(float(el[i]))
#                    
#                    bic_scores = pgmlink.feature_array()
#                    cluster_centers = pgmlink.feature_array()
#                    try: 
#                        pgmlink.gmm_priors_and_centers(data, bic_scores, cluster_centers, config.num_max_objects, ndim, regularization_parameter)
#                    except:
#                        print 'WARNING: GMM computation threw exception, setting BIC = (0,..,0)'
#                        bic_scores = [ 0 for ii in range(ndim) ]
#                    bic_score_list = []
#                    for b in bic_scores:
#                        bic_score_list.append(b)
#                    ###################
                
                
#                    ##### scikit-learn implementation
#                    dim_maxs = []
#                    dim_mins = []
#                    for d in range(ndim):
#                        dim_maxs.append({})
#                        dim_mins.append({})
#                        
#                        for d_other in range(ndim):
#                            if d == d_other:
#                                continue
#                            
#                            if v > dim_maxs[d]:
#                                dim_maxs[d] = v
#                            if v < dim_mins[d]:
#                                dim_mins[d] = v 
                            
                        
                    
                    bic_score_list = []
                    for k in range(1,config.num_max_objects+1):
                        g = mixture.GMM(n_components=k)
#                        g = cluster.KMeans(k=k)
                        
                        g.fit(vals[:,:2])
#                        bic_score_list.append(self.gmm_bic_mod(g,vals[:,:ndim],0.1,k))
                        bic_score_list.append(self.gmm_bic(g,vals[:,:ndim]))
#                        bic_score_list.append(g.score(vals[:,:2]).sum() / vals.shape[0])
#                    print 'scikit BIC = ', bic_score_list
                    ####################
                
                
                
                s = float(sum(bic_score_list))
                if s == 0:
                    for idx,b in enumerate(bic_score_list):
                        bic_score_list[idx] = 1./len(bic_score_list)
                else:            
                    for idx,b in enumerate(bic_score_list):
                        bic_score_list[idx] = b/s
                
                feats_cell_class_cur['GMM_BIC'][label_cur] = numpy.array(bic_score_list)
#                print 'GMM_BIC(',label_cur,') =', numpy.array(bic_score_list)
            
    
    def extractDivisionFeatures(self, feats_div_cur, feats_vigra_cur, feats_vigra_next, img_at_next, divFeatures, 
                                numNeighbors = 3, size_filter_from = 4, 
                                suffix=''):
        ''' adds division features to feats_at_cur '''
        #calculate cell division features according to the voxel scale   
        try:
            scale = config.image_scale
        except:
            scale = [1.0,1.0,1.0]
            print 'no scale given, using the default one'
            
        for label_cur, com_cur in enumerate(feats_vigra_cur['RegionCenter' + suffix]):
            if label_cur == 0:
                continue
            
            coms_next = {}
            sizes_next_all = {}
            labels_next = []  
            
            if feats_vigra_next is not None and img_at_next is not None:
                idx_cur = [round(x) for x in com_cur]
                
                roi = []
                for idx,coord in enumerate(idx_cur):
                    start = max(coord - self.templateSize/2, 0)
                    stop = min(coord + self.templateSize/2, img_at_next.shape[idx])
                    roi.append(slice(start,stop))
                
                
                # find all coms in the neighborhood of com_cur
                subimg_next = img_at_next[roi]
                labels_next = numpy.unique(subimg_next)
                  
                for l in labels_next:
                    if l != 0:
                        coms_next[l] = feats_vigra_next['RegionCenter'][l]
                        sizes_next_all[l] = feats_vigra_next['Count'][l]            
                
                        
            sqDist = self.getSquaredDistances(com_cur, coms_next, sizes_next_all, numNeighbors, size_filter_from, scale)
            coms_next_reduced = {}
            labels_next_reduced = []
            for idx,row in enumerate(sqDist):
                l = row[0]
                dist = row[1]
                name = 'SquaredDistance%02d' % idx
                if name in divFeatures:
                    feats_div_cur[name+suffix][label_cur][0] = dist
                coms_next_reduced[l] = coms_next[l]
                labels_next_reduced.append(l)
            
            if 'AngleDaughters' in divFeatures:
                feats_div_cur['AngleDaughters'+suffix][label_cur][0] = self.getMaxAngle(com_cur, coms_next_reduced, scale)     
            
            if 'ChildrenSizeRatio' in divFeatures:
                sizes_next = []
                for label in coms_next_reduced.keys(): 
                    sizes_next.append(feats_vigra_next['Count'][label])
                feats_div_cur['ChildrenSizeRatio'+suffix][label_cur][0] = self.getChildrenSizeRatio(sizes_next)
            
            if 'SquaredDistanceRatio' in divFeatures:
                feats_div_cur['SquaredDistanceRatio'+suffix][label_cur][0] = self.getSquaredDistanceRatio(sqDist)
            
            if 'ParentChildrenSizeRatio' in divFeatures:
                size_cur = feats_vigra_cur['Count'][label_cur]
                feats_div_cur['ParentChildrenSizeRatio'+suffix][label_cur][0] = self.getParentChildrenSizeRatio(size_cur, sizes_next)
    
            means_next = []
            for l in labels_next_reduced:
                means_next.append(feats_vigra_next['Mean'][l])
            
            mean_cur = feats_vigra_cur['Mean'][label_cur]
                
            if 'ChildrenMeanRatio' in divFeatures:
                feats_div_cur['ChildrenMeanRatio'+suffix][label_cur][0] = self.getChildrenMeanRatio(means_next)
            
            if 'ParentChildrenMeanRatio' in divFeatures:
                feats_div_cur['ParentChildrenMeanRatio'+suffix][label_cur][0] = self.getParentChildrenMeanRatio(mean_cur, means_next)
                
                
    def dotproduct(self, v1, v2):
        return sum((a*b) for a, b in zip(v1, v2))
    
    def length(self, v):
        return math.sqrt(self.dotproduct(v, v))
    
    def angle(self, v1, v2):
        try:
            radians = math.acos(self.dotproduct(v1, v2) / (self.length(v1) * self.length(v2)))
        except Exception as e:
            print str(e), ': math.acos(', self.dotproduct(v1, v2) / (self.length(v1) * self.length(v2)), '), v1 =', v1, ', v2 =', v2
             radians = 0
        return (radians*180)/math.pi
  
  
    def getMaxAngle(self, com_cur, coms_next, scale = [1.0,1.0,1.0], default_value=[0]):
        ''' returns the maximum angle between two potential children '''        
        angles = []
        for idx, key1 in enumerate(sorted(coms_next.keys())):
            com1 = coms_next[key1]
            v1 = (com1 - com_cur) * scale
            for key2 in sorted(coms_next.keys())[idx+1:]:
                com2 = coms_next[key2]                
                v2 = (com2 - com_cur) * scale               
                ang = self.angle(v1,v2)
                if ang > 180:
                    assert ang<=360.01, "the angle must be smaller than 360 degrees"
                    ang = 360-ang
                angles.append(ang)
                    
        if len(angles) == 0:
            angles = default_value
        
#        print 'max(angles) =', max(angles)
        return max(angles)

    
    def getSquaredDistances(self, com_cur, coms_next, sizes_next = None, 
                            num_best = 3, size_filter_from = 4, scale = [1.0,1.0,1.0], default_value = []):
        ''' returns the squared distances to the objects in the neighborhood of com_curr '''  
        squaredDistances = []
        
        for label_next in coms_next.keys():
            if sizes_next is not None and sizes_next[label_next] >= size_filter_from:
                dist = numpy.linalg.norm((coms_next[label_next] - com_cur) * scale)
                squaredDistances.append([label_next,dist])
        
        squaredDistances = numpy.array(squaredDistances)
        # sort the array in the second column in ascending order
        squaredDistances = numpy.array(sorted(squaredDistances, key=lambda a_entry: a_entry[1]))        
        if num_best > squaredDistances.shape[0]:
            num_best = squaredDistances.shape[0]
        
        if len(squaredDistances) == 0:
            return default_value
        
        return squaredDistances[0:num_best,:]
        
    
    def getChildrenSizeRatio(self, sizes_next, default_value=0.):
        size_ratios = []
        for idx, size1 in enumerate(sizes_next):
            for size2 in sizes_next[idx+1:]:
                ratio = float(size1)/size2                
                if ratio > 1:
                    ratio = 1./ratio
                if math.isnan(ratio):
                    ratio = default_value
                size_ratios.append(ratio)
        if len(size_ratios) == 0:
            size_ratios.append(default_value)
        
#        print 'childrenSizeRatio = ', max(size_ratios)
        return max(size_ratios)
    
    def getSquaredDistanceRatio(self, squaredDistancesSorted, default_value = 0.):
        if len(squaredDistancesSorted) < 2:
            return default_value
        dist1 = squaredDistancesSorted[0][1]
        dist2 = squaredDistancesSorted[1][1]                
        
        ratio = float(dist1)/dist2                                    
        if math.isnan(ratio):
            return default_value
        assert ratio <= 1, "the squared distances are not sorted"
                            
        return ratio

    def getParentChildrenSizeRatio(self, size_cur, sizes_next, default_value = 0):
        if len(sizes_next) < 2:
            return default_value
        result = float(size_cur) / (sizes_next[0] + sizes_next[1])
        if math.isnan(result):
            return default_value
        return result 
        
    def getChildrenMeanRatio(self, means_next, default_value = 0):
        if len(means_next) < 2:
            return default_value
        ratio = means_next[0] / float(means_next[1])
        if math.isnan(ratio):
            return default_value
        if ratio > 1 and ratio != 0:
            return 1./ratio
        return ratio

    def getParentChildrenMeanRatio(self, mean_cur, means_next, default_value = 0.):
        if len(means_next) == 0:
            return default_value
        ratios = []
        abs_max_idx = 0
        abs_max = 0
        for idx,m_n in enumerate(means_next):
            r = mean_cur / float(m_n)
            if math.isnan(r):
                r = default_value       
            r = r-1  # shift ratio to 0            
            ratios.append(r)
            if numpy.abs(r) > abs_max:
                abs_max_idx = idx
                abs_max = r
                
        return ratios[abs_max_idx]
    
    
