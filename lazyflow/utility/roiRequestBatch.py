from functools import partial
import threading
import collections
import numpy
from lazyflow.roi import getIntersectingBlocks, getBlockBounds
from lazyflow.graph import OrderedSignal
import itertools
import lazyflow.stype

class RoiRequestBatch( object ):
    """
    A simple utility for requesting a list of rois from an output slot.
    The number of rois requested in parallel is throttled by the batch size given to the constructor.
    The result of each requested roi is provided as a signal, which the user should subscribe() to.
    """
    def __init__( self, outputSlot, roiIterator, totalVolume=None, batchSize=10 ):
        """
        Constructor.
        :param outputSlot: The slot to request data from.
        :param roiIterator: An iterator providing new rois.
        :param totalVolume: The total volume to be processed.  Used to provide the progress reporting signal.  If not provided, then no intermediate progress will be signaled.
        :param batchSize: The maximum number of requests to launch in parallel.
        """
        #: Results signal. Signature: ``f(roi, result)``.  Guaranteed not to be called from multiple threads in parallel.
        self.resultSignal = OrderedSignal()
        #: Progress Signal Signature: ``f(progress_percent)``
        self.progressSignal = OrderedSignal()

        assert isinstance(outputSlot.stype, lazyflow.stype.ArrayLike), "Only Array-like slots supported." # Because progress reporting depends on the roi shape
        self._outputSlot = outputSlot
        self._roiIter = roiIterator
        self._batchSize = batchSize
        self._activeRequests = collections.deque()

        # Progress bookkeeping
        self._totalVolume = totalVolume
        self._processedVolume = 0
    
    def execute(self):
        # Starting...
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

            # Replace with new work
            self._activateNewRequest()
            
            # Signal the user with the result
            self.resultSignal(roi, next_request.result)

            # Report progress (if possible)
            if self._totalVolume is not None:
                self._processedVolume += numpy.prod( roi[1] - roi[0] )
                progress =  100 * self._processedVolume / self._totalVolume
                self.progressSignal( progress )

            # Get next request to wait for
            roi, next_request = self._popOldestActiveRequest()

        # All finished
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
        try:
            roi = self._roiIter.next()
        except StopIteration:
            pass
        else:
            req = self._outputSlot( roi[0], roi[1] )
            self._activeRequests.append( (roi, req) )
            req.submit()


