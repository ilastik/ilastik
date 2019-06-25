from builtins import next

from builtins import range
from builtins import object
from future.utils import raise_with_traceback
import sys

if sys.version_info.major >= 3:
    unicode = str

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
# Python
import logging
import collections
import itertools
import threading
from functools import partial, wraps
from contextlib import contextmanager
import warnings

# SciPy
import numpy

import vigra

# lazyflow
from lazyflow import rtype
from lazyflow.roi import TinyVector
from lazyflow.request import Request
from lazyflow.stype import ArrayLike
from lazyflow.metaDict import MetaDict
from lazyflow.utility import slicingtools, OrderedSignal


class ValueRequest(object):
    """Pseudo request that behaves like a request.Request object.

    This object is used to prevent the heavy construction of complete
    Request objects in simple cases where they are not needed.

    """

    def __init__(self, value):
        self.result = value
        self.started = False

    def wait(self):
        return self.result

    def block(self):
        pass

    def submit(self):
        pass

    def notify_finished(self, callback):
        callback(self.result)

    def notify_failed(self, callback):
        pass

    def notify_cancelled(self, callback):
        pass

    def clean(self):
        self.result = None

    def writeInto(self, destination):
        # Unfortunately, there appears to be a bug when copying masked arrays
        # ( https://github.com/numpy/numpy/issues/5558 ).
        # So, this must be used in the interim.
        if isinstance(destination, numpy.ma.masked_array):
            destination.data[...] = numpy.ma.getdata(self.result)
            destination.mask[...] = numpy.ma.getmaskarray(self.result)
            if isinstance(self.result, numpy.ma.masked_array):
                destination.fill_value = self.result.fill_value
        elif isinstance(destination, collections.MutableSequence) or isinstance(
            self.result, collections.MutableSequence
        ):
            destination[:] = self.result[:]
        else:
            destination[...] = self.result[...]

        return self


def is_setup_fn(func):
    """
    Decorator.  Marks the function as a 'setup' function,
    which means it affects the state of the graph connections.
    All Slot methods that will result in any operator setupOutputs()
    calls should be marked as setup functions using this decorator.

    Executes the function within the context of a
    Graph setup operation, which tells the Graph that we are
    making graph setup changes by incrementing a counter for
    each nested setup function call. See graph.py for details.
    """

    @wraps(func)
    def call_in_setup_context(self, *args, **kwargs):
        if not self.graph:
            return func(self, *args, **kwargs)
        with self.graph.SetupDepthContext(self.graph):
            return func(self, *args, **kwargs)

    call_in_setup_context.__wrapped__ = func  # Emulate python 3 behavior of @wraps
    return call_in_setup_context


class Slot(object):
    """
    Base class for InputSlot, OutputSlot
    """

    loggerName = __name__ + ".Slot"
    logger = logging.getLogger(loggerName)
    traceLogger = logging.getLogger("TRACE." + loggerName)

    # Allow slots to be sorted by their order of creation for debug
    # output and diagramming purposes.
    _global_counter = itertools.count()

    class SlotNotReadyError(Exception):
        pass

    @property
    def graph(self):
        return (self.operator or None) and self.operator.graph

    def __init__(
        self,
        name="",
        operator=None,
        stype=ArrayLike,
        rtype=rtype.SubRegion,
        value=None,
        optional=False,
        level=0,
        nonlane=False,
        allow_mask=False,
    ):
        """Constructor of the Slot class.

        :param name: user readable name of the slot, is normally
          assigned automatically by the Operator

        :param operator: the parent operator of a slot

        :param stype: the slot type (see stype.py)

        :param rtype: the region of interest type (see rtype.py)

        :param value: the default value of the slot

        :param optional: if True this means the slot needs a value or
          connection for its parent operator to be functional

        :param level: defines the dimensionality of the slot. 0 for
          single element (e.g. single numpy.ndarray), 1 for list of
          elements (e.g. list of strings), 2 for list of list of
          elements.

        :param nonlane: For multislot, this flag protects it from
          being considered lane-indexed

        """
        # This assertion is here for a reason: default values do NOT work on OutputSlots.
        # (We should probably change that at some point...)
        assert value is None or isinstance(
            self, InputSlot
        ), "Only InputSlots can have default values.  OutputSlots cannot."

        # If we do not support masked arrays, ensure that we are not being passed one.
        assert allow_mask or not isinstance(value, numpy.ma.masked_array), (
            'The operator, "%s", is being setup to receive a masked array as input to slot, "%s".'
            " This is currently not supported." % (self.operator.name, self.name)
        )

        # Check for simple mistakes in parameter order...
        assert isinstance(name, (str, unicode))
        assert isinstance(optional, bool)

        if not hasattr(self, "_type"):
            self._type = None
        if isinstance(stype, (str, unicode)):
            stype = ArrayLike
        self.downstream_slots = []
        self.name = name
        self._optional = optional
        self.operator = operator
        self.allow_mask = allow_mask
        self._real_operator = None  # Memoized in getRealOperator()

        # in the case of an InputSlot this is the slot to which it is
        # connected
        self.upstream_slot = None
        self.level = level

        # in the case of an InputSlot one can directly assign a value
        # to a slot instead of connecting it to an upstream_slot, this
        # attribute holds the value
        self._value = None

        self._defaultValue = value

        # Causes calls to setValue to be propagated backwards to the
        # upstream_slot. Used by the OperatorWrapper.
        self._backpropagate_values = False

        self.rtype = rtype

        # the MetaDict that holds the slots meta information
        self.meta = MetaDict()

        # if level > 0, this holds the sub-Input/Output slots
        self._subSlots = []
        self._stypeType = stype

        # the slot type instance
        self.stype = stype(self)
        self.nonlane = nonlane

        self._sig_changed = OrderedSignal(hide_cancellation_exceptions=True)
        self._sig_value_changed = OrderedSignal(hide_cancellation_exceptions=True)
        self._sig_ready = OrderedSignal(hide_cancellation_exceptions=True)
        self._sig_unready = OrderedSignal(hide_cancellation_exceptions=True)
        self._sig_dirty = OrderedSignal(hide_cancellation_exceptions=True)
        self._sig_connect = OrderedSignal(hide_cancellation_exceptions=True)
        self._sig_disconnect = OrderedSignal(hide_cancellation_exceptions=True)
        self._sig_resize = OrderedSignal(hide_cancellation_exceptions=True)
        self._sig_resized = OrderedSignal(hide_cancellation_exceptions=True)
        self._sig_remove = OrderedSignal(hide_cancellation_exceptions=True)
        self._sig_removed = OrderedSignal(hide_cancellation_exceptions=True)
        self._sig_insert = OrderedSignal(hide_cancellation_exceptions=True)
        self._sig_inserted = OrderedSignal(hide_cancellation_exceptions=True)

        self._resizing = False

        self._executionCount = 0
        self._settingUp = False
        self._condition = threading.Condition()

        # Allow slots to be sorted by their order of creation for
        # debug output and diagramming purposes.
        self._global_slot_id = next(Slot._global_counter)

    ###########################
    #  A p i    M e t h o d s #
    ###########################
    def _notifyGeneric(self, sig, function, **kwargs):
        """
        Subscribe the given callback function (with optional kwargs) to the given signal.

        Special feature:
            If kwargs['defer'] is True, then we'll defer executing the
            callback until after the graph is completed setup.

            In other words, when the signal is fired, the callback isn't executed immediately.
            Instead, it's queued to the Graph's call_when_setup_finished signal.
            This is useful when you have a GUI callback that you want to execute after the
            graph setup operation is totally finished.

        Returns:
            A callable that will unsubscribe your function from the signal.
        """
        if "defer" in kwargs and kwargs["defer"]:
            del kwargs["defer"]

            def queue_callback(*args):
                self.graph.call_when_setup_finished(partial(function, *args, **kwargs))

            sig.subscribe(queue_callback)
            return partial(sig.unsubscribe, queue_callback)
        else:
            sig.subscribe(function, **kwargs)
            return partial(sig.unsubscribe, function)

    def notifyDirty(self, function, **kwargs):
        """
        calls the corresponding function when the slot gets dirty
        first argument of the function is the slot, second argument the roi
        the keyword arguments follow
        """
        return self._notifyGeneric(self._sig_dirty, function, **kwargs)

    def notifyMetaChanged(self, function, **kwargs):
        """calls the corresponding function when the slot meta
        information is changed

        first argument of the function is the slot
        the keyword arguments follow

        """
        return self._notifyGeneric(self._sig_changed, function, **kwargs)

    def notifyValueChanged(self, function, **kwargs):
        """Used by slots with cached values to notify when the cache
        has changed, even if the output is not dirty.

        """
        return self._notifyGeneric(self._sig_value_changed, function, **kwargs)

    def notifyReady(self, function, **kwargs):
        """Calls the corresponding function when the slot is "ready",
        meaning it is connected and will produce data when called.
        This is implemented by manipulating and monitoring a flag in
        the slot metadata.

        first argument of the function is the slot
        the keyword arguments follow

        """
        return self._notifyGeneric(self._sig_ready, function, **kwargs)

    def notifyUnready(self, function, **kwargs):
        """
        Subscribe to "unready" callbacks.  See notifyReady for details.
        """
        return self._notifyGeneric(self._sig_unready, function, **kwargs)

    def _notifyConnect(self, function, **kwargs):
        """
        calls the corresponding function when the slot is connected
        first argument of the function is the slot
        the keyword arguments follow
        """
        return self._notifyGeneric(self._sig_connect, function, **kwargs)

    def notifyDisconnect(self, function, **kwargs):
        """
        calls the corresponding function when the slot is disconnected
        first argument of the function is the slot
        the keyword arguments follow
        """
        return self._notifyGeneric(self._sig_disconnect, function, **kwargs)

    def notifyResize(self, function, **kwargs):
        """
        calls the corresponding function before the slot is resized
        first argument of the function is the slot
        second argument is the old size and the third
        argument is the new size
        the keyword arguments follow
        """
        return self._notifyGeneric(self._sig_resize, function, **kwargs)

    def notifyResized(self, function, **kwargs):
        """
        calls the corresponding function after the slot is resized
        first argument of the function is the slot
        second argument is the old size and the third
        argument is the new size
        the keyword arguments follow
        """
        return self._notifyGeneric(self._sig_resized, function, **kwargs)

    def notifyRemove(self, function, **kwargs):
        """
        calls the corresponding function BEFORE a slot is removed
        first argument of the function is the slot
        second argument is the old size and the third
        argument is the new size
        the keyword arguments follow
        """
        return self._notifyGeneric(self._sig_remove, function, **kwargs)

    def notifyRemoved(self, function, **kwargs):
        """
        calls the corresponding function AFTER a slot is removed
        first argument of the function is the slot
        second argument is the old size and the third
        argument is the new size
        the keyword arguments follow
        """
        return self._notifyGeneric(self._sig_removed, function, **kwargs)

    def notifyInsert(self, function, **kwargs):
        """
        calls the corresponding function BEFORE a slot has been added
        first argument of the function is the slot
        second argument is the old size and the third
        argument is the new size
        the keyword arguments follow
        """
        return self._notifyGeneric(self._sig_insert, function, **kwargs)

    def notifyInserted(self, function, **kwargs):
        """
        calls the corresponding function AFTER a slot has been added
        first argument of the function is the slot
        second argument is the old size and the third
        argument is the new size
        the keyword arguments follow
        """
        return self._notifyGeneric(self._sig_inserted, function, **kwargs)

    def unregisterDirty(self, function):
        """
        unregister a dirty callback
        """
        self._sig_dirty.unsubscribe(function)

    def _unregisterConnect(self, function):
        """
        unregister a connect callback
        """
        self._sig_connect.unsubscribe(function)

    def unregisterDisconnect(self, function):
        """
        unregister a disconnect callback
        """
        self._sig_disconnect.unsubscribe(function)

    def unregisterMetaChanged(self, function):
        """
        unregister a changed callback
        """
        self._sig_changed.unsubscribe(function)

    def unregisterValueChanged(self, function):
        """
        unregister a value changed callback
        """
        self._sig_value_changed.unsubscribe(function)

    def unregisterReady(self, function):
        """
        unregister a ready callback
        """
        self._sig_ready.unsubscribe(function)

    def unregisterUnready(self, function):
        """
        unregister an unready callback
        """
        self._sig_unready.unsubscribe(function)

    def unregisterResize(self, function):
        """
        unregister a resize callback
        """
        self._sig_resize.unsubscribe(function)

    def unregisterResized(self, function):
        """
        unregister a resized callback
        """
        self._sig_resized.unsubscribe(function)

    def unregisterRemove(self, function):
        """
        unregister a remove callback
        """
        self._sig_remove.unsubscribe(function)

    def unregisterRemoved(self, function):
        """
        unregister a removed callback
        """
        self._sig_removed.unsubscribe(function)

    def unregisterInsert(self, function):
        """
        unregister a insert callback
        """
        self._sig_insert.unsubscribe(function)

    def unregisterInserted(self, function):
        """
        unregister a inserted callback
        """
        self._sig_inserted.unsubscribe(function)

    def _handleUpstreamUnready(self, slot):
        """
        This handler ensures that UNready status propagates quickly
        through the graph (before the normal _changed path)
        """
        if self.meta._ready:
            self.meta._ready = False
            self._sig_unready(self)

    def setOrConnect(self, value_or_slot):
        if isinstance(value_or_slot, Slot):
            self.connect(value_or_slot)
        else:
            self.setValue(value_or_slot)

    def setOrConnectIfAvailable(self, value_or_slot):
        if value_or_slot is None:
            return
        self.setOrConnect(value_or_slot)

    @is_setup_fn
    def connect(self, upstream_slot, notify=True, permit_distant_connection=False):
        """
        Connect a slot to another slot

        Arguments:
          upstream_slot   : the slot to which this slot is conencted
        """
        try:

            if upstream_slot is None:
                self.disconnect()
                return

            assert isinstance(upstream_slot, Slot), (
                "Slot.connect() can only be used to connect other Slots. Did " "you mean to use Slot.setValue()?"
            )
            assert self.allow_mask or (not upstream_slot.meta.has_mask), (
                'The operator, "%s", is being setup to receive a masked array as input to slot, "%s",'
                ' from the output slot, "%s", on operator, "%s". This is currently not supported.'
                % (self.operator.name, self.name, upstream_slot.name, upstream_slot.operator.name)
            )

            my_op = self.getRealOperator()
            partner_op = upstream_slot.getRealOperator()
            if partner_op and not (
                partner_op.parent is my_op.parent
                or (self._type == "output" and partner_op.parent is my_op)
                or (self._type == "input" and my_op.parent is partner_op)
                or my_op is partner_op
            ):
                if not permit_distant_connection:
                    msg = (
                        "It is forbidden to connect slots of operators that are not siblings "
                        "or not directly related as parent and child."
                    )
                    if partner_op.parent is None or my_op.parent is None:
                        msg += "\n(For one of your operators, parent=None.  Was it already cleaned up?"
                    raise Exception(msg)

            if self.upstream_slot is upstream_slot and upstream_slot.level == self.level:
                return
            if self.level == 0:
                self.disconnect()

            if upstream_slot is not None:
                upstream_slot._sig_unready.subscribe(self._handleUpstreamUnready)
                self._value = None
                if upstream_slot.level == self.level:
                    assert upstream_slot.stype.isCompatible(type(self.stype)), (
                        "Can't connect slots of non-matching stypes!"
                        f"Tried to connect {self.getRealOperator()} with {upstream_slot.getRealOperator()}."
                        " Attempting to connect '{}' (stype: {}) to '{}' (stype: {})".format(
                            self.name, self.stype, upstream_slot.name, upstream_slot.stype
                        )
                    )

                    self.upstream_slot = upstream_slot
                    notifyReady = self.upstream_slot.meta._ready and not self.meta._ready
                    self.meta = self.upstream_slot.meta.copy()

                    # the slot with more sub-slots determines
                    # the number of subslots
                    if len(self) < len(upstream_slot):
                        self.resize(len(upstream_slot))
                    elif len(self) > len(upstream_slot):
                        upstream_slot.resize(len(self))

                    upstream_slot.downstream_slots.append(self)
                    for i in range(len(self.upstream_slot)):
                        p = self.upstream_slot[i]
                        self[i].connect(p)

                    # call slot type connect function
                    self.stype.connect(upstream_slot)

                    if self.level > 0 or self.stype.isConfigured():
                        self._changed()

                    # call connect callbacks
                    self._sig_connect(self)

                    # Notify readiness after upstream_slot is updated
                    if notifyReady:
                        self._sig_ready(self)

                elif upstream_slot.level < self.level:
                    self.upstream_slot = upstream_slot
                    notifyReady = self.upstream_slot.meta._ready and not self.meta._ready
                    self.meta = self.upstream_slot.meta.copy()
                    for i, slot in enumerate(self._subSlots):
                        slot.connect(upstream_slot)

                    if notifyReady:
                        self._sig_ready(self)

                    self._changed()
                    # call connect callbacks
                    self._sig_connect(self)

                elif upstream_slot.level > self.level:
                    msg = str(
                        "Can't connect slots:"
                        " {}.{}.level={}, but"
                        " {}.{}.level={}"
                        " (Implicit OpearatorWrapper creation"
                        " is no longer supported.)"
                    ).format(
                        self.getRealOperator().name,
                        self.name,
                        self.level,
                        upstream_slot.getRealOperator().name,
                        upstream_slot.name,
                        upstream_slot.level,
                    )
                    raise RuntimeError(msg)

                # propagate value changed signals from inner to outer
                # operators.
                if self._type == upstream_slot._type == "output":
                    upstream_slot.notifyValueChanged(self._sig_value_changed)

        except:
            try:
                raise
            finally:
                try:
                    # We would like to clean up by calling self.disconnect()
                    # ... but if that raises an exception, it OVERWRITES the original exception.
                    # This complicated nest of try/except/finally is supposed to prevent that from happening.
                    # For example, see the bottom of this site:
                    # http://doughellmann.com/2009/06/19/python-exception-handling-techniques.html
                    # And yet, that DOESN'T work here for some unknown reason.
                    # Hence, we can't actually clean up.
                    # What a bummer.

                    ##self.disconnect() # commented out because it might throw and hide the original exception. See note above.
                    pass
                except:
                    # Well, this is bad.  We caused an exception while handling an exception.
                    # We're more interested in the FIRST exception, so print this one out and
                    #  continue unwinding the stack with the first one.
                    self.logger.error("Error: Caught a secondary exception while handling a different exception.")
                    import traceback

                    traceback.print_exc()
                    pass

    @is_setup_fn
    def disconnect(self):
        """
        Disconnect a InputSlot from its upstream_slot
        """
        if self.backpropagate_values and self.getRealOperator() and not self.getRealOperator()._cleaningUp:
            if self.upstream_slot is not None:
                self.upstream_slot.disconnect()
            return

        for slot in self._subSlots:
            slot.disconnect()

        had_upstream_slot = False
        if self.upstream_slot is not None:
            had_upstream_slot = True
            # safe to unsubscribe, even if not subscribed
            self.upstream_slot._sig_unready.unsubscribe(self._handleUpstreamUnready)
            try:
                self.upstream_slot.downstream_slots.remove(self)
            except ValueError:
                pass
        self.upstream_slot = None
        had_value = self._value is not None
        self._value = None
        oldReady = self.meta._ready
        self.meta = MetaDict()

        if len(self._subSlots) > 0 and self.getRealOperator() and not self.getRealOperator()._cleaningUp:
            self.resize(0)

        # call callbacks
        if had_upstream_slot or had_value:
            self._sig_disconnect(self)

        # Notify our downstream_slots that we changed.
        self._changed()

        # If we were ready before, signal that we aren't any more
        if oldReady:
            self._sig_unready(self)

    @is_setup_fn
    def resize(self, size):
        """
        Resizes a slot to the desired length

        Arguments:
          size    : the desired number of subslots
        """
        assert numpy.issubdtype(type(size), numpy.integer), "Bug: 'size' must be int, not {}".format(type(size))

        if self._resizing:
            return
        if self.level == 0:
            raise RuntimeError("Can't resize a level-0 slot!")

        oldsize = len(self)
        if size == oldsize:
            return

        self._resizing = True
        if self.operator is not None:
            self.logger.debug("Resizing slot {} of operator {} to size {}".format(self.name, self.operator.name, size))

        # call before resize callbacks
        self._sig_resize(self, oldsize, size)

        new_subslots = []
        while size > len(self):
            self.insertSlot(len(self), len(self) + 1, propagate=False)
            new_subslots.append(len(self) - 1)

        while size < len(self):
            self.removeSlot(len(self) - 1, len(self) - 1, propagate=False)

        # propagate size change downward
        for c in self.downstream_slots:
            if c.level == self.level:
                c.resize(size)

        # propagate size change upward
        if self.upstream_slot and len(self.upstream_slot) < size and self.upstream_slot.level == self.level:
            self.upstream_slot.resize(size)

        # connect newly added slots
        # We must connect these subslots here, AFTER all resizes have propagated up and down through the graph.
        # Otherwise, our new subslots may lose downstream_slots (happens in "diamond" shaped graphs.)
        for i in new_subslots:
            self._connectSubSlot(i)

        # call after resize callbacks
        self._sig_resized(self, oldsize, size)

        self._resizing = False

    @is_setup_fn
    def insertSlot(self, position, finalsize, propagate=True):
        """
        Insert a new slot at the specified position
        finalsize indicates the final destination size
        """
        if len(self) >= finalsize:
            return self[position]

        # call after insert callbacks
        self._sig_insert(self, position, finalsize)

        slot = self._insertNew(position)

        # New slot inherits our settings
        slot.backpropagate_values = self.backpropagate_values

        operator_name = "<NO OPERATOR>"
        if self.operator:
            operator_name = self.operator.name
        self.logger.debug(
            "Inserting slot {} into slot {} of operator {} to size {}".format(
                position, self.name, operator_name, finalsize
            )
        )
        if propagate:
            if self.upstream_slot is not None and self.upstream_slot.level == self.level:
                self.upstream_slot.insertSlot(position, finalsize)

            for p in self.downstream_slots:
                if p.level == self.level:
                    p.insertSlot(position, finalsize)

            self._connectSubSlot(position)

        # call after insert callbacks
        self._sig_inserted(self, position, finalsize)
        return slot

    @is_setup_fn
    def removeSlot(self, position, finalsize, propagate=True):
        """
        Remove the slot at position
        finalsize indicates the final size of all subslots
        """
        if len(self) <= finalsize:
            return None
        assert position < len(self)
        if self.operator is not None:
            self.logger.debug(
                "Removing slot {} into slot {} of operator {} to size {}".format(
                    position, self.name, self.operator.name, finalsize
                )
            )

        # call before-remove callbacks
        self._sig_remove(self, position, finalsize)

        slot = self._subSlots.pop(position)
        slot.disconnect()
        slot.operator = None
        slot._real_operator = None
        if propagate:
            if self.upstream_slot is not None and self.upstream_slot.level == self.level:
                self.upstream_slot.removeSlot(position, finalsize)
            for p in self.downstream_slots:
                if p.level == self.level:
                    p.removeSlot(position, finalsize)

        # call after-remove callbacks
        self._sig_removed(self, position, finalsize)

    def get(self, roi):
        """This method is used to retrieve the actual content of a Slot.

        :param roi: the region of interest, e.g. a subregion in the
        case of an ArrayLike stype

        :param destination: this may define a destination area for the
          request, for example a ndarray into which the results should
          be written in the case of an ArrayLike stype

        Returns:
          a request.Request object.

        """
        if self._value is not None:
            # this handles the case of an inputslot
            # having a ._value
            # --> construct cheaper request object for this case
            result = self.stype.writeIntoDestination(None, self._value, roi)
            return ValueRequest(result)
        elif self.upstream_slot is not None:
            # this handles the case of an inputslot
            # --> just relay the request
            return self.upstream_slot.get(roi)
        else:
            if not self.ready():
                # Something is wrong.  Are we cancelled?
                Request.raise_if_cancelled()

                msg = "Can't get data from slot {}.{} yet." " It isn't ready." "First upstream problem slot is: {}"
                problem_slot = Slot._findUpstreamProblemSlot(self)
                problem_str = str(problem_slot)
                if isinstance(problem_slot, Slot):
                    problem_op = problem_slot.getRealOperator()
                    problem_str = problem_op.name + "/" + str(problem_slot)
                msg = msg.format(self.getRealOperator() and self.getRealOperator().__class__, self.name, problem_str)
                raise Slot.SlotNotReadyError(msg)

            # If someone is asking for data from an inputslot that has
            #  no value and no upstream_slot, then something is wrong.
            if self._type == "input":
                # Something is wrong.  Are we cancelled?
                Request.raise_if_cancelled()
                assert (
                    self._type != "input"
                ), "This inputSlot has no value and no upstream_slot.  You can't ask for its data yet!"
            # normal (outputslot) case
            # --> construct heavy request object..
            execWrapper = Slot.RequestExecutionWrapper(self, roi)
            request = Request(execWrapper)

            return request

    @staticmethod
    def _findUpstreamProblemSlot(slot):
        if slot.upstream_slot is not None:
            return Slot._findUpstreamProblemSlot(slot.upstream_slot)
        if slot.getRealOperator() is not None:
            for inputSlot in list(slot.getRealOperator().inputs.values()):
                if not inputSlot._optional and not inputSlot.ready():
                    return inputSlot
        return "Couldn't find an upstream problem slot."

    class RequestExecutionWrapper:
        __slots__ = ("started", "finished", "slot", "operator", "roi")

        def __init__(self, slot, roi):
            self.started = False
            self.finished = False
            self.slot = slot
            self.operator = slot.operator
            self.roi = roi

        def __call__(self, destination=None):
            # store whether the user wants the results in a given
            # destination area
            destination_given = destination is not None

            if destination is None:
                destination = self.slot.stype.allocateDestination(self.roi)
            else:
                if self.slot.meta.dtype is not None and hasattr(destination, "dtype"):
                    assert self.slot.meta.dtype == destination.dtype, (
                        "Can't provide a destination array of the wrong dtype.  "
                        "Slot generates {}, but you gave {}".format(self.slot.meta.dtype, destination.dtype)
                    )

            # We are executing the operator. Incremement the execution
            # count to protect against simultaneous setupOutputs()
            # calls.
            self._incrementOperatorExecutionCount()

            try:
                # Execute the workload, which might not ever return
                # (if we get cancelled).
                result_op = self.operator.execute(self.slot, (), self.roi, destination)

                # copy data from result_op to destination, if
                # destination was actually given by the user, and the
                # returned result_op is different from destination.
                # (but don't copy if result_op is None, this means
                # legacy op which wrote into destination anyway)
                if result_op is not None:
                    self.slot.stype.check_result_valid(self.roi, result_op)

                    if destination_given and id(result_op) != id(destination):
                        self.slot.stype.copy_data(dst=destination, src=result_op)
                    else:
                        destination = result_op

                return destination

            finally:
                self._decrementOperatorExecutionCount()

        def _incrementOperatorExecutionCount(self):
            self.started = True
            assert self.operator._executionCount >= 0, "BUG: How did the execution count get negative?"
            # We can't execute while the operator is in the middle of
            # setupOutputs
            with self.operator._condition:
                while self.operator._settingUp:
                    self.operator._condition.wait()
                self.operator._executionCount += 1

        def _decrementOperatorExecutionCount(self):
            # Only do this once per execution. If we were cancelled
            # after we finished working, don't do anything
            if self.started and not self.finished:
                assert self.operator._executionCount > 0, "BUG: Can't decrement the execution count below zero!"
                self.finished = True
                with self.operator._condition:
                    self.operator._executionCount -= 1
                    self.operator._condition.notifyAll()

    @is_setup_fn
    def setDirty(self, *args, **kwargs):
        """This method is called by a partnering OutputSlot when its
        content changes.

        The 'key' parameter identifies the changed region
        of an numpy.ndarray

        """
        assert self.operator is not None, (
            "Slot '{}' cannot be set dirty," " slot not belonging to any" " actual operator instance".format(self.name)
        )

        if self.stype.isConfigured():
            if len(args) == 0 or not isinstance(args[0], rtype.Roi):
                roi = self.rtype(self, *args, **kwargs)
            else:
                roi = args[0]

            for c in self.downstream_slots:
                c.setDirty(roi)

            # call callbacks
            self._sig_dirty(self, roi)

            if self._type == "input" and self.operator.configured():
                self.operator.propagateDirty(self, (), roi)

    def __iter__(self):
        assert self.level >= 1
        return self._subSlots.__iter__()

    def __getitem__(self, key):
        """If level=0, emulate __call__ but with a slicing instead of
        a roi.

        If level>0, return the subslot corresponding to the key, which
        may be a tuple

                          """
        if self.level > 0:
            if isinstance(key, tuple):
                assert len(key) > 0
                assert len(key) <= self.level
                if len(key) == 1:
                    return self._subSlots[key[0]]
                else:
                    return self._subSlots[key[0]][key[1:]]
            return self._subSlots[key]
        else:
            if self.meta.shape is None:
                # Something is wrong.  Are we cancelled?
                Request.raise_if_cancelled()
                if not self.ready():
                    # msg = "This slot ({}.{}) isn't ready yet, which means " \
                    #      "you can't ask for its data.  Is it connected?".format(self.getRealOperator() and self.getRealOperator().name, self.name)
                    # self.logger.error(msg)
                    problem_slot = Slot._findUpstreamProblemSlot(self)
                    problem_str = str(problem_slot)
                    if isinstance(problem_slot, Slot):
                        problem_op = problem_slot.getRealOperator()
                        if problem_op is not None:
                            problem_str = problem_op.name + "/" + str(problem_slot)
                        else:
                            problem_str = "<NO OPERATOR> /" + str(problem_slot)
                    slotInfoMsg = (
                        "Can't get data from slot {}.{} yet."
                        " It isn't ready."
                        "First upstream problem slot is: {}"
                        "".format(self.getRealOperator() and self.getRealOperator().__class__, self.name, problem_str)
                    )
                    # self.logger.error(slotInfoMsg)
                    raise Slot.SlotNotReadyError(slotInfoMsg)
                assert self.meta.shape is not None, (
                    "Can't ask for slices of this slot yet:"
                    " self.meta.shape is None!"
                    " (operator {} [self={}] slot: {}, key={}".format(self.operator.name, self.operator, self.name, key)
                )
            return self(pslice=key)

    def __setitem__(self, key, value):
        """This method provides access to the subslots of a
        MultiSlot.

        """
        assert not isinstance(value, Slot), "Can't use setitem to connect slots.  Use connect()"
        assert self.level == 0, "setitem can only be used with slots of level 0." " Did you forget to append a key?"
        assert self.operator is not None, "cannot do __setitem__ on Slot '{}' -> no operator !!"
        assert slicingtools.is_bounded(key), "Can't use Slot.__setitem__ with keys that include : or ..."
        # If we do not support masked arrays, ensure that we are not being passed one.
        assert self.allow_mask or not (self.meta.has_mask or isinstance(value, numpy.ma.masked_array)), (
            'The operator, "%s", is being setup to receive a masked array as input to slot, "%s".'
            " This is currently not supported." % (self.operator.name, self.name)
        )
        roi = self.rtype(self, pslice=key)
        if self._value is not None:
            self._value[key] = value

            # only propagate the dirty key at the very beginning of
            # the chain
            self.setDirty(roi)
        if self._type == "input":
            self.operator.setInSlot(self, (), roi, value)

        # Forward to downstream_slots
        for p in self.downstream_slots:
            p[key] = value

    def index(self, slot):
        return self._subSlots.index(slot)

    @is_setup_fn
    def setInSlot(self, slot, subindex, roi, value):
        """For now, Slots of level > 0 pretend to be operators (as far
        as their subslots are concerned). That's why they have to have
        this setInSlot() method.

        """
        # If we do not support masked arrays, ensure that we are not being passed one.
        assert self.allow_mask or not (self.meta.has_mask or isinstance(value, numpy.ma.masked_array)), (
            'The operator, "%s", is being setup to receive a masked array as input to slot, "%s".'
            " This is currently not supported." % (self.operator.name, self.name)
        )
        # Determine which subslot this is and prepend it to the totalIndex
        totalIndex = (self._subSlots.index(slot),) + subindex
        # Forward the call to our operator
        self.operator.setInSlot(self, totalIndex, roi, value)

    def __len__(self):
        """In the case of a MultiSlot this returns the number of
        subslots, i.e. the length of the list

        """
        return len(self._subSlots)

    @property
    def value(self):
        """This method directly returns the full content of a slot.

        Is mainly used when region of interest specification make no
        sense, e.g. in the case of slots which hold a single integer
        or float value

        """
        if self.upstream_slot is not None:
            # outputslot-inputsslot, inputslot-inputslot and outputslot-outputslot case
            temp = self[:].wait()
        elif self._value is None:
            # outputslot case
            temp = self[:].wait()
        else:
            # _value case
            return self._value
        if isinstance(temp, numpy.ndarray):
            if temp.shape == (1,):
                return temp[0]
            return temp
        elif isinstance(temp, list):
            return temp[0]
        else:
            warnings.warn(
                "FIXME: Slot.value for slot {} is {}," " which should be wrapped in an ndarray.".format(self.name, temp)
            )
            return temp

    @is_setup_fn
    def setValue(self, value, notify=True, check_changed=True, extra_meta={}):
        """This method can be used to directly assign a value to an
        InputSlot.

        Usually a slot is either connected to another slot from which
        it retrieves the content when it is queried, or it directly
        holds a value itself. This method can be used to set such a
        value.

        If check_changed is True, the new value is compared to the
        current one and updates are only triggered if the new value differs
        from the old one according to the __eq__ operator.
        The check can be turned off with the check_changed flag.

        If the value is a VigraArray, then shape/axistags/dtype will be automatically
        assigned in self.meta.  Additional metadata fields can be added via the
        extra_meta parameter.
        """
        try:
            assert isinstance(notify, bool)
            assert isinstance(check_changed, bool)

            # This assertion is here to prevent accidental use of setValue
            # when connect should be used. If your use case requires
            # passing slots as values, then this assertion can be refined.
            assert not isinstance(value, Slot), "When using setValue, value cannot be a slot.  Use connect instead."

            # If we do not support masked arrays, ensure that we are not being passed one.
            assert self.allow_mask or not (self.meta.has_mask or isinstance(value, numpy.ma.masked_array)), (
                'The operator, "%s", is being setup to receive a masked array as input to slot, "%s".'
                " This is currently not supported." % (self.operator.name, self.name)
            )

            if not self.backpropagate_values:
                assert self.upstream_slot is None, (
                    "Cannot call setValue on this slot."
                    " It is already connected to a upstream_slot."
                    " Call disconnect first if that's what you really wanted."
                )
            elif self.upstream_slot is not None:
                self.upstream_slot.setValue(value, notify, check_changed)
                return

            changed = True

            # We use == here instead of 'is' to avoid subtle bugs that
            #  can occur if you supplied an equivalent value that 'is not' the original.
            # For example: x=numpy.uint8(3); y=numpy.int64(3); assert x == y;  assert x is not y
            if check_changed:
                changed = False
                # Fast path checks for array types
                if isinstance(value, numpy.ndarray) or isinstance(self._value, numpy.ndarray):
                    if type(value) != type(self._value) or value.shape != self._value.shape:
                        changed = True
                if isinstance(value, numpy.ma.masked_array) and isinstance(self._value, numpy.ma.masked_array):
                    # Type comparison already checked as all masked arrays are subclasses of ndarrays.
                    # NAN does not compare equal so we need a way to check that separately.
                    if (value.fill_value != self._value.fill_value) and not (
                        numpy.isnan(value.fill_value) and numpy.isnan(self._value.fill_value)
                    ):
                        changed = True
                if isinstance(value, vigra.VigraArray) or isinstance(self._value, vigra.VigraArray):
                    if type(value) != type(self._value) or value.axistags != self._value.axistags:
                        changed = True

                if not changed:
                    # Slow path checks
                    same = value is self._value
                    if not same:
                        try:
                            same = value == self._value
                        except ValueError:
                            # Some values can't be compared with __eq__,
                            # in which case we assume the values are different
                            same = False
                        if isinstance(same, (numpy.ndarray, TinyVector)):
                            same = same.all()
                    changed = not same

            if changed:
                # call disconnect callbacks
                self._sig_disconnect(self)
                self._value = value
                self.stype.setupMetaForValue(value)

                for k, v in list(extra_meta.items()):
                    setattr(self.meta, k, v)

                self.meta._dirty = True

                for s in self._subSlots:
                    s.setValue(self._value)

                # a slot with a value is ready unless the value is None.
                if self._value is not None:
                    if self.meta._ready != True:
                        self.meta._ready = True
                        self._sig_ready(self)
                else:
                    if self.meta._ready != False:
                        self.meta._ready = False
                        self._sig_unready(self)

                # call connect callbacks
                self._sig_connect(self)
                self._changed()

                # Propagate dirtyness
                if self.rtype == rtype.List:
                    self.setDirty(())
                else:
                    self.setDirty(slice(None))
        except:
            try:
                raise
            finally:
                try:
                    # We would like to clean up by calling self.disconnect()
                    # ... but if that raises an exception, it OVERWRITES the original exception.
                    # This complicated nest of try/except/finally is supposed to prevent that from happening.
                    # For example, see the bottom of this site:
                    # http://doughellmann.com/2009/06/19/python-exception-handling-techniques.html
                    # And yet, that DOESN'T work here for some unknown reason.
                    # Hence, we can't actually clean up.
                    # What a bummer.

                    ##self.disconnect() # commented out because it might throw and hide the original exception. See note above.
                    pass
                except:
                    # Well, this is bad.  We caused an exception while handling an exception.
                    # We're more interested in the FIRST excpetion, so print this one out and
                    #  continue unwinding the stack with the first one.
                    self.logger.error("Error: Caught a secondary exception while handling a different exception.")
                    import traceback

                    traceback.print_exc()
                    pass

    @is_setup_fn
    def setValues(self, values):
        """Set values of subslots with arraylike object. Resizes the
        multinputslot with the length of the values array

        """
        try:
            # call disconnect callbacks
            self._sig_disconnect(self)
            self.resize(len(values))
            for i, s in enumerate(self._subSlots):
                s.setValue(values[i])
            # call connect callbacks
            self._changed()
            self._sig_connect(self)
        except:
            try:
                exc_info = sys.exc_info()
                self.disconnect()
            except:
                # Well, this is bad.  We caused an exception while handling an exception.
                # We're more interested in the FIRST excpetion, so print this one out and
                #  continue unwinding the stack with the first one.
                self.logger.error("Error: Caught a secondary exception while handling a different exception.")
                import traceback

                traceback.print_exc()
                exc_type, exc_value, exc_tb = exc_info
                raise_with_traceback(exc_type(exc_value), exc_tb)
            raise

    @property
    def backpropagate_values(self):
        return self._backpropagate_values

    @backpropagate_values.setter
    def backpropagate_values(self, backprop):
        self._backpropagate_values = backprop
        for slot in self._subSlots:
            slot.backpropagate_values = backprop

    def connected(self):
        """Returns True if the slot is connected to an upstream_slot or
        has a _value assigned as input

        """
        answer = True
        if self._value is None and self.upstream_slot is None:
            answer = False
        if answer is False and len(self._subSlots) > 0:
            answer = True
            for s in self._subSlots:
                if s.connected() is False:
                    answer = False
                    break
        return answer

    def configured(self):
        """Slots of level >= 1 must implement parts of the operator
        interface, including this function. This "operator" is
        considered "configured" if it is ready.

        """
        return self._optional or self.ready()

    def ready(self):
        if self.level == 0:
            # If this slot is non-multi, then just check our own
            # status
            ready = self.meta._ready
        else:
            # If this slot is multi, check all of our subslots. (If we
            # have no subslots, then we are NOT ready). Operators that
            # can properly handle an empty multi-input slot should
            # mark the input as optional.
            ready = len(self._subSlots) > 0 and all(p.ready() for p in self._subSlots)
        return ready

    def _setReady(self):
        wasReady = self.ready()

        for p in self._subSlots:
            p._setReady()

        self.meta._ready = (self.level == 0) or (len(self._subSlots) > 0)

        # If we just became ready...
        if not wasReady and self.meta._ready:
            # Notify downstream_slots of changed readystatus
            self._changed()
            self._sig_ready(self)

    def __call__(self, *args, **kwargs):
        """The slot relays all arguments to the __init__ method of the
        Roi type. This allows lazyflow to support different types of
        rois without knowing anything about them.

        """
        roi = self.rtype(self, *args, **kwargs)
        return self.get(roi)

    def getRealOperator(self):
        """If a slot is owned by a higher-level slot, self.operator is
        a slot. This function keeps going up the hierarchy until it
        finds the actual operator this slot belongs to.

        """
        if self._real_operator is not None:
            # use memoized
            return self._real_operator

        if isinstance(self.operator, Slot):
            self._real_operator = self.operator.getRealOperator()
        else:
            self._real_operator = self.operator

        return self._real_operator

    #####################
    #  Private  Methods #
    #####################
    def _getInstance(self, operator, **init_kwarg_overrides):
        """
        This method constructs a copy of the slot.
        This method is used when creating an Instance of an Operator.

        All slot parameters (e.g. level, optional, etc.) are copied, but can be overridden with the init_kwarg_overrides parameter.
        """
        init_kwargs = {}
        init_kwargs["stype"] = self._stypeType
        init_kwargs["rtype"] = self.rtype
        init_kwargs["value"] = self._defaultValue
        init_kwargs["level"] = self.level
        init_kwargs["nonlane"] = self.nonlane
        init_kwargs["allow_mask"] = self.allow_mask
        if self._type == "input":
            init_kwargs["optional"] = self._optional

        init_kwargs.update(init_kwarg_overrides)

        if self._type == "input":
            s = InputSlot(self.name, operator, **init_kwargs)
        elif self._type == "output":
            s = OutputSlot(self.name, operator, **init_kwargs)
        return s

    def maybe_call_within_transaction(self, fn):
        if self.graph:
            self.graph.maybe_call_within_transaction(fn)
        else:
            fn()

    def _changed(self):
        self.maybe_call_within_transaction(self._changed_impl)

    def _changed_impl(self):
        oldMeta = self.meta
        old_ready = self.ready()
        if self.upstream_slot is not None and self.meta != self.upstream_slot.meta:
            self.meta = self.upstream_slot.meta.copy()

        if self._type == "output":
            for o in self._subSlots:
                o._changed()

        # Notify readiness after subslots are updated
        if self.ready() != old_ready:
            if self.ready():
                self._sig_ready(self)
            else:
                self._sig_unready(self)

        wasdirty = self.meta._dirty
        if self.meta._dirty:
            assert self.allow_mask or (not self.meta.has_mask), (
                'The operator, "%s", is being setup to receive a masked array as input to slot, "%s".'
                " This is currently not supported." % (self.operator.name, self.name)
            )
            for c in self.downstream_slots:
                c._changed()

            self.meta._dirty = False

        if self._type != "output":
            op = self.getRealOperator()
            if op is not None and not op._cleaningUp:
                self._configureOperator(self)

        if wasdirty:
            # call changed callbacks
            self._sig_changed(self)

    def _configureOperator(self, slot, oldSize=0, newSize=0, notify=True):
        """Call setupOutputs of Operator if all slots of the operator
        are connected and configured.

        """
        if self.operator is not None:
            # check whether all slots are connected and notify operator
            self.maybe_call_within_transaction(self.operator._setupOutputs)

    def _setupOutputs(self):
        """
        """
        self._changed()

    def _connectSubSlot(self, slot, notify=True):
        """Connect a subslot either to the upstream_slot, or set the correct
        value in case of self._value != None

        """
        if type(slot) is int:
            index = slot
            slot = self._subSlots[slot]
        else:
            index = self._subSlots.index(slot)

        if self.upstream_slot is not None:
            if self.upstream_slot.level == self.level:
                if len(self.upstream_slot) > index:
                    slot.connect(self.upstream_slot[index])
            else:
                slot.connect(self.upstream_slot)
        if self._value is not None:
            slot.setValue(self._value, notify=notify)

    def _insertNew(self, position):
        """Construct a new subSlot of correct type and level and
        insert it to the list of subslots

        """
        assert position >= 0 and position <= len(self._subSlots)
        slot = self._getInstance(self, level=self.level - 1)
        self._subSlots.insert(position, slot)
        slot.name = self.name
        if self._value is not None:
            slot.setValue(self._value)
        return slot

    def pop(self, index=-1, event=None):
        if index < 0:
            index = len(self) + index
        self._subSlots.pop(index)

    def propagateDirty(self, slot, subindex, roi):
        """Slots with level > 0 must implement part of the operator
         interface so they look like an operator as far as their
         subslots are concerned. That's why this function is here.

        """
        totalIndex = (self._subSlots.index(slot),) + subindex
        self.operator.propagateDirty(self, totalIndex, roi)

    ######################################
    # methods aimed to enhance usability #
    ######################################

    def setShapeAtAxisTo(self, axis, size):
        tmpshape = list(self.meta.shape)
        tmpshape[self.meta.axistags.index(axis)] = size
        self.meta.shape = tuple(tmpshape)

    def __str__(self):
        mslot_info = ""
        if self.level > 0 or isinstance(self.operator, Slot):
            mslot_info += "["
            if isinstance(self.operator, Slot):
                if self in self.operator._subSlots:
                    mslot_info += " index={}".format(self.operator.index(self))
                else:
                    mslot_info += " index=NOTFOUND"
            if self.level > 0:
                mslot_info += " len={}".format(len(self))
                if self.level > 1:
                    mslot_info += " level={}".format(self.level)
            mslot_info += " ] "

        # For debugging:
        # Should actually never happen if the operator is constructed correctly,
        # however, if it is not, the resulting error message was too cryptic
        if self.getRealOperator() is None:
            realOpName = "Unassigned"
        else:
            realOpName = self.getRealOperator().name

        return "{}.{} {}: \t{}\n".format(realOpName, self.name, mslot_info, self.meta)

    def __repr__(self):
        return self.__str__()


class InputSlot(Slot):
    """The base class for input slots, it provides methods to connect
    the InputSlot to an OutputSlot of another operator (i.e.
    .connect(partner) call) or allows to directly provide a value as
    input (i.e. .setValue(value) call)

    """

    def __init__(self, *args, **kwargs):
        super(InputSlot, self).__init__(*args, **kwargs)
        self._type = "input"
        # configure operator in case of slot change
        self.notifyResized(self._configureOperator)


class OutputSlot(Slot):
    """The base class for output slots, it provides methods to connect
    the OutputSlot to an InputSlot of another operator (i.e.
    .connect(partner) call).

    the content of the OutputSlot e.g. the result of the operator it
    belongs to can be requested with the usual python array slicing
    syntax, i.e.

    outputslot[3,:,14:32]

    This call returns an GetItemRequestObject.

    """

    def __init__(self, *args, **kwargs):
        super(OutputSlot, self).__init__(*args, **kwargs)
        self._type = "output"
        assert "optional" not in kwargs, '"optional" init arg cannot be used with OutputSlot'

    def execute(self, slot, subindex, roi, result):
        """For now, OutputSlots with level > 0 must pretend to be
        operators. That's why this function is here.

        """
        totalIndex = (self._subSlots.index(slot),) + subindex
        return self.operator.execute(self, totalIndex, roi, result)
