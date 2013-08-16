import threading
#import collections
from functools import partial

import numpy

import lazyflow.stype
from lazyflow.utility import OrderedSignal

from lazyflow.request import Request, RequestLock

class RoiRequestBatch( object ):
    """
    A simple utility for requesting a list of rois from an output slot.
    The number of rois requested in parallel is throttled by the batch size given to the constructor.
    The result of each requested roi is provided as a signal, which the user should subscribe() to.
    """
    def __init__( self, outputSlot, roiIterator, totalVolume=None, batchSize=2 ):
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
        
        # Combine threading.Condition + RequestLock:
        # ==> Request-aware condition variable!
        self._condition = threading.Condition( RequestLock() )

        # Progress bookkeeping
        self._totalVolume = totalVolume
        self._processedVolume = 0
        
        self._activated_count = 0
        self._completed_count = 0
    
    def execute(self):
        self.progressSignal( 0 )

        # Start with a batch of N requests
        with self._condition:
            for _ in range(self._batchSize):
                self._activateNewRequest()
                self._activated_count += 1

            try:
                while True: # Loop until StopIteration
                    while (self._activated_count - self._completed_count) == self._batchSize:
                        self._condition.wait()

                    while self._activated_count - self._completed_count < self._batchSize:
                        self._activateNewRequest() # Eventually raises StopIteration
                        self._activated_count += 1
            except StopIteration:
                pass

            # Wait for last N requests to complete
            while self._completed_count < self._activated_count:
                self._condition.wait()

        # All finished
        self.progressSignal( 100 )

    def _handleCompletedRequest(self, roi, result):
        with self._condition:
            # Signal the user with the result
            self.resultSignal(roi, result)
            
            # Report progress (if possible)
            if self._totalVolume is not None:
                self._processedVolume += numpy.prod( roi[1] - roi[0] )
                progress =  100 * self._processedVolume / self._totalVolume
                self.progressSignal( progress )

            self._completed_count += 1
            self._condition.notify()

    def _activateNewRequest(self):
        """
        Creates and activates a new request if there are more rois to process.  Otherwise, raises StopIteration
        """
        # This could raise StopIteration
        roi = self._roiIter.next()
        req = self._outputSlot( roi[0], roi[1] )
        
        # We have to make sure that we didn't get a so-called "ValueRequest"
        # because those don't work the same way.
        # (This can happen if array data was given to a slot via setValue().)
        assert isinstance( req, Request ), \
            "Can't use RoiRequestBatch with non-standard requests.  See comment above."
        
        #self._activeRequests.append( (roi, req) )
        req.notify_finished( partial( self._handleCompletedRequest, roi ) )
        req.submit()

# At module load time, run this quick test to make sure that RequestLock does NOT have RLock semantics
# We require that for 