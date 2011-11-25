import numpy
import context
import vigra
import h5py
from neuro_test_all_3dfeatures_an import createImageFeatureOperators
from neuro_context_from_file_2 import createContextFeatureOperators2D, createContextFeatureOperators3D
from lazyflow.graph import *
from lazyflow import operators

def runTest(rffile, rawdatafile, outputfilenew, outputfileprevious, imagefeaturesfile, opernames, radii, radii_anis):

    g = Graph()

    print "using features file:", imagefeaturesfile
    print "rffile:", rffile
    print "new output file:", outputfilenew
    print "previous output file:", outputfileprevious

    
    RF = vigra.learning.RandomForest(rffile, "RF")

    imf = None
    imfile = None
    outfile = None
    prevfile = None

    nxcut = 2
    nycut = 2

    opMulti = operators.Op50ToMulti(g)
    #read or create the image and context features
    if imagefeaturesfile is not None:
        imfile = h5py.File(imagefeaturesfile)
        oldfeaturestest = imfile["/volume/testfeatures"]
        print "oldfeaturestest shape:", oldfeaturestest.shape
        testfeaturesva = vigra.VigraArray(numpy.asarray(oldfeaturestest), axistags=vigra.VigraArray.defaultAxistags(4))
        print "featuresva shape:", testfeaturesva.shape
        prevfile = h5py.File(outputfileprevious)
        pmaps = prevfile["/DataSets/dataItem00/prediction"][0,...]
        pmapsva = vigra.VigraArray(pmaps, axistags=vigra.VigraArray.defaultAxistags(4))
        print "pmapsva shape:", pmapsva.shape
        pmapslicer = operators.OpMultiArraySlicer(g)
        pmapslicer.inputs["Input"].setValue(pmapsva)
        pmapslicer.inputs["AxisFlag"].setValue('z')
        contOps2D, shifterOps2D = createContextFeatureOperators2D(g, pmapslicer, opernames, radii, use3d=0)
        contOps3D = createContextFeatureOperators3D(g, pmapsva, opernames, radii, radii_anis)
        opMulti.inputs["Input00"].setValue(testfeaturesva)
        for ns, stacker in enumerate(contOps2D):
            opMulti.inputs["Input%02d"%(ns+1)].connect(stacker.outputs["Output"])
        nold = len(contOps2D)+1
        for ns, shifter in enumerate(shifterOps2D):
            opMulti.inputs["Input%02d"%(ns+nold)].connect(shifter.outputs["Output"])
        nold = len(contOps2D)+len(shifterOps2D)+1
        for ns, oper in enumerate(contOps3D):
            opMulti.inputs["Input%02d"%(ns+nold)].connect(oper.outputs["Output"])
        print "operators created"
        
    else:
        #we only need the raw data if the image features haven't been computed yet
        datafile = h5py.File(rawdatafile)
        stack = numpy.array(datafile["/volume/data"])
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
    featurecachetest.inputs["innerBlockShape"].setValue((64,64,30,160))
    featurecachetest.inputs["outerBlockShape"].setValue((64,64,30,160))
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
    predcache.inputs["Input"].connect(opPredict2.outputs["PMaps"])
    predcache.inputs["fixAtCurrent"].setValue(False)


    #REMOVE ME
    #size = (512, 512, 30, 5)    
    size = (256, 256, 30, 5)

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

    #REMOVE ME: test if it's a project problem
    tempfile = h5py.File("/export/home/akreshuk/data/context/temp_predictions_iter0_testtest4.h5", "w")
    temppred = tempfile.create_dataset("/volume/predictions", (1024, 1024, 30, 5))
    
        
    featout = None
    if imagefeaturesfile is None:
        f, ext = os.path.splitext(outputfileprevious)
        imagefeaturesfile = f + "_features_testtest4.h5"
        print "created a file for features: ", imagefeaturesfile
        imf = h5py.File(imagefeaturesfile, "w")
        featout = imf.create_dataset("/volume/testfeatures", shape = featurecachetest.outputs["Output"].shape, compression = 'gzip')
    
    for i, x in enumerate(xmin):
        for j, y in enumerate(ymin):
            print "processing part ", i, j, "x:", xmin[i], xmax[i], "y:", ymin[j], ymax[j]
            if featout is not None:
                featout[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = \
                                featurecachetest.outputs["Output"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
                
                print "features for part done"

            pmapspart = predcache.outputs["Output"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
            print "predictions for part done"
            predout[0, xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = pmapspart[:]
            temppred[xmin[i]:xmax[i], ymin[j]:ymax[j], : :] = pmapspart[:]
    
    print "all done!"
    
    tempfile.close()

    if imf is not None:
        imf.close()
    if imfile is not None:
        imfile.close()
    
    outfile.close()
    if prevfile is not None:
        prevfile.close()
    
    
        
        
if __name__=="__main__":
    classifiers = ["/export/home/akreshuk/data/context/bock_1024_2048_51_81_all_3d_anis_feat_anis_var_iter0_rf.h5", \
                   "/export/home/akreshuk/data/context/bock_1024_2048_51_81_all_3d_anis_feat_anis_var_iter1_rf.h5", \
                   "/export/home/akreshuk/data/context/bock_1024_2048_51_81_all_3d_anis_feat_anis_var_iter2_rf.h5", \
                   "/export/home/akreshuk/data/context/bock_1024_2048_51_81_all_3d_anis_feat_anis_var_iter3_rf.h5", \
                   "/export/home/akreshuk/data/context/bock_1024_2048_51_81_all_3d_anis_feat_anis_var_iter4_rf.h5"]
    rawdata = "/export/home/akreshuk/data/context/TEM_raw/bock_testing_51_81_full.h5"
    outputdir = "/export/home/akreshuk/data/context/TEM_results/"
    outputfiletemplate = "bock_testing_51_81_full.ilp"
    imagefeaturesfile = None
    
   
    niter = len(classifiers)
    niter = 1
    for iter in range(0, 1):
        f, ext = os.path.splitext(outputfiletemplate)
        if iter==0:
            outputfileprevious = outputdir + outputfiletemplate
            outputfile = outputdir + f + "_iter" + str(iter+1) + "_testtest4.ilp"
        else:
            outputfileprevious = outputdir + f + "_iter" + str(iter) + ".ilp"
            outputfile = outputdir + f + "_iter" + str(iter+1) + ".ilp"
            imagefeaturesfile = outputdir + f + "_features.h5" 

    opernames = ["var3Danis"]
    #radii = [1, 3, 5, 10, 15, 20]
    radii = [1, 3, 5, 10, 15, 20, 30, 40]

    radii_anis = [[3, 3, 1], [5, 5, 1], [5, 5, 2], [10, 10, 2], [15, 15, 2], \
                  [15, 15, 3], [20, 20, 3], [30, 30, 3], [40, 40, 3]]


    runTest(classifiers[iter], rawdata, outputfile, outputfileprevious, imagefeaturesfile, opernames, radii, radii_anis)
        
