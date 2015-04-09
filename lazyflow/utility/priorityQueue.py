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
#		   http://ilastik.org/license/
###############################################################################

import heapq
import threading
import itertools

class PriorityQueue(object):
    """
    Threadsafe priority queue based on the python heapq module.

    Ties are resolved by popping the element that was added first. If
    the elements are tuples (p1, p2, ..., element), the elements are
    never considered for comparison!
    """
    def __init__(self):
        self._heap = []
        self._lock = threading.Lock()
        self._count = itertools.count()

    def push(self, item):
        item = self._expandItem(item)
        with self._lock:
            heapq.heappush(self._heap, item)

    def pop(self):
        with self._lock:
            item = heapq.heappop(self._heap)
        return self._reduceItem(item)

    def __len__(self):
        return len(self._heap)

    def _expandItem(self, item):
        """
        convert to internal tuple format, if necessary
        """
        c = self._count.next()
        if isinstance(item, tuple) and len(item) > 1:
            new = list(item)
            new.insert(-1, c)
        else:
            new = [item, c]
        return tuple(new)

    def _reduceItem(self, item):
        """
        restore item to original format
        """
        # if the tuple is of length 2, it was created by the else case
        if len(item) == 2:
            return item[0]
        else:
            item = list(item)
            item.pop(-2)
            return tuple(item)
