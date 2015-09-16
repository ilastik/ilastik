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
#           http://ilastik.org/license/
###############################################################################

import logging
import time
import threading

import numpy
import vigra
import copy

import UfmfParser

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility import Timer

logger = logging.getLogger(__name__)    

AXIS_ORDER = 'tyxc'

class OpStreamingUfmfReader(Operator):
    """
    Imports videos in uFMF format. For more information refer to the Ctrax file tracker: http://ctrax.sourceforge.net/
    """    
    name = "OpStreamingUfmfReader"
    category = "Input"

    position = None
    
    FileName = InputSlot(stype='filestring')
    Output = OutputSlot()

    class DatasetReadError(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super(OpStreamingUfmfReader, self).__init__(*args, **kwargs)
        self._lock = threading.Lock()

    def setupOutputs(self):
        """
        Load the file specified via our input slot and present its data on the output slot.
        """
        fileName = self.FileName.value

        self.fmf = UfmfParser.FlyMovieEmulator(str(fileName))
        frameNum = self.fmf.get_n_frames()
        width = self.fmf.get_width()
        height = self.fmf.get_height()
        
        try:
            self.frame, timestamp = self.fmf.get_next_frame()
        except FMF.NoMoreFramesException, err:
            logger.info("Error reading uFMF frame.")

        self.Output.meta.dtype = self.frame.dtype.type
        self.Output.meta.axistags = vigra.defaultAxistags(AXIS_ORDER)
        self.Output.meta.shape = (frameNum, self.frame.shape[0], self.frame.shape[1], 1)
        self.Output.meta.ideal_blockshape = (1,) + self.Output.meta.shape[1:]
        
    def execute(self, slot, subindex, roi, result):
        start, stop = roi.start, roi.stop
        
        tStart, tStop = start[0], stop[0]
        yStart, yStop = start[1], stop[1]
        xStart, xStop = start[2], stop[2]
        cStart, cStop = start[3], stop[3]    
  
        for tResult, tFrame in enumerate(range(tStart, tStop)):
            with self._lock:
                if self.position != tFrame:
                    self.position = tFrame
                    self.fmf.seek(tStart)
                    self.frame, timestamp = self.fmf.get_next_frame()
                result[tResult, ..., 0] = self.frame[yStart:yStop, xStart:xStop] 

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.FileName:
            self.Output.setDirty( slice(None) )
    
    def cleanUp(self):
        self.fmf.close()
        super(OpStreamingUfmfReader, self).cleanUp()

