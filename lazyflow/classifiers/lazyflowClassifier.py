import abc

def _has_attribute( cls, attr ):
    return any(attr in B.__dict__ for B in cls.__mro__)

def _has_attributes( cls, attrs ):
    return all(_has_attribute(cls, a) for a in attrs)

class LazyflowClassifierFactoryABC(object):
    """
    Defines an interface for classifier 'factory' objects, 
    which lazyflow classifier operators use to construct new classifiers.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def create_and_train(self, X, y):
        raise NotImplementedError

    @abc.abstractproperty
    def description(self):
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is LazyflowClassifierABC:
            return _has_attributes(C, ['create_and_train', 'description'])
        return NotImplemented

class LazyflowClassifierABC(object):
    """
    Defines an interface for classifier objects that can be used by the lazyflow classifier operators.
    All scikit-learn classifiers already satisfy this interface.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def predict_probabilities(self, X):
        raise NotImplementedError

    @abc.abstractproperty
    def known_classes(self):
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is LazyflowClassifierABC:
            return _has_attributes(C, ['predict_probabilities', 'known_classes', 'serialize_hdf5', 'deserialize_hdf5'])
        return NotImplemented

    @abc.abstractmethod
    def serialize_hdf5(self, h5py_group):
        """
        Serialize the classifier as an hdf5 group
        """
        raise NotImplementedError

    @classmethod    
    def deserialize_hdf5(cls, h5py_group):
        raise NotImplementedError
    
    