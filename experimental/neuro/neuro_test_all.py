import context
import vigra
import os
import glob
import vigra
import sys

import threading
from lazyflow.graph import *
import copy

from lazyflow import operators

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

sys.setrecursionlimit(10000)

fileraw = "/home/akreshuk/data/context/TEM_raw/50slices.h5"
filelabels = "/home/akreshuk/data/context/TEM_labels/50slices.h5"
resdir = "/home/akreshuk/data/context/TEM_results/"
resproject = "50slices_all.ilp"
graphfile = "/home/akreshuk/data/context/50slices_graph_all.h5"
h5path = "/data"
nclasses = 5

g = Graph(numThreads = 1, softMaxMem = 16000*1024**2)


axistags=vigra.AxisTags(vigra.AxisInfo('x',vigra.AxisType.Space),vigra.AxisInfo('y',vigra.AxisType.Space), vigra.AxisInfo('z',vigra.AxisType.Space))  

import h5py
f = h5py.File(fileraw)
stack = numpy.array(f[h5path])
stack = stack.reshape(stack.shape + (1,))
stackva = vigra.VigraArray(stack, axistags=vigra.VigraArray.defaultAxistags(4))



#Slicer
slicer = operators.OpMultiArraySlicer(g)
#slicer.inputs["Input"].connect(himage.outputs["Image"])
slicer.inputs["Input"].setValue(stackva)
slicer.inputs["AxisFlag"].setValue('z')

print "THE SLICER:", slicer.outputs["Slices"][0].shape

#Sigma provider 0.9
sigmaProvider = operators.OpArrayPiper(g)
sigmaProvider.inputs["Input"].setValue(0.3) 

#Gaussian Smoothing     
opa = operators.OpGaussianSmoothing(g)   
opa.inputs["Input"].connect(slicer.outputs["Slices"])
opa.inputs["sigma"].connect(sigmaProvider.outputs["Output"])

print "GAUSSIAN SMOOTHING:", opa.outputs["Output"][0].shape
print "one by one"
blagaus = opa.outputs["Output"][0][:].allocate().wait()

#Gaussian stacker
stacker_opa = operators.OpMultiArrayStacker(g)
stacker_opa.inputs["Images"].connect(opa.outputs["Output"])
stacker_opa.inputs["AxisFlag"].setValue('z')
stacker_opa.inputs["AxisIndex"].setValue(2)
#Gaussian #2
opa2 = operators.OpGaussianSmoothing(g)
opa2.inputs["Input"].connect(slicer.outputs["Slices"])
opa2.inputs["sigma"].setValue(0.7)
stacker_opa2 = operators.OpMultiArrayStacker(g)
stacker_opa2.inputs["Images"].connect(opa2.outputs["Output"])
stacker_opa2.inputs["AxisFlag"].setValue('z')
stacker_opa2.inputs["AxisIndex"].setValue(2)
#Gaussian #3
opa3 = operators.OpGaussianSmoothing(g)
opa3.inputs["Input"].connect(slicer.outputs["Slices"])
opa3.inputs["sigma"].setValue(1.5)
stacker_opa3 = operators.OpMultiArrayStacker(g)
stacker_opa3.inputs["Images"].connect(opa3.outputs["Output"])
stacker_opa3.inputs["AxisFlag"].setValue('z')
stacker_opa3.inputs["AxisIndex"].setValue(2)
#Gaussian #4
opa4 = operators.OpGaussianSmoothing(g)
opa4.inputs["Input"].connect(slicer.outputs["Slices"])
opa4.inputs["sigma"].setValue(3.6)
stacker_opa4 = operators.OpMultiArrayStacker(g)
stacker_opa4.inputs["Images"].connect(opa4.outputs["Output"])
stacker_opa4.inputs["AxisFlag"].setValue('z')
stacker_opa4.inputs["AxisIndex"].setValue(2)

#Sigma provider
sigmaProvider2 = operators.OpArrayPiper(g)
sigmaProvider2.inputs["Input"].setValue(0.7)
#Hessian
hog = operators.OpHessianOfGaussianEigenvalues(g)
hog.inputs["Input"].connect(slicer.outputs["Slices"])
hog.inputs["scale"].connect(sigmaProvider2.outputs["Output"])
#Hessian stacker
stacker_hog = operators.OpMultiArrayStacker(g)
stacker_hog.inputs["Images"].connect(hog.outputs["Output"])
stacker_hog.inputs["AxisFlag"].setValue('z')
stacker_hog.inputs["AxisIndex"].setValue(2)
#Hessian #2
hog2 = operators.OpHessianOfGaussianEigenvalues(g)
hog2.inputs["Input"].connect(slicer.outputs["Slices"])
hog2.inputs["scale"].setValue(1)
stacker_hog2 = operators.OpMultiArrayStacker(g)
stacker_hog2.inputs["Images"].connect(hog2.outputs["Output"])
stacker_hog2.inputs["AxisFlag"].setValue('z')
stacker_hog2.inputs["AxisIndex"].setValue(2)
#Hessian #3
hog3 = operators.OpHessianOfGaussianEigenvalues(g)
hog3.inputs["Input"].connect(slicer.outputs["Slices"])
hog3.inputs["scale"].setValue(1.6)
stacker_hog3 = operators.OpMultiArrayStacker(g)
stacker_hog3.inputs["Images"].connect(hog3.outputs["Output"])
stacker_hog3.inputs["AxisFlag"].setValue('z')
stacker_hog3.inputs["AxisIndex"].setValue(2)
#Hessian #4
hog4 = operators.OpHessianOfGaussianEigenvalues(g)
hog4.inputs["Input"].connect(slicer.outputs["Slices"])
hog4.inputs["scale"].setValue(3.5)
stacker_hog4 = operators.OpMultiArrayStacker(g)
stacker_hog4.inputs["Images"].connect(hog4.outputs["Output"])
stacker_hog4.inputs["AxisFlag"].setValue('z')
stacker_hog4.inputs["AxisIndex"].setValue(2)

#Gaussian Gradient Magnitude
opgg = operators.OpGaussinaGradientMagnitude(g)
opgg.inputs["Input"].connect(slicer.outputs["Slices"])
opgg.inputs["sigma"].setValue(0.7)
stacker_opgg = operators.OpMultiArrayStacker(g)
stacker_opgg.inputs["Images"].connect(opgg.outputs["Output"])
stacker_opgg.inputs["AxisFlag"].setValue('z')
stacker_opgg.inputs["AxisIndex"].setValue(2)
#Gaussian Gradient Magnitude #2
opgg2 = operators.OpGaussinaGradientMagnitude(g)
opgg2.inputs["Input"].connect(slicer.outputs["Slices"])
opgg2.inputs["sigma"].setValue(1.0)
stacker_opgg2 = operators.OpMultiArrayStacker(g)
stacker_opgg2.inputs["Images"].connect(opgg2.outputs["Output"])
stacker_opgg2.inputs["AxisFlag"].setValue('z')
stacker_opgg2.inputs["AxisIndex"].setValue(2)
#Gaussian Gradient Magnitude #3
opgg3 = operators.OpGaussinaGradientMagnitude(g)
opgg3.inputs["Input"].connect(slicer.outputs["Slices"])
opgg3.inputs["sigma"].setValue(1.6)
stacker_opgg3 = operators.OpMultiArrayStacker(g)
stacker_opgg3.inputs["Images"].connect(opgg3.outputs["Output"])
stacker_opgg3.inputs["AxisFlag"].setValue('z')
stacker_opgg3.inputs["AxisIndex"].setValue(2)
#Gaussian Gradient Magnitude #4
opgg4 = operators.OpGaussinaGradientMagnitude(g)
opgg4.inputs["Input"].connect(slicer.outputs["Slices"])
opgg4.inputs["sigma"].setValue(3.5)
stacker_opgg4 = operators.OpMultiArrayStacker(g)
stacker_opgg4.inputs["Images"].connect(opgg4.outputs["Output"])
stacker_opgg4.inputs["AxisFlag"].setValue('z')
stacker_opgg4.inputs["AxisIndex"].setValue(2)

#Laplacian
olg=operators.OpLaplacianOfGaussian(g)
olg.inputs["Input"].connect(slicer.outputs["Slices"])
olg.inputs["scale"].setValue(0.7)
stacker_olg = operators.OpMultiArrayStacker(g)
stacker_olg.inputs["Images"].connect(olg.outputs["Output"])
stacker_olg.inputs["AxisFlag"].setValue('z')
stacker_olg.inputs["AxisIndex"].setValue(2)
#Laplacian #2
olg2=operators.OpLaplacianOfGaussian(g)
olg2.inputs["Input"].connect(slicer.outputs["Slices"])
olg2.inputs["scale"].setValue(1.0)
stacker_olg2 = operators.OpMultiArrayStacker(g)
stacker_olg2.inputs["Images"].connect(olg2.outputs["Output"])
stacker_olg2.inputs["AxisFlag"].setValue('z')
stacker_olg2.inputs["AxisIndex"].setValue(2)
#Laplacian #3
olg3=operators.OpLaplacianOfGaussian(g)
olg3.inputs["Input"].connect(slicer.outputs["Slices"])
olg3.inputs["scale"].setValue(1.6)
stacker_olg3 = operators.OpMultiArrayStacker(g)
stacker_olg3.inputs["Images"].connect(olg3.outputs["Output"])
stacker_olg3.inputs["AxisFlag"].setValue('z')
stacker_olg3.inputs["AxisIndex"].setValue(2)
#Laplacian #4
olg4=operators.OpLaplacianOfGaussian(g)
olg4.inputs["Input"].connect(slicer.outputs["Slices"])
olg4.inputs["scale"].setValue(3.5)
stacker_olg4 = operators.OpMultiArrayStacker(g)
stacker_olg4.inputs["Images"].connect(olg4.outputs["Output"])
stacker_olg4.inputs["AxisFlag"].setValue('z')
stacker_olg4.inputs["AxisIndex"].setValue(2)

#Difference of Gaussians
dg = operators.OpDifferenceOfGaussians(g)
dg.inputs["Input"].connect(slicer.outputs["Slices"])
s = 0.7
dg.inputs["sigma0"].setValue(s)
dg.inputs["sigma1"].setValue(3.5*s)
stacker_dg = operators.OpMultiArrayStacker(g)
stacker_dg.inputs["Images"].connect(dg.outputs["Output"])
stacker_dg.inputs["AxisFlag"].setValue('z')
stacker_dg.inputs["AxisIndex"].setValue(2)
#Difference of Gaussians 2
dg2 = operators.OpDifferenceOfGaussians(g)
dg2.inputs["Input"].connect(slicer.outputs["Slices"])
s = 1.0
dg2.inputs["sigma0"].setValue(s)
dg2.inputs["sigma1"].setValue(3.5*s)
stacker_dg2 = operators.OpMultiArrayStacker(g)
stacker_dg2.inputs["Images"].connect(dg2.outputs["Output"])
stacker_dg2.inputs["AxisFlag"].setValue('z')
stacker_dg2.inputs["AxisIndex"].setValue(2)
#Difference of Gaussians 3
dg3 = operators.OpDifferenceOfGaussians(g)
dg3.inputs["Input"].connect(slicer.outputs["Slices"])
s = 1.6
dg3.inputs["sigma0"].setValue(s)
dg3.inputs["sigma1"].setValue(3.5*s)
stacker_dg3 = operators.OpMultiArrayStacker(g)
stacker_dg3.inputs["Images"].connect(dg3.outputs["Output"])
stacker_dg3.inputs["AxisFlag"].setValue('z')
stacker_dg3.inputs["AxisIndex"].setValue(2)
#Difference of Gaussians 4
dg4 = operators.OpDifferenceOfGaussians(g)
dg4.inputs["Input"].connect(slicer.outputs["Slices"])
s = 3.5
dg4.inputs["sigma0"].setValue(s)
dg4.inputs["sigma1"].setValue(3.5*s)
stacker_dg4 = operators.OpMultiArrayStacker(g)
stacker_dg4.inputs["Images"].connect(dg4.outputs["Output"])
stacker_dg4.inputs["AxisFlag"].setValue('z')
stacker_dg4.inputs["AxisIndex"].setValue(2)



#stacker_hog.outputs["Output"]._axistags = axistags
print "THE HESSIAN STACKER:", stacker_hog.outputs["Output"].shape, stacker_hog.outputs["Output"].axistags
#print "allocating..."
#blahog = stacker_hog.outputs["Output"][:].allocate().wait()

#All features stacker
opMulti = operators.Op20ToMulti(g)
opMulti.inputs["Input00"].connect(stacker_opa.outputs["Output"])
opMulti.inputs["Input01"].connect(stacker_opa2.outputs["Output"])
opMulti.inputs["Input02"].connect(stacker_opa3.outputs["Output"])
opMulti.inputs["Input03"].connect(stacker_opa4.outputs["Output"])
opMulti.inputs["Input04"].connect(stacker_hog.outputs["Output"])
opMulti.inputs["Input05"].connect(stacker_hog2.outputs["Output"])
opMulti.inputs["Input06"].connect(stacker_hog3.outputs["Output"])
opMulti.inputs["Input07"].connect(stacker_hog4.outputs["Output"])
opMulti.inputs["Input08"].connect(stacker_opgg.outputs["Output"])
opMulti.inputs["Input09"].connect(stacker_opgg2.outputs["Output"])
opMulti.inputs["Input10"].connect(stacker_opgg3.outputs["Output"])
opMulti.inputs["Input11"].connect(stacker_opgg4.outputs["Output"])
opMulti.inputs["Input12"].connect(stacker_olg.outputs["Output"])
opMulti.inputs["Input13"].connect(stacker_olg2.outputs["Output"])
opMulti.inputs["Input14"].connect(stacker_olg3.outputs["Output"])
opMulti.inputs["Input15"].connect(stacker_olg4.outputs["Output"])
opMulti.inputs["Input16"].connect(stacker_dg.outputs["Output"])
opMulti.inputs["Input17"].connect(stacker_dg2.outputs["Output"])
opMulti.inputs["Input18"].connect(stacker_dg3.outputs["Output"])
opMulti.inputs["Input19"].connect(stacker_dg4.outputs["Output"])



stacker = operators.OpMultiArrayStacker(g)
stacker.inputs["Images"].connect(opMulti.outputs["Outputs"])
stacker.inputs["AxisFlag"].setValue('c')
stacker.inputs["AxisIndex"].setValue(3)
print "THE FEATURE STACKER:", stacker.outputs["Output"].shape, stacker.outputs["Output"].axistags

#print "and now let's allocate the features..."
#bla = stacker.outputs["Output"][:].allocate().wait()
#print bla.shape

#labelsReader = operators.OpH5Reader(g)
#labelsReader.inputs["Filename"].setValue(filelabels)
#labelsReader.inputs["hdf5Path"].setValue(h5path)

#print "THE LABEL READER:", labelsReader.outputs["Image"].shape

import h5py
f = h5py.File(filelabels)
labels = numpy.array(f[h5path])
labels = labels.reshape(labels.shape + (1,))
labelsva = vigra.VigraArray(labels, axistags=vigra.VigraArray.defaultAxistags(4))


#because opTrain has a MultiInputSlot only
opMultiL = operators.Op5ToMulti(g)
opMultiL.inputs["Input0"].setValue(labelsva)

opMultiS = operators.Op5ToMulti(g)
opMultiS.inputs["Input0"].connect(stacker.outputs["Output"])

#Training
opTrain = operators.OpTrainRandomForest(g)
opTrain.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
opTrain.inputs['Images'].connect(opMultiS.outputs["Outputs"])
opTrain.inputs["fixClassifier"].setValue(False)

acache = operators.OpArrayCache(g)
acache.inputs["Input"].connect(opTrain.outputs['Classifier'])

print "Here ########################", opTrain.outputs['Classifier'][:].allocate().wait()    
print
print "++++++++++++++ Trained ++++++++++++++++++++++"
print
#Prediction
opPredict = operators.OpPredictRandomForest(g)
opPredict.inputs['Classifier'].connect(acache.outputs['Output'])    
#opPredict.inputs['Image'].connect(opMultiS.outputs['Outputs'])
opPredict.inputs['Image'].connect(stacker.outputs['Output'])

classCountProvider = operators.OpArrayPiper(g)
classCountProvider.inputs["Input"].setValue(nclasses) 

opPredict.inputs['LabelsCount'].connect(classCountProvider.outputs["Output"])

#print "prediction output:", opPredict.outputs["PMaps"]
#Predict and save without context first
pmaps = opPredict.outputs["PMaps"][:].allocate().wait()[:]
print "shape of pmaps: ", pmaps.shape
#for i in range(pmaps.shape[2]):
    #for c in range(nclasses):
        ##print i, c
        #pmap = pmaps[:, :, i, c]
        #vigra.impex.writeImage(pmap, resdir + "slice00" + str(i) + "_class_" + str(c) + ".tif")

#save into an old ilastik project for easy visualization
outfile = h5py.File(resdir+resproject, "r+")
predfile = outfile["/DataSets/dataItem00/prediction"]
nx = pmaps.shape[0]
ny = pmaps.shape[1]
nz = pmaps.shape[2]
predfile[:] = pmaps.reshape((1, nx, ny, nz, nclasses))[:]
labelsfile = outfile["/DataSets/dataItem00/labels/data"]
labelsfile[:] = labels.reshape((1, nx, ny, nz, 1))[:]
outfile.close()

#save the graph to work with context in a different script
myPersonalEasyGraphNames = {}

myPersonalEasyGraphNames["graph"] = g
myPersonalEasyGraphNames["train"] = opTrain
myPersonalEasyGraphNames["cache"] = acache
myPersonalEasyGraphNames["features"] = stacker
myPersonalEasyGraphNames["predict"] = opPredict
myPersonalEasyGraphNames["nclasses"] = classCountProvider
myPersonalEasyGraphNames["opMultiL"] = opMultiL
myPersonalEasyGraphNames["labels"] = labelsva
myPersonalEasyGraphNames["slicer"] = slicer
#myPersonalEasyGraphNames["opa"] = opa
fgraph = h5py.File(graphfile,"w")
group = fgraph.create_group("graph")
group.dumpObject(myPersonalEasyGraphNames)
g.finalize()