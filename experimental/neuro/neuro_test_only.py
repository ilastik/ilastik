import numpy
import context
import vigra
import h5py
from neuro_test_all_3dfeatures_an import createImageFeatureOperators
from neuro_context_from_file_2 import createContextFeatureOperators2D, createContextFeatureOperators3D
from lazyflow.graph import *
from lazyflow import operators

def runTest(rf, rawdatafile, outputfilenew, outputfileprevious, imagefeaturesfile, opernames, radii, radii_anis):

    g = Graph()
    
    RF = vigra.learning.RandomForest(rffile, "RF")

    imf = None
    imfile = None
    outfile = None
    prevfile = None


    opMulti = operators.Op50ToMulti(g)
    #read or create the image and context features
    if imagefeaturesfile is not None:
        imfile = h5py.File(imagefeaturesfile)
        oldfeaturestest = numpy.array(f["/volume/testfeatures"])
        testfeaturesva = vigra.VigraArray(oldfeaturestest, axistags=vigra.VigraArray.defaultAxistags(4))
        
        prevfile = h5py.File(outputfileprevious)
        pmaps = prevfile["/DataSets/dataItem00/prediction"]
        pmapsva = vigra.VigraArray(pmaps, axistags=vigra.VigraArray.defaultAxistags(4))
        pmapslicer = operators.OpMultiArraySlicer(g)
        pmapslicer.inputs["Input"].setValue(pmapsva)
        pmapslicer.inputs["AxisFlag"].setValue('z')
        contOps2D, shifterOps2D = createContextFeatureOperators2D(g, pmapslicer, opernames, radii, use3d)
        contOps3D = createContextFeatureOperators3D(g, pmapsva, opernames, radii, radii_anis)
        opMulti.inputs["Input00"].setValue(trainfeaturesva)
        for ns, stacker in enumerate(contOps2D):
            opMulti.inputs["Input%02d"%(ns+1)].connect(stacker.outputs["Output"])
        nold = len(contOps2D)+1
        for ns, shifter in enumerate(shifterOps2D):
            opMulti.inputs["Input%02d"%(ns+nold)].connect(shifter.outputs["Output"])
        nold = len(contOps2D)+len(shifterOps2D)+1
        for ns, oper in enumerate(contOps3D):
            opMulti.inputs["Input%02d"%(ns+nold)].connect(oper.outputs["Output"])
        
        
    else:
        #we only need the raw data if the image features haven't been computed yet
        datafile = h5py.File(rawdatafile)
        stack = datafile["/volume/data"]
        stack = stack.reshape(stack.shape + (1,))
        stackva = vigra.VigraArray(stack, axistags=vigra.VigraArray.defaultAxistags(4))
        sigmas = [(1., 1., 1.), (1.6, 1.6, 1.6), (3.5, 3.5, 1.), (5, 5, 1.6)]
        opMulti = createImageFeatureOperators(g, stackva, sigmas)
    
    stackertest = operators.OpMultiArrayStacker(g)
    stackertest.inputs["AxisFlag"].setValue('c')
    stackertest.inputs["AxisIndex"].setValue(3)
    stackertest.inputs["Images"].connect(opMulti.outputs["Outputs"])

    print "STACKERTEST:", stackertest.outputs["Output"].shape

    featurecachetest = operators.OpBlockedArrayCache(g)
    featurecachetest.inputs["innerBlockShape"].setValue((128,128,30,160))
    featurecachetest.inputs["outerBlockShape"].setValue((128,128,30,160))
    featurecachetest.inputs["Input"].connect(stackertest.outputs["Output"])
    featurecachetest.inputs["fixAtCurrent"].setValue(False)  
    
    print "FEATURECACHETEST:", featurecachetest.outputs["Output"].shape

    opPredict2=operators.OpPredictRandomForest(g)
    opPredict2.inputs['Classifier'].setValue(RF)
    opPredict2.inputs['Image'].connect(featurecachetest.outputs["Output"])
    opPredict2.inputs['LabelsCount'].setValue(RF.labelCount())
    
    print "OPPREDICT2:", opPredict2.outputs["PMaps"].shape
    size = opPredict2.outputs["PMaps"].shape

    predcache = operators.OpBlockedArrayCache(g)
    predcache.inputs["innerBlockShape"].setValue((64, 64, 30, size[-1]))
    predcache.inputs["outerBlockShape"].setValue((64, 64, 30, size[-1]))
    predcache.inputs["Input"].connect(opPredic2.outputs["PMaps"])
    predcache.inputs["fixAtCurrent"].setValue(False)

    
    xmin = [i*size[0]/nxcut for i in range(nxcut)]
    ymin = [i*size[1]/nycut for i in range(nycut)]
    xmax = [i*size[0]/nxcut for i in range(1, nxcut+1)]
    ymax = [i*size[1]/nycut for i in range(1, nycut+1)]

    print size
    print xmin, ymin, xmax, ymax
    
    import shutil
    shutil.copy2(outputfileprevious, outputfilenew)
    outfile = h5py.File(outputfilenew, "r+")
    
    predout = outfile["/DataSets/dataItem00/prediction"]   
        
    featout = None
    if imagefeaturesfile is None:
        f, ext = os.path.splitext(outputfileprevious)
        imagefeaturesfile = f + "_features.h5"
        imf = h5py.File("imagefeaturesfile", "w")
        featout = imf.create_dataset("/volume/testfeatures")
    
    for i, x in enumerate(xmin):
        for j, y in enumerate(ymin):
            print "processing part ", i, j
            if featout is not None:
                featout[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = \
                                featurecachetest.outputs["Output"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
                
                print "features for part done"

            pmapspart = predcache.outputs["Output"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
            print "predictions for part done"
            predout[0, xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = pmapspart[:]
    
    print "all done!"
    
    if imf is not None:
        imf.close()
    if imfile is not None:
        imfile.close()
    
    outfile.close()
    if prevfile is not None:
        prevfile.close()
    
    
        
        
if __name__=="__main__":
    classifiers = ["class1", "class2", "class3"]
    rawdata = "rawdatafile"
    outputdir = "outputdir"
    outputfileprefix = "outputfileprefix"
    imagefeaturesfile = "imagefeaturesfile"
    
    
    for rf in classifiers:
        runTest(rf, rawdata, outputfile, outputfileprevious, imagefeaturesfile)
        