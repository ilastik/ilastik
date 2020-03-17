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
import os
import gc
import sys
import time
import numpy
import psutil
import weakref
import threading
import unittest
from lazyflow.graph import Graph, Operator, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpArrayPiper
from lazyflow.request import Request

from lazyflow.utility import BigRequestStreamer

import logging

logger = logging.getLogger(__name__)


class OpNonsense(Operator):
    """
    Provide nonsense data of the correct shape for each request.
    """

    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.dtype = numpy.float32
        self.Output.meta.shape = (2000, 2000, 2000)

    def execute(self, slot, subindex, roi, result):
        """
        Simulate a cascade of requests, to make sure that the entire cascade is properly freed.
        """
        roiShape = roi.stop - roi.start

        def getResults1():
            return numpy.indices(roiShape, self.Output.meta.dtype).sum()

        def getResults2():
            req = Request(getResults1)
            req.submit()
            result[:] = req.wait()
            return result

        req = Request(getResults2)
        req.submit()
        result[:] = req.wait()
        return result

    def propagateDirty(self, slot, subindex, roi):
        pass


class TestBigRequestStreamer(unittest.TestCase):
    def testBasic(self):
        op = OpArrayPiper(graph=Graph())
        inputData = numpy.indices((100, 100)).sum(0)
        op.Input.setValue(inputData)

        results = numpy.zeros((100, 100), dtype=numpy.int32)
        resultslock = threading.Lock()

        resultsCount = [0]

        def handleResult(roi, result):
            acquired = resultslock.acquire(False)
            assert acquired, "resultslock is contested! Access to callback is supposed to be automatically serialized."
            results[roiToSlice(*roi)] = result
            logger.debug("Got result for {}".format(roi))
            resultslock.release()
            resultsCount[0] += 1

        progressList = []

        def handleProgress(progress):
            progressList.append(progress)
            logger.debug("Progress update: {}".format(progress))

        totalVolume = numpy.prod(inputData.shape)
        batch = BigRequestStreamer(op.Output, [(0, 0), (100, 100)], (10, 10))
        batch.resultSignal.subscribe(handleResult)
        batch.progressSignal.subscribe(handleProgress)

        batch.execute()
        logger.debug("Got {} results".format(resultsCount[0]))
        assert (results == inputData).all()

        # Progress reporting MUST start with 0 and end with 100
        assert progressList[0] == 0, "Invalid progress reporting."
        assert progressList[-1] == 100, "Invalid progress reporting."

        # There should be some intermediate progress reporting, but exactly how much is unspecified.
        assert len(progressList) >= 10

        logger.debug("FINISHED")


def test_pool_results_discarded():
    """
    This test checks to make sure that result arrays are discarded in turn as the BigRequestStreamer executes.
    (If they weren't discarded in real time, then it's possible to end up consuming a lot of RAM until the streamer finally finishes.)
    """
    result_refs = []

    def handle_result(roi, result):
        result_refs.append(weakref.ref(result))

        # In this test, all results are discarded immediately after the
        #  request exits.  Therefore, AT NO POINT IN TIME, should more than N requests be alive.
        live_result_refs = [w for w in result_refs if w() is not None]
        assert (
            len(live_result_refs) <= Request.global_thread_pool.num_workers
        ), "There should not be more than {} result references alive at one time!".format(
            Request.global_thread_pool.num_workers
        )

    def handle_progress(progress):
        logger.debug("test_pool_results_discarded: progress: {}".format(progress))

    op = OpNonsense(graph=Graph())
    batch = BigRequestStreamer(op.Output, [(0, 0, 0), (100, 1000, 1000)], (100, 100, 100))
    batch.resultSignal.subscribe(handle_result)
    batch.progressSignal.subscribe(handle_progress)
    batch.execute()

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


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)

    if not ret:
        sys.exit(1)
