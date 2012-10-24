from abc import ABCMeta

class SubclassRegistryMeta(ABCMeta):
    """
    When you use this metaclass, your class will get a list of all its subclasses.    
    Note: You can't use this metaclass directly.  You must subclass it.
    Note: As a convenience, this metaclass inherits from ABCMeta, so your base class can use @abstractmethod
    Example:
        class MySubclassRegistry(SubclassRegistryMeta):
            pass
        
        class MyBase(object):
            __metaclass__ = MySubclassRegistry
        
        ...
        
        print MyBase.all_subclasses
    
    """
    
    def __new__(cls, name, bases, classDict):
        classType = ABCMeta.__new__(cls, name, bases, classDict)
        assert cls != SubclassRegistryMeta, "You can't use this metaclass directly.  You must subclass it.  See docstring."
        assert issubclass(cls, SubclassRegistryMeta)
        if ( '__metaclass__' in classDict and 
             issubclass(classDict['__metaclass__'], SubclassRegistryMeta) ):
            cls.all_subclasses = set()
            cls.base_class = classType
        else:
            SubclassRegistryMeta._registerSubclass(cls.base_class, classType)
        return classType

    @staticmethod
    def _registerSubclass(cls, subcls):
        cls.all_subclasses.add(subcls)
    
if __name__ == "__main__":

    # Must use a separate tracking metaclass for each base class that wants to track its subclasses    
    class SubclassTracker(SubclassRegistryMeta):
        pass
    
    class SomeBase(object):
        __metaclass__ = SubclassTracker
    
    class SomeSubclass(SomeBase):
        pass

    class SomeSubSubclass(SomeSubclass, object):
        pass
    
    assert len(SomeBase.all_subclasses) == 2
    assert SomeSubclass in SomeBase.all_subclasses 
    assert SomeSubSubclass in SomeBase.all_subclasses 
    
    b = SomeBase()
    c = SomeSubclass()
    d = SomeSubSubclass()
    
    