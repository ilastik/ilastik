import numpy as np
import vigra

from lazyflow.operator import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpReorderAxes, OpCompressedCache

import logging
logger = logging.getLogger(__name__)

try:
    import opengm
except ImportError:
    have_opengm = False
else:
    have_opengm = True


# Implements opengm filtering
class OpOpenGMFilter(Operator):
    """
    Operator that uses opengm to cleanup labels
    """
    name = "OpenGM Filter"

    Input = InputSlot()
    RawInput = InputSlot()
    Configuration = InputSlot()

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        # internal threshold for computing mask and energy offset 
        # to avoid log problems
        self._epsilon = 0.000001
        super(OpOpenGMFilter, self).__init__(*args, **kwargs)
        self._cache = OpCompressedCache( parent=self )
        self._cache.Input.connect(self.Input)
        self.Output.connect(self._cache.Output)

        self.opMask = OpBrainMask(parent=self)
        self.opMask.Input.connect(self.RawInput)
        self.Output.connect(self.opMask.CachedOutput)

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

        ts = self.Input.meta.getTaggedShape()
        ts['t'] = 1
        ts['c'] = 1
        blockshape = map(lambda k: ts[k],''.join(ts.keys()))
        self._cache.BlockShape.setValue(tuple(blockshape))

    def propagateDirty(self, slot, subindex, roi):
        # TODO what are the actual conditions here?
        self.Output.setDirty(slice(None)) 

    def execute(self, slot, subindex, roi, result):
        logger.debug("Opengm on roi {}".format(roi))
        # FIXME don't recompute this every time
        # compute mask from raw input channel

        # FIXME We need a chache so the computation is only carried out once
        raw_data = self.RawInput[...].wait()
        print raw_data.shape
        bool_mask = np.ma.masked_less_equal(raw_data[0,...,0],
                                            self._epsilon).mask
        self._mask = np.zeros(bool_mask.shape, dtype=np.uint32)
        self._mask[~bool_mask] = 1.0

        conf = self.Configuration.value
        if 'sigma' not in conf:
            raise ValueError(
                "expected key 'sigma' in configuration")
        sigma = conf['sigma']

        if 'unaries' not in conf:
            raise ValueError(
                "expected key 'unaries' in configuration")
        unaries = conf['unaries']

        print roi, 'ROI'
        print self.Input.meta.shape, 'input metashape'
        tmp_roi = roi.copy()
        for i,a in enumerate(self.Input.meta.shape):
            tmp_roi.setDim(i,0,self.Input.meta.shape[i])        
        print tmp_roi, 'TMP_ROI'

        tmp_data = self.Input.get(tmp_roi).wait().astype( np.float32 )
        print tmp_data.shape, 'data shape'
        return result
        result[0,...,0] = self._opengmFilter(tmp_data, sigma, unaries)
        print result.shape , 'result shape'


    def _opengmFilter(self, vol, filter_size, unaries_scale):
        print unaries_scale, filter_size
        print vol.shape , 'Volume'

        # make uncertainty edge image
        pfiltered = np.zeros_like(vol[0])
        for c in xrange(vol.shape[-1]):
            pfiltered[...,c] = vigra.gaussianSmoothing( vol[0,...,c], 
                                                        float(1.2))
        pmap = np.sort(pfiltered, axis=-1)
        uncertainties  = pmap[...,-1]-pmap[...,-2] 
        # set starting point
        init_data = np.argmax(vol[0],axis=-1).astype( np.uint32 )
        init_data = opengm.getStartingPointMasked(init_data, self._mask)      
        unaries = -unaries_scale*np.log(vol[0] + self._epsilon)
        gm = opengm.pottsModel3dMasked(unaries=unaries, 
                                       regularizer=uncertainties, 
                                       mask=self._mask)
        try:
            inf = opengm.inference.FastPd(gm)
            inf.setStartingPoint(init_data)
            inf.infer(inf.verboseVisitor())
        except:
            inf = opengm.inference.AlphaExpansion(gm)
            inf.setStartingPoint(init_data)
            inf.infer(inf.verboseVisitor())
        pred = opengm.makeMaskedState(self._mask, inf.arg(), labelIdx=0)

        print pred.shape, 'pred shape'
        return pred

class OpBrainMask(Operator):
    """
    This operator computes a mask image based on the assumption that in the 
    MRI input data all values outside of the skull were set to 0 during 
    pre-processing
    """
    
    Input = InputSlot() # the raw data
    Output = OutputSlot()

    CachedOutput = OutputSlot() # second (private) output

    def __init__(self, *args, **kwargs):
        self._epsilon = 0.000001
        super(OpBrainMask, self).__init__(*args, **kwargs)
        self._cache = OpCompressedCache(parent=self )
        self._cache.name = "OpBrainMaskCache"
        self._cache.Input.connect(self.Output) 
        self.CachedOutput.connect(self._cache.Output)

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        tagged_shape = self.Input.meta.getTaggedShape()
        tagged_shape['t'] = 1
        tagged_shape['c'] = 1
        blockshape = map(lambda k: tagged_shape[k],
                         ''.join(tagged_shape.keys()))
        self._cache.BlockShape.setValue(tuple(blockshape))
        self.Output.meta.shape = tuple(tagged_shape.values())

    def execute(self, slot, subindex, roi, result):
        """
        computes brain mask for entire volume
        """
        print 'Brain mask'
        print roi
        raw_data = self.Input[...].wait()
        print raw_data.shape
        bool_mask = np.ma.masked_less_equal(raw_data[0,...,0],
                                            self._epsilon).mask
        result = np.zeros(bool_mask.shape, dtype=np.uint32)
        result[~bool_mask] = 1.0

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.Input:
            self.Output.setDirty(roi)
