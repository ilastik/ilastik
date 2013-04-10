from lazyflow.graph import OperatorWrapper, InputDict, OutputDict
from ilastik.utility import MultiLaneOperatorABC

class OperatorSubViewMetaclass(type):
    """
    Simple metaclass to catch errors the user might make by attempting to access certain class attributes.
    """
    def __getattr__(self, name):
        if name == "inputSlots":
            assert False, "OperatorSubView.inputSlots cannot be accessed as a class member.  It can only be accessed as an instance member"
        if name == "outputSlots":
            assert False, "OperatorSubView.outputSlots cannot be accessed as a class member.  It can only be accessed as an instance member"
        return type.__getattr__(self, name)

class OperatorSubView(object):
    """
    An adapter class that makes a specific lane of a multi-image operator look like a single image operator.
    
    If the adapted operator is an OperatorWrapper, then the view provides all of the members of the inner 
    operator at the specified index, except that the slot members will refer to the OperatorWrapper's 
    slots (i.e. the OUTER slots).
    
    If the adapted operator is NOT an OperatorWrapper, then the view provides all the members of the adapted operator,
    except that ALL MULTISLOT members will be replaced with a reference to the subslot for the specified index.
    Non-multislot members will not be replaced.
    """

    __metaclass__ = OperatorSubViewMetaclass
    
    def viewed_operator(self):
        """
        Returns the original operator that this view is viewing.
        """
        return self.__op
    
    def current_view_index(self):
        """
        Returns the index of this view, even if the originally viewed operator (and its slots) have been resized in the meantime.
        """
        multislot = getattr(self.__op, self.__referenceSlotName)
        innerslot = getattr(self, self.__referenceSlotName)
        return multislot.index( innerslot )

    def __init__(self, op, index):
        """
        Constructor.  Creates a view of the given operator for the specified index.
        
        :param op: The operator to view.
        :param index: The index of this subview.  All multislots of the original 
                      operator will be replaced with the corresponding subslot at this index.
        """
        self.__op = op
        self.__slots = {}
        self.__innerOp = None # Used if op is an OperatorWrapper

        self.__referenceSlotName = None

        self.inputs = InputDict(self)
        for slot in op.inputs.values():
            if slot.level >= 1 and not slot.nonlane:
                self.inputs[slot.name] = slot[index]
                if self.__referenceSlotName is None:
                    self.__referenceSlotName = slot.name
            else:
                self.inputs[slot.name] = slot

            setattr(self, slot.name, self.inputs[slot.name])

        self.inputSlots = list( self.inputs.values() )
                
        self.outputs = OutputDict(self)
        for slot in op.outputs.values():
            if slot.level >= 1 and not slot.nonlane:
                self.outputs[slot.name] = slot[index]
                if self.__referenceSlotName is None:
                    self.__referenceSlotName = slot.name
            else:
                self.outputs[slot.name] = slot

            setattr(self, slot.name, self.outputs[slot.name])

        self.outputSlots = list( self.inputs.values() )

        # If we're an OperatorWrapper, save the inner operator at this index.
        if isinstance(self.__op, OperatorWrapper):
            self.__innerOp = self.__op.innerOperators[index]

        for name, member in self.__op.__dict__.items():
            # If any of our members happens to itself be a multi-lane operator,
            #  then keep a view on it instead of the original.
            if name != '_parent' and isinstance(member, MultiLaneOperatorABC):
                setattr(self, name, OperatorSubView(member, index) )

    def __getattribute__(self, name):
        try:
            # If we have this attr, use it.  It's either a slot, an inner operator, a  view itself.
            return object.__getattribute__(self, name)
        except:
            # Special case for OperatorWrappers: Get the member from the appropriate inner operator.
            # This means that the actual OperatorWrapper members aren't accessible via this view.
            if isinstance(self.__op, OperatorWrapper):
                return getattr(self.__innerOp, name)

            # Get the member from the operator directly.
            return getattr(self.__op, name)





