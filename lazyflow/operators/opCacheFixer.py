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
#          http://ilastik.org/license/
###############################################################################

import numpy
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiFromShape

class OpCacheFixer(Operator):
    """
    Can be inserted in front of a cache operator to implement the "fixAtCurrent" 
    behavior currently implemented by multiple lazyflow caches.
    
    While fixAtCurrent=False, this operator is merely a pass-through.
    
    While fixAtCurrent=True, this operator does not forward dirty notifications 
    to downstream operators. Instead, it remembers the total ROI of the dirty area 
    (as a bounding box), and emits the entire dirty ROI at once as soon as it becomes "unfixed".
    Also, this operator returns only zeros while fixAtCurrent=True.
    """
    fixAtCurrent = InputSlot(value=False)
    Input = InputSlot(allow_mask=True)
    Output = OutputSlot(allow_mask=True)

    def __init__(self, *args, **kwargs):
        super(OpCacheFixer, self).__init__(*args, **kwargs)
        self._fixed = False
        self._fixed_dirty_roi = None

    def setupOutputs(self):
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.dontcache = self.fixAtCurrent.value

        # During initialization, if fixAtCurrent is configured before Input, then propagateDirty was never called.
        # We need to make sure that the dirty logic for fixAtCurrent has definitely been called here.
        self.propagateDirty(self.fixAtCurrent, (), slice(None))

    def execute(self, slot, subindex, roi, result):
        if self._fixed:
            # The downstream user doesn't know he's getting fake data.
            # When we become "unfixed", we need to tell him.
            self._expand_fixed_dirty_roi( (roi.start, roi.stop) )
            result[:] = 0
        else:
            self.Input(roi.start, roi.stop).writeInto(result).wait()
        
    def propagateDirty(self, slot, subindex, roi):
        if slot is self.fixAtCurrent:
            # If we're becoming UN-fixed, send out a big dirty notification
            if ( self._fixed and not self.fixAtCurrent.value and
                 self._fixed_dirty_roi and (self._fixed_dirty_roi[1] - self._fixed_dirty_roi[0] > 0).all() ):
                self.Output.setDirty( *self._fixed_dirty_roi )
                self._fixed_dirty_roi = None
            self._fixed = self.fixAtCurrent.value
        elif slot is self.Input:
            if self._fixed:
                # We can't propagate this downstream,
                #  but we need to remember that it was marked dirty.
                # Expand our dirty bounding box.
                self._expand_fixed_dirty_roi( (roi.start, roi.stop) )
            else:
                self.Output.setDirty(roi.start, roi.stop)

    def _init_fixed_dirty_roi(self):
        # Intentionally flipped: nothing is dirty at first.
        entire_roi = roiFromShape(self.Input.meta.shape)
        self._fixed_dirty_roi = (entire_roi[1], entire_roi[0])

    def _expand_fixed_dirty_roi(self, roi):
        if self._fixed_dirty_roi is None:
            self._init_fixed_dirty_roi()
        start, stop = self._fixed_dirty_roi
        start = numpy.minimum(start, roi[0])
        stop = numpy.maximum(stop, roi[1])
        self._fixed_dirty_roi = (start, stop)
        
