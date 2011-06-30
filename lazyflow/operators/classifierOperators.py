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
            
            labels=labels[:].allocate().wait()
            print "hsahfjkhfjhfsaj", labels.max()
            
            
            print "ajhajkfhjkafhjfhaj",labels.min()
            indexes=numpy.nonzero(labels[...,0].view(numpy.ndarray))
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
        
        RF.learnRF(featMatrix,labelsMatrix.astype(numpy.uint32))
        result[0]=RF
        
        


class OpPredictRandomForest(Operator):
    name = "PredictRandomForest"
    description = "Predict on multiple images"
    
    inputSlots = [MultiInputSlot("Images"),InputSlot("Classifier"),InputSlot("LabelsCount",stype='integer')]
    outputSlots = [MultiOutputSlot("PMaps")]
    
    def notifyConnectAll(self):
        inputSlot = self.inputs["Images"]    
        nlabels=self.inputs["LabelsCount"].value        
        
        print "KKKKKKKKKKKKKKK", len(inputSlot)
        
        self.outputs["PMaps"].resize(len(inputSlot)) #clearAllSlots()
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
        nlabels=self.inputs["LabelsCount"].value

        RF=self.inputs["Classifier"].value
        assert RF.labelCount() == nlabels, "ERROR: OpPredictRandomForest, labelCount differs from true labelCount!"        
                
        newKey = key[:-1]
        newKey += (slice(0,self.inputs["Images"][indexes[0]].shape[-1],None),)
        
        res = self.inputs["Images"][indexes[0]][newKey].allocate().wait()
               
        shape=res.shape
        prod = 1
        for i,e in enumerate(shape):
            if i < len(shape) - 1:
                prod *= e            

        features=res.reshape(prod, shape[-1])
        

        result=RF.predictProbabilities(features)        
        
        result=result.reshape(*(shape[:-1] + (RF.labelCount(),)))

            
            
            
            
            
            

        