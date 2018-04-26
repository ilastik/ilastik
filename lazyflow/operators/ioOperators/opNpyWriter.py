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
#		   http://ilastik.org/license/
###############################################################################
import numpy
from lazyflow.graph import Operator, InputSlot

from lazyflow.roi import roiToSlice, roiFromShape
from lazyflow.utility import BigRequestStreamer, OrderedSignal

import logging
logger = logging.getLogger(__name__)

class OpNpyWriter(Operator):
    Input = InputSlot()
    Filepath = InputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNpyWriter, self ).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
    
    def setupOutputs(self):
        pass
    
    def execute(self, *args):
        pass
    
    def propagateDirty(self, *args):
        pass
    
    def write(self):
        """
        Requests the entire input and saves it to the file.
        This function executes synchronously.
        """
        # TODO: Use a lazyflow.utility.BigRequestStreamer to split up 
        #       this giant request into a series of streamed subrequests.
        
        logger.warning("The current implementation of NPY-format data export computes the entire dataset at once, which requires lots of RAM.")
        path = self.Filepath.value

        self.progressSignal(0)

        final_data = numpy.zeros( self.Input.meta.shape, self.Input.meta.dtype )

        def handle_block_result(roi, data):
            slicing = roiToSlice(*roi)
            final_data[slicing] = data
        requester = BigRequestStreamer( self.Input, roiFromShape( self.Input.meta.shape ) )
        requester.resultSignal.subscribe( handle_block_result )
        requester.progressSignal.subscribe( self.progressSignal )
        requester.execute()

        numpy.save(path, final_data)
        self.progressSignal(100)
    