import vigra
import threading
from lazyflow.graph import *
import copy


from lazyflow import operators
from lazyflow.operators import *

from numpy.testing import *

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

    '''
    #stack = numpy.random.rand(100, 100, 3)
    #stack2 = numpy.random.rand(100, 100, 2)
    stack = numpy.array(range(10))
    stack2 = numpy.array(range(10, 20))
    stack = stack.reshape((5, 2, 1))
    stack2 = stack2.reshape((5, 2, 1))
    print stack.shape
    print stack2.shape

    '''
    stacker=OpMultiArrayStacker(graph=g)


    opMulti = Op5ToMulti(graph=g)
    opMulti.inputs["Input1"].connect(opa.outputs["Output"])
    opMulti.inputs["Input2"].connect(opgg.outputs["Output"])
    #opMulti.inputs["Input0"].setValue(stack)
    #opMulti.inputs["Input1"].setValue(stack2)


    stacker.inputs["Images"].connect(opMulti.outputs["Outputs"])
    stacker.inputs["AxisFlag"].setValue('c')
    stacker.inputs["AxisIndex"].setValue(2)



    print "TESTING C DIMENSION"
    slicer=OpMultiArraySlicer(graph=g)
    slicer.inputs["Input"].connect(stacker.outputs["Output"])
    slicer.inputs["AxisFlag"].setValue('c')


    for index in range(stacker.outputs["Output"].meta.shape[2]):
        print "------------------------------------------------",index

        paa=slicer.outputs["Slices"][index][:].wait()
        desired=stacker.outputs["Output"][:,:,index].wait()
        desired=numpy.squeeze(desired)
        assert_array_equal(paa,desired, "shit at index %r"%(index))


    print "TESTING X DIMENSION"
    slicer2=OpMultiArraySlicer(graph=g)
    slicer2.inputs["Input"].connect(stacker.outputs["Output"])
    slicer2.inputs["AxisFlag"].setValue('x')




    #for index in range(stacker.outputs["Output"].meta.shape[0]):
    for index in range(6):
        print "------------------------------------------------",index
        desired=stacker.outputs["Output"][index,:,:].wait()
        desired=desired[0,:,:]
        paa=slicer2.outputs["Slices"][index][:].wait()
        assert_array_equal(paa,desired, "shit at index %r"%(index))


    print "TESTING Y DIMENSION"
    slicer3=OpMultiArraySlicer(graph=g)
    slicer3.inputs["Input"].connect(stacker.outputs["Output"])
    slicer3.inputs["AxisFlag"].setValue('y')


    #for index in range(stacker.outputs["Output"].meta.shape[1]):
    for index in range(6):
        print "------------------------------------------------",index

        desired=stacker.outputs["Output"][:,index,:].wait()

        desired=desired[:,0,:]
        paa=slicer3.outputs["Slices"][index][:].wait()
        assert_array_equal(paa,desired, "shit at index %r"%(index))


g.finalize()
