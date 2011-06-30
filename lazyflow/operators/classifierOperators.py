import numpy

from lazyflow.graph import Operators, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice, block_view
from Queue import Empty
from collections import deque
import greenlet, threading
import vigra
import copy



class OpTrainRandomForest(Operator):
    name = "TrainRandomForest"
    description = "Train a random forest on multiple images"
    
    inputSlots = [MultiInputSlot("Images"),MultiInputSlot("Labels")]
    outputSlots = [OutputSlot("Classifier")]
    
    def notifyConnectAll(self):
        self.outputs["Classifier"]._dtype = object
        self.outputs["Classifier"]._shape = (1,)
        
    def notifySubConnect(self, slots, indexes):
        print "OpClassifier notifySubConnect"
        self.notifyConnectAll()                 
    
        
    def getOutSlot(self, slot, key, result):
        
        featMatrix=[]
        labelsMatrix=[]
        
        for i,labels in enumerate(self.inputs["Labels"]):
            
            labels=labels[:].allocate().wait()[:,:,0:1]
            indexes=numpy.nonzero(labels[:,:,0])
            print "kjshajvjhvajhv", len(indexes[0])
            #Maybe later request only part of the region?
            image=self.inputs["Images"][i][:].allocate().wait()
            print image.shape, labels.shape
            
            features=image[indexes]
            labels=labels[indexes]
            
            print "GANG",features.shape, labels.shape
            featMatrix.append(features)
            labelsMatrix.append(labels)
        
        print features.shape
        featMatrix=numpy.concatenate(featMatrix,axis=0)
        labelsMatrix=numpy.concatenate(labelsMatrix,axis=0)
        
        RF=vigra.learning.RandomForest(100)        
        
        result=RF.learnRF(featMatrix,labelsMatrix.astype(numpy.uint32))
        return result
        


class OpPredictRandomForest(Operator):
    name = "TrainRandomForest"
    description = "Predict on multiple images"
    
    inputSlots = [MultiInputSlot("Images"),InputSlot("Classifier"),InputSlot("LabelsCount",stype='integer')]
    outputSlots = [MultiOutputSlot("PMaps")]
    
    def notifyConnectAll(self):
        inputSlot = self.inputs["Images"]    
        nlabels=self.inputs["LabelsCount"].value        
        
        self.outputs["MultiOutput"].resize(len(inputSlot)) #clearAllSlots()
        for i,islot in enumerate(self.inputs["Images"]):
            oslot = self.outputs["PMaps"][i]
            if islot.partner is not None:
                oslot._dtype = numpy.float32
                oslot._shape = islot.shape[:-1]+(nlabels,)
                oslot._axistags = islot.axistags
        
        
    def notifySubConnect(self, slots, indexes):
        print "OpClassifier notifySubConnect"
        self.notifyConnectAll()                 
    
        
        

    def getSubOutSlot(self, slots, indexes, key, result):
        res = self.inputs["Images"][indexes[0]][indexes[1]][key].allocate().wait()
               
        shape=res.shape
        if len(shape)==3:        
        
            features=res.reshape(shape[0]*shape[1],shape[2])
        if len(shape)==4:
            features=res.reshape(shape[0]*shape[1]*shape[2],shape[3])
        
        RF=self.inputs["Classfier"][:].allocate().wait()
        
        result=RF.predictProbabilities(features)        
        
        result=result.reshape(shape[0],shape[1],RF.labelCount())
               
        
        nlabels=self.inputs["LabelsCount"].value
        
        if RF.labelCount != nlabels: 
            raise
            
        return result
            
            
            
            
            
            
            

        