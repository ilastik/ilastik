from lazyflow.graph import InputSlot

from ilastik.applets.pixelClassification import OpPixelClassification


class OpVoxelSegmentation(OpPixelClassification):
    SlicBoundaries = InputSlot(level=1)
