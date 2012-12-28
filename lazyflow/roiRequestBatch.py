from functools import partial
import threading
import collections
import numpy
from lazyflow.roi import getIntersectingBlocks, getBlockBounds

class RoiRequestBatch( object ):
    def __init__(self, outputSlot, roiList, resultCallback, batchSize=10):
        self._outputSlot = outputSlot
        self._roiList = collections.deque( roiList )
        self._resultCallback = resultCallback
        self._batchSize = min( batchSize, len(roiList) )
        self._activeRequests = collections.deque()
        self._lock = threading.Lock()
        self._callbackLock = threading.Lock()

    def start(self):
        # Start with a batch of N requests
        for _ in range(self._batchSize):
            self._activateNewRequest()
            
        next_request = self._popOldestActiveRequest()
        while next_request is not None:
            next_request.wait()
            next_request = self._popOldestActiveRequest()

    def _popOldestActiveRequest(self):
        with self._lock:
            if len(self._activeRequests) > 0:
                return self._activeRequests.popleft()
            else:
                return None

    def _activateNewRequest(self):
        """
        Creates and activates a new request.
        """
        with self._lock:
            if len(self._roiList) > 0:
                roi = self._roiList.popleft()
                req = self._outputSlot( roi[0], roi[1] )
                self._activeRequests.append( req )
                req.notify( partial(self._handleFinishedRequest, roi) ) # Auto-submits.

    def _handleFinishedRequest(self, roi, result):
        self._activateNewRequest()

        # Serialize access to the callback function
        with self._callbackLock:
            self._resultCallback(roi, result)

