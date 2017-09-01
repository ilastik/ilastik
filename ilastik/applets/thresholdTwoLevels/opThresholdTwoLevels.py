from __future__ import absolute_import
from __future__ import division
###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
from builtins import range
from past.utils import old_div
import logging

import numpy as np
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpBlockedArrayCache, OpSingleChannelSelector, OpReorderAxes, OpFilterLabels, OpMultiArrayMerger
from ilastik.applets.base.applet import DatasetConstraintError
from lazyflow.operators.generic import OpConvertDtype, OpPixelOperator


# local
from .thresholdingTools import OpAnisotropicGaussianSmoothing5d, select_labels
from .ipht import threshold_from_cores

try:
    from ._OpGraphCut import segmentGC
    _has_graphcut = True
except ImportError:
    _has_graphcut = False    

logger = logging.getLogger(__name__)

class ThresholdMethod(object):
    SIMPLE = 0      # single-threshold
    HYSTERESIS = 1  # hysteresis, a.k.a "two-level"
    GRAPHCUT = 2    # single, but tuned by graphcut
    IPHT = 3        # identity-preserving hysteresis thresholding

class OpThresholdTwoLevels(Operator):
    RawInput = InputSlot(optional=True)  # Display only
    InputChannelColors = InputSlot(optional=True) # Display only

    InputImage = InputSlot()
    MinSize = InputSlot(stype='int', value=10)
    MaxSize = InputSlot(stype='int', value=1000000)
    HighThreshold = InputSlot(stype='float', value=0.5)
    LowThreshold = InputSlot(stype='float', value=0.2)
    SmootherSigma = InputSlot(value={'z': 1.0, 'y': 1.0, 'x': 1.0})
    Channel = InputSlot(value=0)
    CoreChannel = InputSlot(value=0)
    CurOperator = InputSlot(stype='int', value=ThresholdMethod.SIMPLE) # This slot would be better named 'method',
                                                                       # but we're keeping this slot name for backwards
                                                                       # compatibility with old project files
    Beta = InputSlot(value=.2) # For GraphCut

    ## Output slots ##
    Output = OutputSlot()
    CachedOutput = OutputSlot()  # For the GUI (blockwise-access)

    # For serialization
    CacheInput = InputSlot(optional=True)
    CleanBlocks = OutputSlot()

    ## Debug outputs

    InputChannel = OutputSlot()
    Smoothed = OutputSlot()
    BigRegions = OutputSlot()
    SmallRegions = OutputSlot()
    FilteredSmallLabels = OutputSlot()
    BeforeSizeFilter = OutputSlot()
    
    ## Basic schematic (debug outputs not shown)
    ## 
    ## InputImage -> opReorder -> opSmoother -> opSmootherCache --> opFinalChannelSelector --> opSumInputs --------------------> opFinalThreshold -> opFinalFilter -> opReorder -> Output
    ##                                                         \                             /                                  /                                              \
    ##                                                          --> opCoreChannelSelector --> opCoreThreshold -> opCoreFilter --                                                opCache -> CachedOutput
    ##                                                                                                                                                                                 `-> CleanBlocks
    def __init__(self, *args, **kwargs):
        super(OpThresholdTwoLevels, self).__init__(*args, **kwargs)

        self.opReorderInput = OpReorderAxes(parent=self)
        self.opReorderInput.AxisOrder.setValue('tzyxc')
        self.opReorderInput.Input.connect(self.InputImage)

        # PROBABILITIES: Convert to float32
        self.opConvertProbabilities = OpConvertDtype( parent=self )
        self.opConvertProbabilities.ConversionDtype.setValue( np.float32 )
        self.opConvertProbabilities.Input.connect( self.opReorderInput.Output )

        # PROBABILITIES: Normalize drange to [0.0, 1.0]
        self.opNormalizeProbabilities = OpPixelOperator( parent=self )
        def normalize_inplace(a):
            drange = self.opNormalizeProbabilities.Input.meta.drange
            if drange is None or (drange[0] == 0.0 and drange[1] == 1.0):
                return a
            a[:] -= drange[0]
            a[:] = a[:]/float(( drange[1] - drange[0] ))
            return a
        self.opNormalizeProbabilities.Input.connect( self.opConvertProbabilities.Output )
        self.opNormalizeProbabilities.Function.setValue( normalize_inplace )
        
        self.opSmoother = OpAnisotropicGaussianSmoothing5d(parent=self)
        self.opSmoother.Sigmas.connect( self.SmootherSigma )
        self.opSmoother.Input.connect( self.opNormalizeProbabilities.Output )
        
        self.opSmootherCache = OpBlockedArrayCache(parent=self)
        self.opSmootherCache.BlockShape.setValue((1, None, None, None, 1))
        self.opSmootherCache.Input.connect( self.opSmoother.Output )
        
        self.opCoreChannelSelector = OpSingleChannelSelector(parent=self)
        self.opCoreChannelSelector.Index.connect( self.CoreChannel )
        self.opCoreChannelSelector.Input.connect( self.opSmootherCache.Output )
        
        self.opCoreThreshold = OpLabeledThreshold(parent=self)
        self.opCoreThreshold.Method.setValue( ThresholdMethod.SIMPLE )
        self.opCoreThreshold.FinalThreshold.connect( self.HighThreshold )
        self.opCoreThreshold.Input.connect( self.opCoreChannelSelector.Output )

        self.opCoreFilter = OpFilterLabels(parent=self)
        self.opCoreFilter.BinaryOut.setValue(False)
        self.opCoreFilter.MinLabelSize.connect( self.MinSize )
        self.opCoreFilter.MaxLabelSize.connect( self.MaxSize )
        self.opCoreFilter.Input.connect( self.opCoreThreshold.Output )
        
        self.opFinalChannelSelector = OpSingleChannelSelector(parent=self)
        self.opFinalChannelSelector.Index.connect( self.Channel )
        self.opFinalChannelSelector.Input.connect( self.opSmootherCache.Output )

        self.opSumInputs = OpMultiArrayMerger(parent=self) # see setupOutputs (below) for input connections
        self.opSumInputs.MergingFunction.setValue( sum )
        
        self.opFinalThreshold = OpLabeledThreshold(parent=self)
        self.opFinalThreshold.Method.connect( self.CurOperator )
        self.opFinalThreshold.FinalThreshold.connect( self.LowThreshold )
        self.opFinalThreshold.GraphcutBeta.connect( self.Beta )
        self.opFinalThreshold.CoreLabels.connect( self.opCoreFilter.Output )
        self.opFinalThreshold.Input.connect( self.opSumInputs.Output )
        
        self.opFinalFilter = OpFilterLabels(parent=self)
        self.opFinalFilter.BinaryOut.setValue(False)
        self.opFinalFilter.MinLabelSize.connect( self.MinSize )
        self.opFinalFilter.MaxLabelSize.connect( self.MaxSize )
        self.opFinalFilter.Input.connect( self.opFinalThreshold.Output )

        self.opReorderOutput = OpReorderAxes(parent=self)
        #self.opReorderOutput.AxisOrder.setValue('tzyxc') # See setupOutputs()
        self.opReorderOutput.Input.connect(self.opFinalFilter.Output)

        self.Output.connect( self.opReorderOutput.Output )

        self.opCache = OpBlockedArrayCache(parent=self)
        self.opCache.CompressionEnabled.setValue(True)
        self.opCache.Input.connect( self.opReorderOutput.Output )
        
        self.CachedOutput.connect( self.opCache.Output )
        self.CleanBlocks.connect( self.opCache.CleanBlocks )
        
        ## Debug outputs
        self.Smoothed.connect( self.opSmootherCache.Output )
        self.InputChannel.connect( self.opFinalChannelSelector.Output )
        self.SmallRegions.connect( self.opCoreThreshold.Output )
        self.FilteredSmallLabels.connect( self.opCoreFilter.Output )
        self.BeforeSizeFilter.connect( self.opFinalThreshold.Output )

        # Since hysteresis thresholding creates the big regions and immediately discards the bad ones,
        # we have to recreate it here if the user wants to view it as a debug layer 
        self.opBigRegionsThreshold = OpLabeledThreshold(parent=self)
        self.opBigRegionsThreshold.Method.setValue( ThresholdMethod.SIMPLE )
        self.opBigRegionsThreshold.FinalThreshold.connect( self.LowThreshold )
        self.opBigRegionsThreshold.Input.connect( self.opFinalChannelSelector.Output )
        self.BigRegions.connect( self.opBigRegionsThreshold.Output )

    def setupOutputs(self):
        axes = self.InputImage.meta.getAxisKeys()
        self.opReorderOutput.AxisOrder.setValue(axes)

        # Cache individual t,c slices
        blockshape = tuple(1 if k in 'tc' else None for k in axes)
        self.opCache.BlockShape.setValue(blockshape)
        
        if self.CurOperator.value in (ThresholdMethod.HYSTERESIS, ThresholdMethod.IPHT) \
        and self.Channel.value != self.CoreChannel.value:
            self.opSumInputs.Inputs.resize(2)
            self.opSumInputs.Inputs[0].connect( self.opFinalChannelSelector.Output )
            self.opSumInputs.Inputs[1].connect( self.opCoreChannelSelector.Output )
        else:
            self.opSumInputs.Inputs.resize(1)
            self.opSumInputs.Inputs[0].connect( self.opFinalChannelSelector.Output )

    def setInSlot(self, slot, subindex, roi, value):
        self.opCache.setInSlot(self.opCache.Input, subindex, roi, value)

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        pass # dirtiness propagation is handled in the sub-operators


class OpLabeledThreshold(Operator):
    Input = InputSlot() # Must have exactly 1 channel
    CoreLabels = InputSlot(optional=True) # Not used for 'Simple' method.
    Method = InputSlot(value=ThresholdMethod.SIMPLE)
    FinalThreshold = InputSlot(value=0.2)
    GraphcutBeta = InputSlot(value=0.2) # Graphcut only

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpLabeledThreshold, self).__init__(*args, **kwargs)

        execute_funcs = {}
        execute_funcs[ThresholdMethod.SIMPLE]     = self._execute_SIMPLE
        execute_funcs[ThresholdMethod.HYSTERESIS] = self._execute_HYSTERESIS
        execute_funcs[ThresholdMethod.GRAPHCUT]   = self._execute_GRAPHCUT
        execute_funcs[ThresholdMethod.IPHT]       = self._execute_IPHT
        self.execute_funcs = execute_funcs
    
    def setupOutputs(self):
        assert self.Input.meta.getAxisKeys() == list("tzyxc")
        assert self.Input.meta.shape[-1] == 1
        if self.CoreLabels.ready():
            assert self.CoreLabels.meta.getAxisKeys() == list("tzyxc")
        
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.dtype = np.uint32

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty()

    def execute(self, slot, subindex, roi, result):
        result = vigra.taggedView( result, self.Output.meta.axistags )

        # Iterate over time slices to avoid connected component problems.
        for t_index, t in enumerate(range(roi.start[0], roi.stop[0])):
            t_slice_roi = roi.copy()
            t_slice_roi.start[0] = t
            t_slice_roi.stop[0] = t+1

            result_slice = result[t_index:t_index+1]
            self.execute_funcs[self.Method.value](t_slice_roi, result_slice)
        
    def _execute_SIMPLE(self, roi, result):
        assert result.shape[0] == 1
        assert tuple(roi.stop - roi.start) == result.shape

        final_threshold = self.FinalThreshold.value

        data = self.Input(roi.start, roi.stop).wait()
        data = vigra.taggedView(data, self.Input.meta.axistags)
        
        result = vigra.taggedView(result, self.Output.meta.axistags)
        
        binary = (data >= final_threshold).view(np.uint8)
        vigra.analysis.labelMultiArrayWithBackground(binary[0,...,0], out=result[0,...,0])

    def _execute_HYSTERESIS(self, roi, result):
        self._execute_SIMPLE(roi, result)
        final_labels = vigra.taggedView( result, self.Output.meta.axistags )

        core_labels = self.CoreLabels(roi.start, roi.stop).wait()
        core_labels = vigra.taggedView( core_labels, self.CoreLabels.meta.axistags )
        
        select_labels(core_labels, final_labels) # Edits final_labels in-place

    def _execute_IPHT(self, roi, result):
        core_labels = self.CoreLabels(roi.start, roi.stop).wait()
        core_labels = vigra.taggedView( core_labels, self.CoreLabels.meta.axistags )
        
        data = self.Input(roi.start, roi.stop).wait()
        data = vigra.taggedView(data, self.Input.meta.axistags)

        final_threshold = self.FinalThreshold.value
        result = vigra.taggedView( result, self.Output.meta.axistags )
        threshold_from_cores(data[0,...,0], core_labels[0,...,0], final_threshold, out=result[0,...,0])

    def _execute_GRAPHCUT(self, roi, result):
        data = self.Input(roi.start, roi.stop).wait()
        data = vigra.taggedView(data, self.Input.meta.axistags)
        data_zyx = data[0,...,0]

        beta = self.GraphcutBeta.value
        ft = self.FinalThreshold.value

        # The segmentGC() function will implicitly threshold at 0.5,
        # but we want to respect the user's FinalThreshold setting.
        # Here, we scale from input pixels --> gc potentials in the following way:
        #
        # 0.0..FT --> 0.0..0.5
        # 0.5..FT --> 0.5..1.0
        #
        # For instance, input pixels that match the user's FT exactly will map to 0.5,
        # and graphcut will place them on the threshold border.

        above_threshold_mask = (data_zyx >= ft)
        below_threshold_mask = ~above_threshold_mask

        data_zyx[below_threshold_mask] *= old_div(0.5,ft)
        data_zyx[above_threshold_mask] = 0.5 + old_div((data_zyx[above_threshold_mask] - ft),(1-ft))
        
        binary_seg_zyx = segmentGC( data_zyx, beta ).astype(np.uint8)
        del data_zyx
        vigra.analysis.labelMultiArrayWithBackground(binary_seg_zyx, out=result[0,...,0])
