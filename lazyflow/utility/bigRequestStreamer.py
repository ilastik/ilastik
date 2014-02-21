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

import numpy
from lazyflow.utility import RoiRequestBatch
from lazyflow.roi import getIntersectingBlocks, getBlockBounds

import logging
logger = logging.getLogger(__name__)

class BigRequestStreamer(object):
    """
    Execute a big request by breaking it up into smaller requests.
    
    This class encapsulates the logic for dividing big rois into smaller ones to be executed separately.
    It relies on a :py:class:`RoiRequestBatch<lazyflow.utility.roiRequestBatch.RoiRequestBatch>` object,
    which is responsible for creating and scheduling the request for each roi.
    
    Example:
    
    >>> import sys
    >>> import vigra
    >>> from lazyflow.graph import Graph
    >>> from lazyflow.operators.operators import OpArrayCache

    >>> # Example data
    >>> data = numpy.indices( (100,100) ).sum(0)
    >>> data = vigra.taggedView( data, vigra.defaultAxistags('xy') )

    >>> op = OpArrayCache( graph=Graph() )
    >>> op.Input.setValue( data )

    >>> total_roi = [(25, 65), (45, 95)]

    >>> # Init with our output slot and roi to request.
    >>> # batchSize indicates the number of requests to spawn in parallel.
    >>> streamer = BigRequestStreamer( op.Output, total_roi, (10,10), batchSize=2 )

    >>> # Use a callback to handle sub-results one at a time.
    >>> result_count = [0]
    >>> result_total_sum = [0]
    >>> def handle_block_result(roi, result):
    ...     # No need for locking here.
    ...     result_count[0] += 1
    ...     result_total_sum[0] += result.sum()
    >>> streamer.resultSignal.subscribe( handle_block_result )

    >>> # Optional: Subscribe to progress updates
    >>> def handle_progress(progress):
    ...     if progress == 0:
    ...         sys.stdout.write("Progress: ")
    ...     sys.stdout.write( "{} ".format( progress ) )
    >>> streamer.progressSignal.subscribe( handle_progress )

    >>> # Execute the batch of requests, and block for the result.
    >>> streamer.execute()
    Progress: 0 16 33 50 66 83 100 100 
    >>> print "Processed {} result blocks with a total sum of: {}".format( result_count[0], result_total_sum[0] )
    Processed 6 result blocks with a total sum of: 68400
    """
    def __init__(self, outputSlot, roi, minBlockShape, batchSize=None):
        """
        Constructor.
        
        :param outputSlot: The slot to request data from.
        :param roi: The roi `(start, stop)` of interest.  Will be broken up and requested via smaller requests.
        :param minBlockShape: The minimum amount of data to request in each request.
                              Note: The current implementation breaks the big request into smaller 
                              requests of exactly ``minBlockShape`` size. Future implementations could 
                              concatenate smaller requests if it appears the system is not being overloaded by the smaller requests.
        :param batchSize: The maximum number of requests to launch in parallel.
        """
        self._outputSlot = outputSlot
        self._bigRoi = roi
        self._minBlockShape = minBlockShape
        
        if batchSize is None:
            batchSize=2

        # Align the blocking with the start of the roi
        offsetRoi = ([0] * len(roi[0]), numpy.subtract(roi[1], roi[0]))
        self._minBlockStarts = getIntersectingBlocks(minBlockShape, offsetRoi)
        self._minBlockStarts += roi[0] # Un-offset

        totalVolume = numpy.prod( numpy.subtract(roi[1], roi[0]) )
        # For now, simply iterate over the min blocks
        # TODO: Auto-dialate block sizes based on CPU/RAM usage.
        def roiGen():
            block_iter = self._minBlockStarts.__iter__()
            while True:
                block_start = block_iter.next()

                # Use offset blocking
                offset_block_start = block_start - self._bigRoi[0]
                offset_data_shape = numpy.subtract(self._bigRoi[1], self._bigRoi[0])
                offset_block_bounds = getBlockBounds( offset_data_shape, minBlockShape, offset_block_start )
                
                # Un-offset
                block_bounds = ( offset_block_bounds[0] + self._bigRoi[0],
                                 offset_block_bounds[1] + self._bigRoi[0] )
                logger.debug( "Requesting Roi: {}".format( block_bounds ) )
                yield block_bounds
        
        self._requestBatch = RoiRequestBatch( self._outputSlot, roiGen(), totalVolume, batchSize )

    @property
    def resultSignal(self):
        """
        Results signal. Signature: ``f(roi, result)``.
        Guaranteed not to be called from multiple threads in parallel.
        """
        return self._requestBatch.resultSignal

    @property
    def progressSignal(self):
        """
        Progress Signal Signature: ``f(progress_percent)``
        """
        return self._requestBatch.progressSignal

    def execute(self):
        """
        Request the data for the entire roi by breaking it up into many smaller requests,
        and wait for all of them to complete.
        A batch of N requests is launched, and subsequent requests are 
        launched one-by-one as the earlier requests complete.  Thus, there 
        will be N requests executing in parallel at all times.
        
        This method returns ``None``.  All results must be handled via the 
        :py:obj:`resultSignal`.
        """
        self._requestBatch.execute()

if __name__ == "__main__":
    import doctest
    doctest.testmod()
