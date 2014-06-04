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
#		   http://ilastik.org/license.html
###############################################################################
class SimpleSignal(object):
    """
    A simple python-only signal class for implementing the observer pattern.
    For familarity, mimics a SUBSET of the pyqt signal interface.  Not threadsafe.
    No fine-grained unsubcribe mechanism.
    """
    def __init__(self):
        self.subscribers = []

    def connect(self, callable):
        """
        Add a subscriber.
        """
        self.subscribers.append(callable)
    
    def emit(self, *args, **kwargs):
        """
        Fire the signal with the given arguments.
        """
        for f in self.subscribers:
            f(*args, **kwargs)

    def __repr__(self):
        return "SimpleSignal"

    def disconnectAll(self):
        """
        Remove all subscribers.
        """
        self.subscribers = []
            