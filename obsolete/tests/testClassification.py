import vigra
import threading
from lazyflow.graph import *
import copy

from lazyflow import operators
from lazyflow.operators import *


#from OptionsProviders import *
#from VigraFilters import *
#from SourcesAndSinks import *


if __name__=="__main__":


    filename='ostrich.jpg'



    g = Graph()


    vimageReader = OpImageReader(graph=g)
    vimageReader.inputs["Filename"].setValue(filename)


    #Sigma provider 0.9
    sigmaProvider = OpArrayPiper(graph=g)
    sigmaProvider.inputs["Input"].setValue(0.9)


    #Gaussian Smoothing
    opa = OpGaussianSmoothing(graph=g)
    opa.inputs["Input"].connect(vimageReader.outputs["Image"])
    opa.inputs["sigma"].connect(sigmaProvider.outputs["Output"])


    #Gradient Magnitude
    opgg=OpGaussianGradientMagnitude(graph=g)
    opgg.inputs["Input"].connect(vimageReader.outputs["Image"])
    opgg.inputs["sigma"].connect(sigmaProvider.outputs["Output"])


    #Laplacian of Gaussian
    olg=OpLaplacianOfGaussian(graph=g)
    olg.inputs["Input"].connect(vimageReader.outputs["Image"])
    olg.inputs["scale"].connect(sigmaProvider.outputs["Output"])

    #Double sigma provider1
    SigmaProviderP1=OpArrayPiper(graph=g)
    SigmaProviderP1.inputs["Input"].setValue(0.9)

    SigmaProviderP2=OpArrayPiper(graph=g)
    SigmaProviderP2.inputs["Input"].setValue(0.9*1.5)


    #difference of gaussians
    dg=OpDifferenceOfGaussians(graph=g)
    dg.inputs["Input"].connect(vimageReader.outputs["Image"])
    dg.inputs["sigma0"].connect(SigmaProviderP1.outputs["Output"])
    dg.inputs["sigma1"].connect(SigmaProviderP2.outputs["Output"])


    #Double sigma provider2
    SigmaProviderP3=OpArrayPiper(graph=g)
    SigmaProviderP3.inputs["Input"].setValue(0.9)


    SigmaProviderP4=OpArrayPiper(graph=g)
    SigmaProviderP4.inputs["Input"].setValue(0.9*1.2)


    #Coherence Op
    coher=OpCoherenceOrientation(graph=g)
    coher.inputs["Input"].connect(vimageReader.outputs["Image"])
    coher.inputs["sigma0"].connect(SigmaProviderP3.outputs["Output"])
    coher.inputs["sigma1"].connect(SigmaProviderP4.outputs["Output"])

    #Hessian Eigenvalues
    hog = OpHessianOfGaussianEigenvalues(graph=g)
    hog.inputs["Input"].connect(vimageReader.outputs["Image"])
    hog.inputs["scale"].connect(sigmaProvider.outputs["Output"])

    #########################
    #Sigma provider 2.7
    ###########################
    sigmaProvider2 = OpArrayPiper(graph=g)
    sigmaProvider2.inputs["Input"].setValue(2.7)

    opa2 = OpGaussianSmoothing(graph=g)
    opa2.inputs["Input"].connect(vimageReader.outputs["Image"])
    opa2.inputs["sigma"].connect(sigmaProvider2.outputs["Output"])

    #Gradient Magnitude2
    opgg2=OpGaussianGradientMagnitude(graph=g)
    opgg2.inputs["Input"].connect(vimageReader.outputs["Image"])
    opgg2.inputs["sigma"].connect(sigmaProvider2.outputs["Output"])

    #Laplacian of Gaussian
    olg2=OpLaplacianOfGaussian(graph=g)
    olg2.inputs["Input"].connect(vimageReader.outputs["Image"])
    olg2.inputs["scale"].connect(sigmaProvider2.outputs["Output"])

    #################################
    #Double sigma provider3
    #######################################


    #difference of gaussians
    dg2=OpDifferenceOfGaussians(graph=g)
    dg2.inputs["Input"].connect(vimageReader.outputs["Image"])
    dg2.inputs["sigma0"].setValue(2.7)
    dg2.inputs["sigma1"].setValue(2.7*1.5)


    #################################
    #Double sigma provider4
    #######################################

    coher2=OpCoherenceOrientation(graph=g)
    coher2.inputs["Input"].connect(vimageReader.outputs["Image"])
    coher2.inputs["sigma0"].setValue(2.7)
    coher2.inputs["sigma1"].setValue(1.2)


    #Hessian Eigenvalues2
    hog2 = OpHessianOfGaussianEigenvalues(graph=g)
    hog2.inputs["Input"].connect(vimageReader.outputs["Image"])
    hog2.inputs["scale"].connect(sigmaProvider2.outputs["Output"])


    ###################################
    #Merge the stuff together
    ##################################
    ########################################
    #########################################
    stacker=OpMultiArrayStacker(graph=g)
    stacker.inputs["AxisFlag"].setValue('c')
    stacker.inputs["AxisIndex"].setValue(2)

    opMulti = Op20ToMulti(graph=g)
    opMulti.inputs["Input00"].connect(opa.outputs["Output"])
    opMulti.inputs["Input01"].connect(opgg.outputs["Output"])
    opMulti.inputs["Input02"].connect(olg.outputs["Output"])
    opMulti.inputs["Input03"].connect(dg.outputs["Output"])
    opMulti.inputs["Input04"].connect(coher.outputs["Output"])
    opMulti.inputs["Input05"].connect(hog.outputs["Output"])

    opMulti.inputs["Input06"].connect(opa2.outputs["Output"])
    opMulti.inputs["Input07"].connect(opgg2.outputs["Output"])
    opMulti.inputs["Input08"].connect(olg2.outputs["Output"])
    opMulti.inputs["Input09"].connect(dg2.outputs["Output"])
    opMulti.inputs["Input10"].connect(coher2.outputs["Output"])
    opMulti.inputs["Input11"].connect(hog2.outputs["Output"])

    stacker.inputs["Images"].connect(opMulti.outputs["Outputs"])




    #####Get the labels###
    filenamelabels='labels_ostrich.png'


    labelsReader = OpImageReader(graph=g)
    labelsReader.inputs["Filename"].setValue(filenamelabels)


    #######Training

    opMultiL = Op5ToMulti(graph=g)
    opMultiI = Op5ToMulti(graph=g)

    opMultiL.inputs["Input0"].connect(labelsReader.outputs["Image"])
    opMultiI.inputs["Input0"].connect(stacker.outputs["Output"])
    opTrain = OpTrainRandomForest(graph=g)
    opTrain.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
    opTrain.inputs['Images'].connect(opMultiI.outputs["Outputs"])
    opTrain.inputs['fixClassifier'].setValue(False)

    #print "Here ########################", opTrain.outputs['Classifier'][:].allocate().wait()

    ##################Prediction
    opPredict=OpPredictRandomForest(graph=g)
    opPredict.inputs['Classifier'].connect(opTrain.outputs['Classifier'])


    opPredict.inputs['Image'].connect(stacker.outputs['Output'])


    opPredict.inputs['LabelsCount'].setValue(2)



    selector=OpSingleChannelSelector(graph=g)


    selector.inputs["Index"].setValue(1)
    selector.inputs["Input"].connect(opPredict.outputs['PMaps'])

    print selector.outputs["Output"][:].allocate().wait()
