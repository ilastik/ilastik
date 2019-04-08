import logging
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility import timeLogged

logger = logging.getLogger(__name__)


class OpRelabelConsecutive(Operator):
    Input = InputSlot()
    StartLabel = InputSlot(value=0)
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

    @timeLogged(logger)
    def execute(self, slot, subindex, roi, result):
        self.Input.get(roi).writeInto(result).wait()
        result = vigra.taggedView(result, self.Output.meta.axistags).withAxes("zyx")
        _res, _max_label, _labelmap_dict = vigra.analysis.relabelConsecutive(
            result, self.StartLabel.value, keep_zeros=False, out=result
        )

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(roi.start, roi.stop)
