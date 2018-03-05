###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2018, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#          http://ilastik.org/license/
###############################################################################
import functools
import types

from lazyflow.operators.opReorderAxes import OpReorderAxes


def reorder_options(internal_axes_order, ignore_slots=[],
                    output_axes_order='tczyx'):
    """
        Adds reorder options to the specific operator class that the decorator
        reorder accesses. This is not done by handing arguments to the reorder
        decorator directly, because then the reorder decorator would need to be
        wrapped, which would lead return a function (wrapper) as the operator
        class, which conflicts with inheritance of the specific operator (as
        the inheriting operator class appears to be a function). Therefore the
        arguments are outsourced in this decorator.

        note: Use this function decorator only in combination with the reorder
              decorator and as second (inner) decorator.
              (see example usage below)

        @param internal_axes_order: str Axes order the decorated operator
                                        assumes internally.
        @param ignore_slots: list(str) List of slot names that do not need to be
                                       reordered.
        @param output_axes_order: str Output Axes order for all reordered
                                      output slots.

        Example usage: (for a 'real-life example check OpGraphCut in ilastik)

            @reorder
            @reorder_options('tzyxc', ['ResizedShape'])
            class OpResize5D(Operator):
                ...

    """
    assert isinstance(internal_axes_order, str)
    assert isinstance(ignore_slots, list)
    assert all([isinstance(ex, str) for ex in ignore_slots])
    assert isinstance(output_axes_order, str)

    def set_options(cls):
        assert all([ex in [s.name for s in cls.inputSlots + cls.outputSlots]
                    for ex in ignore_slots])
        cls._internal_axes_order = internal_axes_order
        cls._not_reordered_slots = ignore_slots
        cls._output_axes_order = output_axes_order
        return cls
    return set_options


def guard_methods(cls):
    """
        helper function for reorder

        Flag with 'self._inner_call' when methods are called from within the class
        as opposed to accessing a slot of the operator from the "outside"
    """
    methods = [member for member, member_type in cls.__dict__.items()
               if isinstance(member_type, types.FunctionType) and
               member != '__getattribute__' and  # will be adapted individually
               member != '__init__' and  # will be adapted individually
               member != 'setupOutputs'  # will be adapted individually
               ]

    class_methods = [member for member, member_type in cls.__dict__.items()
                     if isinstance(member_type, classmethod)]

    property_methods = [member for member, member_type in cls.__dict__.items()
                        if isinstance(member_type, property)]

    # overwrite methods with guarded versions thereof
    for meth in methods:
        old_meth = getattr(cls, meth)

        def guard(fn):
            @functools.wraps(old_meth)
            def wrap(self, *args, **kwargs):
                if self._inner_call:
                    return fn(self, *args, **kwargs)
                else:
                    try:
                        self._inner_call = True
                        ret = fn(self, *args, **kwargs)
                        self._inner_call = False
                        return ret
                    except Exception:
                        raise
                    finally:
                        self._inner_call = False
            return wrap

        setattr(cls, meth, guard(old_meth))

    # overwrite class methods with guarded versions thereof
    for meth in class_methods:
        old_meth = getattr(cls, meth)

        def guard(fn):
            @functools.wraps(old_meth)
            def wrap(self, *args, **kwargs):
                if self._inner_call:
                    return fn(*args, **kwargs)
                else:
                    try:
                        self._inner_call = True
                        ret = fn(*args, **kwargs)
                        self._inner_call = False
                        return ret
                    except Exception:
                        raise
                    finally:
                        self._inner_call = False
            return wrap

        setattr(cls, meth, guard(old_meth))

    # overwrite property methods with guarded versions thereof
    for meth in property_methods:
        old_get = getattr(cls, meth).__get__

        def guard(fn):
            @property
            def wrap(self):
                if self._inner_call:
                    return fn(self)
                else:
                    try:
                        self._inner_call = True
                        ret = fn(self)
                        self._inner_call = False
                        return ret
                    except Exception:
                        raise
                    finally:
                        self._inner_call = False
            return wrap

        setattr(cls, meth, guard(old_get))

    return cls


def reorder(cls):
    """
        Decorator function to reorder all input and output channels, to preserve an inner axes order within the
        operator.
        Must be used in combination with reorder_options!!!

        For every slot of a decorated operator, the distinction has to be made, if the slot was called by the operator
        itself, i.e. by one of its methods, or on the operator object from the 'outside'.

        Pseudo example to clarify:

        @reorder
        @reorder_options(internal_axis_order='txyzc', # set in stone by original dev
                         ignore_slots=['i_already_follow_the_new_outside_order'],
                         output_axes_order='tczyx' # new order (e.g. the future standard)
                         )
            class MyOp(operator):
            Input = InputSlot()
            Output = OutputSlot()

            anarchySlot = InputSlot()

            def __init__(self):
                super().__init__()
                self.childOp = ChildOp()

                # direct connection of slots, not affected by reorder decorator
                self.childOp.InputA.connect(self.anarchySlot)

            def setupOutputs(self):
                # everything in here is automatically converted with respect to the inner and outer axes orders
                # In-between childOp's slot and this operator's slot a hidden OpReorderAxes is connected, which was
                # added by the reorder decorator
                self.childOp.InputB.connect(self.Input)
                self.Output.connect(self.childOp.Output)
    """
    if '_not_reordered_slots' not in dir(cls):
        cls._not_reordered_slots = []

    cls = guard_methods(cls)

    inputSlots = [s.name for s in cls.inputSlots
                  if s.name not in cls._not_reordered_slots]
    outputSlots = [s.name for s in cls.outputSlots
                   if s.name not in cls._not_reordered_slots]

    cls._inner_call = False  # use this variable to distinguish in __getattribute__, which slot to return

    # change __init__ in order to squeeze in the opReorderAxes ops
    old_init = getattr(cls, '__init__')

    def guard(fn):
        @functools.wraps(old_init)
        def wrap(self, *args, graph=None, parent=None, **kwargs):
            ret = fn(self, *args, graph=graph, parent=parent, **kwargs)
            graph, parent = self.graph, self.parent
            self._inner_call = False

            self._opReorderInput = {}
            for name in inputSlots:
                self._opReorderInput[name] = OpReorderAxes(parent=self)

            self._opReorderOutput = {}
            for name in outputSlots:
                self._opReorderOutput[name] = OpReorderAxes(parent=self)

            return ret
        return wrap

    setattr(cls, '__init__', guard(old_init))

    # change setupOutputs in order to connect the squeezed in opReorderAxes ops
    old_setupOutputs = getattr(cls, 'setupOutputs')

    def guard(fn):
        @functools.wraps(old_setupOutputs)
        def wrap(self, *args, **kwargs):
            self._inner_call = False
            for name in inputSlots:
                self._opReorderInput[name].AxisOrder.setValue(self._internal_axes_order)

                slot = self.__getattribute__(name)
                self._opReorderInput[name].Input.connect(slot)

            for name in outputSlots:
                self._opReorderOutput[name].AxisOrder.setValue(cls._output_axes_order)

                slot = self.__getattribute__(name)
                slot.connect(self._opReorderOutput[name].Output)

            self._inner_call = True
            ret = fn(self, *args, **kwargs)
            self._inner_call = False

            return ret
        return wrap

    setattr(cls, 'setupOutputs', guard(old_setupOutputs))

    # change __getattribute__ in order to squeeze in the opReorderAxes ops
    def __getattribute__(self, name):
        if name in inputSlots:
            if self._inner_call:
                return self._opReorderInput[name].Output

        elif name in outputSlots:
            if self._inner_call:
                return self._opReorderOutput[name].Input

        return super(cls, self).__getattribute__(name)

    setattr(cls, '__getattribute__', __getattribute__)
    return cls
