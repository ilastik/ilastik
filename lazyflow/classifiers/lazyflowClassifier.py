import abc

def _has_attribute( cls, attr ):
    return any(attr in B.__dict__ for B in cls.__mro__)

def _has_attributes( cls, attrs ):
    return all(_has_attribute(cls, a) for a in attrs)

class LazyflowVectorwiseClassifierFactoryABC(object):
    """
    Defines an interface for vector-wise classifier 'factory' objects, 
    which lazyflow classifier operators use to construct new vector-wise classifiers.
    A "vector-wise" classifier is trained with a 2D feature matrix and a 1D label vector.
    """
    __metaclass__ = abc.ABCMeta

    def __new__(cls, *args, **kwargs):
        # Force the VERSION class member to be copied to an instance member.
        obj = object.__new__(cls)
        obj.VERSION = cls.VERSION
        return obj

    @abc.abstractmethod
    def create_and_train(self, X, y):
        """
        Create a new classifier and train it with the feature matrix X and label vector y.
        """
        raise NotImplementedError

    @abc.abstractproperty
    def description(self):
        """
        Return a human-readable description of this classifier.
        """
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        """
        To qualify as a subclass, your class must 
        1) be an actual subclass (so our __new__ method can add the VERSION member to all instances)
        2) override the proper instance methods
        3) have a VERSION class member
        """
        if cls is LazyflowVectorwiseClassifierFactoryABC:
            is_subclass = LazyflowVectorwiseClassifierFactoryABC in C.__mro__
            is_subclass &= _has_attributes(C, ['create_and_train', 'description'])
            is_subclass &= 'VERSION' in C.__dict__
            return is_subclass
        return NotImplemented

class LazyflowVectorwiseClassifierABC(object):
    """
    Defines an interface for "vector-wise" classifier objects that can be used by the lazyflow classifier operators.
    A "vector-wise" classifier is trained with a 2D feature matrix and a 1D label vector.
    
    All scikit-learn classifiers already satisfy this interface.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def predict_probabilities(self, X):
        """
        For each sample in the feature matrix ``X``, predict the probabilities that the
        sample belongs to each label class the classifier was trained with.
        
        Returns: A multi-channel vector (each channel corresponds to a different label class).
        """
        raise NotImplementedError

    @abc.abstractproperty
    def known_classes(self):
        """
        Returns the list of label classes known to this classifier (i.e. the classes it was trained with).
        """
        raise NotImplementedError

    @abc.abstractproperty
    def feature_count(self):
        """
        Return the number of features used to train this classifier.
        """
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is LazyflowVectorwiseClassifierABC:
            return _has_attributes(C, ['predict_probabilities', 'known_classes', 'serialize_hdf5', 'deserialize_hdf5'])
        return NotImplemented

    @abc.abstractmethod
    def serialize_hdf5(self, h5py_group):
        """
        Serialize the classifier as an hdf5 group.
        """
        raise NotImplementedError

    @classmethod    
    def deserialize_hdf5(cls, h5py_group):
        """
        Class method.  Deserialize the classifier stored in the given ``h5py.Group`` object, and return it.
        """
        raise NotImplementedError
    
class LazyflowPixelwiseClassifierFactoryABC(object):
    """
    Defines an interface for pixel-wise classifier 'factory' objects, 
    which lazyflow classifier operators use to construct new pixel-wise classifiers.
    A "pixel-wise" classifier is trained with a list of ND feature images (with M feature channels),
    and a list of corresponding ND label images, with 1 channel each.

    Note: It is assumed here that 'channel' is always the last axis of the image.
    """
    __metaclass__ = abc.ABCMeta

    def __new__(cls, *args, **kwargs):
        # Force the VERSION class member to be copied to an instance member.
        obj = object.__new__(cls)
        obj.VERSION = cls.VERSION
        return obj

    @abc.abstractmethod
    def create_and_train_pixelwise(self, feature_images, label_images, axistags=None):
        """
        Create a new classifier and train it with the given list of feature images and the given list of label images.
        Generally, it is assumed that the channel dimension is the LAST axis for each image.  
        (The label image must include a singleton channel dimension.)
        Each pair of corresponding feature and label images must have matching shapes (except for the channel dimension).
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_halo_shape(self, data_axes='zyxc'):
        """
        Return the halo dimensions required for optimal classifier performance.
        For example, for a classifier that performs an internal 3D convolution with sigma=1.5 and window_size = 2.0,
        halo_shape = (3, 3, 3, 0).
        
        Clients are not required to provide the halo during training.  
        (For example, it may not be possible for labels near the image border.)
        
        data_axes: A string representing the axis order of the data that will be used for training/prediction.
                   Examples: 'yxc', 'zyxc', or 'tzyxc'.
        """
        raise NotImplementedError

    @abc.abstractproperty
    def description(self):
        """
        Return a human-readable description of this classifier.
        """
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        """
        To qualify as a subclass, your class must 
        1) be an actual subclass (so our __new__ method can add the VERSION member to all instances)
        2) override the proper instance methods
        3) have a VERSION class member
        """
        if cls is LazyflowPixelwiseClassifierFactoryABC:
            is_subclass = LazyflowPixelwiseClassifierFactoryABC in C.__mro__
            is_subclass &= _has_attributes(C, ['create_and_train_pixelwise', 'description', 'get_halo_shape'])
            is_subclass &= 'VERSION' in C.__dict__
            return is_subclass
        return NotImplemented
    
    def __eq__(self, other):
        """
        Classifier factories must be both copyable and (in)equality comparable.
        """
        raise NotImplementedError

    def __ne__(self, other):
        raise NotImplementedError    

class LazyflowPixelwiseClassifierABC(object):
    """
    Defines an interface for "pixel-wise" classifier objects that can be used by the lazyflow classifier operators.
    A "pixel-wise" classifier expects its input be given as a list of ND feature images (with M feature channels).
    (It was trained with a list of ND label images, with 1 channel each.)
    
    Note: It is assumed here that 'channel' is always the last axis of the image.
    
    (This interface is typically used with classifiers that must generate their own features internally,
    and thus require the knowledge of the image structure and context around each training/prediction point.)
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def predict_probabilities_pixelwise(self, feature_image, axistags=None):
        """
        For each pixel in the given feature_image, predict the probabilities that the
        pixel belongs to each label class the classifier was trained with.
        
        feature_image: An ND image.  Last axis must be channel.
        axistags: Optional.  A vigra.AxisTags object describing the feature_image.
        
        Returns: A multi-channel image (each channel corresponds to a different label class).
        """
        raise NotImplementedError

    @abc.abstractproperty
    def known_classes(self):
        """
        Returns the list of label classes known to this classifier (i.e. the classes it was trained with).
        """
        raise NotImplementedError

    @abc.abstractproperty
    def feature_count(self):
        """
        Return the number of features used to train this classifier.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_halo_shape(self, data_axes='zyxc'):
        """
        Same as LazyflowPixelwiseClassifierFactoryABC.get_halo_shape().  See that function for details.
        """
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is LazyflowPixelwiseClassifierABC:
            return _has_attributes(C, ['predict_probabilities_pixelwise', 'known_classes', 'get_halo_shape', 'serialize_hdf5', 'deserialize_hdf5'])
        return NotImplemented

    @abc.abstractmethod
    def serialize_hdf5(self, h5py_group):
        """
        Serialize the classifier as an hdf5 group
        """
        raise NotImplementedError

    @classmethod    
    def deserialize_hdf5(cls, h5py_group):
        """
        Class method.  Deserialize the classifier stored in the given ``h5py.Group`` object, and return it.
        """
        raise NotImplementedError
    
    
        