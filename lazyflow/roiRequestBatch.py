from functools import partial
import threading
import collections
import numpy
from lazyflow.roi import getIntersectingBlocks, getBlockBounds
from lazyflow.graph import OrderedSignal
import itertools

class RoiRequestBatch( object ):
    """
    A simple utility for requesting a list of rois from an output slot.
    The number of rois requested in parallel is throttled by the batch size given to the constructor.
    The result of each requested roi is provided to the user's given callback.
    """
    def __init__(self, outputSlot, roiList, resultCallback, batchSize=10):
        self._outputSlot = outputSlot
        self._roiList = collections.deque( roiList )
        self._numRois = len( roiList )
        self._resultCallback = resultCallback
        self._batchSize = min( batchSize, len(roiList) )
        self._activeRequests = collections.deque()
        self._callbackLock = threading.Lock()
        self._roiCount = itertools.count()

        # Public member for progress reporting
        self.progressSignal = OrderedSignal()

    def start(self):
        self.progressSignal( 0 )
        # Start with a batch of N requests
        for _ in range(self._batchSize):
            self._activateNewRequest()

        # Wait for each request in FIFO order.  
        # When each is finished, pull it off the "active requests" queue and replace it with a new request until there are none left.
        #
        # NOTE: This is extremely non-optimal.
        #       We are simply waiting for the oldest active request, but requests may finish in an arbitrary (non-FIFO) order.
        #       What we would *like* is to put the queue operations inside a request notify_finished callback handler,
        #       but that is complicated by the fact that request.wait() is allowed to return BEFORE the callbacks are finished.
        #       A future version of the request system will fix this, so we'll wait for that instead of hand-optimizing this function today.
        roi, next_request = self._popOldestActiveRequest()
        while next_request is not None:
            next_request.wait()
            self._activateNewRequest()
            self._resultCallback(roi, next_request.result)
            count = self._roiCount.next()
            progress =  100 * count / self._numRois
            self.progressSignal( progress )
            roi, next_request = self._popOldestActiveRequest()

        self.progressSignal( 100 )

    def _popOldestActiveRequest(self):
        """
        If the active request queue is not empty, return a roi and its request (in FIFO order).
        Otherwise, return (None,None)
        """
        if len(self._activeRequests) > 0:
            return self._activeRequests.popleft()
        else:
            return (None, None)

    def _activateNewRequest(self):
        """
        Creates and activates a new request if there are more rois to process.  Otherwise, does nothing.
        """
        if len(self._roiList) > 0:
            roi = self._roiList.popleft()
            req = self._outputSlot( roi[0], roi[1] )
            self._activeRequests.append( (roi, req) )
            req.submit()


