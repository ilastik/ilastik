from functools import partial
import numpy
import vigra
from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.rtype import SubRegion
from lazyflow.operators import OpArrayPiper, OpMultiArraySlicer2

class TestOpMultiArraySlicer2(object):

    def setUp(self):
        graph = Graph()
        self.graph = graph
        # Data is tagged by channel
        data = numpy.indices((10,10,10,3))[3]
        data = data.view(vigra.VigraArray)
        data.axistags = vigra.defaultAxistags('xyzc')
        
        self.opProvider = OpArrayPiper(graph=graph)
        self.opProvider.Input.setValue(data)
        
        self.opSlicer = OpMultiArraySlicer2(graph=graph)
        self.opSlicer.AxisFlag.setValue('c')
        self.opSlicer.Input.connect(self.opProvider.Output)

    def testBasic(self):
        opSlicer = self.opSlicer
        assert len(opSlicer.Slices) == 3
        for i, slot in enumerate(opSlicer.Slices):
            assert slot.meta.shape == (10,10,10,1)
            assert (slot[...].wait() == i).all()

    def testBasicWithObjectDtype(self):
        """
        Make sure the slicer works even if dtype is 'object'
        """
        class SpecialNumber(object):
            def __init__(self, x):
                self.n = x
        
        data = numpy.ndarray(shape=(2,3), dtype=object)
        data = data.view(vigra.VigraArray)
        data.axistags = vigra.defaultAxistags('tc')
        for i in range(2):
            for j in range(3):
                data[i,j] = SpecialNumber(i*j)
        
        graph = Graph()
        opSlicer = OpMultiArraySlicer2(graph=graph)
        opSlicer.AxisFlag.setValue('t')
        opSlicer.Input.setValue( data )
        assert len(opSlicer.Slices) == 2
        assert opSlicer.Input.meta.dtype == object
        assert opSlicer.Slices[0].meta.dtype == object
        
        for i, slot in enumerate( opSlicer.Slices ):
            a = slot[:].wait()
            assert a.shape == (1,3)
            for j in range(3):
                val = a[0,j]
                assert type(val) == SpecialNumber
                assert val.n == i*j

    def testDirty(self):
        opSlicer = self.opSlicer

        dirtyRois = {}
        def handleDirty(i, slot, roi):
            assert opSlicer.Slices[i] == slot
            dirtyRois[i] = roi
        
        for i, slot in enumerate(opSlicer.Slices):
            slot.notifyDirty( partial(handleDirty, i) )
        
        dirtyInputRoi = SubRegion(slot=opSlicer.Input, start=[4,3,2,1], stop=[6,5,4,3])
        opSlicer.Input.setDirty(dirtyInputRoi)
        assert len(dirtyRois) == 2
        assert dirtyRois[1].start == [4,3,2,0]
        assert dirtyRois[1].stop == [6,5,4,1]
        assert dirtyRois[2].start == [4,3,2,0]
        assert dirtyRois[2].stop == [6,5,4,1]

        # Reset
        dirtyRois = {}
        opSlicer.AxisFlag.setValue('x')
        assert len(dirtyRois) == 3
        assert dirtyRois[0].start == [0,0,0,0]
        assert dirtyRois[0].stop == [10,10,10,3]
        assert dirtyRois[1].start == [0,0,0,0]
        assert dirtyRois[1].stop == [10,10,10,3]
        assert dirtyRois[2].start == [0,0,0,0]
        assert dirtyRois[2].stop == [10,10,10,3]
        

    def testReshape(self):
        opSlicer = self.opSlicer

        dirtyRois = {}
        def handleDirty(i, slot, roi):
            assert opSlicer.Slices[i] == slot
            dirtyRois[i] = roi
        
        for i, slot in enumerate(opSlicer.Slices):
            slot.notifyDirty( partial(handleDirty, i) )

        # Initial data has 3 channels with values 0,1,2
        # Simulate removing the middle one: Now data has two channels with values 0,2
        data = numpy.indices((10,10,10,2))[3]
        data = data * 2
        data = data.view(vigra.VigraArray)
        data.axistags = vigra.defaultAxistags('xyzc')
        
        # Connect a new data provider
        opNewProvider = OpArrayPiper(graph=opSlicer.graph)
        opNewProvider.Input.setValue(data)
        opSlicer.Input.connect(opNewProvider.Output)
        
        assert len(opSlicer.Slices) == 2
        for i, slot in enumerate(opSlicer.Slices):
            assert slot.meta.shape == (10,10,10,1)
            assert (slot[...].wait() == i*2).all()
        
        assert len(dirtyRois) == 2
        assert dirtyRois[0].start == [0,0,0,0]
        assert dirtyRois[0].stop == [10,10,10,1]
        assert dirtyRois[1].start == [0,0,0,0]
        assert dirtyRois[1].stop == [10,10,10,1]

    def testSelectedSlices(self):
        """
        Test the ability to select a specific set of slices from the input image (instead of selecting all of them).
        """
        opSlicer = self.opSlicer
        assert len(opSlicer.Slices) == 3
        
        opSlicer.SliceIndexes.setValue([1,2])
        assert len(opSlicer.Slices) == 2
        
        for i, slot in enumerate(opSlicer.Slices):
            assert slot.meta.shape == (10,10,10,1)
            assert (slot[...].wait() == i+1).all()

    def testWrapped(self):
        """
        Make sure the MulitArraySlicer2 functions as expected, even when wrapped with an OperatorWrapper.
        """
        # Note: This test creates its own opSlicer and opProvider.
        #       ( Doesn't use the ones created in self.setUp() )
        # Data is tagged by channel
        opProvider = OperatorWrapper( OpArrayPiper, graph=self.graph )
        opSlicer = OperatorWrapper( OpMultiArraySlicer2, graph=self.graph )

        opSlicer.AxisFlag.setValue('c')
        opSlicer.Input.connect(opProvider.Output)

        data = numpy.indices((10,10,10,3))[3]
        data = data.view(vigra.VigraArray)
        data.axistags = vigra.defaultAxistags('xyzc')
        opProvider.Input.resize(2)
        opProvider.Input[0].setValue(data)
        opProvider.Input[1].setValue(2*data)

        assert len(opSlicer.Slices) == len(opProvider.Output)
        assert len(opSlicer.Slices[0]) == 3
        assert len(opSlicer.Slices[1]) == 3

        for i, slot in enumerate(opSlicer.Slices[0]):
            assert slot.meta.shape == (10,10,10,1)
            assert (slot[...].wait() == i).all()

        for i, slot in enumerate(opSlicer.Slices[1]):
            assert slot.meta.shape == (10,10,10,1)
            assert (slot[...].wait() == 2*i).all()
        
        opSlicer.SliceIndexes.setValue([1,2])
        assert len(opSlicer.Slices[0]) == 2
        assert len(opSlicer.Slices[1]) == 2
        
        for i, slot in enumerate(opSlicer.Slices[0]):
            assert slot.meta.shape == (10,10,10,1)
            assert (slot[...].wait() == i+1).all()

        for i, slot in enumerate(opSlicer.Slices[1]):
            assert slot.meta.shape == (10,10,10,1)
            assert (slot[...].wait() == 2*(i+1)).all()

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)

    if not ret: sys.exit(1)
