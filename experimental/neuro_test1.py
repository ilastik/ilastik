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



fileraw = "/home/akreshuk/data/context/TEM_raw/50slices_down5.h5"
filelabels = "/home/akreshuk/data/context/TEM_labels/50slices_down5.h5"
resdir = "/home/akreshuk/data/context/TEM_results/"
resproject = "50slices_down5.ilp"
graphfile = "/home/akreshuk/data/context/50slices_down5_graph.h5"
h5path = "/volume/data"
nclasses = 5

g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)

#FIXME: can't do that now, axis tags go off
#himage = operators.OpH5Reader(g)
#himage.inputs["Filename"].setValue(fileraw)
#himage.inputs["hdf5Path"].setValue(h5path)

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
sigmaProvider.inputs["Input"].setValue(0.9) 

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

#stacker_opa.outputs["Output"]._axistags = axistags
print "THE GAUSSIAN STACKER:", stacker_opa.outputs["Output"].shape, stacker_opa.outputs["Output"].axistags
#print "allocating..."
#blaopa = stacker_opa.outputs["Output"][:].allocate().wait()



#Sigma provider 0.9
sigmaProvider2 = operators.OpArrayPiper(g)
sigmaProvider2.inputs["Input"].setValue(0.9)
#Hessian
hog = operators.OpHessianOfGaussianEigenvalues(g)
hog.inputs["Input"].connect(slicer.outputs["Slices"])
hog.inputs["scale"].connect(sigmaProvider2.outputs["Output"])
#Hessian stacker
stacker_hog = operators.OpMultiArrayStacker(g)
stacker_hog.inputs["Images"].connect(hog.outputs["Output"])
stacker_hog.inputs["AxisFlag"].setValue('z')
stacker_hog.inputs["AxisIndex"].setValue(2)

#stacker_hog.outputs["Output"]._axistags = axistags
print "THE HESSIAN STACKER:", stacker_hog.outputs["Output"].shape, stacker_hog.outputs["Output"].axistags
#print "allocating..."
#blahog = stacker_hog.outputs["Output"][:].allocate().wait()

#All features stacker
opMulti = operators.Op5ToMulti(g)
opMulti.inputs["Input0"].connect(stacker_opa.outputs["Output"])
opMulti.inputs["Input1"].connect(stacker_hog.outputs["Output"])

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
opPredict.inputs['Image'].connect(opMultiS.outputs['Outputs'])
#opPredict.inputs['Image'].connect(stacker.outputs['Output'])

classCountProvider = operators.OpArrayPiper(g)
classCountProvider.inputs["Input"].setValue(nclasses) 

opPredict.inputs['LabelsCount'].connect(classCountProvider.outputs["Output"])

#print "prediction output:", opPredict.outputs["PMaps"]
#Predict and save without context first
pmaps = opPredict.outputs["PMaps"][0][:].allocate().wait()[:]
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
#myPersonalEasyGraphNames["opa"] = opa
fgraph = h5py.File(graphfile,"w")
group = fgraph.create_group("graph")
group.dumpObject(myPersonalEasyGraphNames)
g.finalize()