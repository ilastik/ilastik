import vigra
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

#this test creates a graph for classifying two images (labels only on one)
#and saves it to a file. graph_load.py test then loads the graph and 
#tests that everything was saved correctly and the operators can be used again.


if __name__=="__main__":
    
    filenametrain='ostrich.jpg'
    filenametest ='ostrich_test1.jpg' 
    
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)
    
    listMerger = ListToMultiOperator(g)
    listMerger.inputs["List"].setValue([filenametrain, filenametest])
            
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
    
    
    ###################################
    #Merge the stuff together
    ##################################
    ########################################
    #########################################
    stacker=OpMultiArrayStacker(g)
    
    stacker.inputs["Images"].connectAdd(opa.outputs["Output"])
    
    #####Get the labels###
    filenamelabels='labels_ostrich.png'
    

    listMerger2 = ListToMultiOperator(g)
    listMerger2.inputs["List"].setValue([filenamelabels, None])

    labelsReader = OpImageReader(g)
    labelsReader.inputs["Filename"].connect(listMerger2.outputs["Items"])

    #######Training
    
    opTrain = OpTrainRandomForest(g)
    opTrain.inputs["fixClassifier"].setValue(False)
    opTrain.inputs['Labels'].connect(labelsReader.outputs["Image"])
    opTrain.inputs['Images'].connect(stacker.outputs["Output"])
    
    acache = OpArrayCache(g)
    acache.inputs["Input"].connect(opTrain.outputs['Classifier'])
    
    print "Here ########################", opTrain.outputs['Classifier'][:].allocate().wait()    
    
    ##################Prediction
    opPredict=OpPredictRandomForest(g)
    

    opPredict.inputs['Classifier'].connect(acache.outputs['Output'])    
    opPredict.inputs['Image'].connect(stacker.outputs['Output'])

    
    classCountProvider=OpArrayPiper(g)
    classCountProvider.inputs["Input"].setValue(2) 
    
    opPredict.inputs['LabelsCount'].connect(classCountProvider.outputs["Output"])
    
    vigra.impex.writeImage(opPredict.outputs["PMaps"][0][:].allocate().wait()[:,:,0],"images/test_ostrich_0.png")
    vigra.impex.writeImage(opPredict.outputs["PMaps"][1][:].allocate().wait()[:,:,0],"images/test_ostrich_1.png")
    
    myPersonalEasyGraphNames = {}
    
    myPersonalEasyGraphNames["listmulti"] = listMerger2
    myPersonalEasyGraphNames["reader"] = vimageReader
    myPersonalEasyGraphNames["graph"] = g
    myPersonalEasyGraphNames["train"] = opTrain
    myPersonalEasyGraphNames["cache"] = acache
    myPersonalEasyGraphNames["features"] = stacker
    myPersonalEasyGraphNames["predict"] = opPredict
    myPersonalEasyGraphNames["nclasses"] = classCountProvider
    myPersonalEasyGraphNames["labelReader"] = labelsReader
    
    import h5py
    f = h5py.File("graph_ostrich_gs_only.h5","w")
    
    group = f.create_group("graph")
    assert isinstance(classCountProvider.outputs["Output"].shape, tuple)
    group.dumpObject(myPersonalEasyGraphNames)
    
    g.finalize()  
    