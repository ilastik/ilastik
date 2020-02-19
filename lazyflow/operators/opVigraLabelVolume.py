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
# 		   http://ilastik.org/license/
###############################################################################

import warnings

import numpy
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot


class _OpVigraLabelVolume(Operator):
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
        timeIndex = self.Input.meta.axistags.index("t")
        assert timeIndex == len(inputShape) or inputShape[timeIndex] == 1

        # Must have at most 1 channel
        channelIndex = self.Input.meta.axistags.channelIndex
        assert channelIndex == len(inputShape) or inputShape[channelIndex] == 1

        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.uint32

    def execute(self, slot, subindex, roi, destination):
        assert slot == self.Output

        resultView = destination.view(vigra.VigraArray)
        resultView.axistags = self.Input.meta.axistags

        inputData = self.Input(roi.start, roi.stop).wait()
        inputData = inputData.view(vigra.VigraArray)
        inputData.axistags = self.Input.meta.axistags

        # Drop the time axis, which vigra.labelVolume doesn't remove automatically
        axiskeys = [tag.key for tag in inputData.axistags]
        if "t" in axiskeys:
            inputData = inputData.bindAxis("t", 0)
            resultView = resultView.bindAxis("t", 0)

        # Drop the channel axis, too.
        if "c" in axiskeys:
            inputData = inputData.bindAxis("c", 0)
            resultView = resultView.bindAxis("c", 0)

        # I have no idea why, but vigra sometimes throws a precondition error if this line is present.
        # ...on the other hand, I can't remember why I added this line in the first place...
        # inputData = inputData.view(numpy.ndarray)

        if self.BackgroundValue.ready():
            bg = self.BackgroundValue.value
            if isinstance(bg, numpy.ndarray):
                # If background value was given as a 1-element array, extract it.
                assert bg.size == 1
                bg = bg.squeeze()[()]
            if isinstance(bg, numpy.float):
                bg = float(bg)
            else:
                bg = int(bg)
            if len(inputData.shape) == 2:
                vigra.analysis.labelImageWithBackground(inputData, background_value=bg, out=resultView)
            else:
                vigra.analysis.labelVolumeWithBackground(inputData, background_value=bg, out=resultView)
        else:
            if len(inputData.shape) == 2:
                vigra.analysis.labelImageWithBackground(inputData, out=resultView)
            else:
                vigra.analysis.labelVolumeWithBackground(inputData, out=resultView)

        return destination

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot == self.Input:
            # If anything changed, the whole image is now dirty
            #  because a single pixel change can trigger a cascade of relabeling.
            self.Output.setDirty(slice(None))
        elif inputSlot == self.BackgroundValue:
            self.Output.setDirty(slice(None))


class OpVigraLabelVolume(_OpVigraLabelVolume):
    def __init__(self, *args, **kwargs):
        warnings.warn("Usage of OpVigraLabelVolume is deprecated, use OpLabelVolume instead!", DeprecationWarning)
        super(OpVigraLabelVolume, self).__init__(*args, **kwargs)
