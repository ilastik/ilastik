from lazyflow.graph import Operator, InputSlot, OutputSlot
import numpy
import vigra
import opGridCreator
from ilastik.utility import MultiLaneOperatorABC, OperatorSubView
from lazyflow.request import RequestLock

def make_grid(shape, patch, grid, offset):
    """Make a grid.

    Parameters
    ----------
    shape: tuple (x dim, y dim)
    patch: tuple (x size, y size)
    grid; tuple(x grid size, y grid size)
    offset: tuple (x offset, y offset)

    example:
    >>> make_grid(shape=(100, 100), patch=(5, 5), grid=(50, 50), offset=(11, 11))

    """
    arr = numpy.zeros(shape, dtype=numpy.uint8)

    xdim, ydim = shape
    xstart, ystart = offset
    xsize, ysize = patch
    xgrid, ygrid = grid

    xmult = xgrid // xsize
    ymult = ygrid // ysize

    xstop = xstart + xsize * xmult + 1
    ystop = ystart + ysize * ymult + 1

    # insert horizontal grid lines
    for x in range(xstart, xstop, xsize):
        arr[x, ystart:ystop] = 1
    # insert vertical grid lines
    for y in range(ystart, ystop, ysize):
        arr[xstart:xstop, y] = 1

    return arr


class OpGridCreator(Operator):
    """Creates list of patches from all filter responses."""
    PatchWidth = InputSlot()    # width of patch in pixel
    PatchHeight = InputSlot()   # height of patch in pixel
    GridStartVertical = InputSlot()    # Vertical - start of patch grid in pixel
    GridStartHorizontal = InputSlot()    # Horizontal - start of patch grid in pixel
    GridWidth = InputSlot()     # width of patch grid in pixel
    GridHeight = InputSlot()    # height of patch grid in pixel
    ImageWidth = InputSlot()    # width of raw image
    ImageHeight = InputSlot()    # height of raw image

    Output = OutputSlot()   # number of patches in x/y-direction

    def __init__(self, *args, **kwargs):
        super(OpGridCreator, self).__init__(*args, **kwargs)
        self.gridArray = None
        self.lock = RequestLock()

    def setupOutputs(self):
        self.Output.meta.shape = (self.ImageWidth.value, self.ImageHeight.value)

        # the viewer uses a different coordinate system
        self.Output.meta.axistags = vigra.defaultAxistags('yx')
        self.Output.meta.dtype = numpy.uint8


    def execute(self, slot, subindex, roi, result):
        """create grid"""
        try:
            self.lock.acquire()
            if self.gridArray is None:
                shape = (self.ImageHeight.value, self.ImageWidth.value)
                patch = (self.PatchHeight.value, self.PatchWidth.value)
                offset = (self.GridStartVertical.value, self.GridStartHorizontal.value)
                grid = (self.GridHeight.value, self.GridWidth.value)
                self.gridArray = make_grid(shape, patch, grid, offset)
            return self.gridArray[roi.toSlice()]
        finally:
            self.lock.release()


    def propagateDirty(self, slot, subindex, roi):
        try:
            self.lock.acquire()
            self.gridArray = None
            self.Output.setDirty(slice(None))
        finally:
            self.lock.release()
