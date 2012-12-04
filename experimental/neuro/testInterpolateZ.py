from lazyflow.operators import OpPixelFeaturesInterpPresmoothed, OpPixelFeaturesPresmoothed
from lazyflow import graph
import lazyflow
import numpy
import vigra
import copy

scaleZ = 2
scales = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
featureIds = [ 'GaussianSmoothing', 'LaplacianOfGaussian',\
                   'GaussianGradientMagnitude',
                   'DifferenceOfGaussians',
                   'StructureTensorEigenvalues',
                   'HessianOfGaussianEigenvalues' ]

a = numpy.zeros((20, 20, 20, 1), dtype=numpy.float32)
for i in range(a.shape[2]):
    a[:, :, i, 0]=i
    
sourceArrayV = a.view(vigra.VigraArray)
sourceArrayV.axistags =  vigra.VigraArray.defaultAxistags(4)
            
g = graph.Graph()
opFeatures = OpPixelFeaturesInterpPresmoothed(graph=g)
opFeaturesOld = OpPixelFeaturesPresmoothed(graph=g)
opFeatures.Input.setValue(sourceArrayV)

rows = 6
cols = 7
defaultFeatures = numpy.zeros((rows,cols), dtype=bool)
#self.featureDlg.selectedFeatureBoolMatrix = defaultFeatures
#featureMatrix = numpy.asarray(self.featureDlg.selectedFeatureBoolMatrix)
defaultFeatures[0, 5]=True
opFeatures.Matrix.setValue( defaultFeatures  )
opFeatures.Scales.setValue(scales)
opFeatures.FeatureIds.setValue(featureIds)

opFeatures.InterpolationScaleZ.setValue(scaleZ)

sub1 = lazyflow.rtype.SubRegion(None, start=[5, 5, 5, 0], stop=[10, 10, 10, 1])
res1 = opFeatures.outputs["Output"](sub1.start, sub1.stop).wait()

print
print res1.shape
print res1[0, 0, :] 

newRangeZ = scaleZ*(sourceArrayV.shape[2]-1)+1
inter = vigra.sampling.resizeVolumeSplineInterpolation(sourceArrayV.squeeze(), \
                                                       shape=(sourceArrayV.shape[0], sourceArrayV.shape[1], newRangeZ))
inter.resize(inter.shape+(1,))
sourceArrayInterV = inter.view(vigra.VigraArray)
sourceArrayInterV.axistags =  vigra.VigraArray.defaultAxistags(4)
print sourceArrayInterV.shape
opFeaturesOld.Input.setValue(sourceArrayInterV)
opFeaturesOld.Matrix.setValue(defaultFeatures)
opFeaturesOld.Scales.setValue(scales)
opFeaturesOld.FeatureIds.setValue(featureIds)


sub2 = lazyflow.rtype.SubRegion(None, start=[5, 5, 10, 0], stop=[10, 10, 20, 1])
res2 = opFeaturesOld.outputs["Output"](sub2.start, sub2.stop).wait()
print res2[0, 0, :]

#smoothed = vigra.filters.gaussianSmoothing(inter, scales[5])
#print smoothed[5, 5, 10]

