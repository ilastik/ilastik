import unittest
import itertools
import vigra
import numpy
from functools import partial
from lazyflow.roi import TinyVector, roiToSlice
from lazyflow.graph import Graph
from lazyflow.operators.imgFilterOperators import OpGaussianSmoothing,\
     OpLaplacianOfGaussian, OpStructureTensorEigenvaluesSummedChannels,\
     OpHessianOfGaussianEigenvalues, OpGaussianGradientMagnitude,\
     OpDifferenceOfGaussians, OpHessianOfGaussian, OpStructureTensorEigenvalues
from lazyflow.operators.obsolete import vigraOperators

# Change this to view debug output files
GENERATE_VISUAL_DEBUG_IMAGES = False

class TestOpBaseVigraFilter(unittest.TestCase):
   
    def setUp(self):
        self.testDimensions = ['xyc','xyzc','txyzc','txyc']
        self.graph = Graph()
            
    def expandByShape(self,start,stop,shape,inputShape):
        dim = len(start)
        if type(shape == int):
            tmp = shape
            shape = numpy.zeros(dim).astype(int)
            shape[:] = tmp
        tmpStart = [x-s for x,s in zip(start,shape)]
        tmpStop = [x+s for x,s in zip(stop,shape)]
        start = [max(t,i) for t,i in zip(tmpStart,numpy.zeros_like(inputShape))]
        stop = [min(t,i) for t,i in zip(tmpStop,inputShape)]
        return start,stop
    
    def adjustChannel(self,start,stop,cPerC,cIndex):
        if cPerC != 1:
            start = [start[i]/cPerC if i == cIndex else start[i] for i in range(len(start))]
            stop = [stop[i]/cPerC+1 if i==cIndex else stop[i] for i in range(len(stop))]
            start = TinyVector(start)
            stop = TinyVector(stop)
        return start,stop
    
    def setStartToZero(self,start,stop):
        start = [0]*len(start)
        stop = [end-begin for begin,end in zip(start,stop)]
        start = TinyVector(start)
        stop = TinyVector(stop)
        return start,stop

    def generalOperatorTest(self,operator):
        for dim in self.testDimensions:
            testArray = vigra.VigraArray((20,)*len(dim),axistags=vigra.VigraArray.defaultAxistags(dim))
            testArray[(slice(2,5,None),)*len(dim)] = 10
            operator.inputs["Input"].setValue(testArray)
            for i,j in [(i,j) for i,j in itertools.permutations(range(0,10),2) if i<j]:
                start = [i]*len(dim)
                stop = [j]*len(dim)
                operator.outputs["Output"](start,stop).wait()
            
    def visualTest(self,operator):
        if GENERATE_VISUAL_DEBUG_IMAGES:
            start,stop  = [200,200,0],[400,400,1]
            testArray = vigra.VigraArray((400,400,3))
            roiResult = vigra.VigraArray(tuple([sto-sta for sta,sto in zip(start,stop)]))
            testArray[100:300,100:300,0] = 1
            testArray[200:300,200:300,1] = 1
            testArray[100:200,100:200,2] = 1
            operator.inputs["Input"].setValue(testArray)
            wholeResult = operator.outputs["Output"]().wait()
            wholeResult = wholeResult[:,:,0:3]
            roiResult[:,:,0:1] = operator.outputs["Output"](start,stop).wait()
            vigra.impex.writeImage(testArray,operator.name+'before.png')
            vigra.impex.writeImage(wholeResult,operator.name+'afterWhole.png')
            vigra.impex.writeImage(roiResult,operator.name+'afterRoi.png')
        
    def compareToFilter(self,op,Filter):
        for dim in self.testDimensions:
            max = 15
            testArray = vigra.VigraArray(numpy.random.rand(*(max,)*len(dim)),axistags=vigra.VigraArray.defaultAxistags(dim))
            op.Input.setValue(testArray)
            for i in range(10):
                start = [numpy.random.randint(0,max-1) for i in range(len(dim))]
                stop = [numpy.random.randint(start[i]+1,max) for i in range(len(dim))]
                start = list((0,)*len(dim))
                stop = list((max,)*(len(dim)-1)+(3,))
                #adjust rois for structureTensoreEigenvalues
                if Filter.func.__name__ == "structureTensorEigenvaluesSummedChannels":
                    start[-1] = numpy.random.randint(0,testArray.axistags.axisTypeCount(vigra.AxisType.Space)-1)
                    stop[-1] = numpy.random.randint(start[-1]+1,testArray.axistags.axisTypeCount(vigra.AxisType.Space))
                resOp = op.Output(start,stop).wait()
                cstart,cstop = start.pop(),stop.pop()
                #handle txyc,txyzc
                if testArray.axistags.index('t') < len(dim):
                    tstart,tstop = start.pop(0),stop.pop(0)
                    resF = numpy.zeros_like(resOp)
                    #cPerC > 1
                    if op.channelsPerChannel() > 1:
                        if Filter.func.__name__ == "structureTensorEigenvaluesSummedChannels":
                            for j in range(0,tstop-tstart):
                                resF[(j,)+(slice(0,None),)*(len(dim)-1)] = Filter(testArray[(j+tstart,)+(slice(0,None),)*(len(dim)-1)],roi=(start,stop))[(slice(0,None),)*(len(dim)-2)+(slice(cstart,cstop),)]
                            self.assertTrue(numpy.allclose(resOp,resF))
                            continue
                        if Filter.func.__name__ == "structureTensorEigenvalues":
                            pass
                        cPerC = op.channelsPerChannel()
                        if cstop%cPerC == 0:
                            reqCstart,reqCstop = cstart/cPerC,cstop/cPerC
                        else:
                            reqCstart,reqCstop = cstart/cPerC,cstop/cPerC+1
                        resF = numpy.zeros(tuple(resOp.shape[:-1])+((reqCstop-reqCstart)*cPerC,))
                        for j in range(0,tstop-tstart):
                            for i in range(0,reqCstop-reqCstart):
                                resF[(j,)+(slice(0,None),)*(len(dim)-2)+(slice(i*cPerC,(i+1)*cPerC),)] = Filter(testArray[(j+tstart,)+(slice(0,None),)*(len(dim)-2)+(i+reqCstart,)],roi=(start,stop))
                        cstart2 = cstart%cPerC
                        cstop2 = cstart2+cstop-cstart
                        resF = resF[(slice(0,None),)*(len(dim)-1)+(slice(cstart2,cstop2),)]
                        self.assertTrue(numpy.allclose(resOp,resF))
                    #cPerC = 1
                    else:
                        #handle gaussianGradientMagnitude, its special
                        if Filter.func.__name__ == "gaussianGradientMagnitude":
                            resF = numpy.zeros_like(resOp)
                            for j in range(0,tstop-tstart):
                                for i in range(0,cstop-cstart):
                                    resF[(j,)+(slice(0,None),)*(len(dim)-2)+(i,)] = Filter(testArray[(tstart+j,)+(slice(0,None),)*(len(dim)-2)+(cstart+i,)],roi=(start,stop))
                        else:        
                            for i in range(0,tstop-tstart):
                                resF[(i,)+(slice(0,None),)*(len(dim)-1)] = Filter(testArray[(i+tstart,)+(slice(0,None),)*(len(dim)-2)+(slice(cstart,cstop),)],roi=(start,stop))
                        self.assertTrue(numpy.allclose(resOp,resF))
                #handle xyc,xyzc
                else:
                    #cPerC > 1
                    if op.channelsPerChannel() > 1:
                        #handle structureTensorEigenvaluesSummedChannels
                        if Filter.func.__name__ == "structureTensorEigenvaluesSummedChannels":
                            resF = Filter(testArray,roi=(start,stop))[(slice(0,None),)*(len(dim)-1)+(slice(cstart,cstop),)]
                            self.assertTrue(numpy.allclose(resOp,resF))
                            continue
                        cPerC = op.channelsPerChannel()
                        
                        if cstop%cPerC == 0:
                            reqCstart,reqCstop = cstart/cPerC,cstop/cPerC
                        else:
                            reqCstart,reqCstop = cstart/cPerC,cstop/cPerC+1
                        resF = numpy.zeros(tuple(resOp.shape[:-1])+((reqCstop-reqCstart)*cPerC,))
                        for i in range(0,reqCstop-reqCstart):
                            resF[(slice(0,None),)*(len(dim)-1)+(slice(i*cPerC,(i+1)*cPerC),)] = Filter(testArray[(slice(0,None),)*(len(dim)-1)+(i+reqCstart,)],roi=(start,stop))
                        resF = vigra.VigraArray(resF,axistags=vigra.defaultAxistags(dim))
                        cstart2 = cstart%cPerC
                        cstop2 = cstart2+cstop-cstart
                        resF = resF[(slice(0,None),)*(len(dim)-1)+(slice(cstart2,cstop2),)] 
                        self.assertTrue(numpy.allclose(resOp,resF))
                    #cPerC == 1
                    else:
                        #handle gaussianGradientMagnitude, its special
                        if Filter.func.__name__ == "gaussianGradientMagnitude":
                            resF = numpy.zeros_like(resOp)
                            for i in range(0,cstop-cstart):
                                resF[(slice(0,None),)*(len(dim)-1)+(i,)] = Filter(testArray[(slice(0,None),)*(len(dim)-1)+(cstart+i,)],roi=(start,stop))
                        else:
                            resF = Filter(testArray[(slice(0,None),)*(len(dim)-1)+(slice(cstart,cstop),)],roi=(start,stop))
                        self.assertTrue(numpy.allclose(resOp,resF))

    def test_GaussianSmoothing(self):
        opGaussianSmoothing = OpGaussianSmoothing(graph=self.graph)
        opGaussianSmoothing.Sigma.setValue(2.0)
        def tmpFilter(source,sigma,window_size,roi):
            tmpfilter = vigra.filters.gaussianSmoothing
            return tmpfilter(array=source,sigma=sigma,window_size=window_size,roi=(roi[0],roi[1]))
        gaussianSmoothingFilter = partial(tmpFilter,sigma=2.0,window_size=4)
        self.generalOperatorTest(opGaussianSmoothing)
        #self.visualTest(opGaussianSmoothing)
        self.compareToFilter(opGaussianSmoothing,gaussianSmoothingFilter)
        
    def test_DifferenceOfGaussians(self):
        opDifferenceOfGaussians = OpDifferenceOfGaussians(graph=self.graph)
        opDifferenceOfGaussians.Sigma.setValue(2.0)
        opDifferenceOfGaussians.Sigma2.setValue(3.0)
        def tmpFilter(source,s0,s1,window_size,roi):
            tmpfilter = vigra.filters.gaussianSmoothing
            return tmpfilter(array=source,sigma=s0,window_size=window_size,roi=(roi[0],roi[1]))\
                   -tmpfilter(array=source,sigma=s1,window_size=window_size,roi=(roi[0],roi[1]))
        gaussianSmoothingFilter = partial(tmpFilter,s0=2.0,s1=3.0,window_size=4)
        self.generalOperatorTest(opDifferenceOfGaussians)
        #self.visualTest(opDifferenceOfGaussians)
        self.compareToFilter(opDifferenceOfGaussians,gaussianSmoothingFilter)

    def test_LaplacianOfGaussian(self):
        opLaplacianOfGaussian = OpLaplacianOfGaussian(graph=self.graph)
        opLaplacianOfGaussian.Sigma.setValue(2.0)
        def tmpFilter(source,sigma,window_size,roi):
            tmpfilter = vigra.filters.laplacianOfGaussian
            return tmpfilter(array=source,scale=sigma,window_size=window_size,roi=(roi[0],roi[1]))
        laplacianofGaussianFilter = partial(tmpFilter,sigma=2.0,window_size=4)
        self.generalOperatorTest(opLaplacianOfGaussian)
        #self.visualTest(opLaplacianOfGaussian)
        self.compareToFilter(opLaplacianOfGaussian, laplacianofGaussianFilter)
        
    def test_GaussianGradientMagnitude(self):
        opGaussianGradientMagnitude = OpGaussianGradientMagnitude(graph=self.graph)
        opGaussianGradientMagnitude.Sigma.setValue(2.0)
        def gaussianGradientMagnitude(source,sigma,window_size,roi):
            tmpfilter = vigra.filters.gaussianGradientMagnitude
            return tmpfilter(source,sigma=sigma,window_size=window_size,roi=(roi[0],roi[1]))
        gaussianGradientMagnitudeFilter = partial(gaussianGradientMagnitude,sigma=2.0,window_size=4)
        self.generalOperatorTest(opGaussianGradientMagnitude)
        #self.visualTest(opGaussianGradientMagnitude)
        self.compareToFilter(opGaussianGradientMagnitude, gaussianGradientMagnitudeFilter)

    def test_StructureTensorEigenvaluesSummedChannels(self):
        opStructureTensorEigenvaluesSummedChannels = OpStructureTensorEigenvaluesSummedChannels(graph=self.graph)
        opStructureTensorEigenvaluesSummedChannels.Sigma.setValue(1.5)
        opStructureTensorEigenvaluesSummedChannels.Sigma2.setValue(2.0)
        def structureTensorEigenvaluesSummedChannels(source,innerScale,outerScale,window_size,roi):
            tmpfilter = vigra.filters.structureTensorEigenvalues
            return tmpfilter(image=source,innerScale=innerScale,outerScale=outerScale,window_size=window_size,roi=(roi[0],roi[1]))
        structureTensorEigenvaluesSummedChannelsFilter = partial(structureTensorEigenvaluesSummedChannels,innerScale=1.5,outerScale=2.0,window_size=4)
        self.compareToFilter(opStructureTensorEigenvaluesSummedChannels,structureTensorEigenvaluesSummedChannelsFilter)
        self.generalOperatorTest(opStructureTensorEigenvaluesSummedChannels)
        #self.visualTest(opStructureTensorEigenvaluesSummedChannels)
        
    def test_StructureTensorEigenvalues(self):
        opStructureTensorEigenvalues = OpStructureTensorEigenvalues(graph=self.graph)
        opStructureTensorEigenvalues.Sigma.setValue(1.5)
        opStructureTensorEigenvalues.Sigma2.setValue(2.0)
        def structureTensorEigenvalues(source,innerScale,outerScale,window_size,roi):
            tmpfilter = vigra.filters.structureTensorEigenvalues
            return tmpfilter(image=source,innerScale=innerScale,outerScale=outerScale,window_size=window_size,roi=(roi[0],roi[1]))
        structureTensorEigenvaluesFilter = partial(structureTensorEigenvalues,innerScale=1.5,outerScale=2.0,window_size=4)
        self.compareToFilter(opStructureTensorEigenvalues,structureTensorEigenvaluesFilter)
        self.generalOperatorTest(opStructureTensorEigenvalues)
        self.visualTest(opStructureTensorEigenvalues)   

    def test_HessianOfGaussian(self):
        opHessianOfGaussian = OpHessianOfGaussian(graph=self.graph)
        opHessianOfGaussian.Sigma.setValue(2.0)
        def hessianOfGaussianFilter(source,sigma,window_size,roi):
            tmpfilter = vigra.filters.hessianOfGaussian
            if source.axistags.axisTypeCount(vigra.AxisType.Space) == 2:
                return tmpfilter(image=source,sigma=sigma,window_size=window_size,roi=(roi[0],roi[1]))
            elif source.axistags.axisTypeCount(vigra.AxisType.Space) == 3:
                return tmpfilter(volume=source,sigma=sigma,window_size=window_size,roi=(roi[0],roi[1]))
        hessianOfGaussianFilter = partial(hessianOfGaussianFilter,sigma=2.0,window_size=4)
        self.generalOperatorTest(opHessianOfGaussian)
        #self.visualTest(opHessianOfGaussian)
        self.compareToFilter(opHessianOfGaussian, hessianOfGaussianFilter)
        
    def test_HessianOfGaussianEigenvalues(self):
        opHessianOfGaussianEigenvalues = OpHessianOfGaussianEigenvalues(graph=self.graph)
        opHessianOfGaussianEigenvalues.Sigma.setValue(2.0)
        def tmpFilter(source,sigma,window_size,roi):
            tmpfilter = vigra.filters.hessianOfGaussianEigenvalues
            return tmpfilter(source,scale=sigma,window_size=window_size,roi=(roi[0],roi[1]))
        hessianOfGaussianEigenvaluesFilter = partial(tmpFilter,sigma=2.0,window_size=4)
        self.generalOperatorTest(opHessianOfGaussianEigenvalues)
        #self.visualTest(opHessianOfGaussianEigenvalues)
        self.compareToFilter(opHessianOfGaussianEigenvalues,hessianOfGaussianEigenvaluesFilter)



if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
