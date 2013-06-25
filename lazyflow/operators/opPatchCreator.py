from lazyflow.graph import Operator, InputSlot, OutputSlot, Graph
from lazyflow.request import RequestLock
import numpy
import vigra
import opGridCreator


def _add_channel(img):
    # FIXME: use axistags
    if img.ndim == 2:
        img = img.reshape(img.shape + (1,))
    if img.ndim != 3:
        raise Exception('wrong number of dimensions: {}'.format(img.ndim))
    return img


def patchify(img, patchShape, overlap, gridInit, gridShape):
    """Break image into overlapping patches.

    :param img: 2d or 3d (2d + channels) numpy array
    :param patchShape = (x, y) = (height, width)
    :param pWidth: size of patch edge in Y-direction
    :param pHeight: size of patch edge in X-direction
    :param overlap: overlap (x, y) in pixels

    returns:
        (patches, positions)

    """
    img = _add_channel(img)
    height, width, channels = img.shape

    pHeight, pWidth = patchShape
    gStartVertical, gStartHorizontal = gridInit
    gHeight, gWidth = gridShape

    # check parameter settings
    if width < pWidth:
        raise Exception('patch width too large')
    if height < pHeight:
        raise Exception('patch height too large')
    if pWidth < 1:
        raise Exception('invalid patch width')
    if pHeight < 1:
        raise Exception('invalid patch height')
    if gStartVertical < 0:
        raise Exception('invalid grid vertical start')
    if gStartVertical > (height - pHeight):
        raise Exception('invalid grid vertical start')
    if gStartHorizontal < 0:
        raise Exception('invalid grid horizontal start')
    if gStartHorizontal > (width - pWidth):
        raise Exception('invalid grid horizontal start')
    if gWidth < pWidth:
        raise Exception('invalid grid width')
    if (gStartHorizontal + gWidth) > width:
        raise Exception('invalid grid width')
    if gHeight < pHeight:
        raise Exception('invalid grid height')
    if (gStartVertical + gHeight) > height:
        raise Exception('invalid grid height')

    xstop = gStartVertical + gHeight - pHeight + 1
    ystop = gStartHorizontal + gWidth - pWidth + 1

    overlapVertical, overlapHorizontal = overlap

    skipVertical = pHeight - overlapVertical
    skipHorizontal = pWidth - overlapHorizontal

    patches = []
    posns = []

    for x in range(gStartVertical, int(xstop), int(skipVertical)):
        for y in range(gStartHorizontal, int(ystop), int(skipHorizontal)):
            patch = img[x : x + pHeight, y : y + pWidth]
            patches.append(patch.reshape(1, pHeight, pWidth, -1))
            posns.append((x, y))
    return numpy.vstack(patches), numpy.vstack(posns)


class OpPatchCreator(Operator):
    """Patchifies an image."""
    PatchWidth = InputSlot()    # width of patch in pixel
    PatchHeight = InputSlot()   # height of patch in pixel
    PatchOverlapVertical = InputSlot()    # vertical overlap between patches in pixels
    PatchOverlapHorizontal = InputSlot()    # horizontal overlap between patches in pixels
    GridStartVertical = InputSlot()    # X - start of patch grid in pixel
    GridStartHorizontal = InputSlot()    # Y - start of patch grid in pixel
    GridWidth = InputSlot()     # width of patch grid in pixel
    GridHeight = InputSlot()    # height of patch grid in pixel

    RawInput = InputSlot()       # raw input image
    FilteredInput = InputSlot()  # filtered input image

    Patches = OutputSlot()      # output patches
    Positions = OutputSlot()    # output positions of patches
    NumPatches = OutputSlot()   # number of patches in x/y-direction

    GridOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpPatchCreator, self).__init__(*args, **kwargs)
        self.patches = None
        self.posns = None
        self.lock = RequestLock()

        self.opGrid = opGridCreator.OpGridCreator(graph=Graph())
        self.GridOutput.connect(self.opGrid.Output)

        self.opGrid.GridStartVertical.connect(self.GridStartVertical)
        self.opGrid.GridStartHorizontal.connect(self.GridStartHorizontal)
        self.opGrid.GridWidth.connect(self.GridWidth)
        self.opGrid.GridHeight.connect(self.GridHeight)
        self.opGrid.PatchWidth.connect(self.PatchWidth)
        self.opGrid.PatchHeight.connect(self.PatchHeight)


    def setupOutputs(self):
        skipVertical = self.PatchHeight.value - self.PatchOverlapVertical.value
        skipHorizontal = self.PatchWidth.value - self.PatchOverlapHorizontal.value

        if skipVertical <= 0 or skipHorizontal <= 0:
            return

        # total number of patches in x-direction
        numPatchesVertical = (self.GridHeight.value - self.PatchHeight.value) // skipVertical + 1

        # total number of patches in y-direction
        numPatchesHorizontal = (self.GridWidth.value - self.PatchWidth.value) // skipHorizontal + 1

        # total number of patches on the image
        totNumPatches = numPatchesVertical * numPatchesHorizontal

        # number of pixel per patch
        numPixelsPerPatch = self.PatchWidth.value * self.PatchHeight.value

        # set shape of output data
        self.NumPatches.meta.shape = (2,)
        self.NumPatches.meta.dtype = numpy.uint32
        self.NumPatches.meta.axistags = None

        self.Positions.meta.shape = (totNumPatches, 2)
        self.Positions.meta.dtype = numpy.uint32
        self.Positions.meta.axistags = None

        n_channels = self.FilteredInput.meta.shape[2]

        self.Patches.meta.shape = (totNumPatches, self.PatchWidth.value,
                                   self.PatchHeight.value,
                                   n_channels)


        self.Patches.meta.dtype = numpy.float32
        self.Patches.meta.axistags = None

        # set input slots for operator opGridCreator
        self.opGrid.ImageHeight.setValue(self.RawInput.meta.shape[1])
        self.opGrid.ImageWidth.setValue(self.RawInput.meta.shape[0])


    def execute(self, slot, subindex, roi, result):
        """Create patches from filtered input image slot.

        shape of output patches [number of patches, number of pixels
        per patch, number of filter responses = channels]

        """
        skipVertical = self.PatchHeight.value - self.PatchOverlapVertical.value
        skipHorizontal = self.PatchWidth.value - self.PatchOverlapHorizontal.value

        if slot is self.NumPatches:
            pWidth = self.PatchWidth.value
            pHeight = self.PatchHeight.value
            gWidth = self.GridWidth.value
            gHeight = self.GridHeight.value

            numPatchesVertical = int((gHeight - pHeight) / skipVertical) + 1
            numPatchesHorizontal = int((gWidth - pWidth) / skipHorizontal) + 1
            numpatches = numpy.zeros((2,))
            numpatches[:] = (numPatchesVertical, numPatchesHorizontal)
            return numpatches

        try:
            self.lock.acquire()
            if self.patches is None:
                img = self.FilteredInput[:].wait()
                pWidth = self.PatchWidth.value
                pHeight = self.PatchHeight.value
                overlapVertical = self.PatchOverlapVertical.value
                overlapHorizontal = self.PatchOverlapHorizontal.value
                gStartVertical = self.GridStartVertical.value
                gStartHorizontal = self.GridStartHorizontal.value
                gWidth = self.GridWidth.value
                gHeight = self.GridHeight.value

                img = self.FilteredInput[:].wait()
                img.axistags = self.FilteredInput.meta.axistags
                img = numpy.asarray(img.transposeToNumpyOrder())

                self.patches, self.posns = patchify(
                    img,
                    (pHeight, pWidth),
                    (overlapVertical, overlapHorizontal),
                    (gStartVertical, gStartHorizontal),
                    (gHeight, gWidth)
                )

            if slot is self.Patches:
                return self.patches
            elif slot is self.Positions:
                return self.posns
        finally:
            self.lock.release()


    def propagateDirty(self, slot, subindex, roi):
        try:
            self.lock.acquire()
            self.patches = None
            self.posns = None
            roi = slice(None)
            self.Patches.setDirty(roi)
            self.Positions.setDirty(roi)
            self.NumPatches.setDirty(roi)
        finally:
            self.lock.release()


if __name__ == "__main__":
    from lazyflow.graph import Graph
    op = OpPatchCreator(graph=Graph())

    shape = (301,301)
    zeros = numpy.zeros(shape, dtype=numpy.float)
    ones = numpy.ones(shape, dtype=numpy.float)
    twos = 2*numpy.ones(shape, dtype=numpy.float)

    patchWidth = 16
    patchHeight = 16
    overlapVertical = 8
    overlapHorizontal = 8
    gridStartVertical = 6
    gridStartHorizontal = 6
    gridWidth = 288
    gridHeight = 288

    op.PatchWidth.setValue(patchWidth)
    op.PatchHeight.setValue(patchHeight)
    op.PatchOverlapVertical.setValue(overlapVertical)
    op.PatchOverlapHorizontal.setValue(overlapHorizontal)

    op.GridStartVertical.setValues(gridStartVertical)
    op.GridStartHorizontal.setValues(gridStartHorizontal)
    op.GridWidth.setValues(gridWidth)
    op.GridHeight.setValues(gridHeight)

    op.FilteredInput.resize(3)
    op.FilteredInput[0].setValue(zeros)
    op.FilteredInput[1].setValue(ones)
    opFilteredInput[2].setValue(twos)

    outPatches = op.Patches[1][:].wait()
    outPositions = op.Positions[1][:].wait()
