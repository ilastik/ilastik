import numpy

from lazyflow.graph import Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice, block_view
from Queue import Empty
from collections import deque
import greenlet, threading
import vigra
import copy



class OpTrainRandomForest(Operator):
    name = "TrainRandomForest"
    description = "Train a random forest on multiple images"
    category = "Learning"
    
    inputSlots = [MultiInputSlot("Images"),MultiInputSlot("Labels"), InputSlot("fixClassifier", stype="bool")]
    outputSlots = [OutputSlot("Classifier")]
    
    def notifyConnectAll(self):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"]._dtype = object
            self.outputs["Classifier"]._shape = (1,)
            self.outputs["Classifier"]._axistags  = "classifier"
            self.outputs["Classifier"].setDirty((slice(0,1,None),))            
             
    
    def getOutSlot(self, slot, key, result):
        
        featMatrix=[]
        labelsMatrix=[]
        for i,labels in enumerate(self.inputs["Labels"]):
            if labels.shape is not None:
                labels=labels[:].allocate().wait()
                
                indexes=numpy.nonzero(labels[...,0].view(numpy.ndarray))
                #Maybe later request only part of the region?
                
                image=self.inputs["Images"][i][:].allocate().wait()
                
                features=image[indexes]
                labels=labels[indexes]
                
                featMatrix.append(features)
                labelsMatrix.append(labels)
        

        featMatrix=numpy.concatenate(featMatrix,axis=0)
        labelsMatrix=numpy.concatenate(labelsMatrix,axis=0)
        
        RF=vigra.learning.RandomForest(100)        
        try:
            RF.learnRF(featMatrix.astype(numpy.float32),labelsMatrix.astype(numpy.uint32))
        except:
            print "ERROR: could not learn classifier"
            print featMatrix, labelsMatrix
            print featMatrix.shape, featMatrix.dtype
            print labelsMatrix.shape, labelsMatrix.dtype            
            
        result[0]=RF
        
    def setInSlot(self, slot, key, value):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))

    def setSubInSlot(self,slots,indexes, key,value):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))

    def notifySubSlotDirty(self, slots, indexes, key):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))    

    def notifyDirty(self, slot, key):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))            


class OpTrainRandomForestBlocked(Operator):
    name = "TrainRandomForestBlocked"
    description = "Train a random forest on multiple images"
    category = "Learning"
    
    inputSlots = [MultiInputSlot("Images"),MultiInputSlot("Labels"), InputSlot("fixClassifier", stype="bool"), \
                  MultiInputSlot("nonzeroLabelBlocks")]
    outputSlots = [OutputSlot("Classifier")]
    
    def setupOutputs(self):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"]._dtype = object
            self.outputs["Classifier"]._shape = (1,)
            self.outputs["Classifier"]._axistags  = "classifier"
            
            # No need to set dirty here: notifyDirty handles it.
            #self.outputs["Classifier"].setDirty((slice(0,1,None),))            
             
    
    def execute(self, slot, roi, result):
        key = roi.toSlice()
        featMatrix=[]
        labelsMatrix=[]
        for i,labels in enumerate(self.inputs["Labels"]):
            if labels.shape is not None:
                #labels=labels[:].allocate().wait()
                blocks = self.inputs["nonzeroLabelBlocks"][i][0].allocate().wait()
                reqlistlabels = []
                reqlistfeat = []
                for b in blocks[0]:
                    
                    request = labels[b].allocate()
                    featurekey = list(b)
                    featurekey[-1] = slice(None, None, None)
                    request2 = self.inputs["Images"][i][featurekey].allocate()
                    
                    reqlistlabels.append(request)
                    reqlistfeat.append(request2)

                def dummyNotify(req):
                    pass

                for ir, req in enumerate(reqlistfeat):
                    image = req.notify(dummyNotify)

                for ir, req in enumerate(reqlistlabels):
                    labblock = req.notify(dummyNotify)
                    
                for ir, req in enumerate(reqlistlabels):
                    labblock = req.wait()
                    image = reqlistfeat[ir].wait()
                    indexes=numpy.nonzero(labblock[...,0].view(numpy.ndarray))
                    
                    features=image[indexes]
                    labbla=labblock[indexes]
                    
                    featMatrix.append(features)
                    labelsMatrix.append(labbla)
        

        featMatrix=numpy.concatenate(featMatrix,axis=0)
        labelsMatrix=numpy.concatenate(labelsMatrix,axis=0)
        
        RF=vigra.learning.RandomForest(100)        
        try:
            RF.learnRF(featMatrix.astype(numpy.float32),labelsMatrix.astype(numpy.uint32))
        except:
            print "ERROR: couldnt learn classifier"
            print featMatrix, labelsMatrix
            print featMatrix.shape, featMatrix.dtype
            print labelsMatrix.shape, labelsMatrix.dtype            
        assert RF is not None, "RF = %r" % RF    
        result[0]=RF
        
    def setInSlot(self, slot, key, value):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))

    def setSubInSlot(self,slots,indexes, key,value):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))

    def notifySubSlotDirty(self, slots, indexes, key):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))    

    def notifyDirty(self, slot, key):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))            


class OpPredictRandomForest(Operator):
    name = "PredictRandomForest"
    description = "Predict on multiple images"
    category = "Learning"
    
    inputSlots = [InputSlot("Image"),InputSlot("Classifier"),InputSlot("LabelsCount",stype='integer')]
    outputSlots = [OutputSlot("PMaps")]
    
    def setupOutputs(self):
        inputSlot = self.inputs["Image"]    
        nlabels=self.inputs["LabelsCount"].value
        
        
        """
        self.outputs["PMaps"].resize(len(inputSlot)) #clearAllSlots()
        for i,islot in enumerate(self.inputs["Images"]):
            oslot = self.outputs["PMaps"][i]
            if islot.partner is not None:
                oslot._dtype = numpy.float32
                oslot._shape = islot.shape[:-1]+(nlabels,)
                oslot._axistags = islot.axistags
        
        """
        oslot = self.outputs["PMaps"]
        islot=self.inputs["Image"]

        oslot._dtype = numpy.uint8
        #oslot._dtype = numpy.float32
        
        oslot._axistags = islot.axistags
        oslot._shape = islot.shape[:-1]+(nlabels,)
        

    def execute(self,slot, roi, result):
        key = roi.toSlice()
        nlabels=self.inputs["LabelsCount"].value

        RF=self.inputs["Classifier"].value
        assert RF.labelCount() == nlabels, "ERROR: OpPredictRandomForest, labelCount differs from true labelCount! %r vs. %r" % (RF.labelCount(), nlabels)        
                
        newKey = key[:-1]
        newKey += (slice(0,self.inputs["Image"].shape[-1],None),)
        
        res = self.inputs["Image"][newKey].allocate().wait()
               
        shape=res.shape
        prod = 1
        for i,e in enumerate(shape):
            if i < len(shape) - 1:
                prod *= e            

        features=res.reshape(prod, shape[-1])
        
        prediction=RF.predictProbabilities(features.astype(numpy.float32))        
        
        prediction = prediction.reshape(*(shape[:-1] + (RF.labelCount(),)))
        
        #result[:]=prediction[...,key[-1]]
        result[:]=prediction[...,key[-1]]*255


            
    def notifyDirty(self, slot, key):
        if slot == self.inputs["Classifier"]:
            print "OpPredict: Classifier changed, setting dirty"
            self.outputs["PMaps"].setDirty(slice(None,None,None))     
        elif slot == self.inputs["Image"]:
            nlabels=self.inputs["LabelsCount"].value
            self.outputs["PMaps"].setDirty(key[:-1] + (slice(0,nlabels,None),))
            
            
class OpSegmentation(Operator):
    name = "OpSegmentation"
    description = "displaying highest probability class for each pixel"

    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]    
    
    def notifyConnectAll(self):

        inputSlot = self.inputs["Input"]
        
        self.outputs["Output"]._shape = inputSlot.shape[:-1]
        self.outputs["Output"]._dtype = inputSlot.dtype
        self.outputs["Output"]._axistags = inputSlot.axistags
        
          
    def getOutSlot(self, slot, key, result):
        
        shape = self.inputs["Input"].shape
        rstart, rstop = sliceToRoi(key, self.outputs["Output"]._shape)  
        rstart.append(0)
        rstop.append(shape[-1])
        rkey = roiToSlice(rstart,rstop)
        img = self.inputs["Input"][rkey].allocate().wait()       
        
        stop = img.size
    
        seg = []
          
        for i in range(0,stop,img.shape[-1]):
            curr_prob = -1
            highest_class = -1
            for c in range(img.shape[-1]):
                prob = img.ravel()[i+c] 
                if prob > curr_prob:
                    curr_prob = prob
                    highest_class = c
            assert highest_class != -1, "OpSegmentation: Strange classes/probabilities"

            seg.append(highest_class)
    
        seg = numpy.array(seg)
        seg.resize(img.shape[:-1])

        result[:] = seg[:]            
            


    def notifyDirty(self,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape
    
    @property
    def dtype(self):
        return self.outputs["Output"]._dtype        
        
        
class OpAreas(Operator):
    name = "OpAreas"
    description = "counting pixel areas"

    inputSlots = [InputSlot("Input"), InputSlot("NumberOfChannels")]
    outputSlots = [OutputSlot("Areas")]    
       
    def notifyConnectAll(self):
        
        self.outputs["Areas"]._shape = (self.inputs["NumberOfChannels"].value,)
 
    def getOutSlot(self, slot, key, result):
         
        img = self.inputs["Input"][:].allocate().wait()   
        
        numC = self.inputs["NumberOfChannels"].value
        
        areas = []
        for i in range(numC):
            areas.append(0)
         
        for i in img.flat:
            areas[int(i)] +=1

        result[:] = numpy.array(areas)
            


    def notifyDirty(self,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape
    
    @property
    def dtype(self):
        return self.outputs["Output"]._dtype  
            

        
