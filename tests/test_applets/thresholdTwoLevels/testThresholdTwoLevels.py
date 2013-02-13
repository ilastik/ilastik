import numpy
from lazyflow.graph import Graph
from ilastik.applets.thresholdTwoLevels.opThresholdTwoLevels import OpThresholdTwoLevels

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()


class TestThresholdTwoLevels(object):
    def setUp(self):
        self.nx = 20
        self.ny = 20
        self.nz = 20
        #self.data = numpy.zeros((self.nx, self.ny, self.nz))
        #cluster of 4 points
        self.cluster1 = numpy.zeros((self.nx, self.ny, self.nz))
        self.cluster1[1:3, 1:3, 1]=0.9
        #cluster of 18 points
        self.cluster2 = numpy.zeros((self.nx, self.ny, self.nz))
        self.cluster2[5:8, 5:8, 5:8]=0.7
        #cluster of lower probability
        self.cluster3 = numpy.zeros((self.nx, self.ny, self.nz))
        self.cluster3[4:7, 11:14, 9:11]=0.3
        #cluster of 64 points
        self.cluster4 = numpy.zeros((self.nx, self.ny, self.nz))
        self.cluster4[2:10, 2:10, 15]=0.9
        
        self.data = self.cluster1 + self.cluster2 + self.cluster3 + self.cluster4
        
        self.minSize = 5 #first cluster doesn't pass this
        self.maxSize = 30 #fourth cluster doesn't pass this
        self.highThreshold = 0.65 #third cluster doesn't pass
        self.lowThreshold = 0.1
        
        self.sigma = (0.3, 0.3, 0.3)
        
    def testStuff(self):
        g = Graph()
        oper = OpThresholdTwoLevels(graph = g)
        oper.InputImage.setValue(self.data)
        oper.MinSize.setValue(self.minSize)
        oper.MaxSize.setValue(self.maxSize)
        oper.HighThreshold.setValue(self.highThreshold)
        oper.LowThreshold.setValue(self.lowThreshold)
        oper.SmootherSigma.setValue(self.sigma)
        
        output = oper.Output[:].wait()
        cluster1 = numpy.logical_and(output, self.cluster1)
        assert numpy.any(cluster1!=0)==False
        cluster2 = numpy.logical_and(output, self.cluster2)
        assert numpy.any(cluster2!=0)==True
        cluster3 = numpy.logical_and(output, self.cluster3)
        assert numpy.any(cluster3!=0)==False
        cluster4 = numpy.logical_and(output, self.cluster4)
        assert numpy.any(cluster4!=0)==False
        
        
if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})