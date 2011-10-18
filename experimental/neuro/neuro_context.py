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

import guppy
from guppy import hpy
hp = hpy()

graphfile = "/home/akreshuk/data/context/50slices_down2_graph_1.h5"
outputfile = "/home/akreshuk/data/context/TEM_results/50slices_down2_templ.ilp"
tempfile = "/home/akreshuk/data/context/50slices_down2_hist_temp_iter1.h5"

numIter = 1

sys.setrecursionlimit(10000)

f = h5py.File(graphfile)
group = f["graph"]

myPersonalEasyGraphNames = group.reconstructObject()

g = myPersonalEasyGraphNames["graph"]
opTrain = myPersonalEasyGraphNames["train"]
opPredict = myPersonalEasyGraphNames["predict"]
classCountProvider = myPersonalEasyGraphNames["nclasses"]
#slicer = myPersonalEasyGraphNames["slicer"]
stacker = myPersonalEasyGraphNames["features"]
opMultiL = myPersonalEasyGraphNames["opMultiL"]
labels = myPersonalEasyGraphNames["labels"]
featurecache = myPersonalEasyGraphNames["featurecache"]

g.maxMem = 18000*1024**2


#opTrain.inputs["fixClassifier"].setValue(True)
#acache = operators.OpArrayCache(g)
#acache.inputs["Input"].connect(opTrain.outputs['Classifier'])

print "file read"
#Allocate the previous predictions - we have to connect the context to something
oldfeatures = featurecache.outputs["Output"][:].allocate().wait()
pmaps = opPredict.outputs["PMaps"][:].allocate().wait()

print "old predictions computed"

#classifiers = [acache]
#contexts3D = []
#contexts2D = []
#predictions=[opPredict]
#prevPredict = opPredict


#3D-----------------------------
#contOp = operators.OpContextStar3D(g)
#radii_triplets = numpy.zeros((3, 3), dtype = numpy.uint32)
#radii_triplets[0,:] = [1,1,1]
#radii_triplets[1,:] = [5,5,1]
#radii_triplets[2,:] = [10,10,1]
#contOp.inputs["Radii_triplets"].setValue(radii_triplets)
#contOp.inputs["ClassesCount"].connect(classCountProvider.outputs["Output"])
#contOp.inputs["PMaps"].connect(opPredict.outputs["PMaps"])

#2D-----------------------------



print "=============================================="
#import sys
#sys.exit(1)

print hp.heap()


for numStage in range(0,numIter):
    gc.collect()
    print
    print "in the loop"
    print "iteration ", numStage
    print
    print hp.heap()
    contOpAv = operators.OpContextHistogram(g)

    pmapslicer = operators.OpMultiArraySlicer(g)
    #pmapslicer.inputs["Input"].connect(prevPredict.outputs["PMaps"])
    pmapslicer.inputs["Input"].setValue(pmaps)
    pmapslicer.inputs["AxisFlag"].setValue('z')

    contOpAv.inputs["PMaps"].connect(pmapslicer.outputs["Slices"])
    contOpAv.inputs["Radii"].setValue([1, 3, 5, 10, 15, 20])
    contOpAv.inputs["LabelsCount"].connect(classCountProvider.outputs["Output"])
    contOpAv.inputs["BinsCount"].setValue(5)

    stacker_cont = operators.OpMultiArrayStacker(g)
    stacker_cont.inputs["Images"].connect(contOpAv.outputs["Output"])
    #stacker_cont.inputs["Images"].connect(tempcache.outputs["Output"])
    stacker_cont.inputs["AxisFlag"].setValue('z')
    stacker_cont.inputs["AxisIndex"].setValue(2)
    #contexts2D.append(stacker_cont)
    
    opMultiS = operators.Op5ToMulti(g)
    opMultiS.inputs["Input0"].connect(featurecache.outputs["Output"])
    
    stacker2 = operators.OpMultiArrayStacker(g)
    stacker2.inputs["AxisFlag"].setValue('c')
    stacker2.inputs["AxisIndex"].setValue(3)
    
    #if len(contexts3D)>0:
        #opMulti2 = operators.Op5ToMulti(g)
        #opMulti2.inputs["Input0"].connect(opMultiS.outputs["Outputs"])
        #opMulti2.inputs["Input1"].connect(contexts3D[-1].outputs["Output"])
        #stacker2.inputs["Images"].connect(opMulti2.outputs["Outputs"])
    #else:
    #opMultiS.inputs["Input1"].connect(contexts2D[-1].outputs["Output"])
    opMultiS.inputs["Input1"].connect(stacker_cont.outputs["Output"])
    stacker2.inputs["Images"].connect(opMultiS.outputs["Outputs"])
    
    featurecache2 = operators.OpArrayCache(g)
    featurecache2.inputs["Input"].connect(stacker2.outputs["Output"])
    
    opMultiTr = operators.Op5ToMulti(g)
    opMultiTr.inputs["Input0"].connect(featurecache2.outputs["Output"])
    
    opTrain2 = operators.OpTrainRandomForest(g)
    opTrain2.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
    opTrain2.inputs['Images'].connect(opMultiTr.outputs["Outputs"])
    opTrain2.inputs['fixClassifier'].setValue(False)
    
    acache2 = operators.OpArrayCache(g)
    acache2.inputs["Input"].connect(opTrain2.outputs['Classifier'])

    opPredict2=operators.OpPredictRandomForest(g)
    opPredict2.inputs['Classifier'].connect(acache2.outputs['Output'])
    opPredict2.inputs['Image'].connect(featurecache2.outputs["Output"])
    opPredict2.inputs['LabelsCount'].connect(classCountProvider.outputs["Output"])
    
    #pmaps = opPredict2.outputs["PMaps"][:].allocate().wait()
    opPredict2.outputs["PMaps"][:].writeInto(pmaps).wait()
    #save into an old ilastik project for easy visualization
    import shutil
    fName, fExt = os.path.splitext(outputfile)
    outfilenew = fName + "_hist_" + str(numStage+1) + ".ilp"
    shutil.copy2(outputfile, outfilenew)
    
    outfile = h5py.File(outfilenew, "r+")
    predfile = outfile["/DataSets/dataItem00/prediction"]
    nx = pmaps.shape[0]
    ny = pmaps.shape[1]
    nz = pmaps.shape[2]
    nclasses = pmaps.shape[3]
    predfile[:] = pmaps.reshape((1, nx, ny, nz, nclasses))[:]
    labelsfile = outfile["/DataSets/dataItem00/labels/data"]
    labelsfile[:] = labels.reshape((1, nx, ny, nz, 1))[:]
    outfile.close()
    
    
    temp = h5py.File(tempfile, "w")
    temp.create_dataset("/volume/pmaps", data = pmaps)
    temp.create_dataset("/volume/labels", data = labels)
    temp.create_dataset("/volume/features", data=oldfeatures)
    temp.close()
    
    
    #contOp2=operators.OpContextStar3D(g)
    #contOp2.inputs["Radii_triplets"].setValue(radii_triplets)
    #contOp2.inputs["PMaps"].connect(predictions[-1].outputs["PMaps"])
    #contOp2.inputs["ClassesCount"].connect(classCountProvider.outputs["Output"])
    
    #contexts.append(contOp2)
    #contOpAv2 = operators.OpVarianceContext2D(g)
    ##Slicer
    #pmapslicer2 = operators.OpMultiArraySlicer(g)
    #pmapslicer2.inputs["Input"].connect(opPredict2.outputs["PMaps"])
    #pmapslicer2.inputs["AxisFlag"].setValue('z')
    
    #contOpAv2.inputs["PMaps"].connect(pmapslicer2.outputs["Slices"])
    #contOpAv2.inputs["Radii"].setValue([1, 3, 5, 10, 15, 20])
    #contOpAv2.inputs["ClassesCount"].connect(classCountProvider.outputs["Output"])
    
    #stacker_cont2 = operators.OpMultiArrayStacker(g)
    #stacker_cont2.inputs["Images"].connect(contOpAv2.outputs["Output"])
    #stacker_cont2.inputs["AxisFlag"].setValue('z')
    #stacker_cont2.inputs["AxisIndex"].setValue(2)
    #contexts2D.append(stacker_cont2)
    
    

    #for i, pmap in enumerate(predictions[-1].outputs["PMaps"]):
        #print "IMAGE ", i
        #res = predictions[-1].outputs["PMaps"][i][:].allocate().wait()
        #vigra.impex.writeImage(res[:,:,0],"images/testload_" + str(numStage) + "_" + str(i+2) + ".png")


g.finalize()


