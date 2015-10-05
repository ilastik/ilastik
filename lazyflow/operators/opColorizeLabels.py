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
import zlib
import copy
import numpy
import os
import tempfile
import threading
from functools import partial
import math
from lazyflow.utility import FileLock

import numpy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import TinyVector

import logging
logger = logging.getLogger(__name__)

def applyToElement(axistags, tagkey, tup, f):
    """
    Axistags utility function.
    Apply f to the element of the tuple/list specified by the given axistags and key.
    """
    index = axistags.index(tagkey)
    if hasattr(f, '__call__'):
        e = f(tup[index])
    else:
        e = f
    return tup[:index] + type(tup)([e]) + tup[index+1:]

def getElement(axistags, tagkey, tup):
    """
    Axistags utility function.
    Get the value from the sequence tup according to the location of tagkey within tags.
    """
    return tup[axistags.index(tagkey)]

class OpColorizeLabels(Operator):
    name = "OpColorizeLabels"
    category = "display adaptor"
    
    Input = InputSlot()
    OverrideColors = InputSlot(stype='object', value={0 : (0,0,0,0)} )  # dict of { label : (R,G,B,A) }
                                                                        # By default, label 0 is black and transparent
    Output = OutputSlot() # 4 channels: RGBA

    colortable = None
    _lock = threading.Lock()
        
    def __init__(self, *args, **kwargs):
        super(OpColorizeLabels, self).__init__(*args, **kwargs)

        self.overrideColors = {}

        with OpColorizeLabels._lock:
            if OpColorizeLabels.colortable is None:
                OpColorizeLabels.colortable = OpColorizeLabels.generateColortable(2**22)

        # Pre-generate the table of data
        self.colortable = copy.copy(OpColorizeLabels.colortable)
        
    def setupOutputs(self):
        inputTags = self.Input.meta.axistags
        inputShape = self.Input.meta.shape
        self.channelIndex = inputTags.index('c')
        assert inputShape[self.channelIndex] == 1, "Input must be a single-channel label image"
                
        self.Output.meta.assignFrom(self.Input.meta)

        applyToChannel = partial(applyToElement, inputTags, 'c')
        self.Output.meta.shape = applyToChannel(inputShape, 4) # RGBA
        self.Output.meta.dtype = numpy.uint8
        self.Output.meta.drange = (0, 255)
        self.Output.meta.axistags["c"].description = "rgba"

        newOverrideColors = self.OverrideColors.value
        if newOverrideColors != self.overrideColors:
            # Add new overrides
            for label, color in newOverrideColors.items():
                if label not in self.overrideColors:
                    self.colortable[label] = color
            # Replace removed overrides with their original random values
            for label, color in self.overrideColors.items():
                if label not in newOverrideColors:
                    self.colortable[label] = OpColorizeLabels.colortable[label]

        self.overrideColors = newOverrideColors
    
    def setStartToZero(self,start,stop):
        start = [0]*len(start)
        stop = [end-begin for begin,end in zip(start,stop)]
        start = TinyVector(start)
        stop = TinyVector(stop)
        return start,stop
    
    def execute(self, slot, subindex, roi, result):
        fullKey = roi.toSlice()
        roiCopy = copy.copy(roi)
        roiCopy.start, roiCopy.stop = self.setStartToZero(roi.start, roi.stop)
        resultKey = roiCopy.toSlice()
        
        # Input has only one channel
        thinKey = applyToElement(self.Input.meta.axistags, 'c', fullKey, slice(0,1))
        inputData = self.Input[thinKey].wait()
        dropChannelKey = applyToElement(self.Input.meta.axistags, 'c', resultKey, 0)
        channellessInput = inputData[dropChannelKey]

        # Advanced indexing with colortable applies the relabeling from labels to colors.
        # If we get an error here, we may need to expand the colortable (currently supports only 2**22 labels.)
        channelSlice = getElement(self.Input.meta.axistags, 'c', fullKey)
        # channellessInput % self.colortable.shape[0]
        channellessInput &= self.colortable.shape[0]-1 # Cheaper than mod for 2**X
        result[...] = self.colortable[:, channelSlice][channellessInput]
        return result

    @staticmethod
    def generateColortable(size):
        lg = math.log(size, 2)
        # The execute function makes this assumption, so check it.
        assert lg == math.floor(lg), "Colortable size must be a power of 2."
        
        lazyflowSettingsDir = os.path.expanduser('~/.lazyflow')
        try:
            if not os.path.exists( lazyflowSettingsDir ):
                os.makedirs( lazyflowSettingsDir )
        except Exception, ex:
            import warnings
            warnings.warn("Not able to create dir: ~/.lazyflow.  Writing random_color_table.npy to /tmp instead.")
            # Write to a temporary directory.
            lazyflowSettingsDir = tempfile.mkdtemp()

        cachedColortablePath = os.path.join(lazyflowSettingsDir, 'random_color_table.npy')

        with FileLock(cachedColortablePath):
            # If possible, load the table from disk
            loadedTable = False
            if os.path.exists( cachedColortablePath ):
                try:
                    table = numpy.load(cachedColortablePath)
                    if table.shape[0] == size:
                        loadedTable = True
                    else:
                        table = None
                except: 
                    table = None
            
            if not loadedTable:
                randState = numpy.random.mtrand.RandomState(0)
                table = numpy.zeros((size,4), dtype=numpy.uint8)
                table[...] = randState.random_integers( 0, 255, table.shape )
                table[...,3] = 255 # Alpha is 255 by default.
    
                # Save it for next session
                saved = False
                ex = None
                try:
                    if not os.path.exists( lazyflowSettingsDir ):
                        os.makedirs( lazyflowSettingsDir )
                except Exception, ex:
                    pass
                else:
                    try:
                        numpy.save(cachedColortablePath, table)
                        saved = True
                    except Exception, ex:
                        pass
    
                if not saved:
                    # It's not worth crashing if the table can't be cached.
                    logger.warn( "Wasn't able to create cache file: " + cachedColortablePath )
                    logger.warn( "Caught exception: " + str(ex) )
                        
            return table

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot == self.Input:
            self.Output.setDirty(roi)
        elif inputSlot == self.OverrideColors:
            self.Output.setDirty(slice(None))
        else:
            assert False, "Unknown input slot"
            
