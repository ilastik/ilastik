from unittest import TestCase
import vigra,numpy
from lazyflow.graph import Graph,Operator,InputSlot,OutputSlot
from lazyflow.operators import OpArrayPiper
from lazyflow.helpers import generateRandomRoi

import lazyflow.roi

class OpRoiTest(Operator):

    inputSlots = [InputSlot("input")]
    outputSlots = [OutputSlot("output")]

    def setupOutputs(self):

        self.outputs["output"].meta.dtype = self.inputs["input"].meta.dtype
        self.outputs["output"].meta.shape = self.inputs["input"].meta.shape
        self.outputs["output"].meta.axistags = self.inputs["input"].meta.axistags

    def execute(self, slot, subindex, roi, result):

        tmpRes = self.inputs["input"](start=roi.start,stop=roi.stop).wait()
        result[:] = tmpRes
        return result

    def propagateDirty(self, inputSlot, roi):
        self.output.setDirty(roi)

class TestRoiInterdace(TestCase):

    def setUp(self):
        self.testVol = vigra.VigraArray((200,200,200))
        self.testVol[:] = numpy.random.rand(200,200,200)
        self.graph = Graph()
        self.op = OpArrayPiper(self.graph)
        self.op.inputs["Input"].setValue(self.testVol)
        self.roiOp = OpRoiTest(self.graph)
        self.roiOp.inputs["input"].setValue(self.testVol)

    def test_roi(self):

        for i in range(20):
            roi = generateRandomRoi((200,200,200))
            result=self.op.outputs["Output"](start=roi[0], stop=roi[1]).wait()

    def test_RoiOp(self):

        for i in range(20):
            roi = generateRandomRoi((200,200,200))
            result=self.roiOp.outputs["output"](start=roi[0], stop=roi[1]).wait()

class TestRoiUtilities(TestCase):

    def test_expandSlicing(self):
        shape = (2,4,6,8,10)
        
        # Single index
        assert lazyflow.roi.expandSlicing(1, shape) == (1,) + 4*(slice(None),)

        # Single slice
        assert lazyflow.roi.expandSlicing(slice(None), shape) == 5*(slice(None),)
        assert lazyflow.roi.expandSlicing(slice(0,1), shape) == (slice(0,1),) + 4*(slice(None),)

        # As list
        assert lazyflow.roi.expandSlicing([slice(0,1)], shape) == (slice(0,1),) + 4*(slice(None),)
        assert lazyflow.roi.expandSlicing([slice(0,1), 3, 4], shape) == (slice(0,1),3, 4) + 2*(slice(None),)

        # As tuple
        assert lazyflow.roi.expandSlicing((slice(0,1),), shape) == (slice(0,1),) + 4*(slice(None),)
        assert lazyflow.roi.expandSlicing((slice(0,1), 3, 4), shape) == (slice(0,1),3, 4) + 2*(slice(None),)

        # Single Ellipsis
        assert lazyflow.roi.expandSlicing(Ellipsis, shape) == 5*(slice(None),)

        # Tuple/list with Ellipsis
        assert lazyflow.roi.expandSlicing((0, 1, Ellipsis, 9), shape) == (0, 1, slice(None), slice(None), 9)
        assert lazyflow.roi.expandSlicing([0, 1, Ellipsis, 9], shape) == (0, 1, slice(None), slice(None), 9)
    
        # Special cases for empty shapes
        emptyShape = ()
        assert lazyflow.roi.expandSlicing(Ellipsis, emptyShape ) == emptyShape
        assert lazyflow.roi.expandSlicing(slice(None), emptyShape ) == emptyShape
    
    def test_sliceToRoi(self):
        from lazyflow.roi import TinyVector
        shape = (2,4,6,8,10)
        
        # -- With extendSingleton=True

        # Single index
        assert lazyflow.roi.sliceToRoi(1, shape) == (TinyVector((1,0,0,0,0)), TinyVector((2,4,6,8,10)))

        # Single slice
        assert lazyflow.roi.sliceToRoi(slice(None), shape) == (TinyVector((0,0,0,0,0)), TinyVector((2,4,6,8,10)))
        assert lazyflow.roi.sliceToRoi(slice(0,1), shape) == (TinyVector((0,0,0,0,0)), TinyVector((1,4,6,8,10)))

        # As list
        assert lazyflow.roi.sliceToRoi([slice(0,1)], shape) == (TinyVector((0,0,0,0,0)), TinyVector((1,4,6,8,10)))
        assert lazyflow.roi.sliceToRoi([slice(0,1), 3, 4], shape) == (TinyVector((0,3,4,0,0)), TinyVector((1,4,5,8,10)))

        # As tuple
        assert lazyflow.roi.sliceToRoi((slice(0,1),), shape) == (TinyVector((0,0,0,0,0)), TinyVector((1,4,6,8,10)))
        assert lazyflow.roi.sliceToRoi((slice(0,1), 3, 4), shape) == (TinyVector((0,3,4,0,0)), TinyVector((1,4,5,8,10)))

        # Single Ellipsis
        assert lazyflow.roi.sliceToRoi(Ellipsis, shape) == (TinyVector((0,0,0,0,0)), TinyVector((2,4,6,8,10)))

        # Tuple/list with Ellipsis
        assert lazyflow.roi.sliceToRoi((0, 1, Ellipsis, 9), shape) == (TinyVector((0,1,0,0,9)), TinyVector((1,2,6,8,10)))
        assert lazyflow.roi.sliceToRoi([0, 1, Ellipsis, 9], shape) == (TinyVector((0,1,0,0,9)), TinyVector((1,2,6,8,10)))

        # -- With extendSingleton=False (for some of these, it makes no difference)

        # Single index
        assert lazyflow.roi.sliceToRoi(1, shape, extendSingleton=False) == (TinyVector((1,0,0,0,0)), TinyVector((1,4,6,8,10)))

        # Single slice
        assert lazyflow.roi.sliceToRoi(slice(None), shape, extendSingleton=False) == (TinyVector((0,0,0,0,0)), TinyVector((2,4,6,8,10)))
        assert lazyflow.roi.sliceToRoi(slice(0,1), shape, extendSingleton=False) == (TinyVector((0,0,0,0,0)), TinyVector((1,4,6,8,10)))

        # As list
        assert lazyflow.roi.sliceToRoi([slice(0,1)], shape, extendSingleton=False) == (TinyVector((0,0,0,0,0)), TinyVector((1,4,6,8,10)))
        assert lazyflow.roi.sliceToRoi([slice(0,1), 3, 4], shape, extendSingleton=False) == (TinyVector((0,3,4,0,0)), TinyVector((1,3,4,8,10)))

        # As tuple
        assert lazyflow.roi.sliceToRoi((slice(0,1),), shape, extendSingleton=False) == (TinyVector((0,0,0,0,0)), TinyVector((1,4,6,8,10)))
        assert lazyflow.roi.sliceToRoi((slice(0,1), 3, 4), shape, extendSingleton=False) == (TinyVector((0,3,4,0,0)), TinyVector((1,3,4,8,10)))

        # Single Ellipsis
        assert lazyflow.roi.sliceToRoi(Ellipsis, shape, extendSingleton=False) == (TinyVector((0,0,0,0,0)), TinyVector((2,4,6,8,10)))

        # Tuple/list with Ellipsis
        assert lazyflow.roi.sliceToRoi((0, 1, Ellipsis, 9), shape, extendSingleton=False) == (TinyVector((0,1,0,0,9)), TinyVector((0,1,6,8,9)))
        assert lazyflow.roi.sliceToRoi([0, 1, Ellipsis, 9], shape, extendSingleton=False) == (TinyVector((0,1,0,0,9)), TinyVector((0,1,6,8,9)))


    def test_roiToSlice(self):
        from lazyflow.roi import TinyVector
        shape = (2,4,6,8,10)
        
        roi = (TinyVector((1,2,3,4,5)), TinyVector(shape))
        assert lazyflow.roi.roiToSlice(roi[0], roi[1]) == (slice(1,2), slice(2,4), slice(3,6), slice(4,8), slice(5,10))
        
if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})





















