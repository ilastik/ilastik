from functools import partial
from lazyflow.graph import Slot, OperatorWrapper

class OperatorWrapperAdapter(object):
    """
    Provides access to an inner operator of an OperatorWrapper, 
    but ensures that calls to setValue() on the operator's input 
    slots are broadcasted to all inner operators in the wrapper.
    """
    def __init__(self, wrapper, index):        
        assert type(wrapper) == OperatorWrapper
        self.inputs = {}
        self.wrapper = wrapper

        # Input slots are provided via AdapterSlots        
        for slotName, slot in wrapper.inputs.items():
            adapterSlot = AdapterSlot(slot, slot[index])
            self.inputs[slotName] = adapterSlot
            setattr(self, slotName, adapterSlot)
                    
        self.outputs = {}
        for slotName, slot in wrapper.outputs.items():
            self.outputs[slotName] = slot[index]
            setattr(self, slotName, slot[index])

    def __getattribute__(self, name):
        """
        For all members other than slot access, we simply pretend we are the wrapper object.
        """
        try:
            # If we have this attr, then return it (i.e. its a slot)
            return object.__getattribute__(self, name)
        except:
            # Otherwise, return the wrapper's attr by this name
            return getattr(self.wrapper, name)

class AdapterSlot(object):
    """
    Given a multislot and one of its subslots, simply acts as a handle for the 
    subslot in all respects EXCEPT that all calls to setValue are intercepted and forwarded to the MultiSlot.
    """
    def __init__(self, multislot, subslot):
        self._multislot = multislot
        self._subslot = subslot

    def setValue(self, *args, **kwargs):
        print 'broadcasting call to ' + self._multislot.name + '.setValue'
        self._multislot.setValue(*args, **kwargs)

    def __getattribute__(self, name):
        """
        Forward all attribute requests to the original subslot except for setValue()
        """
        try:
            # If we have this attr, then return it
            return object.__getattribute__(self, name)
        except:
            # Otherwise, return the original subslot's attr by this name
            return getattr(self._subslot, name)

    # Forward all special calls to the subslot
    def __len__(self):
        return len(self._subslot)

    def __getitem__(self, key):
        return self._subslot.__getitem__(key)

    def __setitem__(self, key, value):
        return self._subslot.__getitem__(key, value)

    def __call__(self, *args, **kwargs):
        return self._subslot.__call__(*args, **kwargs)

    