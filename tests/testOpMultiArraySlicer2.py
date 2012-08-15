from functools import partial
import numpy
import vigra
from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.rtype import SubRegion
from lazyflow.operators import OpArrayPiper, OpMultiArraySlicer2

class TestOpMultiArraySlicer2(object):

    def setUp(self):
        graph = Graph()
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

    def testReshape(self):
        opProvider = self.opProvider        
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

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)

