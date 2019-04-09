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
from __future__ import division
from builtins import map
from builtins import range
from builtins import object
import threading
from functools import partial

import os
import numpy
import h5py
import greenlet


class TestH5Py(object):
    """
    This test does NOT test anything ilastik, but instead tests h5py in conjunction with greenlet.
    """

    def test(self):
        shape = (2, 100, 100, 6)  # Make this bigger to try hammering hdf5 with bigger data accesses...

        filename1 = "test1.h5"
        self.prepare_tstfile(shape, filename1)

        filename2 = "test2.h5"
        self.prepare_tstfile(shape, filename2)

        f1 = h5py.File(filename1)
        f2 = h5py.File(filename2)

        self.tst_multithread_greenlet([f1, f2])

        f1.close()
        f2.close()

        os.remove(filename1)
        os.remove(filename2)

    def readFromGroup(self, h5Group, path):
        shape = numpy.array(h5Group[path].shape)

        # Choose a random lower bound in the lower half-space
        lb = (numpy.random.rand(len(shape)) * shape / 2).astype(int)

        # Choose a random upper bound in the upper half-space
        ub = (numpy.random.rand(len(shape)) * shape / 2).astype(int) + shape // 2

        # Combine into a slicing we can index with
        sl = list(map(slice, lb, ub))

        sample = h5Group[path][tuple(sl)]
        # print sample.shape

    def prepare_tstfile(self, shape, filename):
        f = h5py.File(filename, "w")
        f.create_dataset("test_dataset", data=numpy.random.rand(*shape))
        f.close()

    def tst_multithread(self, filename):
        f = h5py.File(filename)

        threads = []
        for i in range(100):
            threads.append(threading.Thread(target=partial(self.readFromGroup, f, "test_dataset")))
            threads[-1].start()

        for i in range(10):
            threads[i].join()

        f.close()

    def readInGreenlet(self, h5Group, path, next_greenlet, i):
        self.readFromGroup(h5Group, path)
        if next_greenlet is not None:
            next_greenlet.switch()

    def tst_greenlet(self, f):
        greenlets = []
        next_greenlet = None
        for i in range(10):
            gr = greenlet.greenlet(partial(self.readInGreenlet, f, "test_dataset", next_greenlet, i))
            greenlets.append(gr)
            next_greenlet = greenlets[i]

        # Each greenlet switches to the previous one...
        greenlets[-1].switch()

    def tst_multithread_greenlet(self, files):
        threads = []
        for i in range(10):
            threads.append(threading.Thread(target=partial(self.tst_greenlet, files[i % 2])))
            threads[-1].start()

        for i in range(10):
            threads[i].join()
