###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
# 		   http://ilastik.org/license.html
###############################################################################

from typing import Callable, Iterable, Union
from contextlib import contextmanager

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject

from lazyflow.slot import Slot


def enable_when_ready(
    widgets: Union[QWidget, Iterable[QWidget]], slots: Union[Slot, Iterable[Slot]]
) -> Callable[[], None]:
    """Enable widgets only if all slots are ready.

    When one of the slots becomes dirty,
    check the ready status of all the slots.
    If all of them are ready, enable all the widgets.
    Otherwise, disable the widgets.

    Args:
        widgets: Widgets to enable or disable.
        slots: Slots to check.

    Returns:
        Unsubscribe callable.
    """
    if not isinstance(widgets, Iterable):
        widgets = (widgets,)
    if not isinstance(slots, Iterable):
        slots = (slots,)

    def set_enabled(*_args):
        enabled = all(s.ready() for s in slots)
        for w in widgets:
            w.setEnabled(enabled)

    funcs = [s.notifyDirty(set_enabled) for s in slots]

    def cleanup():
        for f in funcs:
            f()

    return cleanup


@contextmanager
def silent_qobject(qobject: QObject) -> QObject:
    """Disable notifying connected callbacks/slots."""
    blocked_status: bool = qobject.blockSignals(True)
    try:
        yield qobject
    finally:
        qobject.blockSignals(blocked_status)
