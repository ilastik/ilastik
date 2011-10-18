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

#This file computes a lot of image features


sys.setrecursionlimit(10000)

fileraw = "/home/akreshuk/data/context/TEM_raw/50slices_down2.h5"
filelabels = "/home/akreshuk/data/context/TEM_labels/50slices_down2.h5"
resdir = "/home/akreshuk/data/context/TEM_results/"
resproject = "50slices_down2_templ_gaus_float.ilp"
graphfile = "/home/akreshuk/data/context/50slices_down2_graph_all.h5"
tempfile = "/home/akreshuk/data/context/50slices_down2_gaus_float_iter0.h5"
h5path = "/volume/data"
nclasses = 5

g = Graph()


#for blockwise final prediction
nxcut = 2
nycut = 2

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

#Same sigmas as in Classification Workflow"
#sigmas = [0.7, 1.0, 1.6, 3.5, 5]
sigmas = [3.5, 5]
opMulti = operators.Op50ToMulti(g)
count = 0
#Create all our favorite features with all sigmas, we have the space now
for sigma in sigmas:
    #Gaussian smoothing
    opa = operators.OpGaussianSmoothing(g)
    opa.inputs["Input"].connect(slicer.outputs["Slices"])
    opa.inputs["sigma"].setValue(sigma)
    stacker_opa = operators.OpMultiArrayStacker(g)
    stacker_opa.inputs["Images"].connect(opa.outputs["Output"])
    stacker_opa.inputs["AxisFlag"].setValue('z')
    stacker_opa.inputs["AxisIndex"].setValue(2)
    opMulti.inputs["Input%02d"%count].connect(stacker_opa.outputs["Output"])
    count +=1
    
    #Hessian eigenvalues
    #hog = operators.OpHessianOfGaussianEigenvalues(g)
    #hog.inputs["Input"].connect(slicer.outputs["Slices"])
    #hog.inputs["scale"].setValue(sigma)
    #stacker_hog = operators.OpMultiArrayStacker(g)
    #stacker_hog.inputs["Images"].connect(hog.outputs["Output"])
    #stacker_hog.inputs["AxisFlag"].setValue('z')
    #stacker_hog.inputs["AxisIndex"].setValue(2)
    
    #opMulti.inputs["Input%02d"%count].connect(stacker_hog.outputs["Output"])
    #count +=1
    
    ##Structure tensor eigenvalues
    #strten = operators.OpStructureTensorEigenvalues(g)
    #strten.inputs["Input"].connect(slicer.outputs["Slices"])
    #strten.inputs["innerScale"].setValue(sigma)
    #strten.inputs["outerScale"].setValue(0.5*sigma)
    #stacker_ten = operators.OpMultiArrayStacker(g)
    #stacker_ten.inputs["Images"].connect(strten.outputs["Output"])
    #stacker_ten.inputs["AxisFlag"].setValue('z')
    #stacker_ten.inputs["AxisIndex"].setValue(2)
    #opMulti.inputs["Input%02d"%count].connect(stacker_ten.outputs["Output"])
    #count +=1
    
    ##Laplacian
    #lap = operators.OpLaplacianOfGaussian(g)
    #lap.inputs["Input"].connect(slicer.outputs["Slices"])
    #lap.inputs["scale"].setValue(sigma)
    #stacker_lap = operators.OpMultiArrayStacker(g)
    #stacker_lap.inputs["Images"].connect(lap.outputs["Output"])
    #stacker_lap.inputs["AxisFlag"].setValue('z')
    #stacker_lap.inputs["AxisIndex"].setValue(2)
    #opMulti.inputs["Input%02d"%count].connect(stacker_lap.outputs["Output"])
    #count +=1
    
    ##Gradient Magnitude
    #opg = operators.OpGaussianGradientMagnitude(g)
    #opg.inputs["Input"].connect(slicer.outputs["Slices"])
    #opg.inputs["sigma"].setValue(sigma)
    #stacker_opg = operators.OpMultiArrayStacker(g)
    #stacker_opg.inputs["Images"].connect(opg.outputs["Output"])
    #stacker_opg.inputs["AxisFlag"].setValue('z')
    #stacker_opg.inputs["AxisIndex"].setValue(2)
    #opMulti.inputs["Input%02d"%count].connect(stacker_opg.outputs["Output"])
    #count +=1
    
    ##Diff of Gaussians
    #diff = operators.OpDifferenceOfGaussians(g)
    #diff.inputs["Input"].connect(slicer.outputs["Slices"])
    #diff.inputs["sigma0"].setValue(sigma)            
    #diff.inputs["sigma1"].setValue(sigma*0.66)
    #stacker_diff = operators.OpMultiArrayStacker(g)
    #stacker_diff.inputs["Images"].connect(diff.outputs["Output"])
    #stacker_diff.inputs["AxisFlag"].setValue('z')
    #stacker_diff.inputs["AxisIndex"].setValue(2)
    #opMulti.inputs["Input%02d"%count].connect(stacker_diff.outputs["Output"])
    #count +=1
    

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
labels = numpy.array(f[h5path]).astype(numpy.uint8)
labels = labels.reshape(labels.shape + (1,))
labelsva = vigra.VigraArray(labels, axistags=vigra.VigraArray.defaultAxistags(4))

#make a dummy labeler to use its blocks and sparsity
opLabeler = operators.OpBlockedSparseLabelArray(g)
opLabeler.inputs["shape"].setValue(labelsva.shape)
opLabeler.inputs["blockShape"].setValue((64, 64, 1, 1))
opLabeler.inputs["eraser"].setValue(100)
#find the labeled slices, slow and baaad
lpixels = numpy.nonzero(labels)
luns = numpy.unique(lpixels[2])
for z in luns:
    #We kind of assume the last slice is not labeled here.
    #But who would label the last slice???
    assert z!=labels.shape[2]-1
    zslice = labels[:, :, z:z+1, :]
    print "setting labels in slice:", z
    key = (slice(None, None, None), slice(None, None, None), slice(z, z+1, None), slice(None, None, None))
    opLabeler.setInSlot(opLabeler.inputs["Input"], key, zslice)
    
#because opTrain has a MultiInputSlot only
opMultiL = operators.Op5ToMulti(g)
opMultiL.inputs["Input0"].connect(opLabeler.outputs["Output"])

opMultiLblocks = operators.Op5ToMulti(g)
opMultiLblocks.inputs["Input0"].connect(opLabeler.outputs["nonzeroBlocks"])


featurecache = operators.OpBlockedArrayCache(g)
featurecache.inputs["innerBlockShape"].setValue((8,8,8,180))
featurecache.inputs["outerBlockShape"].setValue((64,64,64,180))
featurecache.inputs["Input"].connect(stacker.outputs["Output"])
featurecache.inputs["fixAtCurrent"].setValue(False)  

opMultiS = operators.Op5ToMulti(g)
opMultiS.inputs["Input0"].connect(featurecache.outputs["Output"])

print "opMultiS outputs shape:", opMultiS.outputs["Outputs"][0].shape

#Training
opTrain = operators.OpTrainRandomForestBlocked(g)
opTrain.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
opTrain.inputs['Images'].connect(opMultiS.outputs["Outputs"])
opTrain.inputs['fixClassifier'].setValue(False)
opTrain.inputs['nonzeroLabelBlocks'].connect(opMultiLblocks.outputs["Outputs"])

acache = operators.OpArrayCache(g)
acache.inputs["Input"].connect(opTrain.outputs['Classifier'])

print "Here ########################", opTrain.outputs['Classifier'][:].allocate().wait()    
print
print "++++++++++++++ Trained ++++++++++++++++++++++"
print
#import sys
#sys.exit(1)
#Prediction
opPredict = operators.OpPredictRandomForest(g)
opPredict.inputs['Classifier'].connect(acache.outputs['Output'])    
#opPredict.inputs['Image'].connect(opMultiS.outputs['Outputs'])
opPredict.inputs['Image'].connect(stacker.outputs['Output'])

classCountProvider = operators.OpArrayPiper(g)
classCountProvider.inputs["Input"].setValue(nclasses) 

opPredict.inputs['LabelsCount'].setValue(nclasses)

#print "prediction output:", opPredict.outputs["PMaps"]
#Predict and save without context first
#pmaps = opPredict.outputs["PMaps"][:].allocate().wait()[:]
#print "shape of pmaps: ", pmaps.shape
#for i in range(pmaps.shape[2]):
    #for c in range(nclasses):
        ##print i, c
        #pmap = pmaps[:, :, i, c]
        #vigra.impex.writeImage(pmap, resdir + "slice00" + str(i) + "_class_" + str(c) + ".tif")


size = opPredict.outputs["PMaps"].shape
xmin = [i*size[0]/nxcut for i in range(nxcut)]
ymin = [i*size[1]/nycut for i in range(nycut)]
xmax = [i*size[0]/nxcut for i in range(1, nxcut+1)]
ymax = [i*size[1]/nycut for i in range(1, nycut+1)]

print size
print xmin, ymin, xmax, ymax
pmaps = numpy.zeros(size, dtype=numpy.float32)
oldfeatures = numpy.zeros(featurecache.outputs["Output"].shape, dtype=numpy.float32)
for i, x in enumerate(xmin):
    for j, y in enumerate(ymin):
        print "processing part ", i, j
        featurepart = featurecache.outputs["Output"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
        print "features for part done"
        pmapspart = opPredict.outputs["PMaps"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
        print "predictions for part done"
        pmaps[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = pmapspart[:]
        oldfeatures[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :]=featurepart[:]
        #print numpy.min(pmaps), numpy.max(pmaps), numpy.max(pmapspart)
        #print numpy.min(oldfeatures), numpy.max(oldfeatures)
       



print "Prediction done!"
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

print "old ilastik project done!"

#save the predictions, features and labels for later on
temp = h5py.File(tempfile, "w")
temp.create_dataset("/volume/pmaps", data = pmaps, compression='gzip')
temp.create_dataset("/volume/labels", data = labels, compression='gzip')
temp.create_dataset("/volume/features", data=oldfeatures, compression='gzip')
temp.close()

#save the graph to work with context in a different script
#myPersonalEasyGraphNames = {}

#myPersonalEasyGraphNames["graph"] = g
#myPersonalEasyGraphNames["train"] = opTrain
#myPersonalEasyGraphNames["cache"] = acache
#myPersonalEasyGraphNames["features"] = stacker
#myPersonalEasyGraphNames["predict"] = opPredict
#myPersonalEasyGraphNames["nclasses"] = classCountProvider
#myPersonalEasyGraphNames["opMultiL"] = opMultiL
#myPersonalEasyGraphNames["labels"] = labelsva
#myPersonalEasyGraphNames["slicer"] = slicer
##myPersonalEasyGraphNames["opa"] = opa
#fgraph = h5py.File(graphfile,"w")
#group = fgraph.create_group("graph")
#group.dumpObject(myPersonalEasyGraphNames)
#g.finalize()