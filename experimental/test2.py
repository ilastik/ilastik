import context
import vigra
import os
import glob
import shutil

import threading
from lazyflow.graph import *
import copy

from lazyflow.operators.operators import OpArrayPiper 
from lazyflow.operators.vigraOperators import *
from lazyflow.operators.valueProviders import *
from lazyflow.operators.classifierOperators import *
from lazyflow.operators.generic import *

from lazyflow.operators import OpStarContext2D
from lazyflow.operators import OpAverageContext2D


tempfolder = "/home/akreshuk/data/Luca/temprawdata"
tempfolder1 = "/home/akreshuk/data/Luca/templabels"
resfolder = "/home/akreshuk/data/Luca/tempresults"

files = glob.glob(tempfolder + '/*.tiff')
files = sorted(files, key=str.lower)
ntraining = 1
trainfiles = files[0:ntraining]

g = Graph(numThreads = 8, softMaxMem = 2000*1024**2)

listMerger = ListToMultiOperator(g)
listMerger.inputs["List"].setValue(trainfiles)
        
vimageReader = OpImageReader(g)
#vimageReader.inputs["Filename"].setValue(filename)
vimageReader.inputs["Filename"].connect(listMerger.outputs["Items"])

#Sigma provider 0.9
sigmaProvider = OpArrayPiper(g)
sigmaProvider.inputs["Input"].setValue(0.9) 

#Gaussian Smoothing     
opa = OpGaussianSmoothing(g)   
opa.inputs["Input"].connect(vimageReader.outputs["Image"])
opa.inputs["sigma"].connect(sigmaProvider.outputs["Output"])

stacker=OpMultiArrayStacker(g)

stacker.inputs["Images"].connectAdd(opa.outputs["Output"])

#####Get the labels###
filenamelabels = glob.glob(tempfolder1 + '/*.tiff')
trainlabels = sorted(files, key=str.lower)
#filenamelabels=os.listdir(tempfolder1)
trainlabels = filenamelabels[0:ntraining]

listMerger2 = ListToMultiOperator(g)
listMerger2.inputs["List"].setValue(trainlabels)

labelsReader = OpImageReader(g)
labelsReader.inputs["Filename"].connect(listMerger2.outputs["Items"])

#######Training

opTrain = OpTrainRandomForest(g)
opTrain.inputs["fixClassifier"].setValue(False)
opTrain.inputs['Labels'].connect(labelsReader.outputs["Image"])
opTrain.inputs['Images'].connect(stacker.outputs["Output"])

acache = OpArrayCache(g)
acache.inputs["Input"].connect(opTrain.outputs['Classifier'])



filespredict = files[ntraining:2*ntraining]
listMerger3 = ListToMultiOperator(g)
listMerger3.inputs["List"].setValue(filespredict)

vimageReader3 = OpImageReader(g)
vimageReader3.inputs["Filename"].connect(listMerger3.outputs["Items"])
#Gaussian Smoothing     
opa3 = OpGaussianSmoothing(g)   
opa3.inputs["Input"].connect(vimageReader3.outputs["Image"])
opa3.inputs["sigma"].connect(sigmaProvider.outputs["Output"])

stacker3=OpMultiArrayStacker(g)

stacker3.inputs["Images"].connectAdd(opa3.outputs["Output"])


##################Prediction
opPredict=OpPredictRandomForest(g)


classCountProvider=OpArrayPiper(g)
classCountProvider.inputs["Input"].setValue(2) 
opPredict.inputs['LabelsCount'].connect(classCountProvider.outputs["Output"])

opPredict.inputs['Classifier'].connect(acache.outputs['Output'])    
opPredict.inputs['Image'].connect(stacker3.outputs['Output'])

print "Here ########################", opTrain.outputs['Classifier'][:].allocate().wait()    

for i, p in enumerate(opPredict.outputs["PMaps"][:]):
    fname = os.path.split(trainlabels[i])
    print resfolder + "/" + fname[1]
    bla=p[:].allocate().wait()[:, :, 0]
    
    vigra.impex.writeImage(bla, resfolder + "/" + fname[1])

