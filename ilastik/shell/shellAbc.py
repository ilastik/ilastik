from abc import ABCMeta, abstractmethod, abstractproperty

def _has_attribute( cls, attr ):
    return True if any(attr in B.__dict__ for B in cls.__mro__) else False

def _has_attributes( cls, attrs ):
    return True if all(_has_attribute(cls, a) for a in attrs) else False

class ShellABC(object):
    """
    This ABC defines the minimum interface that both the IlastikShell and HeadlessShell must implement.
    """
    
    __metaclass__ = ABCMeta

    @abstractproperty
    def workflow(self):
        raise NotImplementedError

    @abstractmethod
    def createAndLoadNewProject(self, newProjectFilePath, workflow_class):
        """
        """
        raise NotImplementedError

    @abstractmethod
    def openProjectFile(self, projectFilePath):
        """
        """
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is ShellABC:
            return _has_attributes(C, ['workflow', 'createAndLoadNewProject', 'openProjectFile'])
        return NotImplemented
