import numpy
from lazyflow.graph import Graph
from lazyflow.operators import Op5ifyer
from ilastik.applets.thresholdTwoLevels.opThresholdTwoLevels import OpThresholdTwoLevels4d, OpThresholdTwoLevels, \
                                                                    OpThresholdOneLevel

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

import vigra

def generateData((nx, ny, nz, nc)):
  
    clusters = []
    
    #cluster of 4 points
    cluster1 = numpy.zeros((nx, ny, nz))
    cluster1[1:3, 1:3, 1]=0.9
    clusters.append(cluster1)
    
    #cluster of 18 points
    cluster2 = numpy.zeros((nx, ny, nz))
    cluster2[5:8, 5:8, 5:8]=0.7
    clusters.append(cluster2)
    
    #cluster of lower probability (18 points)
    cluster3 = numpy.zeros((nx, ny, nz))
    cluster3[4:7, 11:14, 9:11]=0.3
    clusters.append(cluster3)
    
    #cluster of 64 points
    cluster4 = numpy.zeros((nx, ny, nz))
    cluster4[2:10, 2:10, 15]=0.9
    clusters.append(cluster4)
    
    #dual cluster
    cluster5 = numpy.zeros((nx, ny, nz))
    cluster5[20:30, 20:30, 20] = 0.4 #bigger cluster of lower prob
    cluster5[25:30, 25:30, 20] = 0.95 #smaller core of high prob
    clusters.append(cluster5)
    
    return clusters

class TestThresholdOneLevel(object):
    def setUp(self):
        self.nx = 50
        self.ny = 50
        self.nz = 50
        self.nc = 3
        
        clusters = generateData((self.nx, self.ny, self.nz, self.nc))
        self.data = clusters[0] + clusters[1] + clusters[2] + clusters[3] + clusters[4]
        self.data = self.data.reshape(self.data.shape+(1,))
        self.data5d = self.data.reshape((1,)+self.data.shape)
        self.data = self.data.view(vigra.VigraArray)
        self.data.axistags = vigra.VigraArray.defaultAxistags('xyzc')
        self.data5d = self.data5d.view(vigra.VigraArray)
        self.data5d.axistags = vigra.VigraArray.defaultAxistags('txyzc')
        
        self.minSize = 0
        self.maxSize = 50
        
        self.sigma = { 'x' : 0.3, 'y' : 0.3, 'z' : 0.3 }
        self.data = vigra.filters.gaussianSmoothing(self.data.astype(numpy.float32), 0.3)
        
    def test(self):
        g = Graph()
        oper = OpThresholdOneLevel(graph=g)
        oper.MinSize.setValue(self.minSize)
        oper.MaxSize.setValue(self.maxSize)
        oper.Threshold.setValue(0.5)
        oper.InputImage.setValue(self.data)
        
        output = oper.Output[:].wait()
        
        clusters = generateData((self.nx, self.ny, self.nz, self.nc))
        
        cluster1 = numpy.logical_and(output, clusters[0])
        assert numpy.any(cluster1!=0)
                
        oper.MinSize.setValue(5)
        output = oper.Output[:].wait()
        cluster1 = numpy.logical_and(output, clusters[0])
        assert numpy.all(cluster1==0)
        
        cluster4 = numpy.logical_and(output.squeeze(), clusters[3])
        assert numpy.all(cluster4==0)
        
        cluster5 = numpy.logical_and(output.squeeze(), clusters[2])
        assert numpy.all(cluster5==0)
        oper.Threshold.setValue(0.2)
        output = oper.Output[:].wait()
        cluster5 = numpy.logical_and(output.squeeze(), clusters[2])
        assert numpy.any(cluster5!=0)
        
        oper5d = OpThresholdTwoLevels(graph=g)
        oper5d.InputImage.setValue(self.data5d)
        oper5d.MinSize.setValue(oper.MinSize.value)
        oper5d.MaxSize.setValue(oper.MaxSize.value)
        oper5d.SingleThreshold.setValue(oper.Threshold.value)
        oper5d.SmootherSigma.setValue(self.sigma)
        oper5d.Channel.setValue(0)
        oper5d.CurOperator.setValue(0)
        
        output5d = oper5d.Output[:].wait()
        
        tIndex= oper5d.Output.meta.axistags.index('t')
        slicing = 5*[slice(None, None, None)]
        slicing[tIndex]= slice(0, 1, None)
        #print out5d.axistags, output.shape.axistags
        assert numpy.all(output5d[slicing].squeeze()==output[:].squeeze())


class TestThresholdTwoLevels(object):
    def setUp(self):
        
        self.nx = 50
        self.ny = 50
        self.nz = 50
        self.nc = 3
        
        clusters = generateData((self.nx, self.ny, self.nz, self.nc))
        self.data = clusters[0] + clusters[1] + clusters[2] + clusters[3] + clusters[4]
        self.data = self.data.reshape(self.data.shape+(1,))
        self.data = self.data.view(vigra.VigraArray)
        self.data.axistags = vigra.VigraArray.defaultAxistags('xyzc')
        
        self.dataChannels = numpy.zeros((self.nx, self.ny, self.nz, self.nc))
        self.dataChannels[:, :, :, 2] = clusters[0] + clusters[1] + clusters[2] + clusters[3] + clusters[4]
        self.data5d = self.dataChannels.reshape((1,)+self.dataChannels.shape)
        self.dataChannels = self.dataChannels.view(vigra.VigraArray)
        self.dataChannels.axistags = vigra.VigraArray.defaultAxistags('xyzc')
        
        self.dataRandom = numpy.random.rand(self.nx, self.ny, self.nz)
        self.dataRandom = self.dataRandom.reshape(self.dataRandom.shape+(1,))
        self.dataRandom = self.dataRandom.view(vigra.VigraArray)
        self.dataRandom.axistags = vigra.VigraArray.defaultAxistags("xyzc")
        
        
        self.data5d = self.data5d.view(vigra.VigraArray)
        self.data5d.axistags = vigra.VigraArray.defaultAxistags("txyzc")
        
        self.minSize = 5 #first cluster doesn't pass this
        self.maxSize = 30 #fourth cluster doesn't pass this
        self.highThreshold = 0.65 #third cluster doesn't pass
        self.lowThreshold = 0.1
        
        self.sigma = { 'x' : 0.3, 'y' : 0.3, 'z' : 0.3 }
        #pre-smooth all 3d and 4d data
        self.data = vigra.filters.gaussianSmoothing(self.data.astype(numpy.float32), 0.3)
        self.dataChannels = vigra.filters.gaussianSmoothing(self.dataChannels[..., 2:3].astype(numpy.float32), 0.3)
        
    def test4dAnd5d(self):
        g = Graph()
        
        oper = OpThresholdTwoLevels4d(graph = g)
        oper.InputImage.setValue(self.data)
        oper.MinSize.setValue(self.minSize)
        oper.MaxSize.setValue(self.maxSize)
        oper.HighThreshold.setValue(self.highThreshold)
        oper.LowThreshold.setValue(self.lowThreshold)
        #oper.SmootherSigma.setValue(self.sigma)
        
        output = oper.Output[:].wait()
        output = output.reshape((self.nx, self.ny, self.nz))
        
        clusters = generateData((self.nx, self.ny, self.nz, self.nc))
        
        cluster1 = numpy.logical_and(output, clusters[0])
        assert numpy.any(cluster1!=0)==False
        cluster2 = numpy.logical_and(output, clusters[1])
        assert numpy.any(cluster2!=0)==True
        cluster3 = numpy.logical_and(output, clusters[2])
        assert numpy.any(cluster3!=0)==False
        cluster4 = numpy.logical_and(output, clusters[3])
        assert numpy.any(cluster4!=0)==False
        cluster5 = numpy.logical_and(output, clusters[4])
        assert numpy.all(cluster5==0)
        
        oper.InputImage.setValue(self.dataChannels)
        output = oper.Output[:].wait()
        output = output.reshape((self.nx, self.ny, self.nz))
        cluster1 = numpy.logical_and(output, clusters[0])
        assert numpy.any(cluster1!=0)==False
        cluster2 = numpy.logical_and(output, clusters[1])
        assert numpy.any(cluster2!=0)==True
        cluster3 = numpy.logical_and(output, clusters[2])
        assert numpy.any(cluster3!=0)==False
        cluster4 = numpy.logical_and(output, clusters[3])
        assert numpy.any(cluster4!=0)==False
        
        
        oper5d = OpThresholdTwoLevels(graph=g)
        oper5d.InputImage.setValue(self.data5d)
        oper5d.MinSize.setValue(self.minSize)
        oper5d.MaxSize.setValue(self.maxSize)
        oper5d.HighThreshold.setValue(self.highThreshold)
        oper5d.LowThreshold.setValue(self.lowThreshold)
        oper5d.SmootherSigma.setValue(self.sigma)
        oper5d.Channel.setValue(2)
        oper5d.CurOperator.setValue(1)
        
        out5d = oper5d.Output[:].wait()
        
        tIndex= oper5d.Output.meta.axistags.index('t')
        slicing = 5*[slice(None, None, None)]
        slicing[tIndex]= slice(0, 1, None)
        #print out5d.axistags, output.shape.axistags
        assert numpy.all(out5d[slicing].squeeze()==output[:].squeeze())
        
    def thresholdTwoLevels(self, data):
        #this function is the same as the operator, but without any lazyflow stuff
        #or memory management
        
        #sigmatuple = (self.sigma['x'], self.sigma['y'], self.sigma['z'])
        #data = vigra.filters.gaussianSmoothing(data.astype(numpy.float32), sigmatuple)
        
        th_high = data>self.highThreshold
        th_low = data>self.lowThreshold
        
        cc_high = vigra.analysis.labelVolumeWithBackground(th_high.astype(numpy.uint8))
        cc_low = vigra.analysis.labelVolumeWithBackground(th_low.astype(numpy.uint8))
        
        sizes = numpy.bincount(cc_high.flat)
        new_labels = numpy.zeros((sizes.shape[0]+1,))
        for icomp, comp in enumerate(sizes):
            if comp<self.minSize or comp>self.maxSize:
                new_labels[icomp]=0
            else:
                new_labels[icomp]=1
        
        cc_high_filtered = numpy.asarray(new_labels[cc_high]).astype(numpy.bool)
    
        prod = cc_high_filtered.astype(numpy.uint8) * numpy.asarray(cc_low)
        
        passed = numpy.unique(prod)
        del prod
        all_label_values = numpy.zeros( (cc_low.max()+1,), dtype=numpy.uint8 )
        for i, l in enumerate(passed):
            all_label_values[l] = i+1
        all_label_values[0] = 0
        
        filtered1 = all_label_values[ cc_low ]
        
        sizes2 = numpy.bincount(filtered1.flat)
        final_label_values = numpy.zeros((filtered1.max()+1,))
        for icomp, comp in enumerate(sizes2):
            if comp<self.minSize or comp>self.maxSize:
                final_label_values[icomp]=0
            else:
                final_label_values[icomp]=1
        filtered2 = final_label_values[filtered1]
        return filtered2.squeeze()
        
    
    def testAgainstOwn(self):
        g = Graph()
        oper = OpThresholdTwoLevels4d(graph = g)
        oper.InputImage.setValue(self.data)
        oper.MinSize.setValue(self.minSize)
        oper.MaxSize.setValue(self.maxSize)
        oper.HighThreshold.setValue(self.highThreshold)
        oper.LowThreshold.setValue(self.lowThreshold)
        #oper.SmootherSigma.setValue(self.sigma)
        
        output = oper.Output[:].wait()
        output = output.reshape((self.nx, self.ny, self.nz))
        
        output2 = self.thresholdTwoLevels(self.data)
        output2 = output2.astype(numpy.bool).astype(numpy.uint8)
       
        clusters = generateData((self.nx, self.ny, self.nz, self.nc))
       
        cluster1 = numpy.logical_and(output2, clusters[0])
        assert numpy.any(cluster1!=0)==False
        cluster2 = numpy.logical_and(output2, clusters[1])
        assert numpy.any(cluster2!=0)==True
        cluster3 = numpy.logical_and(output2, clusters[2])
        assert numpy.any(cluster3!=0)==False
        cluster4 = numpy.logical_and(output2, clusters[3])
        assert numpy.all(cluster4==0)
        cluster5 = numpy.logical_and(output2, clusters[4])
        assert numpy.all(cluster5==0)

        output = output.astype(numpy.bool).astype(numpy.uint8)
        assert numpy.all(output==output2)
        
        oper.InputImage.setValue(self.dataRandom)
        output = oper.Output[:].wait()
        output = output.reshape((self.nx, self.ny, self.nz))
        output2 = self.thresholdTwoLevels(self.dataRandom)
        output2 = output2.astype(numpy.bool).astype(numpy.uint8)
        output = output.astype(numpy.bool).astype(numpy.uint8)
        assert numpy.all(output==output2)
        
        
        
if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})