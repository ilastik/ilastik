from builtins import object

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
import pytest

import sys
import numpy
import threading
from lazyflow.graph import Graph
from lazyflow.roi import getIntersectingBlocks, getBlockBounds, roiToSlice
from lazyflow.operators import OpArrayPiper

from lazyflow.utility import RoiRequestBatch

import logging

logger = logging.getLogger("tests.testRoiRequestBatch")


class TestRoiRequestBatch(object):
    def testBasic(self):
        op = OpArrayPiper(graph=Graph())
        inputData = numpy.indices((100, 100)).sum(0)
        op.Input.setValue(inputData)
        roiList = []
        block_starts = getIntersectingBlocks([10, 10], ([0, 0], [100, 100]))
        for block_start in block_starts:
            roiList.append(getBlockBounds([100, 100], [10, 10], block_start))

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
        batch = RoiRequestBatch(op.Output, roiList.__iter__(), totalVolume, batchSize=10, allowParallelResults=False)
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

    def testFailedProcessing(self):
        op = OpArrayPiper(graph=Graph())
        inputData = numpy.indices((100, 100)).sum(0)
        op.Input.setValue(inputData)
        roiList = []
        block_starts = getIntersectingBlocks([10, 10], ([0, 0], [100, 100]))
        for block_start in block_starts:
            roiList.append(getBlockBounds([100, 100], [10, 10], block_start))

        class SpecialException(Exception):
            pass

        def handleResult(roi, result):
            raise SpecialException("Intentional Exception: raised while handling the result")

        totalVolume = numpy.prod(inputData.shape)
        batch = RoiRequestBatch(op.Output, roiList.__iter__(), totalVolume, batchSize=10, allowParallelResults=False)
        batch.resultSignal.subscribe(handleResult)

        # FIXME: There are multiple places where the RoiRequestBatch tool should be prepared to handle exceptions.
        #        This only tests one of them (in the notify_finished() handler)
        with pytest.raises(SpecialException):
            batch.execute()


if __name__ == "__main__":
    # Run this file independently to see debug output.
    handler = logging.StreamHandler(sys.stdout)
    logger.setLevel(logging.DEBUG)
    logging.getLogger("lazyflow.utility.roiRequestBatch").setLevel(logging.INFO)

    logger.addHandler(handler)
    logging.getLogger("lazyflow.utility.roiRequestBatch").addHandler(handler)

    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)

    if not ret:
        sys.exit(1)
