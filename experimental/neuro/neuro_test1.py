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

#This script only computes a couple of image features

fileraw = "/home/akreshuk/data/context/TEM_raw/50slices_down2.h5"
filelabels = "/home/akreshuk/data/context/TEM_labels/50slices_down2.h5"
resdir = "/home/akreshuk/data/context/TEM_results/"
resproject = "50slices_down2_templ.ilp"
graphfile = "/home/akreshuk/data/context/50slices_down2_graph_1.h5"
h5path = "/volume/data"
tempfile = "/home/akreshuk/data/context/50slices_down2_hist_temp_iter0.h5"
nclasses = 5

g = Graph()

axistags=vigra.AxisTags(vigra.AxisInfo('x',vigra.AxisType.Space),vigra.AxisInfo('y',vigra.AxisType.Space), vigra.AxisInfo('z',vigra.AxisType.Space))  

import h5py
f = h5py.File(fileraw)
stack = numpy.array(f[h5path])
stack = stack.reshape(stack.shape + (1,))
stackva = vigra.VigraArray(stack, axistags=vigra.VigraArray.defaultAxistags(4))

#Slice the stack in z
slicer = operators.OpMultiArraySlicer(g)
#slicer.inputs["Input"].connect(himage.outputs["Image"])
slicer.inputs["Input"].setValue(stackva)
slicer.inputs["AxisFlag"].setValue('z')

print "THE SLICER:", slicer.outputs["Slices"][0].shape

#Gaussian Smoothing     
sigma1 = 0.9
opa = operators.OpGaussianSmoothing(g)   
opa.inputs["Input"].connect(slicer.outputs["Slices"])
opa.inputs["sigma"].setValue(sigma1)

print "GAUSSIAN SMOOTHING:", opa.outputs["Output"][0].shape
#print "one by one"
#blagaus = opa.outputs["Output"][0][:].allocate().wait()

#Gaussian stacker
stacker_opa = operators.OpMultiArrayStacker(g)
stacker_opa.inputs["Images"].connect(opa.outputs["Output"])
stacker_opa.inputs["AxisFlag"].setValue('z')
stacker_opa.inputs["AxisIndex"].setValue(2)

#stacker_opa.outputs["Output"]._axistags = axistags
print "THE GAUSSIAN STACKER:", stacker_opa.outputs["Output"].shape, stacker_opa.outputs["Output"].axistags
#print "allocating..."
#blaopa = stacker_opa.outputs["Output"][:].allocate().wait()


#Hessian
sigma2 = 0.7
hog = operators.OpHessianOfGaussianEigenvalues(g)
hog.inputs["Input"].connect(slicer.outputs["Slices"])
hog.inputs["scale"].setValue(sigma2)
#Hessian stacker
stacker_hog = operators.OpMultiArrayStacker(g)
stacker_hog.inputs["Images"].connect(hog.outputs["Output"])
stacker_hog.inputs["AxisFlag"].setValue('z')
stacker_hog.inputs["AxisIndex"].setValue(2)

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

#cache the features
featurecache = operators.OpArrayCache(g)
featurecache.inputs["Input"].connect(stacker.outputs["Output"])

#allocate all to save into a file
oldfeatures = featurecache.outputs["Output"][:].allocate().wait()

#because opTrain has a MultiInputSlot only
opMultiL = operators.Op5ToMulti(g)
opMultiL.inputs["Input0"].setValue(labelsva)

opMultiS = operators.Op5ToMulti(g)
#opMultiS.inputs["Input0"].connect(stacker.outputs["Output"])
opMultiS.inputs["Input0"].connect(featurecache.outputs["Output"])

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
#opPredict.inputs['Image'].connect(stacker.outputs['Output'])
opPredict.inputs['Image'].connect(featurecache.outputs['Output'])

classCountProvider = operators.OpArrayPiper(g)
classCountProvider.inputs["Input"].setValue(nclasses) 

opPredict.inputs['LabelsCount'].setValue(nclasses)

#print "prediction output:", opPredict.outputs["PMaps"]
#Predict and save without context first
pmaps = opPredict.outputs["PMaps"][:].allocate().wait()[:]
print "+++++++++++++++ Predicted +++++++++++++++", "shape of pmaps: ", pmaps.shape, pmaps.dtype
print "min and max of prediction:", numpy.min(pmaps), numpy.max(pmaps)
#for i in range(pmaps.shape[2]):
    #for c in range(nclasses):
        ##print i, c
        #pmap = pmaps[:, :, i, c]
        #vigra.impex.writeImage(pmap, resdir + "slice00" + str(i) + "_class_" + str(c) + ".tif")

#save into an old ilastik project for easy visualization
#outfile = h5py.File(resdir+resproject, "r+")
#predfile = outfile["/DataSets/dataItem00/prediction"]
#nx = pmaps.shape[0]
#ny = pmaps.shape[1]
#nz = pmaps.shape[2]
#predfile[:] = pmaps.reshape((1, nx, ny, nz, nclasses))[:]
#labelsfile = outfile["/DataSets/dataItem00/labels/data"]
#labelsfile[:] = labels.reshape((1, nx, ny, nz, 1))[:]
#outfile.close()

print "old ilastik project saved"

temp = h5py.File(tempfile, "w")
temp.create_dataset("/volume/pmaps", data = pmaps)
temp.create_dataset("/volume/labels", data = labels)
temp.create_dataset("/volume/features", data=oldfeatures)
temp.close()

#save the graph to work with context in a different script
#FIXME: something got broken in graph saving, don't use for now
#myPersonalEasyGraphNames = {}

#myPersonalEasyGraphNames["graph"] = g
#myPersonalEasyGraphNames["train"] = opTrain
#myPersonalEasyGraphNames["cache"] = acache
#myPersonalEasyGraphNames["features"] = stacker
#myPersonalEasyGraphNames["featurecache"] = featurecache
#myPersonalEasyGraphNames["predict"] = opPredict
#myPersonalEasyGraphNames["nclasses"] = classCountProvider
#myPersonalEasyGraphNames["opMultiL"] = opMultiL
#myPersonalEasyGraphNames["labels"] = labelsva
##myPersonalEasyGraphNames["stacker_opa"] = stacker_opa
##myPersonalEasyGraphNames["stacker_hog"] = stacker_hog
##myPersonalEasyGraphNames["opMulti"] = opMulti
##myPersonalEasyGraphNames["slicer"] = slicer
##myPersonalEasyGraphNames["opa"] = opa
##myPersonalEasyGraphNames["hog"] = hog
##myPersonalEasyGraphNames["opa"] = opa
#fgraph = h5py.File(graphfile,"w")
#group = fgraph.create_group("graph")
#group.dumpObject(myPersonalEasyGraphNames)
#g.finalize()