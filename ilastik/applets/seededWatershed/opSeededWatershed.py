import numpy

from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.roi import determineBlockShape
from lazyflow.operators import OpArrayCache, OpMaskedWatershed

from ilastik.applets.labeling import OpLabelingSingleLane

class OpSeededWatershed(OpLabelingSingleLane):
    Mask = InputSlot()
    FreezeCache = InputSlot()
    CachedWatershed = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpSeededWatershed, self ).__init__(*args, **kwargs)
        self._opMaskedWatershed = OpMaskedWatershed( parent=self )
        self._opMaskedWatershed.Input.connect( self.InputImage )
        self._opMaskedWatershed.Mask.connect( self.Mask )
        self._opMaskedWatershed.Seeds.connect( self.opLabelArray.Output ) # From superclass member

        self.FreezeCache.setValue(True)
        self._opCache = OpArrayCache( parent=self )
        self._opCache.name = "watershed-cache"
        self._opCache.fixAtCurrent.connect( self.FreezeCache )
        self._opCache.Input.connect( self._opMaskedWatershed.Output )
        
        self.CachedWatershed.connect( self._opCache.Output )
        
    def setupOutputs(self):
        assert self.InputImage.meta.getAxisKeys() == list('txyzc'),\
            "This applet assumes that all slots are 5D txyzc"
        self._opCache.blockShape.setValue( self.InputImage.meta.shape )
        super( OpSeededWatershed, self ).setupOutputs()

    def propagateDirty(self, inputSlot, subindex, roi):
        super( OpSeededWatershed, self ).propagateDirty(inputSlot, subindex, roi)
        self.CachedWatershed.setDirty()

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here"
    