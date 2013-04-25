#Python
import collections
import logging
import threading
import functools

#lazyflow
from lazyflow.slot import InputSlot, OutputSlot, Slot
from lazyflow.utility import Tracer

class InputDict(collections.OrderedDict):

    def __init__(self, operator):
        super(InputDict, self).__init__()
        self.operator = operator

    def __setitem__(self, key, value):
        assert isinstance(value, InputSlot), \
            ("ERROR: all elements of .inputs must be of type InputSlot."
             " You provided {}!".format(value))
        return super(InputDict, self).__setitem__(key, value)

    def __getitem__(self, key):
        if self.has_key(key):
            return super(InputDict, self).__getitem__(key)
        elif hasattr(self.operator, key):
            return getattr(self.operator, key)
        else:
            raise Exception("Operator {} (class: {}) has no input slot named '{}'."
                            " Available input slots are: {}".format(
                                self.operator.name, self.operator.__class__, key, self.keys()))


class OutputDict(collections.OrderedDict):

    def __init__(self, operator):
        super(OutputDict, self).__init__()
        self.operator = operator

    def __setitem__(self, key, value):
        assert isinstance(value, OutputSlot), \
            ("ERROR: all elements of .outputs must be of type"
             " OutputSlot. You provided {}!".format(value))
        return super(OutputDict, self).__setitem__(key, value)

    def __getitem__(self, key):
        if self.has_key(key):
            return super(OutputDict, self).__getitem__(key)
        elif hasattr(self.operator, key):
            return getattr(self.operator, key)
        else:
            raise Exception("Operator {} (class: {}) has no output slot named '{}'."
                            " Available output slots are: {}".format(
                                self.operator.name, self.operator.__class__, key, self.keys()))


from abc import ABCMeta
class OperatorMetaClass(ABCMeta):

    def __new__(cls, name, bases, classDict):
        cls = super(OperatorMetaClass, cls).__new__(cls, name, bases, classDict)

        setattr(cls, "inputSlots", list(cls.inputSlots))
        setattr(cls, "outputSlots", list(cls.outputSlots))

        # Support fancy syntax.
        # If the user typed this in his class definition:
        #    MySlot = InputSlot()
        #    MySlot2 = InputSlot()
        #
        # Make it equivalent to this:
        #    inputSlots = [ InputSlot("MySlot"), InputSlot("MySlot2") ]

        for k, v in cls.__dict__.items():
            if isinstance(v, InputSlot):
                v.name = k
                cls.inputSlots.append(v)

            if isinstance(v, OutputSlot):
                v.name = k
                cls.outputSlots.append(v)
        return cls

    def __call__(cls, *args, **kwargs):
        # type.__call__ calls instance.__init__ internally
        try:
            instance = ABCMeta.__call__(cls, *args, **kwargs)
        except Exception as e:
            err = "Could not create instance of '{}'\n".format(cls)
            err += "args   = {}\n".format(args)
            err += "kwargs = {}\n".format(kwargs)
            err += "The exception was:\n"
            err += str(e)
            err += "\nTraceback:\n"
            import traceback
            import StringIO
            s = StringIO.StringIO()
            traceback.print_exc(file=s)
            err += s.getvalue()
            raise RuntimeError(err)
        instance._after_init()
        return instance


class Operator(object):
    """
    The base class for all Operators.

    Operators consist of a class inheriting from this class
    and need to specify their inputs and outputs via
    thei inputSlot and outputSlot class properties.

    Each instance of an operator obtains individual
    copies of the inputSlots and outputSlots, which are
    available in the self.inputs and self.outputs instance
    properties.

    these instance properties can be used to connect
    the inputs and outputs of different operators.

    Example:
        operator1.inputs["InputA"].connect(operator2.outputs["OutputC"])


    Different examples for simple operators are provided
    in an example directory. plese read through the
    examples to learn how to implement your own operators...
    """

    loggerName = __name__ + '.Operator'
    logger = logging.getLogger(loggerName)
    traceLogger = logging.getLogger('TRACE.' + loggerName)

    #definition of inputs slots
    inputSlots  = []

    #definition of output slots -> operators instances
    outputSlots = []
    name = "Operator (base class)"
    description = ""
    category = "lazyflow"

    __metaclass__ = OperatorMetaClass

    def __new__(cls, *args, **kwargs):
        ##
        # before __init__
        ##
        obj = object.__new__(cls)
        obj.inputs = InputDict(obj)
        obj.outputs = OutputDict(obj)
        return obj

    def __init__(self, parent=None, graph=None):
        if not(parent is None or isinstance(parent, Operator)):
            raise Exception("parent of operator name='{}' must be an operator,"
                            " not {} of type {}".format(self.name, parent, type(parent)))
        if graph is None:
            if parent is None:
                raise Exception("Operator.__init__() [self.name='{}']:"
                                " parent and graph can't be both None".format(self.name))
            graph = parent.graph

        self._cleaningUp = False
        self.graph = graph
        self._children = collections.OrderedDict()
        self._parent = None
        if parent is not None:
            parent._add_child(self)

        self._initialized = False

        self._condition = threading.Condition()
        self._executionCount = 0
        self._settingUp = False

        self._instantiate_slots()

        # We normally assert if an operator's upstream partners are
        # yanked away. If operator is marked as "externally_managed",
        # then we'll avoid the assert. In that case, it's assumed that
        # you know what you're doing, and you weren't planning to use
        # that operator, anyway.
        self.externally_managed = False

    @property
    def children(self):
        return list(self._children.keys())

    def _add_child(self, child):
        # We're just using an OrderedDict for O(1) lookup with
        # in-order iteration but we don't actually store any values
        assert child.parent is None
        self._children[child] = None
        child._parent = self

    # continue initialization, when user overrides __init__
    def _after_init(self):
        #provide simple default name for lazy users
        if self.name == Operator.name:
            self.name = type(self).__name__
        assert self.graph is not None, \
            ("Operator {}: self.graph is None, the parent ({})"
             " given to the operator must have a valid .graph attribute!".format(
                 self, self._parent))
        # check for slot uniqueness
        temp = {}
        for i in self.inputSlots:
            if temp.has_key(i.name):
                raise Exception("ERROR: Operator {} has multiple slots with name {},"
                                " please make sure that all input and output slot"
                                " names are unique".format(self.name, i.name))
            temp[i.name] = True

        for i in self.outputSlots:
            if temp.has_key(i.name):
                raise Exception("ERROR: Operator {} has multiple slots with name {},"
                                " please make sure that all input and output slot"
                                " names are unique".format(self.name, i.name))
            temp[i.name] = True

        self._instantiate_slots()

        self._setDefaultInputValues()

        for islot in self.inputs.values():
            islot.notifyUnready(self.handleInputBecameUnready)


        self._initialized = True
        if self.configured():
            self._setupOutputs()

    def _instantiate_slots(self):
        # replicate input slot connections
        # defined for the operator for the instance
        for i in sorted(self.inputSlots, key=lambda s: s._global_slot_id):
            if not self.inputs.has_key(i.name):
                ii = i._getInstance(self)
                ii.connect(i.partner)
                self.inputs[i.name] = ii

        for k, v in self.inputs.items():
            self.__dict__[k] = v

        # relicate output slots
        # defined for the operator for the instance
        for o in sorted(self.outputSlots, key=lambda s: s._global_slot_id):
            if not self.outputs.has_key(o.name):
                oo = o._getInstance(self)
                self.outputs[o.name] = oo

        for k, v in self.outputs.items():
            self.__dict__[k] = v

    @property
    def parent(self):
        return self._parent

    def __setattr__(self, name, value):
        """This method safeguards that operators do not overwrite slot
        names with custom instance attributes.

        """
        if self.__dict__.has_key("inputs") and self.__dict__.has_key("outputs"):
            if self.inputs.has_key(name) or self.outputs.has_key(name):
                assert isinstance(value, Slot), \
                    ("ERROR: trying to set attribute {} of operator {}"
                     " to value {}, which is not of type Slot !".format(name, self, value))
        object.__setattr__(self, name, value)

    def configured(self):
        """Returns True if all input slots that are non-optional are
        connected and configured.

        """
        allConfigured = self._initialized
        for slot in self.inputs.values():
            allConfigured &= (slot.ready() or slot._optional)
        return allConfigured

    def _setDefaultInputValues(self):
        for i in self.inputs.values():
            if (i.partner is None and
                i._value is None and
                i._defaultValue is not None):
                i.setValue(i._defaultValue)

    def _disconnect(self):
        """Disconnect our slots from their upstream partners (not
        their downstream ones) and recursively do the same to all our
        child operators.

        """
        for s in self.inputs.values() + self.outputs.values():
            s.disconnect()

        for child in self._children.keys():
            child._disconnect()

    def _initCleanup(self):
        self._cleaningUp = True
        for child in self._children.keys():
            child._initCleanup()

    def cleanUp(self):
        if not self._cleaningUp:
            self._initCleanup()
        if self._parent is not None:
            del self._parent._children[self]

        # Disconnect ourselves and all children
        self._disconnect()

        for s in self.inputs.values() + self.outputs.values():
            # See note about the externally_managed flag in Operator.__init__
            partners = list(p for p in s.partners
                            if p.getRealOperator() is not None and
                            not p.getRealOperator().externally_managed)
            if len(partners) > 0:
                msg = ("Cannot clean up this operator: Slot '{}'"
                       " is still providing data to downstream"
                       " operators!\n".format(s.name))
                for i, p in enumerate(s.partners):
                    msg += "Downstream Partner {}: {}.{}".format(
                        i, p.getRealOperator().name, p.name)
                raise RuntimeError(msg)

        # Work with a copy of the child list
        # (since it will be modified with each iteration)
        children = set(self._children.keys())
        for child in children:
            child.cleanUp()

    def propagateDirty(self, slot, subindex, roi):
        """This method is called when an output of another operator on
        which this operators depends, i.e. to which it is connected gets
        invalid. The region of interest of the inputslot which is now
        dirty is specified in the key property, the input slot which got
        dirty is specified in the inputSlot property.

        This method must calculate what output ports and which subregions
        of them are invalidated by this, and must call the .setDirty(key)
        of the corresponding outputslots.

        """
        raise NotImplementedError(".propagateDirty() of Operator {}"
                                  " is not implemented !".format(self.name))

    @staticmethod
    def forbidParallelExecute(func):
        """Use this decorator with functions that must not be run in
        parallel with the execute() function.

        - Your function won't start until no threads are in execute().

        - Calls to execute() will wait until your function is complete.

        This is better than using a simple lock in execute() because
        it allows execute() to be run in parallel with itself.

        """
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            with self._condition:
                while self._executionCount > 0:
                    self._condition.wait()
                self._settingUp = True

                try:
                    return func(self, *args, **kwargs)
                finally:
                    self._settingUp = False
                    self._condition.notifyAll()
        wrapper.__wrapped__ = func # Emulate python 3 behavior of @wraps
        return wrapper

    def _setupOutputs(self):
        with Tracer(self.traceLogger, msg=self.name):
            # Don't setup this operator if there are currently
            # requests on it.
            with self._condition:
                while self._executionCount > 0:
                    self._condition.wait()
                self._settingUp = True

                # Outputslots may become "ready" during setupOutputs().
                # Save a copy of the ready flag for each output slot
                # so we can decide whether or not to fire the ready
                # signal.
                readyFlags = {}
                for k, oslot in self.outputs.items():
                    readyFlags[k] = oslot.meta._ready

                # Call the subclass
                self.setupOutputs()

                self._settingUp = False
                self._condition.notifyAll()

            try:
                # Determine new "ready" flags
                for k, oslot in self.outputs.items():
                    if oslot.partner is None:
                        # Special case, operators can flag an output as not actually being ready yet,
                        #  in which case we do NOT notify downstream connections.
                        if oslot.meta.NOTREADY:
                            oslot.disconnect() # Forces unready state
                        else:
                            # All unconnected outputs are ready after
                            # setupOutputs
                            oslot._setReady()
                    else:
                        assert oslot.meta.NOTREADY is None, \
                            "The special NOTREADY setting can only be used for output " \
                            "slots that have no explicit upstream connection."
    
                #notify outputs of probably changed meta information
                for k, v in self.outputs.items():
                    v._changed()
            except:
                # Something went wrong
                # Make the operator-supplied outputs unready again
                for k, oslot in self.outputs.items():
                    if oslot.partner is None:
                        oslot.disconnect() # Forces unready state
                raise

    def handleInputBecameUnready(self, slot):
        with Tracer(self.traceLogger, msg=self.name):
            # One of our input slots was disconnected.
            # If it was optional, we don't care.
            if slot._optional:
                return

            # Keep track of the old ready statuses so we know if
            # something changed
            readyFlags = {}
            for k, oslot in self.outputs.items():
                readyFlags[k] = oslot.meta._ready

            # All unconnected outputs are no longer ready
            for oslot in self.outputs.values():
                oslot.meta._ready &= (oslot.partner is not None)

            # If the ready status changed, signal it.
            for k, oslot in self.outputs.items():
                if readyFlags[k] != oslot.meta._ready:
                    oslot._sig_unready(self)
                    oslot._changed()

    def setupOutputs(self):
        """This method is called when all input slots of an operator
        are successfully connected, a successful connection is also
        established if the input slot is not connected to another
        slot, but has a default value defined.

        In this method the operator developer should stup
        the .meta information of the outputslots.

        The default implementation emulates the old api behaviour.

        """
        pass

    def execute(self, slot, subindex, roi, result):
        """ This method of the operator is called when a connected
        operator or an outside user of the graph wants to retrieve the
        calculation results from the operator.

        The slot which is requested is specified in the slot arguemt,
        the region of interest is specified in the key property. The
        result area into which the calculation results MUST be written
        is specified in the result argument. "result" is an
        numpy.ndarray that has the same shape as the region of
        interest(key).

        The method must retrieve all required inputs that are
        neccessary to calculate the requested output area from its
        input slots, run the calculation and put the results into the
        provided result argument. """

        raise NotImplementedError("Operator {} does not implement"
                                  " execute()".format(self.name))

    def setInSlot(self, slot, subindex, key, value):
        raise NotImplementedError("Can't use __setitem__ with Operator {}"
                                  " because it doesn't implement"
                                  " setInSlot()".format(self.name))
