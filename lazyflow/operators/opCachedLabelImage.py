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

from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.operators import OpLabelImage, OpCompressedCache, Operator
from lazyflow.operators.opCache import OpCache

class OpCachedLabelImage(OpCache):
    """
    Combines OpLabelImage with OpCompressedCache, and provides a default block shape.
    """
    Input = InputSlot()
    
    BackgroundLabels = InputSlot(optional=True) # Optional. See OpLabelImage for details.
    BlockShape = InputSlot(optional=True)   # If not provided, blockshape is 1 time slice, 1 channel slice, 
                                            #  and the entire volume in xyz.
    Output = OutputSlot()

    # Serialization support
    InputHdf5 = InputSlot(optional=True)
    CleanBlocks = OutputSlot()
    OutputHdf5 = OutputSlot() # See OpCachedLabelImage for details
    
    # Schematic:
    #
    # BackgroundLabels --     BlockShape --
    #                    \                 \
    # Input ------------> OpLabelImage ---> OpCompressedCache --> Output
    #                                                        \
    #                                                         --> CleanBlocks
    
    def __init__(self, *args, **kwargs):
        super(OpCachedLabelImage, self).__init__(*args, **kwargs)
        
        # Hook up the labeler
        self._opLabelImage = OpLabelImage( parent=self )
        self._opLabelImage.Input.connect( self.Input )
        self._opLabelImage.BackgroundLabels.connect( self.BackgroundLabels )

        # Hook up the cache
        self._opCache = OpCompressedCache( parent=self )
        self._opCache.Input.connect( self._opLabelImage.Output )
        self._opCache.InputHdf5.connect( self.InputHdf5 )
        
        # Hook up our output slots
        self.Output.connect( self._opCache.Output )
        self.CleanBlocks.connect( self._opCache.CleanBlocks )
        self.OutputHdf5.connect( self._opCache.OutputHdf5 )
        
    def generateReport(self, report):
        return self._opCache.generateReport(report)
    
    def usedMemory(self):
        return self._opCache.usedMemory()
    
    def fractionOfUsedMemoryDirty(self):
        return self._opCache.fractionOfUsedMemoryDirty()
    
    def lastAccessTime(self):
        return self._opCache.lastAccessTime()
    
    def setupOutputs(self):
        if self.BlockShape.ready():
            self._opCache.BlockShape.setValue( self.BlockShape.value )
        else:
            # By default, block shape is the same as the entire image shape,
            #  but only 1 time slice and 1 channel slice
            taggedBlockShape = self.Input.meta.getTaggedShape()
            taggedBlockShape['t'] = 1
            taggedBlockShape['c'] = 1
            self._opCache.BlockShape.setValue( tuple( taggedBlockShape.values() ) )

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."
    
    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do...

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.Input or slot == self.InputHdf5, "Invalid slot for setInSlot(): {}".format( slot.name )
        # Nothing to do here.
        # Our Input slots are directly fed into the cache, 
        #  so all calls to __setitem__ are forwarded automatically 
            
