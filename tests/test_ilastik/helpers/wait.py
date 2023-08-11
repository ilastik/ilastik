###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2023, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################
import contextlib
import threading
import time
from typing import Optional

from PyQt5.QtCore import QEventLoop, Qt, QTimer
from PyQt5.QtWidgets import QApplication


def wait_until(f, timeout=10):
    result = f()
    while not result and timeout:
        timeout -= 1
        time.sleep(1)
        result = f()
    if not result:
        raise Exception(f"TIMEOUT! waiting for {f}")
    return result


@contextlib.contextmanager
def wait_signal(signal, timeout=1000):
    """
    Context manager
    on exit would wait for signal to fire before continuing
    :param timeout: timeout in ms
    :param signal:
    """
    evtLoop = QEventLoop()
    # QueuedConnection so we don't receive signal before entering the loop
    signal.connect(evtLoop.quit, Qt.QueuedConnection)

    yield

    _exec_with_timeout(evtLoop, timeout, signal)


@contextlib.contextmanager
def wait_slot_ready(slot, timeout=1000):
    """
    Wait for slot to become ready
    :param timeout: timeout in ms
    :param slot: lazyflow slot
    :return:
    """
    evtLoop = QEventLoop()

    def _register():
        if slot.ready():
            evtLoop.quit()
        else:
            slot.notifyReady(lambda *a, **kw: evtLoop.quit())

    # Use QTimer to avoid event firing before waiting has started
    QTimer.singleShot(0, _register)

    yield

    _exec_with_timeout(evtLoop, timeout, slot)


def _exec_with_timeout(loop, timeout, timeout_obj):
    timeout_exceeded = False

    def _timeout():
        nonlocal timeout_exceeded
        timeout_exceeded = True
        loop.quit()

    QTimer.singleShot(timeout, _timeout)
    loop.exec_()

    if timeout_exceeded:
        raise RuntimeError(f"Timeout exceeded for {timeout_obj}")


def wait_process_events(timeout: float = 1.0, event: Optional[threading.Event] = None):
    """
    Wait for a certain amount of time or until an event is set

    useful in situations in which there might be interplay of UI and
    requests.

    this is ugly, especially used without an event there is no guarantee
    that the state is as expected. but for now, don't know how else to
    let gui and all requests settle for some actions.
    """
    start = time.time()
    while not (event and event.is_set()):
        QApplication.processEvents()
        if time.time() - start > timeout:
            return
