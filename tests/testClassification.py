import vigra
import threading
from lazyflow.graph import *
import copy

from lazyflow.operators.operators import OpArrayPiper 
from lazyflow.operators.vigraOperators import *
from lazyflow.operators.valueProviders import *
from lazyflow.operators.classifierOperators import *
from lazyflow.operators.generic import *

#from OptionsProviders import *
#from VigraFilters import *
#from SourcesAndSinks import *


if __name__=="__main__":
    
   
    filename='ostrich.jpg'
    
    
    
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)

    filenameProvider = SingleValueProvider("Filename")
    filenameProvider.setValue(filename)
    
            
    vimageReader = OpImageReader(g)
    vimageReader.inputs["Filename"].connect(filenameProvider)

    
    #Sigma provider 0.9
    sigmaProvider = SingleValueProvider("Sigma", object)
    sigmaProvider.setValue(0.9) 
    
    
    #Gaussian Smoothing     
    opa = OpGaussianSmoothing(g)   
    opa.inputs["Input"].connect(vimageReader.outputs["Image"])
    opa.inputs["sigma"].connect(sigmaProvider)
    
    
    #Gradient Magnitude
    opgg=OpGaussinaGradientMagnitude(g)
    opgg.inputs["Input"].connect(vimageReader.outputs["Image"])
    opgg.inputs["sigma"].connect(sigmaProvider)
    
    
    #Laplacian of Gaussian
    olg=OpLaplacianOfGaussian(g)
    olg.inputs["Input"].connect(vimageReader.outputs["Image"])
    olg.inputs["scale"].connect(sigmaProvider)
    
    #Double sigma provider1
    SigmaProviderP1=SingleValueProvider("Sigma", object)
    SigmaProviderP1.setValue(0.9) 
    
    SigmaProviderP2=SingleValueProvider("Sigma", object)
    SigmaProviderP2.setValue(0.9*1.5) 
        
    
    #difference of gaussians
    dg=OpDifferenceOfGaussians(g)
    dg.inputs["Input"].connect(vimageReader.outputs["Image"])
    dg.inputs["sigma0"].connect(SigmaProviderP1)
    dg.inputs["sigma1"].connect(SigmaProviderP2)
    
        
    #Double sigma provider2
    SigmaProviderP3=SingleValueProvider("Sigma", object)
    SigmaProviderP3.setValue(0.9) 
    
    
    SigmaProviderP4=SingleValueProvider("Sigma", object)
    SigmaProviderP4.setValue(0.9*1.2) 
        
    
    #Coherence Op
    coher=OpCoherenceOrientation(g)
    coher.inputs["Input"].connect(vimageReader.outputs["Image"])
    coher.inputs["sigma0"].connect(SigmaProviderP3)
    coher.inputs["sigma1"].connect(SigmaProviderP4)
    
    #Hessian Eigenvalues
    hog = OpHessianOfGaussianEigenvalues(g)
    hog.inputs["Input"].connect(vimageReader.outputs["Image"])
    hog.inputs["scale"].connect(sigmaProvider)
    
    #########################
    #Sigma provider 2.7
    ###########################
    sigmaProvider2 = SingleValueProvider("Sigma", object)
    sigmaProvider2.setValue(2.7) 
    
    opa2 = OpGaussianSmoothing(g)   
    opa2.inputs["Input"].connect(vimageReader.outputs["Image"])
    opa2.inputs["sigma"].connect(sigmaProvider2)

    #Gradient Magnitude2
    opgg2=OpGaussinaGradientMagnitude(g)
    opgg2.inputs["Input"].connect(vimageReader.outputs["Image"])
    opgg2.inputs["sigma"].connect(sigmaProvider2)
    
    #Laplacian of Gaussian
    olg2=OpLaplacianOfGaussian(g)
    olg2.inputs["Input"].connect(vimageReader.outputs["Image"])
    olg2.inputs["scale"].connect(sigmaProvider2)
    
    #################################
    #Double sigma provider3
    #######################################
    SigmaProviderP5=SingleValueProvider("Sigma", object)
    SigmaProviderP5.setValue(2.7) 
    
    SigmaProviderP6=SingleValueProvider("Sigma", object)
    SigmaProviderP6.setValue(2.7*1.5) 
        
    #difference of gaussians
    dg2=OpDifferenceOfGaussians(g)
    dg2.inputs["Input"].connect(vimageReader.outputs["Image"])
    dg2.inputs["sigma0"].connect(SigmaProviderP5)
    dg2.inputs["sigma1"].connect(SigmaProviderP6)
        
    
    #################################
    #Double sigma provider4
    #######################################
    SigmaProviderP7=SingleValueProvider("Sigma", object)
    SigmaProviderP7.setValue(2.7) 
    
    SigmaProviderP8=SingleValueProvider("Sigma", object)
    SigmaProviderP8.setValue(1.2)     
    
    coher2=OpCoherenceOrientation(g)
    coher2.inputs["Input"].connect(vimageReader.outputs["Image"])
    coher2.inputs["sigma0"].connect(SigmaProviderP7)
    coher2.inputs["sigma1"].connect(SigmaProviderP8)
    
    
    #Hessian Eigenvalues2
    hog2 = OpHessianOfGaussianEigenvalues(g)
    hog2.inputs["Input"].connect(vimageReader.outputs["Image"])
    hog2.inputs["scale"].connect(sigmaProvider2)
    
    
    ###################################
    #Merge the stuff together
    ##################################
    ########################################
    #########################################
    stacker=OpMultiArrayStacker(g)
    
    stacker.inputs["Images"].connectAdd(opa.outputs["Output"])
    stacker.inputs["Images"].connectAdd(opgg.outputs["Output"])
    stacker.inputs["Images"].connectAdd(olg.outputs["Output"])
    stacker.inputs["Images"].connectAdd(dg.outputs["Output"])
    stacker.inputs["Images"].connectAdd(coher.outputs["Output"])
    stacker.inputs["Images"].connectAdd(hog.outputs["Output"])
    
    stacker.inputs["Images"].connectAdd(opa2.outputs["Output"])
    stacker.inputs["Images"].connectAdd(opgg2.outputs["Output"])
    stacker.inputs["Images"].connectAdd(olg2.outputs["Output"])
    stacker.inputs["Images"].connectAdd(dg2.outputs["Output"])
    stacker.inputs["Images"].connectAdd(coher2.outputs["Output"])
    stacker.inputs["Images"].connectAdd(hog2.outputs["Output"])
    
    
   
    
    #####Get the labels###
    filenamelabels='labels_ostrich.png'
    
    filenameProvider2 = SingleValueProvider("Filename")
    filenameProvider2.setValue(filenamelabels)
        
    
    labelsReader = OpImageReader(g)
    labelsReader.inputs["Filename"].connect(filenameProvider2)

        
    #######Training
    
    opTrain = OpTrainRandomForest(g)
    opTrain.inputs['Labels'].connectAdd(labelsReader.outputs["Image"])
    opTrain.inputs['Images'].connectAdd(stacker.outputs["Output"])
    
    #print "Here ########################", opTrain.outputs['Classifier'][:].allocate().wait()    
    
    ##################Prediction
    opPredict=OpPredictRandomForest(g)
    opPredict.inputs['Classifier'].connect(opTrain.outputs['Classifier'])    
    

    opPredict.inputs['Image'].connect(stacker.outputs['Output'])
    classes=SingleValueProvider("Classes")
    classes.setValue(2)
    
    opPredict.inputs['LabelsCount'].connect(classes)
    
    
    
    selector=OpSingleChannelSelector(g)
    
    index=SingleValueProvider("Index")
    index.setValue(1)
    
    selector.inputs["Index"].connect(index)
    selector.inputs["Input"].connect(opPredict.outputs['PMaps'])
    
    print selector.outputs["Output"][:].allocate().wait()
    
    