import numpy as np
import math

def dotproduct(v1, v2):
    return sum((a*b) for a, b in zip(v1, v2))


def length(v):
    return math.sqrt(dotproduct(v, v))


def angle(v1, v2):
    try:
        if length(v1) * length(v2) == 0:
            radians = 0
        else:
            radians = math.acos(dotproduct(v1, v2) / (length(v1) * length(v2)))
    except Exception as e:
        #print str(e), ': math.acos(', dotproduct(v1, v2) / (length(v1) * length(v2)), '), v1 =', v1, ', v2 =', v2
        radians = 0
    return (radians*180)/math.pi



##### Feature base class #######

class Feature( object ):
    name = 'Feature'
    plugin = 'Tracking Features'
    default_value = 0
    dimensionality = None

    def __init__(self, feats_name, default_value=None, delim='_', scales=[1.0,1.0,1.0], ndim=2, feat_dim=1):
        self.name += str(delim) + str(feats_name)
        self.feats_name = feats_name
        if default_value != None:
            self.default_value = default_value
        self.scales = scales
        self.ndim = ndim
        self.feat_dim = feat_dim

    def compute(self, feats_cur, feats_next, **kwargs):
        raise NotImplementedError('Feature not fully implemented yet.')

    def getName(self):
        return self.name

    def getPlugin(self):
        return self.plugin

    def dim(self):
        return self.dimensionality


class ParentChildrenRatio( Feature ):
    name = 'ParentChildrenRatio'
    dimensionality = 1
    
    def compute(self, feats_cur, feats_next, **kwargs):
        if len(feats_next) < 2:
            return np.array(len(feats_cur) * [self.default_value,])
        result = np.array(feats_cur) / np.array(feats_next[0] + feats_next[1])
        for i in range(len(result)):
            if math.isnan(result[i]):
                result[i] = self.default_value
        return result

    def dim(self):
        return self.dimensionality * self.feat_dim

class ChildrenRatio( Feature ):
    name = 'ChildrenRatio'
    dimensionality = 1

    def compute(self, feats_cur, feats_next, **kwargs):
        if len(feats_next) < 2:
            return np.array(len(feats_cur) * [self.default_value,])
        ratio = np.array(feats_next[0]) / np.array(feats_next[1])
        for i in range(len(ratio)):
            if math.isnan(ratio[i]):
                ratio[i] = self.default_value
            if ratio[i] > 1 and ratio[i] != 0:
                ratio[i] = 1./ratio[i]
        return ratio

    def dim(self):
        return self.dimensionality * self.feat_dim

class SquaredDistances( Feature ):
    name = 'SquaredDistances'

    def compute(self, feats_cur, feats_next, **kwargs):
        return feats_cur

    def dim(self):
        return self.ndim


class ParentChildrenAngle( Feature ):
    name = 'ParentChildrenAngle'
    dimensionality = 1

    def compute(self, feats_cur, feats_next, **kwargs):
        angles = []
        for idx, com1 in enumerate(feats_next):
            v1 = (com1 - feats_cur) * self.scales[0:com1.shape[0]]
            for com2 in feats_next[idx+1:]:
                v2 = (com2 - feats_cur) * self.scales[0:com2.shape[0]]
                ang = angle(v1,v2)
                if ang > 180:
                    assert ang<=360.01, "the angle must be smaller than 360 degrees"
                    ang = 360-ang
                angles.append(ang)

        if len(angles) == 0:
            angles = [self.default_value]

        return max(angles)




class ParentIdentity( Feature ):
    name = ''
    
    def compute(self, feats_cur, feats_next, **kwargs):
        return feats_cur


class FeatureManager( object ):
    
    feature_mappings = {'ParentIdentity': ParentIdentity,
                        'SquaredDistances': SquaredDistances,
                        'ChildrenRatio': ChildrenRatio,
                        'ParentChildrenRatio': ParentChildrenRatio, 
                        'ParentChildrenAngle': ParentChildrenAngle
                        }
                   
    def __init__(self, scales = [1.0, 1.0, 1.0], n_best = 3, com_name_cur='RegionCenter',
                    com_name_next = 'RegionCenter', size_name='Count', delim='_', template_size=50, ndim=2,
                    size_filter = 4, squared_distance_default = 9999):
        self.scales = scales[0:ndim]
        self.n_best = n_best
        self.com_name_cur = com_name_cur
        self.com_name_next = com_name_next
        self.size_name = size_name
        self.delim = delim
        self.template_size = template_size
        self.ndim = ndim
        self.size_filter = size_filter
        self.squared_distance_default = squared_distance_default

    def _getBestSquaredDistances(self, com_cur, coms_next, size_filter = None, sizes_next = [], default_value = 9999):
        ''' returns the squared distances to the objects in the neighborhood of com_curr, optionally with size filter '''
        squaredDistances = []

        for label_next in coms_next.keys():
            assert label_next in sizes_next.keys()
            if size_filter != None and sizes_next[label_next] >= size_filter:
                dist = np.linalg.norm(coms_next[label_next] - com_cur * self.scales)                
                squaredDistances.append([label_next,dist])

        squaredDistances = np.array(squaredDistances)
        # sort the array in the second column in ascending order
        squaredDistances = np.array(sorted(squaredDistances, key=lambda a_entry: a_entry[1]))        
        
        # initialize with label -1 and default value
        result = np.array([ [-1, default_value] for x in range(self.n_best) ], dtype=np.float32)
        if squaredDistances.shape[0] != 0:
            result[0:min(squaredDistances.shape[0],result.shape[0]),:] = squaredDistances[0:min(squaredDistances.shape[0],result.shape[0]),:]

        return result
 

    def computeFeatures_at(self, feats_cur, feats_next, img_next, feat_names): 

#         n_labels = feats_cur.values()[0].shape[0]
        result = {}
        
        vigra_feat_names = set([self.com_name_cur, self.com_name_next, self.size_name])

        feat_classes = {}

        for name in feat_names:
            name_split = name.split(self.delim)
            if "SquaredDistances" in name_split:
                continue
            
            if len(name_split) != 2:                
                raise Exception, 'tracking features consist of an operator and a feature name only, given name={}'.format(name_split) 
            feat_dim = len(feats_cur[name_split[1]][0])
            feat_classes[name] = self.feature_mappings[name_split[0]](name_split[1], delim=self.delim, ndim=self.ndim, feat_dim=feat_dim)

            shape = (feats_cur.values()[0].shape[0],feat_classes[name].dim())
            result[name] = np.ones(shape) * feat_classes[name].default_value

            vigra_feat_names.add(name_split[1])
        

        for idx in range(self.n_best):
            name = 'SquaredDistances_' + str(idx)
            result[name] = np.ones((feats_cur.values()[0].shape[0], 1)) * self.squared_distance_default

        for label_cur, com_cur in enumerate(feats_cur[self.com_name_cur]):
            if label_cur == 0:
                continue

            feats_next_subset = {}
            for k in vigra_feat_names:
                feats_next_subset[k] = {}

            if feats_next is not None and img_next is not None:
                idx_cur = [round(x) for x in com_cur]

                roi = []
                for idx,coord in enumerate(idx_cur):
                    start = max(coord - self.template_size/2, 0)
                    stop = min(coord + self.template_size/2, img_next.shape[idx])
                    roi.append(slice(int(start),int(stop)))


                # find all coms in the neighborhood of com_cur
                subimg_next = img_next[roi]
                labels_next = np.unique(subimg_next).tolist()

                for l in labels_next:
                    if l != 0:
                        for n in vigra_feat_names:
                            feats_next_subset[n][l] = np.array([feats_next[n][l]]).flatten()                            

            sq_dist_label = self._getBestSquaredDistances(com_cur, feats_next_subset[self.com_name_next], 
                                self.size_filter, feats_next_subset[self.size_name], default_value=self.squared_distance_default)

            feats_next_subset_best = {}
            for n in vigra_feat_names:
                feats_next_subset_best[n] = []
                for idx, row in enumerate(sq_dist_label):
                    l = row[0]
                    if l != -1:
                        feats_next_subset_best[n].append(feats_next_subset[n][l])

            # first add squared distances
            for idx in range(self.n_best):
                name = 'SquaredDistances_' + str(idx)                
                result[name][label_cur] = sq_dist_label[idx][1]

            # add all other features
            for name, feat_class in feat_classes.items():
                if feat_class.feats_name == 'SquaredDistances':
                    f_next = sq_dist_label[0:2,1]
                    f_cur = None
                else:   
                    f_cur = np.array([feats_cur[feat_class.feats_name][label_cur]]).flatten()
                    f_next = np.array([feats_next_subset_best[feat_class.feats_name]]).reshape((-1,f_cur.shape[0]))
                result[name][label_cur] = feat_class.compute(f_cur, f_next)

        return result



if __name__ == '__main__':
    import vigra
    import numpy as np

    img_cur = vigra.readImage('/home/mschiegg/tmp/segmentImage.tif')
    img_next = img_cur

    labels_cur = vigra.analysis.labelImage(img_cur)
    feats_cur = vigra.analysis.extractRegionFeatures(labels_cur.astype(np.float32), labels_cur.astype(np.uint32), features='all', ignoreLabel=0)

    feat_names = ['ParentChildrenRatio_Count', 'ParentChildrenRatio_Mean', 'ChildrenRatio_Count', 'ChildrenRatio_Mean',
                   'ParentChildrenAngle_RegionCenter', 'ChildrenRatio_SquaredDistances'
                   ]
    fm = FeatureManager()
    res = fm.computeFeatures_at(feats_cur, feats_cur, img_cur, feat_names)
