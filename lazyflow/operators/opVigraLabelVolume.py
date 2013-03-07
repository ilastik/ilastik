import logging

import numpy
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot

logger = logging.getLogger(__name__)

class OpVigraLabelVolume(Operator):
    """
    Operator that simply wraps vigra's labelVolume function.
    """
    name = "OpVigraLabelVolume"
    category = "Vigra"
    
    Input = InputSlot() 
    BackgroundValue = InputSlot(optional=True)
    
    Output = OutputSlot()
    
    def setupOutputs(self):
        inputShape = self.Input.meta.shape

        # Must have at most 1 time slice
        timeIndex = self.Input.meta.axistags.index('t')
        assert timeIndex == len(inputShape) or inputShape[timeIndex] == 1
        
        # Must have at most 1 channel
        channelIndex = self.Input.meta.axistags.channelIndex
        assert channelIndex == len(inputShape) or inputShape[channelIndex] == 1

        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.uint32
        
    def execute(self, slot, subindex, roi, destination):
        assert slot == self.Output
        
        resultView = destination.view( vigra.VigraArray )
        resultView.axistags = self.Input.meta.axistags
        
        inputData = self.Input(roi.start, roi.stop).wait()
        inputData = inputData.view(vigra.VigraArray)
        inputData.axistags = self.Input.meta.axistags

        # Drop the time axis, which vigra.labelVolume doesn't remove automatically
        axiskeys = [tag.key for tag in inputData.axistags]        
        if 't' in axiskeys:
            inputData = inputData.bindAxis('t', 0)
            resultView = resultView.bindAxis('t', 0)

        # Drop the channel axis, too.
        if 'c' in axiskeys:
            inputData = inputData.bindAxis('c', 0)
            resultView = resultView.bindAxis('c', 0)

        inputData = inputData.view(numpy.ndarray)

        if self.BackgroundValue.ready():
            bg = self.BackgroundValue.value
            if isinstance( bg, numpy.ndarray ):
                # If background value was given as a 1-element array, extract it.
                assert bg.size == 1
                bg = bg.squeeze()[()]
            if isinstance( bg, numpy.float ):
                bg = float(bg)
            else:
                bg = int(bg)
            vigra.analysis.labelVolumeWithBackground(inputData, background_value=bg, out=resultView)
        else:
            vigra.analysis.labelVolumeWithBackground(inputData, out=resultView)
        
        return destination

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot == self.Input:
            # If anything changed, the whole image is now dirty 
            #  because a single pixel change can trigger a cascade of relabeling.
            self.Output.setDirty( slice(None) )
        elif inputSlot == self.BackgroundValue:
            self.Output.setDirty( slice(None) )

