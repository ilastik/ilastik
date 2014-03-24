# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

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
            