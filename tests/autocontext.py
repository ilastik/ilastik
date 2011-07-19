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


#from OptionsProviders import *
#from VigraFilters import *
#from SourcesAndSinks import *


if __name__=="__main__":
    
    filename='ostrich.jpg'
    
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)
            
    vimageReader = OpImageReader(g)
    vimageReader.inputs["Filename"].setValue(filename)
    
    #Sigma provider 0.9
    sigmaProvider = OpArrayPiper(g)
    sigmaProvider.inputs["Input"].setValue(0.9) 
    
    #Gaussian Smoothing     
    opa = OpGaussianSmoothing(g)   
    opa.inputs["Input"].connect(vimageReader.outputs["Image"])
    opa.inputs["sigma"].connect(sigmaProvider.outputs["Output"])
    
    #Gradient Magnitude
    opgg=OpGaussinaGradientMagnitude(g)
    opgg.inputs["Input"].connect(vimageReader.outputs["Image"])
    opgg.inputs["sigma"].connect(sigmaProvider.outputs["Output"])
    
    #Laplacian of Gaussian
    olg=OpLaplacianOfGaussian(g)
    olg.inputs["Input"].connect(vimageReader.outputs["Image"])
    olg.inputs["scale"].connect(sigmaProvider.outputs["Output"])
    
    #Double sigma provider1
    SigmaProviderP1=OpArrayPiper(g)
    SigmaProviderP1.inputs["Input"].setValue(0.9) 
    
    SigmaProviderP2=OpArrayPiper(g)
    SigmaProviderP2.inputs["Input"].setValue(0.9*1.5) 
        
    #difference of gaussians
    dg=OpDifferenceOfGaussians(g)
    dg.inputs["Input"].connect(vimageReader.outputs["Image"])
    dg.inputs["sigma0"].connect(SigmaProviderP1.outputs["Output"])
    dg.inputs["sigma1"].connect(SigmaProviderP2.outputs["Output"])
    
        
    #Double sigma provider2
    SigmaProviderP3=OpArrayPiper(g)
    SigmaProviderP3.inputs["Input"].setValue(0.9) 
    
    
    SigmaProviderP4=OpArrayPiper(g)
    SigmaProviderP4.inputs["Input"].setValue(0.9*1.2) 
        
    
    #Coherence Op
    coher=OpCoherenceOrientation(g)
    coher.inputs["Input"].connect(vimageReader.outputs["Image"])
    coher.inputs["sigma0"].connect(SigmaProviderP3.outputs["Output"])
    coher.inputs["sigma1"].connect(SigmaProviderP4.outputs["Output"])
    
    #Hessian Eigenvalues
    hog = OpHessianOfGaussianEigenvalues(g)
    hog.inputs["Input"].connect(vimageReader.outputs["Image"])
    hog.inputs["scale"].connect(sigmaProvider.outputs["Output"])
    
    #########################
    #Sigma provider 2.7
    ###########################
    sigmaProvider2 = OpArrayPiper(g)
    sigmaProvider2.inputs["Input"].setValue(2.7) 
    
    opa2 = OpGaussianSmoothing(g)   
    opa2.inputs["Input"].connect(vimageReader.outputs["Image"])
    opa2.inputs["sigma"].connect(sigmaProvider2.outputs["Output"])

    #Gradient Magnitude2
    opgg2=OpGaussinaGradientMagnitude(g)
    opgg2.inputs["Input"].connect(vimageReader.outputs["Image"])
    opgg2.inputs["sigma"].connect(sigmaProvider2.outputs["Output"])
    
    #Laplacian of Gaussian
    olg2=OpLaplacianOfGaussian(g)
    olg2.inputs["Input"].connect(vimageReader.outputs["Image"])
    olg2.inputs["scale"].connect(sigmaProvider2.outputs["Output"])
    
    #################################
    #Double sigma provider3
    #######################################

        
    #difference of gaussians
    dg2=OpDifferenceOfGaussians(g)
    dg2.inputs["Input"].connect(vimageReader.outputs["Image"])
    dg2.inputs["sigma0"].setValue(2.7)
    dg2.inputs["sigma1"].setValue(2.7*1.5)
        
    
    #################################
    #Double sigma provider4
    #######################################
    
    coher2=OpCoherenceOrientation(g)
    coher2.inputs["Input"].connect(vimageReader.outputs["Image"])
    coher2.inputs["sigma0"].setValue(2.7)
    coher2.inputs["sigma1"].setValue(1.2)
    
    
    #Hessian Eigenvalues2
    hog2 = OpHessianOfGaussianEigenvalues(g)
    hog2.inputs["Input"].connect(vimageReader.outputs["Image"])
    hog2.inputs["scale"].connect(sigmaProvider2.outputs["Output"])
    
    
    ###################################
    #Merge the stuff together
    ##################################
    ########################################
    #########################################
    stacker=OpMultiArrayStacker(g)
    
    stacker.inputs["Images"].connectAdd(opa.outputs["Output"])
    """
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
    
    """
   
    
    #####Get the labels###
    filenamelabels='labels_ostrich.png'
    
    
    labelsReader = OpImageReader(g)
    labelsReader.inputs["Filename"].setValue(filenamelabels)

        
    #######Training
    
    opTrain = OpTrainRandomForest(g)
    opTrain.inputs['Labels'].connectAdd(labelsReader.outputs["Image"])
    opTrain.inputs['Images'].connectAdd(stacker.outputs["Output"])
    opTrain.inputs["fixClassifier"].setValue(False)
    
    
    acache = OpArrayCache(g)
    acache.inputs["Input"].connect(opTrain.outputs['Classifier'])
    
    #print "Here ########################", opTrain.outputs['Classifier'][:].allocate().wait()    
    
    ##################Prediction
    opPredict=OpPredictRandomForest(g)
    opPredict.inputs['Classifier'].connect(acache.outputs['Output'])    
    

    opPredict.inputs['Image'].connect(stacker.outputs['Output'])

    
    classCountProvider=OpArrayPiper(g)
    classCountProvider.inputs["Input"].setValue(2) 
    
    opPredict.inputs['LabelsCount'].connect(classCountProvider.outputs["Output"])
    
    
    vigra.impex.writeImage(opPredict.outputs["PMaps"][:].allocate().wait()[:,:,0],"images/test_00000000.png")
    
 
    contOp=OpAverageContext2D(g)
    contOp.inputs["Radii"].setValue([2,5,10, 12, 15, 20, 25, 30, 35, 40])
    contOp.inputs["PMaps"].connect(opPredict.outputs["PMaps"])
    contOp.inputs["ClassesCount"].connect(classCountProvider.outputs["Output"])
    
    
    print "dsjaflkjflksajflkfjsakjdfkla", stacker.outputs["Output"][:].allocate().wait().shape
    print "jlkhsajkhfjkhfjkhfjhafsjahdfjahdsjkahfsd"
    #print contOp.outputs["Output"][:].allocate().wait().shape 
    
    
    classifiers = [acache]
    contexts = [contOp]
    predictions=[opPredict]
    
    for numStage in range(0,5):
        
        stacker2=OpMultiArrayStacker(g)
        
        stacker2.inputs["Images"].connectAdd(stacker.outputs["Output"])
        stacker2.inputs["Images"].connectAdd(contexts[-1].outputs["Output"])
        
    
        #######Training2
        
        opTrain2 = OpTrainRandomForest(g)
        opTrain2.inputs["fixClassifier"].setValue(False)
        opTrain2.inputs['Labels'].connectAdd(labelsReader.outputs["Image"])
        opTrain2.inputs['Images'].connectAdd(stacker2.outputs["Output"])
        
        #print "Here ########################", opTrain.outputs['Classifier'][:].allocate().wait()    
        
        ##################Prediction
        opPredict2=OpPredictRandomForest(g)
        
        acache2 = OpArrayCache(g)
        acache2.inputs["Input"].connect(opTrain2.outputs['Classifier'])
        
        
        
        classifiers.append(acache2)
        classifiers.append(acache2)
        opPredict2.inputs['Classifier'].connect(acache2.outputs['Output'])
            
        
        opPredict2.inputs['Image'].connect(stacker2.outputs['Output'])
        opPredict2.inputs['LabelsCount'].connect(classCountProvider.outputs["Output"])
        
        predictions.append(opPredict2)
        
        contOp2=OpAverageContext2D(g)
        contOp2.inputs["Radii"].setValue([2,5,10, 12, 15, 20, 25, 30, 35, 40])
        contOp2.inputs["PMaps"].connect(predictions[-1].outputs["PMaps"])
        contOp2.inputs["ClassesCount"].connect(classCountProvider.outputs["Output"])
        
        contexts.append(contOp2)

        vigra.impex.writeImage(predictions[-1].outputs["PMaps"][:].allocate().wait()[:,:,0],"images/test4_" + str(numStage) + ".png")
        
        #imwriter2=OpImageWriter(g)
        #imwriter2.inputs["Filename"].setValue("res_"+str(numStage)+".png")
        
        
        
        #chsel=OpSingleChannelSelector(g)
        #chsel.inputs["Index"].setValue(0)
        #chsel.inputs["Input"].connect(predictions[-1].outputs["PMaps"])
        
        #imwriter2.inputs["Image"].connect(chsel.outputs["Output"])
    


g.finalize()


