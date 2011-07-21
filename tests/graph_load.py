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

#this is the second part of graph_save.py test. It loads the graph elements, saved
#in graph_save.py, attaches a context operator to them and processes the images.

if __name__=="__main__":
    import h5py

    f = h5py.File("graph_ostrich_gs_only.h5")
    group = f["graph"]

    myPersonalEasyGraphNames = group.reconstructObject()

    g = myPersonalEasyGraphNames["graph"]
    opTrain = myPersonalEasyGraphNames["train"]
    opPredict = myPersonalEasyGraphNames["predict"]
    classCountProvider = myPersonalEasyGraphNames["nclasses"]
    stacker = myPersonalEasyGraphNames["features"]
    labelReader = myPersonalEasyGraphNames["labelReader"]
    imageReader = myPersonalEasyGraphNames["reader"]
    opa = myPersonalEasyGraphNames["opa"]
    
    opTrain.inputs["fixClassifier"].setValue(True)
    acache = OpArrayCache(g)
    acache.inputs["Input"].connect(opTrain.outputs['Classifier'])
    
    #add our stuff
    contOp=OpAverageContext2D(g)
    contOp.inputs["Radii"].setValue([2,5,10, 12, 15, 20, 25, 30, 35, 40])
    contOp.inputs["ClassesCount"].connect(classCountProvider.outputs["Output"])
    contOp.inputs["PMaps"].connect(opPredict.outputs["PMaps"])



    #connect new images
    filenametest2 ='ostrich_test2.jpg'
    filenametest3 ='ostrich_test3.jpg' 
    filekiller = 'killer_ostrich.jpg'
    
    listMerger = ListToMultiOperator(g)
    #listMerger.inputs["List"].setValue([filenametest2, filenametest3,filekiller])
    listMerger.inputs["List"].setValue([filekiller])
            
            
            
    print "----------", classCountProvider.inputs["Input"].shape

    print "///////////////////0", opa.outputs["Output"][0].shape
    #print "///////////////////1", opa.outputs["Output"][1].shape


    imageReader.inputs["Filename"].connect(listMerger.outputs["Items"])
    #imageReader.inputs["Filename"].disconnect()
    #imageReader.inputs["Filename"].setValue(filekiller)
    
    print "////////////////0", imageReader.outputs["Image"][0].shape
    #print "////////////////1", imageReader.outputs["Image"][1].shape
    
    print "///////////////////0", opa.outputs["Output"][0].shape
    #print "///////////////////1", opa.outputs["Output"][1].shape


    print "////////////////////0", stacker.inputs["Images"][0][0].shape
    #print "////////////////////1", stacker.inputs["Images"][1][0].shape


    print "////////////////////0", stacker.outputs["Output"][0].shape
    #print "////////////////////1", stacker.outputs["Output"][1].shape

    print "//////////////////////////////0", opPredict.outputs["PMaps"][0].shape
    #print "//////////////////////////////1", opPredict.outputs["PMaps"][1].shape
    print "/////////////////////////////////0", contOp.outputs["Output"][0].shape
    #print "/////////////////////////////////1", contOp.outputs["Output"][1].shape
    #print "/////////////////////////////////2", contOp.outputs["Output"][2].shape
    #sys.exit(1)

    print opPredict.outputs["PMaps"][0][:].allocate().wait()[:,:,0]
    

    #vigra.impex.writeImage(opPredict.outputs["PMaps"][0][:].allocate().wait()[:,:,0],"images/testload_ostrich_2.png")
    #vigra.impex.writeImage(opPredict.outputs["PMaps"][1][:].allocate().wait()[:,:,0],"images/testload_ostrich_3.png")
    vigra.impex.writeImage(opPredict.outputs["PMaps"][0][:].allocate().wait()[:,:,0],"images/testload_killer_ostrich.png")

    print "#####################", len(imageReader.outputs["Image"])
    print "#####################", len(opa.outputs["Output"])
    print "#####################", len(stacker.outputs["Output"])
    print "#####################", len(opPredict.outputs["PMaps"])

    

    classifiers = [acache]
    contexts = [contOp]
    predictions=[opPredict]

    print "==============================================",stacker.outputs["Output"][0].shape

    #for numStage in range(0,3):
        
        #stacker2=OpMultiArrayStacker(g)
        
        #stacker2.inputs["Images"].connectAdd(stacker.outputs["Output"])
        #print "==============================================",stacker.outputs["Output"][0].shape
        #stacker2.inputs["Images"].connectAdd(contexts[-1].outputs["Output"])
        #print "==============================================",stacker.outputs["Output"][0].shape
        
        ########Training2
        
        #opTrain2 = OpTrainRandomForest(g)
        #opTrain2.inputs['Labels'].connect(labelReader.outputs["Image"])
        #opTrain2.inputs['Images'].connect(stacker2.outputs["Output"])
        #opTrain2.inputs['fixClassifier'].setValue(False)
        
        ##print "Here ########################", opTrain.outputs['Classifier'][:].allocate().wait()    
        
        ###################Prediction
        #opPredict2=OpPredictRandomForest(g)
        
        #acache2 = OpArrayCache(g)
        #acache2.inputs["Input"].connect(opTrain2.outputs['Classifier'])
        
        
        
        #classifiers.append(acache2)
        #classifiers.append(acache2)
        #opPredict2.inputs['Classifier'].connect(acache2.outputs['Output'])
            
        
        #opPredict2.inputs['Image'].connect(stacker2.outputs['Output'])
        #opPredict2.inputs['LabelsCount'].connect(classCountProvider.outputs["Output"])
        
        #predictions.append(opPredict2)
        
        #contOp2=OpAverageContext2D(g)
        #contOp2.inputs["Radii"].setValue([2,5,10, 12, 15, 20, 25, 30, 35, 40])
        #contOp2.inputs["PMaps"].connect(predictions[-1].outputs["PMaps"])
        #contOp2.inputs["ClassesCount"].connect(classCountProvider.outputs["Output"])
        
        #contexts.append(contOp2)

        #for i, pmap in enumerate(predictions[-1].outputs["PMaps"]):
            #print "IMAGE ", i
            #res = predictions[-1].outputs["PMaps"][i][:].allocate().wait()
            #vigra.impex.writeImage(res[:,:,0],"images/testload_" + str(numStage) + "_" + str(i+2) + ".png")


    g.finalize()