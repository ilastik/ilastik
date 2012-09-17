from abc import ABCMeta, abstractmethod

def _has_attribute( cls, attr ):
    return True if any(attr in B.__dict__ for B in cls.__mro__) else False

def _has_attributes( cls, attrs ):
    return True if all(_has_attribute(cls, a) for a in attrs) else False    

class DrawableABC:
    __metaclass__ = ABCMeta

    @abstractmethod
    def size(self):
        return NotImplemented

    @abstractmethod
    def drawAt(self, canvas, upperLeft):
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is DrawableABC:
            return True if _has_attributes(C, ['size', 'drawAt']) else False
        return NotImplemented

class ConnectableABC:
    __metaclass__ = ABCMeta

    @abstractmethod
    def inputPointOffset(self):
        return NotImplemented

    @abstractmethod
    def outputPointOffset(self):
        return NotImplemented

    @classmethod
    def __subclasshook__(cls, C):
        if cls is DrawableABC:
            return True if _has_attributes(C, ['inputPointOffset', 'outputPointOffset']) else False
        return NotImplemented

class ConnectionABC:
    __metaclass__ = ABCMeta

    @abstractmethod
    def draw(self, outputPoint, inputPoint):
        return NotImplemented
