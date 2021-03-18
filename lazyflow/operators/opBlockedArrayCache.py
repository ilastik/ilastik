from __future__ import absolute_import

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

import copy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility import RamMeasurementContext

from .opCacheFixer import OpCacheFixer
from .opCache import ManagedBlockedCache
from .opSimpleBlockedArrayCache import OpSimpleBlockedArrayCache


class OpBlockedArrayCache(Operator, ManagedBlockedCache):
    """
    A blockwise array cache designed to replace the old OpBlockedArrayCache.
    Instead of a monolithic implementation, this operator is a small pipeline of three simple operators.

    The actual caching of data is handled by an unblocked cache, so the "blocked" functionality is
    implemented via separate "splitting" operator that comes after the cache.
    Also, the "fixAtCurrent" feature is implemented in a special operator, which comes before the cache.
    """

    fixAtCurrent = InputSlot(value=False)
    Input = InputSlot(allow_mask=True)
    # BlockShape = InputSlot()
    BlockShape = InputSlot(optional=True)  # If 'None' is present, those items will be treated as max for the dimension.
    # If not provided, will be set to Input.meta.shape
    BypassModeEnabled = InputSlot(value=False)
    CompressionEnabled = InputSlot(value=False)

    Output = OutputSlot(allow_mask=True)
    CleanBlocks = OutputSlot()  # A list of slicings indicating which blocks are stored in the cache and clean.

    def __init__(self, *args, **kwargs):
        super(OpBlockedArrayCache, self).__init__(*args, **kwargs)

        # SCHEMATIC WHEN BypassModeEnabled == False:
        #
        # Input ---------> opCacheFixer -> opSimpleBlockedArrayCache -> (indirectly via execute) -> Output
        #                 /               /
        # fixAtCurrent --                /
        #                               /
        # BlockShape -------------------

        # SCHEMATIC WHEN BypassModeEnabled == True:
        #
        # Input --> (indirectly via execute) -> Output

        self._opCacheFixer = OpCacheFixer(parent=self)
        self._opCacheFixer.Input.connect(self.Input)
        self._opCacheFixer.fixAtCurrent.connect(self.fixAtCurrent)

        self._opSimpleBlockedArrayCache = OpSimpleBlockedArrayCache(parent=self)
        self._opSimpleBlockedArrayCache.CompressionEnabled.connect(self.CompressionEnabled)
        self._opSimpleBlockedArrayCache.Input.connect(self._opCacheFixer.Output)
        self._opSimpleBlockedArrayCache.BlockShape.connect(self.BlockShape)
        self._opSimpleBlockedArrayCache.BypassModeEnabled.connect(self.BypassModeEnabled)
        self.CleanBlocks.connect(self._opSimpleBlockedArrayCache.CleanBlocks)
        self.Output.connect(self._opSimpleBlockedArrayCache.Output)

        # Instead of connecting our Output directly to our internal pipeline,
        # We manually forward the data via the execute() function,
        #  which allows us to implement a bypass for the internal pipeline if Enabled
        # self.Output.connect( self._opSimpleBlockedArrayCache.Output )

        # Since we didn't directly connect the pipeline to our output, explicitly forward dirty notifications
        self._opSimpleBlockedArrayCache.Output.notifyDirty(lambda slot, roi: self.Output.setDirty(roi.start, roi.stop))

        # This member is used by tests that check RAM usage.
        self.setup_ram_context = RamMeasurementContext()
        self.registerWithMemoryManager()

    def setupOutputs(self):
        if not self.BlockShape.connected() and not self.BlockShape.ready():
            self.BlockShape.setValue(self.Input.meta.shape)
        # Copy metadata from the internal pipeline to the output
        self.Output.meta.assignFrom(self._opSimpleBlockedArrayCache.Output.meta)

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here"

    def propagateDirty(self, slot, subindex, roi):
        pass

    def setInSlot(self, slot, subindex, key, value):
        pass  # Nothing to do here: Input is connected to an internal operator

    # ======= mimic cache interface for wrapping operators =======

    def usedMemory(self):
        return self._opSimpleBlockedArrayCache.usedMemory()

    def fractionOfUsedMemoryDirty(self):
        # dirty memory is discarded immediately
        return self._opSimpleBlockedArrayCache.fractionOfUsedMemoryDirty()

    def lastAccessTime(self):
        return self._opSimpleBlockedArrayCache.lastAccessTime()

    def getBlockAccessTimes(self):
        return self._opSimpleBlockedArrayCache.getBlockAccessTimes()

    def freeMemory(self):
        return self._opSimpleBlockedArrayCache.freeMemory()

    def freeBlock(self, key):
        return self._opSimpleBlockedArrayCache.freeBlock(key)

    def freeDirtyMemory(self):
        return self._opSimpleBlockedArrayCache.freeDirtyMemory()

    def generateReport(self, report):
        self._opSimpleBlockedArrayCache.generateReport(report)
        child = copy.copy(report)
        super(OpBlockedArrayCache, self).generateReport(report)
        report.children.append(child)
