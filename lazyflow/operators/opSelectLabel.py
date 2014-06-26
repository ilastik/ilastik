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
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility import Timer

import logging
logger = logging.getLogger(__name__)

class OpSelectLabel(Operator):
    """
    Given a label image and a label number of interest, produce a 
    boolean mask of those pixels that match the selected label.
    """
    Input = InputSlot() # label image
    SelectedLabel = InputSlot() # int
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpSelectLabel, self ).__init__( *args, **kwargs )
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.uint8
        # As a convenience, store the selected label in the metadata.
        self.Output.meta.selected_label = self.SelectedLabel.value
    
    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot: {}".format( slot.name )
        if self.SelectedLabel.value == 0:
            # Special case: Label zero selects nothing.
            result[:] = 0
            return

        with Timer() as timer: 
            # Can't use writeInto() here because dtypes don't match.
            inputLabels = self.Input(roi.start, roi.stop).wait()
            
            # Use two in-place bitwise operations instead of numpy.where
            # This avoids the temporary variable created by (inputLabels == x)
            #result[:] = numpy.where( inputLabels == self.SelectedLabel.value, 1, 0 )
            numpy.bitwise_xor(inputLabels, self.SelectedLabel.value, out=inputLabels) # All 
            numpy.logical_not(inputLabels, out=inputLabels)
            result[:] = inputLabels # Copy from uint32 to uint8
        
        logger.debug( "OpSelectLabel took {} seconds for roi {}".format( timer.seconds(), roi ) )
        return result
    
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            self.Output.setDirty( roi.start, roi.stop )
        elif slot == self.SelectedLabel:
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Dirty slot is unknown: {}".format( slot.name )

