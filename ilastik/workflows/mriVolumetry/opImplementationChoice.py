
from lazyflow.operator import Operator, InputSlot


class OpImplementationChoice(Operator):
    '''
    choose from a predefined set of implementations
    '''

    # use this slot for choosing the implementation (type: string)
    Implementation = InputSlot()

    # fill this with your implementations (type: dict)
    implementations = None

    _current_impl = None
    _impl_name = "Unconfigured OpImplementationChoice"
    _custom_name = False
    _op = None

    @property
    def name(self):
        return self._impl_name

    @name.setter
    def name(self, s):
        self._impl_name = s
        self._custom_name = True

    def __init__(self, implementationABC, *args, **kwargs):
        super(OpImplementationChoice, self).__init__(*args, **kwargs)

        # promote API from implementationABC to this operator
        # mostly stolen from OperatorWrapper

        # replicate input slot definitions
        for innerSlot in sorted(implementationABC.inputSlots,
                                key=lambda s: s._global_slot_id):
            level = innerSlot.level
            outerSlot = innerSlot._getInstance(self, level=level)
            self.inputs[outerSlot.name] = outerSlot
            setattr(self, outerSlot.name, outerSlot)

        # replicate output slot definitions
        for innerSlot in sorted(implementationABC.outputSlots,
                                key=lambda s: s._global_slot_id):
            level = innerSlot.level
            outerSlot = innerSlot._getInstance(self, level=level)
            self.outputs[outerSlot.name] = outerSlot
            setattr(self, outerSlot.name, outerSlot)

        # set all slots to unready until some implementation provides them
        for k in self.outputs:
            self.outputs[k].meta.NOTREADY = True

    def setupOutputs(self):
        impl = self.Implementation.value
        if impl == self._current_impl:
            return

        if self.implementations is None:
            raise RuntimeError("No implementations provided")

        if impl not in self.implementations:
            raise ValueError("Implementation '{}' unknown".format(impl))

        # disconnect former implementation
        if self._op is not None:
            op = self._op
            self._op = None
            for k in self.outputs:
                self.outputs[k].meta.NOTREADY = True  # also disconnects
            for k in op.inputs:
                op.inputs[k].disconnect()

        # connect new implementation
        op = self.implementations[impl](parent=self)
        for k in op.inputs:
            if not k.startswith("_"):
                op.inputs[k].connect(self.inputs[k])
        for k in op.outputs:
            if not k.startswith("_"):
                self.outputs[k].connect(op.outputs[k])
                self.outputs[k].meta.NOTREADY = None
        self._op = op

        self._current_impl = impl
        if not self._custom_name:
            fmt_str = "OpImplementationChoice[selected={}]"
            self._impl_name = fmt_str.format(self._op.name)

    def propagateDirty(self, slot, subindex, roi):
        pass

    def setInSlot(self, slot, subindex, key, value):
        # TODO is it correct to pass here?
        pass
