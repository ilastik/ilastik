import numpy
import context
import vigra
import os
import glob
import sys
import h5py
import gc


import threading
from lazyflow.graph import *
import copy

from lazyflow import operators

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

#import guppy
#from guppy import hpy
#hp = hpy()

#graphfile = "/home/akreshuk/data/context/50slices_down2_graph_1.h5"
outputfile = "/home/akreshuk/data/context/TEM_results/50slices_down2_templ.ilp"
outfilenew = "/home/akreshuk/data/context/TEM_results/50slices_down2_hist_i1.ilp"

tempfile = "/home/akreshuk/data/context/50slices_down2_hist_temp_iter0.h5"
tempfilenew = "/home/akreshuk/data/context/50slices_down2_hist_temp_iter1.h5"

#numIter = 4

#for blockwise final prediction
nxcut = 3
nycut = 3

sys.setrecursionlimit(10000)
#g = Graph(numThreads = 1, softMaxMem = 18000*1024**2)
g = Graph()

f = h5py.File(tempfile)
pmaps = numpy.array(f["/volume/pmaps"])
pmapsva = vigra.VigraArray(pmaps, axistags=vigra.VigraArray.defaultAxistags(4))
pmapsva = pmapsva/255.
labels = numpy.array(f["/volume/labels"]).astype(numpy.uint8)
labelsva = vigra.VigraArray(labels, axistags=vigra.VigraArray.defaultAxistags(4))
oldfeatures = numpy.array(f["/volume/features"])
featuresva = vigra.VigraArray(oldfeatures, axistags=vigra.VigraArray.defaultAxistags(4))

print "READ FROM FILE, PMAPS:", pmapsva.shape, "LABELS:", labelsva.shape, "FEATURES:", featuresva.shape

pmapslicer = operators.OpMultiArraySlicer(g)
pmapslicer.inputs["Input"].setValue(pmapsva)
pmapslicer.inputs["AxisFlag"].setValue('z')

#contOpAv = operators.OpVarianceContext2D(g)
#contOpAv.inputs["PMaps"].connect(pmapslicer.outputs["Slices"])
#contOpAv.inputs["Radii"].setValue([1, 3, 5, 10, 15, 20])
#contOpAv.inputs["ClassesCount"].setValue(pmaps.shape[-1])

contOpHist = operators.OpContextHistogram(g)
contOpHist.inputs["PMaps"].connect(pmapslicer.outputs["Slices"])
contOpHist.inputs["Radii"].setValue([1, 3, 5, 10, 15, 20])
contOpHist.inputs["LabelsCount"].setValue(pmaps.shape[-1])
contOpHist.inputs["BinsCount"].setValue(5)


stacker_cont = operators.OpMultiArrayStacker(g)
#stacker_cont.inputs["Images"].connect(contOpAv.outputs["Output"])
stacker_cont.inputs["Images"].connect(contOpHist.outputs["Output"])
stacker_cont.inputs["AxisFlag"].setValue('z')
stacker_cont.inputs["AxisIndex"].setValue(2)

print "Stacker context output shape:", stacker_cont.outputs["Output"].shape

#combine the image and context features
opMultiS = operators.Op5ToMulti(g)
opMultiS.inputs["Input0"].setValue(featuresva)
opMultiS.inputs["Input1"].connect(stacker_cont.outputs["Output"])

stacker2 = operators.OpMultiArrayStacker(g)
stacker2.inputs["AxisFlag"].setValue('c')
stacker2.inputs["AxisIndex"].setValue(3)
stacker2.inputs["Images"].connect(opMultiS.outputs["Outputs"])

#Let's cache the stacker, it's used both in training and in prediction
#featurecache2 = operators.OpArrayCache(g)
#featurecache2.inputs["Input"].connect(stacker2.outputs["Output"])
#featurecache2.inputs["blockShape"].setValue((64, 64, 1, 180))

featurecache2 = operators.OpBlockedArrayCache(g)
featurecache2.inputs["innerBlockShape"].setValue((8,8,8,180))
featurecache2.inputs["outerBlockShape"].setValue((64,64,64,180))
featurecache2.inputs["Input"].connect(stacker2.outputs["Output"])
featurecache2.inputs["fixAtCurrent"].setValue(False)  


#wrap the features, because opTrain has a multi input slot
opMultiTr = operators.Op5ToMulti(g)
opMultiTr.inputs["Input0"].connect(featurecache2.outputs["Output"])

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
    

#opMultiL = operators.Op5ToMulti(g)
#opMultiL.inputs["Input0"].setValue(labelsva)
opMultiL = operators.Op5ToMulti(g)    
opMultiL.inputs["Input0"].connect(opLabeler.outputs["Output"])

opMultiLblocks = operators.Op5ToMulti(g)
opMultiLblocks.inputs["Input0"].connect(opLabeler.outputs["nonzeroBlocks"])


opTrain2 = operators.OpTrainRandomForestBlocked(g)
opTrain2.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
opTrain2.inputs['Images'].connect(opMultiTr.outputs["Outputs"])
opTrain2.inputs['fixClassifier'].setValue(False)
opTrain2.inputs['nonzeroLabelBlocks'].connect(opMultiLblocks.outputs["Outputs"])

acache2 = operators.OpArrayCache(g)
acache2.inputs["Input"].connect(opTrain2.outputs['Classifier'])

opPredict2=operators.OpPredictRandomForest(g)
opPredict2.inputs['Classifier'].connect(acache2.outputs['Output'])
opPredict2.inputs['Image'].connect(featurecache2.outputs["Output"])
opPredict2.inputs['LabelsCount'].setValue(pmaps.shape[-1])

size = pmaps.shape
xmin = [i*size[0]/nxcut for i in range(nxcut)]
ymin = [i*size[1]/nycut for i in range(nycut)]
xmax = [i*size[0]/nxcut for i in range(1, nxcut+1)]
ymax = [i*size[1]/nycut for i in range(1, nycut+1)]

print size
print xmin, ymin, xmax, ymax
pmaps2 = numpy.zeros(size)
for i, x in enumerate(xmin):
    for j, y in enumerate(ymin):
        print "processing part ", i, j
        pmapspart = opPredict2.outputs["PMaps"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
        pmaps2[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = pmapspart[:]
    
#pmaps2 = opPredict2.outputs["PMaps"][0:20, 0:20, 0:20, :].allocate().wait()
print "prediction done"
print pmaps2.shape

#import sys
#sys.exit(1)

#opPredict2.outputs["PMaps"][:].writeInto(pmaps).wait()
#save into an old ilastik project for easy visualization
import shutil
#fName, fExt = os.path.splitext(outputfile)
#outfilenew = fName + "_" + str(numStage) + ".ilp"
shutil.copy2(outputfile, outfilenew)

outfile = h5py.File(outfilenew, "r+")
predfile = outfile["/DataSets/dataItem00/prediction"]
nx = pmaps2.shape[0]
ny = pmaps2.shape[1]
nz = pmaps2.shape[2]
nclasses = pmaps2.shape[3]
predfile[:] = pmaps2.reshape((1, nx, ny, nz, nclasses))[:]
labelsfile = outfile["/DataSets/dataItem00/labels/data"]
labelsfile[:] = labels.reshape((1, nx, ny, nz, 1))[:]
outfile.close()


temp = h5py.File(tempfilenew, "w")
temp.create_dataset("/volume/pmaps", data = pmaps2)
temp.create_dataset("/volume/labels", data = labels)
temp.create_dataset("/volume/features", data=oldfeatures)
temp.close()

