from abc import ABCMeta, abstractproperty

from lazyflow.graph import Operator

class Workflow( Operator ):
    
    __metaclass__ = ABCMeta # Force subclasses to override abstract methods and properties

    @abstractproperty
    def applets(self):
        return []

    @abstractproperty
    def imageNameListSlot(self):
        return None
