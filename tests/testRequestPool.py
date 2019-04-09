from builtins import next
from builtins import range

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
import time
from functools import partial
import numpy

from lazyflow.request.request import Request, RequestPool

from test_utilities import fail_after_timeout

import logging

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")
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
        time.sleep(0.001)
        next(result_counter)

    pool = RequestPool()
    for _ in range(500):
        pool.add(Request(increase_counter))
    pool.wait()

    assert next(result_counter) == 500, "RequestPool has not run all submitted requests: {} out of 500".format(
        next(result_counter) - 1
    )


@fail_after_timeout(5)
def test_pool_with_failed_requests():
    """
    When one of the requests in a RequestPool fails,
    the exception should be propagated back to the caller of RequestPool.wait()
    """

    class ExpectedException(Exception):
        pass

    l = []
    pool = RequestPool()

    def workload(index):
        if index == 9:
            raise ExpectedException("Intentionally failed request.")
        l.append(index)

    for i in range(10):
        pool.add(Request(partial(workload, i)))

    try:
        pool.wait()
    except ExpectedException:
        pass
    else:
        assert False, "Expected the pool to fail.  Why didn't it?"

    time.sleep(0.2)


def test_empty_pool():
    """
    Test the edge case when we wait() for a
    RequestPool that has no requests in it.
    """
    pool = RequestPool()
    pool.wait()


def _impl_test_pool_results_discarded():
    """
    After a RequestPool executes, none of its data should linger if the user didn't hang on to it.
    """
    import weakref
    from functools import partial
    import threading

    result_refs = []

    def workload():
        # In this test, all results are discarded immediately after the
        #  request exits.  Therefore, AT NO POINT IN TIME, should more than N requests be alive.
        live_result_refs = [w for w in result_refs if w() is not None]
        assert (
            len(live_result_refs) <= Request.global_thread_pool.num_workers
        ), "There should not be more than {} result references alive at one time!".format(
            Request.global_thread_pool.num_workers
        )

        return numpy.zeros((10,), dtype=numpy.uint8) + 1

    lock = threading.Lock()

    def handle_result(req, result):
        with lock:
            result_refs.append(weakref.ref(result))

    def handle_cancelled(req, *args):
        assert False

    def handle_failed(req, exc, exc_info):
        raise exc

    pool = RequestPool()
    for _ in range(100):
        req = Request(workload)
        req.notify_finished(partial(handle_result, req))
        req.notify_cancelled(partial(handle_cancelled, req))
        req.notify_failed(partial(handle_failed, req))
        pool.add(req)
        del req
    pool.wait()

    # This test verifies that
    #  (1) references to all child requests have been discarded once the pool is complete, and
    #  (2) therefore, all references to the RESULTS in those child requests are also discarded.
    # There is a tiny window of time between a request being 'complete' (for all intents and purposes),
    #  but before its main execute function has exited back to the main ThreadPool._Worker loop.
    #  The request is not finally discarded until that loop discards it, so let's wait a tiny extra bit of time.
    time.sleep(0.01)

    # Now check that ALL results are truly lost.
    for ref in result_refs:
        assert ref() is None, "Some data was not discarded."


def test_pool_results_discarded_THREAD_CONTEXT():
    _impl_test_pool_results_discarded()


def test_pool_results_discarded_REQUEST_CONTEXT():
    mainreq = Request(_impl_test_pool_results_discarded)
    mainreq.submit()
    mainreq.wait()


if __name__ == "__main__":
    # Logging is OFF by default when running from command-line nose, i.e.:
    # nosetests thisFile.py)
    # but ON by default if running this test directly, i.e.:
    # python thisFile.py
    logging.getLogger().addHandler(handler)
    logger.setLevel(logging.DEBUG)
    traceLogger.setLevel(logging.DEBUG)

    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.

    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
