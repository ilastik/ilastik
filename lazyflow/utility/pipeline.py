###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
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
# 		   http://ilastik.org/license/
###############################################################################

from collections import abc
from typing import Any, Callable, TypeVar

from lazyflow.operator import Operator
from lazyflow.slot import Slot


T = TypeVar("T", bound=Operator)


class Pipeline(abc.Sequence):
    """Connect operators in a linear chain.

    Each operator in the pipeline should have an input slot named "Input" and an output slot named "Output",
    with the exception of the first operator (no "Input" required) and the last operator (no "Output" required).
    For every operator in the pipeline except the first one, it's slot named "Input" gets connected
    to the slot named "Output" of the previous operator.

    Examples:

        Pipeline of 3 operators with the last op having an extra input from another op::

            graph = Graph()
            opSideways = OpSideways(graph=graph)
            with Pipeline(graph=graph) as pipeline:
                pipeline.add(StartOp, Input="spam")
                pipeline.add(MiddleOp, SomeFlag=True)
                pipeline.add(FinalOp, OtherConnection=opSideways.Output)
                pipeline[-1].Output[:].wait()
    """

    def __init__(self, **op_init_kwargs: Any):
        """Create a new, empty pipeline.

        Args:
            **op_init_kwargs: Keyword arguments passed to ``opfunc`` in :meth:`add`.
        """
        self._op_init_kwargs = op_init_kwargs
        self._ops = []

    def add(self, opfunc: Callable[..., T], **slots: Any) -> T:
        """Add a new operator to the end of this pipeline.

        The operator instance is created with the ``**op_init_kwargs`` previously passed to ``__init__``,
        it's "Input" gets connected to "Output" of previous operator (if it exists), and it's other input slots
        are configured, based on the contents of `**slots``.
        For each argument in `**slots`, it's name is used as a name of the input slot of the new operator,
        and, if a value of that argument is a :class:`Slot`, it is connected to the new operator
        with :meth:`Operator.connect`. Otherwise, :meth:`Operator.setValue` is used.

        Args:
            opfunc: Callable used to create a new operator.
            **slots: values or output slots that get assigned to the new operator.

        Returns:
            The new, configured operator.
        """
        op = opfunc(**self._op_init_kwargs)

        default_connect = self and hasattr(op, "Input") and hasattr(self[-1], "Output")
        if self:
            if "Input" in slots:
                raise ValueError('slot with the name "Input" cannot be manually assigned for non-first operator')
            if not hasattr(op, "Input") and not slots:
                raise ValueError(f'new operator {op} does not have a slot with the name "Input"')
            if not hasattr(self[-1], "Output") and not slots:
                raise ValueError(f'previous operator {self[-1]} does not have a slot with the name "Output"')
            if default_connect:
                op.Input.connect(self[-1].Output)

        for name, value in slots.items():
            if isinstance(value, Slot):
                op.inputs[name].connect(value)
            else:
                op.inputs[name].setValue(value)

        self._ops.append(op)
        return op

    def close(self) -> None:
        """Cleanup all operators in this pipeline in the LIFO order."""
        for op in reversed(self):
            op.cleanUp()

    def __getitem__(self, item: int) -> Operator:
        return self._ops.__getitem__(item)

    def __len__(self) -> int:
        return self._ops.__len__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
