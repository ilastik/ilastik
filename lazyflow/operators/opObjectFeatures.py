from lazyflow.graph import Operator,InputSlot,OutputSlot
from lazyflow.helpers import AxisIterator
from lazyflow.stype import ArrayLike, Opaque
import numpy,vigra


class OpObjectFeatures(Operator):

    Image = InputSlot()  # 2D image
    Labels = InputSlot() # 2D or 3D image, if 3D last dimension is interpreted as channel
    SelectedFeatures = InputSlot(value = ["all"]) # a list of strings, or a string like "all". the string entries should equal the names returned by the AvailableFeatures slot

    FeatureDict = OutputSlot() # a python dictionary consisting of the features names as keys and numpy arrays as values
    FeatureMatrix = OutputSlot() # a 2D numpy array of with regions along axis 0 and features along axis 1

    AvailableFeatures = OutputSlot() # a list of strings of the feature names

    def __init__(self,parent):
        Operator.__init__(self, parent)

    def setupOutputs(self):
        features = self.SelectedFeatures[0].wait()

        assert(self.Image.shape[:-1] == self.Labels.shape[:-1])

        self.FeatureDict.meta.shape = (1,)
        self.FeatureDict.meta.dtype = object
        
        self.FeatureMatrix.meta.shape = (1,)
        self.FeatureMatrix.meta.dtype = object

        self.AvailableFeatures.meta.shape = (1,)
        self.AvailableFeatures.meta.dtype = object

    def execute(self, slot, roi, result):
        if slot == self.FeatureDict:

            features = self.SelectedFeatures[0].wait()[0]

            image = self.Image[:].wait().astype(numpy.float32)
            labels = self.Labels[:].wait().astype(numpy.uint32)
            assert(len(labels.shape) == len(image.shape))

            # standard behaviour, last dimension of equal size
            if image.shape[-1] == labels.shape[-1]:
                image.shape = image.shape + (1,)
                labels.shape = labels.shape + (1,)
                
            # treat last dim of labels as channels, which is to be applied to all channels of image

            result = {}
            for ic in range(image.shape[-1]):
                c_features = {}
                c_features_maxlen = {}
                for cc in range(labels.shape[-1]):
                    regionFeatures = vigra.analysis.extractRegionFeatures(image[...,ic], labels[...,cc], features)
                    for name in regionFeatures.activeNames():
                        if not c_features.has_key(name):
                            c_features[name] = []
                            c_features_maxlen[name] = regionFeatures[name]

                        c_features[name].append(regionFeatures[name])

                        if c_features_maxlen[name].shape[0] < regionFeatures[name].shape[0]:
                            c_features_maxlen[name] = regionFeatures[name]
            
                for name,feat in c_features_maxlen.items():
                    for cc in range(labels.shape[-1]):
                        labs = numpy.unique(labels[...,cc])
                        feat[labs,...] = c_features[name][cc][labs,...]

                
                for name,feat in c_features_maxlen.items():
                    if not result.has_key(name):
                        result[name] = []
                    result[name].append(feat)
            
            # result now is a dict of arrays, where each array holds the regions features for the corresponding channles of the image
            return [result]

        if slot == self.FeatureMatrix:
            c_features = self.FeatureDict[0].wait()[0]

            flat_arr = []

            for name,feat_arr in c_features.items():
                for i, arr in enumerate(feat_arr):
                    prod = 1
                    for ds in arr.shape[1:]:
                        prod = prod*ds

                    flat_arr.append(arr.reshape(arr.shape[0], prod))

            return [numpy.concatenate(flat_arr, axis=1)]


        if slot == self.AvailableFeatures:
            img = numpy.zeros((1,2), numpy.float32)
            lab = numpy.zeros((1,2), numpy.uint32)

            rf = vigra.analysis.extractRegionFeatures(img, lab, features = "all")

            # return a list of strings of the available features
            return rf.activeNames()


    def propagateDirty(self, slot, roi):
        # regardless of the slot which is dirty, all of the calculated features get dirty
        self.FeatureDict.setDirty((slice(None), ))
        self.FeatureMatrix.setDirty((slice(None), ))



if __name__ == "__main__":
    op = OpObjectFeatures(None)
    
    image = numpy.zeros((10,20,1), numpy.float32)
    labels = numpy.random.randint(10,30,(10,20,2))
    
    op.Image.setValue(image)
    op.Labels.setValue(labels)

    print "Available Features: \n", op.AvailableFeatures[0].wait()

    op.SelectedFeatures.setValue(['Skewness', 'Variance', 'Covariance', 'Kurtosis', 'Maximum', 'Mean', 'Minimum'])

    calculated_features = op.FeatureDict[:].wait()[0]   # get dict of channel-feature arrays
    print "Calculated Features: \n", calculated_features

    print calculated_features["Mean"][0].shape   # shape of feature "Mean" for channel 0


    feature_matrix = op.FeatureMatrix[:].wait()[0] # get feature matrix
    print "Shape of Feature Matrix", feature_matrix.shape

