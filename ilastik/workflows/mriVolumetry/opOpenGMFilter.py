import numpy as np
import vigra

from lazyflow.operator import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpReorderAxes, OpCompressedCache

from lazyflow.rtype import SubRegion

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

    _Output = OutputSlot()
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpOpenGMFilter, self).__init__(*args, **kwargs)

        self._cache = OpCompressedCache( parent=self )
        self._cache.Input.connect(self._Output)
        self.Output.connect(self._cache.Output)

        self.opMask = OpBrainMask(parent=self)
        self.opMask.Input.connect(self.RawInput)

    def setupOutputs(self):
        self._Output.meta.assignFrom(self.Input.meta)
        self._Output.meta.dtype = np.uint32

        ts = self.Input.meta.getTaggedShape()
        ts['c'] = 1
        self._Output.meta.shape = tuple(ts.values())
        ts['t'] = 1
        self._cache.BlockShape.setValue(tuple(ts.values()))

    def propagateDirty(self, slot, subindex, roi):
        # TODO what are the actual conditions here?
        if slot in [self.Configuration, self.Input, self.RawInput]:
            self._Output.setDirty(slice(None))

    def execute(self, slot, subindex, roi, result):
        logger.debug("Opengm on roi {}".format(roi))
        if not have_opengm:
            raise RuntimeError("Cannot run OpOpenGMFilter without opengm!")

        conf = self.Configuration.value
        if 'sigma' not in conf:
            raise ValueError(
                "expected key 'sigma' in configuration")
        sigma = conf['sigma']

        if 'unaries' not in conf:
            raise ValueError(
                "expected key 'unaries' in configuration")
        unaries = conf['unaries']

        # compute mask from raw input channel
        mask = self.opMask.Output.get(roi).wait()
        tags = self.opMask.Output.meta.axistags
        mask = vigra.taggedView(mask, axistags=tags).withAxes(*'xyz')

        # assuming channel is last axis
        start = roi.start
        stop = tuple(roi.stop[:4]) + (self.Input.meta.shape[4],)
        newroi = SubRegion(self.Input, start=start, stop=stop)

        # new view on result
        tags = self._Output.meta.axistags
        resview = vigra.taggedView(result, axistags=tags)
        resview = resview.withAxes(*'xyz')

        pred = self.Input.get(newroi).wait().astype(np.float32)
        self._opengmFilter(pred, mask, sigma, unaries, resview)

    @staticmethod
    def _opengmFilter(vol, mask, sigma, unaries, out, eps=1e-6):
        # make uncertainty edge image
        pfiltered = np.empty(vol[0].shape, dtype=vol.dtype)
        for c in xrange(vol.shape[-1]):
            vigra.gaussianSmoothing(vol[0, ..., c],
                                    sigma,
                                    out=pfiltered[..., c])
        print(type(pfiltered))
        pmap = np.sort(pfiltered, axis=-1)
        uncertainties = pmap[..., -1] - pmap[..., -2]
        # set starting point
        init_data = np.argmax(vol[0], axis=-1).astype(np.uint32)
        init_data = opengm.getStartingPointMasked(init_data, mask)
        unaries = -unaries * np.log(vol[0] + eps)
        gm = opengm.pottsModel3dMasked(unaries=unaries,
                                       regularizer=uncertainties,
                                       mask=mask)
        try:
            inf = opengm.inference.FastPd(gm)
        except AttributeError:
            logger.info('Using AlphaExpansion')
            inf = opengm.inference.AlphaExpansion(gm)
        else:
            logger.info('Using FastPD')
            
        inf.setStartingPoint(init_data)
        inf.infer(inf.verboseVisitor())
        out[:] = opengm.makeMaskedState(mask, inf.arg(), labelIdx=0)+1
        # +1 to adjust the indices
        out[mask==0] = 0


class OpBrainMask(Operator):
    """
    This operator computes a mask image based on the assumption that in the 
    MRI input data all values outside of the skull were set to 0 during 
    pre-processing
    """

    Input = InputSlot()  # the raw data
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        self._epsilon = 0.000001
        super(OpBrainMask, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = np.uint32

    def execute(self, slot, subindex, roi, result):
        """
        computes brain mask for entire volume
        """
        raw_data = self.Input.get(roi).wait()
        result[:] = raw_data > self._epsilon

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.Input:
            self.Output.setDirty(roi)
