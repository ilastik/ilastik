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

import sys
import os
import time
import psutil
import numpy
import gc

from lazyflow.request.request import Request, RequestPool
from lazyflow.utility.tracer import traceLogged

import logging
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)

# Test
logger = logging.getLogger("tests.testRequestRewrite")
# Test Trace
traceLogger = logging.getLogger("TRACE." + logger.name)

def test_basic():
    """
    Check if a request pool executes all added requests.
    """
    # threadsafe way to count how many requests ran
    import itertools
    result_counter = itertools.count()

    def increase_counter():
        time.sleep(0.1)
        result_counter.next()

    pool = RequestPool()
    for i in xrange(500):
        pool.add(Request(increase_counter))
    pool.wait()

    assert result_counter.next() == 500, "RequestPool has not run all submitted requests {} out of 500".format(result_counter.next() - 1)

def test_cleanup():
    """
    Check if requests added to a RequestPool are cleaned when they are
    completed without waiting for the RequestPool itself to be cleaned.
    """
    cur_process = psutil.Process(os.getpid())
    def getMemoryUsage():
        # Collect garbage first
        gc.collect()
        return cur_process.memory_info().vms
        #return mem_usage_mb

    starting_usage = getMemoryUsage()
    def getMemoryIncrease():
        return getMemoryUsage() - starting_usage


    num_workers = len(Request.global_thread_pool.workers)
    # maximum memory this tests should use
    # tests should not cause the machine to swap unnecessarily
    max_mem = 1<<29 # 512 Mb
    mem_per_req = max_mem / num_workers

    # some leeway
    max_allowed_mem = (max_mem + 2*mem_per_req)

    def memoryhog():
        increase = getMemoryIncrease()
        assert increase < max_allowed_mem, "memory use should not go beyond {}, current use: {}".format(max_mem, increase)
        return numpy.zeros(mem_per_req, dtype=numpy.uint8)

    pool = RequestPool()
    for i in xrange(num_workers**2):
        pool.add(Request(memoryhog))

    pool.wait()

    assert len(pool._requests) == 0, "Not all requests were executed by the RequestPool"


if __name__ == "__main__":

    # Logging is OFF by default when running from command-line nose, i.e.:
    # nosetests thisFile.py)
    # but ON by default if running this test directly, i.e.:
    # python thisFile.py
    logging.getLogger().addHandler( handler )
    logger.setLevel(logging.DEBUG)
    traceLogger.setLevel(logging.DEBUG)

    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
