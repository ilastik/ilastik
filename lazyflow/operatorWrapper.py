#Python
import functools
import logging

#lazyflow
from lazyflow.operator import Operator
from lazyflow.utility import Tracer

class OperatorWrapper(Operator):
    name = "OperatorWrapper"

    loggerName = __name__ + '.OperatorWrapper'
    logger = logging.getLogger(loggerName)
    traceLogger = logging.getLogger('TRACE.' + loggerName)

    def __init__(self, operatorClass, operator_args=None,
                 operator_kwargs=None, parent=None, graph=None,
                 promotedSlotNames=None, broadcastingSlotNames=None):
        """Constructs a wrapper for the given operator. That is,
        manages a list of copies of the original operator, and
        provides access to these inner operators' slots via external
        multislots.

        :param operatorClass: An operator type that can be constructed
          with the given args and kwargs

        :param operator_args: Positional arguments for operator's
          constructor. Note: Do not include 'parent' and 'graph'
          arguments.

        :param operator_kwargs: Keyword arguments for the operator's
          constructor. Note: Do not include 'parent' and 'graph'
          arguments

        :param parent: The parent of the OperatorWrapper

        :param graph: the graph operator to init each inner operator with

        :param promotedSlotNames:

          If provided, only those slots will be promoted when
            replicated. All other slots will be replicated without
            promotion, and their input values will be broadcasted to
            all inner operators.

          If not provided (i.e. promotedSlotNames=None), the default
            behavior is to promote ALL replicated slots.

          Note: Outputslots are always promoted, regardless of whether
            or not they appear in the promotedSlotNames argument.

        """
        # Base class init
        super(OperatorWrapper, self).__init__(parent=parent, graph=graph)
        if operator_args == None:
            operator_args = ()
        if operator_kwargs == None:
            operator_kwargs = {}
        assert isinstance(operator_args, (tuple, list))
        assert isinstance(operator_kwargs, dict)
        self._createInnerOperator = functools.partial(
            operatorClass, parent=self,
            *operator_args, **operator_kwargs)

        self._initialized = False

        if operatorClass.name == "":
            self._name = "Wrapped " + operatorClass.__name__
        else:
            self._name = "Wrapped " + operatorClass.name

        self._customName = False

        if promotedSlotNames is not None:
            assert broadcastingSlotNames is None, \
                ("Please specify either the promoted slots or the"
                 " broadcasting slots, not both.")
            # 'Promoted' slots will be exposed as multi-slots
            # All others will be broadcasted
            promotedSlotNames = set(promotedSlotNames)

        elif broadcastingSlotNames is not None:
            # 'Broadcasting' slots are NOT exposed as multi-slots.
            # Each is exposed as a single slot that is shared by all
            # inner operators.
            allInputSlotNames = set(map(lambda s: s.name, operatorClass.inputSlots))

            # set difference
            promotedSlotNames = allInputSlotNames - set(broadcastingSlotNames)

        else:
            # No slots specified: All original slots are promoted by
            # default
            promotedSlotNames = set(slot.name for slot in operatorClass.inputSlots)

        # All Outputs are always promoted
        promotedSlotNames |= set(slot.name for slot in operatorClass.outputSlots)

        self.promotedSlotNames = promotedSlotNames

        self.innerOperators = []
        self.logger.log(logging.DEBUG,
                        "wrapping operator '{}'".format(
                            operatorClass.name))

        # replicate input slot definitions
        for innerSlot in sorted(operatorClass.inputSlots,
                                key=lambda s: s._global_slot_id):
            level = innerSlot.level
            if innerSlot.name in self.promotedSlotNames:
                level += 1
            outerSlot = innerSlot._getInstance(self, level=level)
            self.inputs[outerSlot.name] = outerSlot
            setattr(self, outerSlot.name, outerSlot)

        # replicate output slot definitions
        for innerSlot in sorted(operatorClass.outputSlots,
                                key=lambda s: s._global_slot_id):
            level = innerSlot.level + 1
            outerSlot = innerSlot._getInstance(self, level=level)
            self.outputs[outerSlot.name] = outerSlot
            setattr(self, outerSlot.name, outerSlot)

        # register callbacks for inserted and removed input subslots
        for s in self.inputs.values():
            if s.name in self.promotedSlotNames:
                s.notifyInserted(self._callbackInserted)
                s.notifyRemoved(self._callbackRemove)
                s._notifyConnect(self._callbackConnect)

        # register callbacks for inserted and removed output subslots
        for s in self.outputs.values():
            s.notifyInserted(self._callbackInserted)
            s.notifyRemoved(self._callbackRemove)

        for s in self.inputs.values():
            assert len(s) == 0
        for s in self.outputs.values():
            assert len(s) == 0

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        self._customName = True

    def __getitem__(self, key):
        return self.innerOperators[key]

    def __len__(self):
        return len(self.innerOperators)

    def _callbackInserted(self, slot, index, size):
        with Tracer(self.traceLogger, msg=self.name):
            self._insertInnerOperator(index, size)

    def _callbackRemove(self, slot, index, size):
        with Tracer(self.traceLogger, msg=self.name):
            self._removeInnerOperator(index, size)

    def _callbackConnect(self, slot):
        with Tracer(self.traceLogger, msg=self.name):
            slot.resize(len(self.innerOperators))
            for index, innerOp in enumerate(self.innerOperators):
                innerOp.inputs[slot.name].connect(slot[index])

    def propagateDirty(self, slot, subindex, roi):
        # Nothing to do: All inputs are directly connected to internal
        # operators.
        pass

    def _insertInnerOperator(self, index, length):
        with Tracer(self.traceLogger, msg=self.name):
            if len(self.innerOperators) >= length:
                return self.innerOperators[index]
            op = self._createInnerOperator()

            # Update our name (if the client didn't already give us a
            # special one)
            if self._customName is False:
                self._name = "Wrapped " + op.name

            # If anyone calls setValue() on one of these slots,
            # forward the setValue call to the slot's partner (the
            # outer slot on the operator wrapper)
            for slot in op.inputs.values():
                slot.backpropagate_values = True
                slot.notifyDisconnect(self.handleEarlyDisconnect)

            self.innerOperators.insert(index, op)

            # Connect the inner operator's inputs to our outer input
            # slots
            for key, outerSlot in self.inputs.items():
                # Only connect to a subslot if it was promoted during
                # wrapping
                if outerSlot.name in self.promotedSlotNames:
                    outerSlot.insertSlot(index, length)
                    partner = outerSlot[index]
                else:
                    partner = outerSlot
                if op.inputs[key].partner is not None:
                    msg = ("Can't set up OperatorWrapper connections."
                           " Input slot {} is already connected to a"
                           " partner (must have happened in {}'s"
                           " constructor".format(key, op.name))
                    raise RuntimeError(msg)
                op.inputs[key].connect(partner)

            # Connect our outer output slots to the inner operator's output slots.
            for key, mslot in self.outputs.items():
                mslot.insertSlot(index, length)
                mslot[index].backpropagate_values = True
                mslot[index].connect(op.outputs[key])
                mslot[index].notifyDisconnect(self.handleEarlyDisconnect)
                #mslot[index]._changed()
            return op

    def handleEarlyDisconnect(self, slot):
        assert False, \
            ("You aren't allowed to disconnect the internal"
             " connections of an operator wrapper.")

    def _removeInnerOperator(self, index, length):
        with Tracer(self.traceLogger, msg=self.name):
            if len(self.innerOperators) <= length:
                return
            assert index < len(self.innerOperators)

            for key, mslot in self.outputs.items():
                if len(mslot) > length:
                    mslot[index].backpropagate_values = False
                    mslot[index].unregisterDisconnect(self.handleEarlyDisconnect)

            op = self.innerOperators.pop(index)
            for slot in op.inputs.values():
                slot.backpropagate_values = False
                slot.unregisterDisconnect(self.handleEarlyDisconnect)

            for oslot in self.outputs.values():
                oslot.removeSlot(index, length)

            for islot in self.inputs.values():
                islot.removeSlot(index, length)

            op.cleanUp()
            length = len(self.innerOperators)

    def _setupOutputs(self):
        with Tracer(self.traceLogger, msg=self.name):
            for oslot in self.outputs.values():
                oslot._changed()

    def execute(self, slot, subindex, roi, result):
        #this should never be called !!!
        assert False, \
            "OperatorWrapper execute() function should never be called.  "\
            "You can only ask for data from SUBslots, not the outer multi-slots themselves."

    def setInSlot(self, slot, subindex, key, value):
        # Nothing to do here. Calls to Slot.setitem are already
        # forwarded to all slot partners.
        pass
