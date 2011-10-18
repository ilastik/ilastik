import context
import vigra
import os
import glob
import vigra
import sys

import threading
from lazyflow.graph import *
import copy

from lazyflow import operators

import h5py

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

#This file computes a lot of image features. Unlike neuro_test_all.py script, it uses
#different files for training and testing


def runPrediction():
    sys.setrecursionlimit(10000)

    #Knott data
    #fileraw = "/home/akreshuk/data/context/TEM_raw/50slices_down2.h5"
    #filelabels = "/home/akreshuk/data/context/TEM_labels/50slices_down2.h5"
    #resdir = "/home/akreshuk/data/context/TEM_results/"
    #resproject = "50slices_down2_templ_gaus_float.ilp"
    #graphfile = "/home/akreshuk/data/context/50slices_down2_graph_all.h5"
    #tempfile = "/home/akreshuk/data/context/50slices_down2_gaus_float_iter0.h5"

    #Bock data
    filerawtrain = "/home/akreshuk/data/context/TEM_raw/bock_training_1024_2048_5_28_slices.h5"
    filerawtest = "/home/akreshuk/data/context/TEM_raw/bock_testing_51_81_slices.h5"
    filelabels = "/home/akreshuk/data/context/TEM_labels/bock_training_1024_2048_5_28_labels_from_ilastik.h5"
    resdir = "/home/akreshuk/data/context/TEM_results/"
    resproject = "bock_testing_1024_2048_51_81_all_3dfeat_iter0.ilp"
    tempfile = "/home/akreshuk/data/context/bock_1024_2048_51_81_all_3dfeat_iter0.h5"

    h5path = "/volume/data"
    nclasses = 5

    g = Graph()

    temp = h5py.File(tempfile, "w")
    outfile = h5py.File(resdir+resproject, "r+")

    #for blockwise final prediction
    nxcut = 5
    nycut = 5

    axistags=vigra.AxisTags(vigra.AxisInfo('x',vigra.AxisType.Space),vigra.AxisInfo('y',vigra.AxisType.Space), vigra.AxisInfo('z',vigra.AxisType.Space))  

    ftrain = h5py.File(filerawtrain)
    stack = numpy.array(ftrain[h5path])
    stack = stack.reshape(stack.shape + (1,))
    stackva = vigra.VigraArray(stack, axistags=vigra.VigraArray.defaultAxistags(4))

    ftest = h5py.File(filerawtest)
    stacktest = numpy.array(ftest[h5path])
    stacktest = stacktest.reshape(stacktest.shape + (1,))
    stacktestva = vigra.VigraArray(stacktest, axistags=vigra.VigraArray.defaultAxistags(4))

    print "READ STACKS: stack ", stackva.shape, ", stacktest ", stacktestva.shape


    ##Slicer
    #slicer = operators.OpMultiArraySlicer(g)
    ##slicer.inputs["Input"].connect(himage.outputs["Image"])
    #slicer.inputs["Input"].setValue(stackva)
    #slicer.inputs["AxisFlag"].setValue('z')

    ##Slicer test
    #slicertest = operators.OpMultiArraySlicer(g)
    #slicertest.inputs["Input"].setValue(stacktestva)
    #slicertest.inputs["AxisFlag"].setValue('z')


    #print "THE SLICER:", len(slicer.outputs["Slices"]), slicer.outputs["Slices"][0].shape
    #print "SLICER TEST:", len(slicertest.outputs["Slices"]), slicertest.outputs["Slices"][0].shape

    #Same sigmas as in Classification Workflow"
    #sigmas = [0.7, 1.0, 1.6, 3.5]
    sigmas = [3.5]
    #opMulti = operators.Op50ToMulti(g)
    count = 0
    #Create all our favorite features with all sigmas, we have the space now
    opMulti = createImageFeatureOperators(g, stackva, sigmas)
    opMultiTest = createImageFeatureOperators(g, stacktestva, sigmas)
    
    print "OPMULTI:", len(opMulti.outputs["Outputs"]), opMulti.outputs["Outputs"][0].shape
    print "OPMULTITEST:", len(opMultiTest.outputs["Outputs"]), opMultiTest.outputs["Outputs"][0].shape
    

    stacker = operators.OpMultiArrayStacker(g)
    stacker.inputs["Images"].connect(opMulti.outputs["Outputs"])
    stacker.inputs["AxisFlag"].setValue('c')
    stacker.inputs["AxisIndex"].setValue(3)
    print "THE FEATURE STACKER:", stacker.outputs["Output"].shape, stacker.outputs["Output"].axistags

    stackerTest = operators.OpMultiArrayStacker(g)
    stackerTest.inputs["Images"].connect(opMultiTest.outputs["Outputs"])
    stackerTest.inputs["AxisFlag"].setValue('c')
    stackerTest.inputs["AxisIndex"].setValue(3)
    print "THE FEATURE STACKER TEST:", stackerTest.outputs["Output"].shape, stackerTest.outputs["Output"].axistags

    
    f = h5py.File(filelabels)
    labels = numpy.array(f[h5path]).astype(numpy.uint8)
    labels = labels.reshape(labels.shape + (1,))
    labelsva = vigra.VigraArray(labels, axistags=vigra.VigraArray.defaultAxistags(4))

    #make a dummy labeler to use its blocks and sparsity
    opLabeler = operators.OpBlockedSparseLabelArray(g)
    opLabeler.inputs["shape"].setValue(labelsva.shape)
    opLabeler.inputs["blockShape"].setValue((8, 8, 8, 1))
    opLabeler.inputs["eraser"].setValue(100)
    #find the labeled slices, slow and baaad
    lpixels = numpy.nonzero(labels)
    print "LABELED PIXELS: ", len(lpixels[2])
    print "min label:", numpy.min(labels), "max label:", numpy.max(labels)
    luns = numpy.unique(lpixels[2])
    #luns = [luns[0]]
    for z in luns:
        #We kind of assume the last slice is not labeled here.
        #But who would label the last slice???
        assert z!=labels.shape[2]-1
        zslice = labels[:, :, z:z+1, :]
        print "setting labels in slice:", z
        key = (slice(None, None, None), slice(None, None, None), slice(z, z+1, None), slice(None, None, None))
        opLabeler.setInSlot(opLabeler.inputs["Input"], key, zslice)
        
    #because opTrain has a MultiInputSlot only
    opMultiL = operators.Op5ToMulti(g)
    opMultiL.inputs["Input0"].connect(opLabeler.outputs["Output"])

    opMultiLblocks = operators.Op5ToMulti(g)
    opMultiLblocks.inputs["Input0"].connect(opLabeler.outputs["nonzeroBlocks"])


    featurecache = operators.OpBlockedArrayCache(g)
    featurecache.inputs["innerBlockShape"].setValue((16,16,16,60))
    featurecache.inputs["outerBlockShape"].setValue((64,64,64,60))
    featurecache.inputs["Input"].connect(stacker.outputs["Output"])
    featurecache.inputs["fixAtCurrent"].setValue(False)  

    featurecacheTest = operators.OpBlockedArrayCache(g)
    featurecacheTest.inputs["innerBlockShape"].setValue((16,16,16,60))
    featurecacheTest.inputs["outerBlockShape"].setValue((64,64,64,60))
    featurecacheTest.inputs["Input"].connect(stackerTest.outputs["Output"])
    featurecacheTest.inputs["fixAtCurrent"].setValue(False)  
    

    opMultiS = operators.Op5ToMulti(g)
    opMultiS.inputs["Input0"].connect(featurecache.outputs["Output"])

    print "opMultiS outputs shape:", opMultiS.outputs["Outputs"][0].shape

    #Training
    opTrain = operators.OpTrainRandomForestBlocked(g)
    opTrain.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
    opTrain.inputs['Images'].connect(opMultiS.outputs["Outputs"])
    opTrain.inputs['fixClassifier'].setValue(False)
    opTrain.inputs['nonzeroLabelBlocks'].connect(opMultiLblocks.outputs["Outputs"])

    acache = operators.OpArrayCache(g)
    acache.inputs["Input"].connect(opTrain.outputs['Classifier'])

    print "Here ########################", acache.outputs['Output'][:].allocate().wait()    
    print
    print "++++++++++++++ Trained ++++++++++++++++++++++"
    print
    #import sys
    #sys.exit(1)
    #Prediction
    opPredict = operators.OpPredictRandomForest(g)
    opPredict.inputs['Classifier'].connect(acache.outputs['Output'])    
    #opPredict.inputs['Image'].connect(opMultiS.outputs['Outputs'])
    opPredict.inputs['Image'].connect(featurecacheTest.outputs['Output'])

    classCountProvider = operators.OpArrayPiper(g)
    classCountProvider.inputs["Input"].setValue(nclasses) 

    opPredict.inputs['LabelsCount'].setValue(nclasses)

    #print "prediction output:", opPredict.outputs["PMaps"]
    #Predict and save without context first
    #pmaps = opPredict.outputs["PMaps"][:].allocate().wait()[:]
    #print "shape of pmaps: ", pmaps.shape
    #for i in range(pmaps.shape[2]):
        #for c in range(nclasses):
            ##print i, c
            #pmap = pmaps[:, :, i, c]
            #vigra.impex.writeImage(pmap, resdir + "slice00" + str(i) + "_class_" + str(c) + ".tif")


    size = opPredict.outputs["PMaps"].shape
    xmin = [i*size[0]/nxcut for i in range(nxcut)]
    ymin = [i*size[1]/nycut for i in range(nycut)]
    xmax = [i*size[0]/nxcut for i in range(1, nxcut+1)]
    ymax = [i*size[1]/nycut for i in range(1, nycut+1)]

    print "PMaps shape:", size
    print xmin, ymin, xmax, ymax
    #pmaps = numpy.zeros(size, dtype=numpy.float32)
    #oldfeatures = numpy.zeros(featurecache.outputs["Output"].shape, dtype=numpy.float32)
    
    
    predfile = outfile["/DataSets/dataItem00/prediction"]
   
    labelsfile = outfile["/DataSets/dataItem00/labels/data"]
    labelsfile[:] = numpy.zeros(labelsfile.shape)
    
    
    
    temppredfile = temp.create_dataset("/volume/pmaps", shape = size, dtype = opPredict.outputs["PMaps"].dtype, compression='gzip')
    
    temp.create_dataset("/volume/labels", data = labels, compression='gzip')
    trainfeaturesfile = temp.create_dataset("/volume/trainfeatures", shape = featurecache.outputs["Output"].shape, compression='gzip')
    testfeaturesfile = temp.create_dataset("/volume/testfeatures", shape = featurecacheTest.outputs["Output"].shape, compression='gzip')
    
    #we do both training and testing features here, because they are from the same stack
    #and have the same x and y dimensions
    
    for i, x in enumerate(xmin):
        for j, y in enumerate(ymin):
            print "processing part ", i, j
            testfeaturesfile[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = \
                                featurecacheTest.outputs["Output"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
             
            trainfeaturesfile[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = \
                                featurecache.outputs["Output"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
            
            print "features for part done"
            pmapspart = opPredict.outputs["PMaps"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
            print "predictions for part done"
            predfile[0, xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = pmapspart[:]
            temppredfile[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = pmapspart[:]
            
            #pmaps[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = pmapspart[:]
            #oldfeatures[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :]=featurepart[:]
            #print numpy.min(pmaps), numpy.max(pmaps), numpy.max(pmapspart)
            #print numpy.min(oldfeatures), numpy.max(oldfeatures


    print "Prediction done!"
    
    outfile.close()
    temp.close()
    
    
    #save into an old ilastik project for easy visualization
    #outfile = h5py.File(resdir+resproject, "r+")
    #predfile = outfile["/DataSets/dataItem00/prediction"]
    #nx = pmaps.shape[0]
    #ny = pmaps.shape[1]
    #nz = pmaps.shape[2]
    #predfile[:] = pmaps.reshape((1, nx, ny, nz, nclasses))[:]
    #labelsfile = outfile["/DataSets/dataItem00/labels/data"]
    #labelsfile[:] = labels.reshape((1, nx, ny, nz, 1))[:]
    #outfile.close()

    #print "old ilastik project done!"

    ##save the predictions, features and labels for later on
    #temp = h5py.File(tempfile, "w")
    #temp.create_dataset("/volume/pmaps", data = pmaps, compression='gzip')
    #temp.create_dataset("/volume/labels", data = labels, compression='gzip')
    #temp.create_dataset("/volume/features", data=oldfeatures, compression='gzip')
    #temp.close()

    #save the graph to work with context in a different script
    #myPersonalEasyGraphNames = {}

    #myPersonalEasyGraphNames["graph"] = g
    #myPersonalEasyGraphNames["train"] = opTrain
    #myPersonalEasyGraphNames["cache"] = acache
    #myPersonalEasyGraphNames["features"] = stacker
    #myPersonalEasyGraphNames["predict"] = opPredict
    #myPersonalEasyGraphNames["nclasses"] = classCountProvider
    #myPersonalEasyGraphNames["opMultiL"] = opMultiL
    #myPersonalEasyGraphNames["labels"] = labelsva
    #myPersonalEasyGraphNames["slicer"] = slicer
    ##myPersonalEasyGraphNames["opa"] = opa
    #fgraph = h5py.File(graphfile,"w")
    #group = fgraph.create_group("graph")
    #group.dumpObject(myPersonalEasyGraphNames)
    #g.finalize()
    
    
def createImageFeatureOperators(g, stack, sigmas):
    opMulti = operators.Op50ToMulti(g)
    count = 0
    for sigma in sigmas:
        #Gaussian smoothing
        opa = operators.OpGaussianSmoothing(g)
        opa.inputs["Input"].setValue(stack)
        opa.inputs["sigma"].setValue(sigma)
        opMulti.inputs["Input%02d"%count].connect(opa.outputs["Output"])
        count +=1
        
        #Hessian eigenvalues
        hog = operators.OpHessianOfGaussianEigenvalues(g)
        hog.inputs["Input"].setValue(stack)
        hog.inputs["scale"].setValue(sigma)
        opMulti.inputs["Input%02d"%count].connect(hog.outputs["Output"])
        count +=1
        
        #Structure tensor eigenvalues
        strten = operators.OpStructureTensorEigenvalues(g)
        strten.inputs["Input"].setValue(stack)
        strten.inputs["innerScale"].setValue(sigma)
        strten.inputs["outerScale"].setValue(0.5*sigma)
        opMulti.inputs["Input%02d"%count].connect(strten.outputs["Output"])
        count +=1
        
        #Laplacian
        lap = operators.OpLaplacianOfGaussian(g)
        lap.inputs["Input"].setValue(stack)
        lap.inputs["scale"].setValue(sigma)
        opMulti.inputs["Input%02d"%count].connect(lap.outputs["Output"])
        count +=1
        
        #Gradient Magnitude
        opg = operators.OpGaussianGradientMagnitude(g)
        opg.inputs["Input"].setValue(stack)
        opg.inputs["sigma"].setValue(sigma)
        opMulti.inputs["Input%02d"%count].connect(opg.outputs["Output"])
        count +=1
        
        #Diff of Gaussians
        diff = operators.OpDifferenceOfGaussians(g)
        diff.inputs["Input"].setValue(stack)
        diff.inputs["sigma0"].setValue(sigma)            
        diff.inputs["sigma1"].setValue(sigma*0.66)
        opMulti.inputs["Input%02d"%count].connect(diff.outputs["Output"])
        count +=1
    
    return opMulti

if __name__=="__main__":
    runPrediction()