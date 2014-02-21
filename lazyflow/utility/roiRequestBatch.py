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

import threading
from functools import partial

import numpy

import lazyflow.stype
from lazyflow.utility import OrderedSignal
from lazyflow.request import Request, SimpleRequestCondition

class RoiRequestBatch( object ):
    """
    A simple utility for requesting a list of rois from an output slot.
    The number of rois requested in parallel is throttled by the batch size given to the constructor.
    The result of each requested roi is provided as a signal, which the user should subscribe() to.

    Example usage:
    
    >>> import sys
    >>> import vigra
    >>> from lazyflow.graph import Graph
    >>> from lazyflow.operators.operators import OpArrayCache

    >>> # Example data
    >>> data = numpy.indices( (100,100) ).sum(0)
    >>> data = vigra.taggedView( data, vigra.defaultAxistags('xy') )

    >>> op = OpArrayCache( graph=Graph() )
    >>> op.Input.setValue( data )

    >>> # Create a list of rois to iterate through.
    >>> # Typically you'll want to automate this
    >>> #  with e.g. lazyflow.roi.getIntersectingBlocks
    >>> rois = []
    >>> rois.append( ( (0, 0), (10,10) ) )
    >>> rois.append( ( (0,10), (10,20) ) )
    >>> rois.append( ( (0,20), (10,30) ) )
    >>> rois.append( ( (0,30), (10,40) ) )
    >>> rois.append( ( (0,40), (10,50) ) )

    >>> # Init with our output slot and list of rois to request.
    >>> # `batchSize` indicates the number of requests to spawn in parallel.
    >>> # Provide `totalVolume` if you want progress reporting.
    >>> batch_requester = RoiRequestBatch( op.Output, iter(rois), totalVolume=500, batchSize=2 )

    >>> # Use a callback to handle sub-results one at a time.
    >>> result_count = [0]
    >>> result_total_sum = [0]
    >>> def handle_block_result(roi, result):
    ...     # No need for locking here.
    ...     result_count[0] += 1
    ...     result_total_sum[0] += result.sum()
    >>> batch_requester.resultSignal.subscribe( handle_block_result )

    >>> # Optional: Subscribe to progress updates
    >>> def handle_progress(progress):
    ...     if progress == 0:
    ...         sys.stdout.write("Progress: ")
    ...     sys.stdout.write( "{} ".format( progress ) )
    >>> batch_requester.progressSignal.subscribe( handle_progress )

    >>> # Execute the batch of requests, and block for the result.
    >>> batch_requester.execute()
    Progress: 0 20 40 60 80 100 100 
    >>> print "Processed {} result blocks with a total sum of: {}".format( result_count[0], result_total_sum[0] )
    Processed 5 result blocks with a total sum of: 14500
    """
    def __init__( self, outputSlot, roiIterator, totalVolume=None, batchSize=2 ):
        """
        Constructor.

        :param outputSlot: The slot to request data from.
        :param roiIterator: An iterator providing new rois.
        :param totalVolume: The total volume to be processed.  
                            Used to provide the progress reporting signal. 
                            If not provided, then no intermediate progress will be signaled.
        :param batchSize: The maximum number of requests to launch in parallel.
        """
        self._resultSignal = OrderedSignal()
        self._progressSignal = OrderedSignal()

        assert isinstance(outputSlot.stype, lazyflow.stype.ArrayLike), \
            "Only Array-like slots supported." # Because progress reporting depends on the roi shape
        self._outputSlot = outputSlot
        self._roiIter = roiIterator
        self._batchSize = batchSize
        
        self._condition = SimpleRequestCondition()

        self._activated_count = 0
        self._completed_count = 0

        # Progress bookkeeping
        self._totalVolume = totalVolume
        self._processedVolume = 0
    
    @property
    def resultSignal(self):
        """
        Results signal. Signature: ``f(roi, result)``.
        Guaranteed not to be called from multiple threads in parallel.
        """
        return self._resultSignal
    
    @property
    def progressSignal(self):
        """
        Progress Signal Signature: ``f(progress_percent)``
        """
        return self._progressSignal
    
    def execute(self):
        """
        Execute the batch of requests and wait for all of them to complete.
        A batch of N requests is launched, and subsequent requests are 
        launched one-by-one as the earlier requests complete.  Thus, there 
        will be N requests executing in parallel at all times.

        This method returns ``None``.  All results must be handled via the 
        :py:obj:`resultSignal`.
        """
        self.progressSignal( 0 )

        with self._condition:
            # Start by activating a batch of N requests
            for _ in range(self._batchSize):
                self._activateNewRequest()
                self._activated_count += 1

            try:
                # Loop until StopIteration
                while True:
                    # Wait for at least one active request to finish
                    while (self._activated_count - self._completed_count) == self._batchSize:
                        self._condition.wait()

                    # Launch new requests until we have the correct number of active requests
                    while self._activated_count - self._completed_count < self._batchSize:
                        self._activateNewRequest() # Eventually raises StopIteration
                        self._activated_count += 1
            except StopIteration:
                # We've run out of requests to launch.
                # Wait for the remaining active requests to finish.
                while self._completed_count < self._activated_count:
                    self._condition.wait()

        self.progressSignal( 100 )

    def _activateNewRequest(self):
        """
        Creates and activates a new request if there are more rois to process.
        Otherwise, raises StopIteration
        """
        # This could raise StopIteration
        roi = self._roiIter.next()
        req = self._outputSlot( roi[0], roi[1] )
        
        # We have to make sure that we didn't get a so-called "ValueRequest"
        # because those don't work the same way.
        # (This can happen if array data was given to a slot via setValue().)
        assert isinstance( req, Request ), \
            "Can't use RoiRequestBatch with non-standard requests.  See comment above."
        
        req.notify_finished( partial( self._handleCompletedRequest, roi ) )
        req.submit()

    def _handleCompletedRequest(self, roi, result):
        with self._condition:
            # Signal the user with the result
            self.resultSignal(roi, result)
            
            # Report progress (if possible)
            if self._totalVolume is not None:
                self._processedVolume += numpy.prod( numpy.subtract(roi[1], roi[0]) )
                progress = 100 * self._processedVolume / self._totalVolume
                self.progressSignal( progress )

            self._completed_count += 1
            self._condition.notify()

if __name__ == "__main__":
    import doctest
    doctest.testmod()
