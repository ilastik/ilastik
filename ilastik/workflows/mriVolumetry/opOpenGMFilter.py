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

    def setupOutputs(self):
        super(OpOpenGMFilter, self).setupOutputs()
        self.Output.meta.dtype = np.float32

    def propagateDirty(self, slot, subindex, roi):
        # TODO what are the actual conditions here?
        self.Output.setDirty(slice(None)) 

    def execute(self, slot, subindex, roi, result):
        # FIXME don't recompute this every time
        # compute mask from raw input channel
        raw_data = self.op.RawInput.get(slice(None)).wait()
        bool_mask = np.ma.masked_less_equal(raw_data[0,...,0],
                                            self._epsilon).mask
        self._mask = np.zeros(raw_data.shape, dtype=np.uint32)
        self._mask[~bool_mask] = 1.0

        logger.debug("Smoothing roi {}".format(roi))

        conf = self.Configuration.value
        if 'sigma' not in conf:
            raise self.ConfigurationError(
                "expected key 'sigma' in configuration")
        sigma = conf['sigma']

        if 'unaries' not in conf:
            raise self.ConfigurationError(
                "expected key 'unaries' in configuration")
        unaries = conf['unaries']

        result[...] = self.Input.get(roi).wait().astype(
            self.Output.meta.dtype)
        self._opengmFilter(result, sigma, unaries)

    @staticmethod
    def _opengmFilter(vol, filter_size, unaries_scale):
        print "TODO implement me"
        print unaries, filter_size
        return vol
        
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


