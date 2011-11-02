import numpy
import context
import vigra
import os
import glob
import sys
import h5py
import gc


import threading
from lazyflow.graph import *
import copy

from lazyflow import operators

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

#this file uses different datasets for training and testing. The features are read from file,
#but the classifier is re-trained


def Train(tempfile, tempfilenew, rffile, opernames, radii, use3d):
    print "will read from a temp file:", tempfile
    
    nxcut = 12
    nycut = 12
    g = Graph()

    f = h5py.File(tempfile)
    pmaps = numpy.array(f["/volume/pmapstrain"])
    pmapsva = vigra.VigraArray(pmaps, axistags=vigra.VigraArray.defaultAxistags(4))
    if numpy.max(pmaps)>2:
        pmapsva = pmapsva/255.
        
    labels = numpy.array(f["/volume/labels"]).astype(numpy.uint8)
    labelsva = vigra.VigraArray(labels, axistags=vigra.VigraArray.defaultAxistags(4))

    oldfeaturestrain = numpy.array(f["/volume/trainfeatures"])
    trainfeaturesva = vigra.VigraArray(oldfeaturestrain, axistags=vigra.VigraArray.defaultAxistags(4))
    print "READ FROM FILE, PMAPS:", pmapsva.shape, "LABELS:", labelsva.shape, "FEATURES:", trainfeaturesva.shape
    #prepare the features for train dataset, we have everything
    pmapslicer = operators.OpMultiArraySlicer(g)
    pmapslicer.inputs["Input"].setValue(pmapsva)
    pmapslicer.inputs["AxisFlag"].setValue('z')
   
    opMultiStrain = createContextFeatureOperators(g, trainfeaturesva, pmapslicer, opernames, radii, use3d)
    stackertrain = operators.OpMultiArrayStacker(g)
    stackertrain.inputs["AxisFlag"].setValue('c')
    stackertrain.inputs["AxisIndex"].setValue(3)
    stackertrain.inputs["Images"].connect(opMultiStrain.outputs["Outputs"])

    print "STACKERTRAIN:", stackertrain.outputs["Output"].shape

    featurecachetrain = operators.OpBlockedArrayCache(g)
    featurecachetrain.inputs["innerBlockShape"].setValue((16,16,16,120))
    featurecachetrain.inputs["outerBlockShape"].setValue((64,64,64,120))
    featurecachetrain.inputs["Input"].connect(stackertrain.outputs["Output"])
    featurecachetrain.inputs["fixAtCurrent"].setValue(False)  
    
    print "FEATURECACHETrain:", featurecachetrain.outputs["Output"].shape
    #make a dummy labeler to use its blocks and sparsity
    opLabeler = operators.OpBlockedSparseLabelArray(g)
    opLabeler.inputs["shape"].setValue(labelsva.shape)
    opLabeler.inputs["blockShape"].setValue((16, 16, 1, 1))
    opLabeler.inputs["eraser"].setValue(100)
    #find the labeled slices, slow and baaad
    lpixels = numpy.nonzero(labels)
    luns = numpy.unique(lpixels[2])
    #REMOVE ME:
    #luns = [luns[1]]
    for z in luns:
        #We kind of assume the last slice is not labeled here.
        #But who would label the last slice???
        assert z!=labels.shape[2]-1
        zslice = labels[:, :, z:z+1, :]
        print "setting labels in slice:", z
        key = (slice(None, None, None), slice(None, None, None), slice(z, z+1, None), slice(None, None, None))
        opLabeler.setInSlot(opLabeler.inputs["Input"], key, zslice)
        
    opMultiL = operators.Op5ToMulti(g)    
    opMultiL.inputs["Input0"].connect(opLabeler.outputs["Output"])

    opMultiLblocks = operators.Op5ToMulti(g)
    opMultiLblocks.inputs["Input0"].connect(opLabeler.outputs["nonzeroBlocks"])
    
    #wrap the features, because opTrain has a multi input slot
    opMultiTr = operators.Op5ToMulti(g)
    opMultiTr.inputs["Input0"].connect(featurecachetrain.outputs["Output"])
    
    #opTrain = operators.OpTrainRandomForestBlocked(g)
    opTrain = operators.OpTrainRandomForestBlocked(g)
    opTrain.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
    opTrain.inputs['Images'].connect(opMultiTr.outputs["Outputs"])
    opTrain.inputs['fixClassifier'].setValue(False)
    opTrain.inputs['nonzeroLabelBlocks'].connect(opMultiLblocks.outputs["Outputs"])

    acache = operators.OpArrayCache(g)
    acache.inputs["Input"].connect(opTrain.outputs['Classifier'])
    
    #predict the pmaps to be used for the next iteration
    opPredict=operators.OpPredictRandomForest(g)
    opPredict.inputs['Classifier'].connect(acache.outputs['Output'])
    opPredict.inputs['Image'].connect(featurecachetrain.outputs["Output"])
    opPredict.inputs['LabelsCount'].setValue(pmaps.shape[-1])
    
    rf = acache.outputs['Output'][0].allocate().wait()[0]
    print rf
    
    
    sys.exit(1)
    #rfout = h5py.File(rffile, "w") 
    rf.writeHDF5(rffile, "/RF")
    #sys.exit(1)
    
    size = pmaps.shape
    xmin = [i*size[0]/nxcut for i in range(nxcut)]
    ymin = [i*size[1]/nycut for i in range(nycut)]
    xmax = [i*size[0]/nxcut for i in range(1, nxcut+1)]
    ymax = [i*size[1]/nycut for i in range(1, nycut+1)]

    print size
    print xmin, ymin, xmax, ymax
    
    fout = h5py.File(tempfilenew, "w")
    predout = fout.create_dataset("/volume/pmapstrain", shape = size, dtype = opPredict.outputs["PMaps"].dtype, compression='gzip')
    
    fout.create_dataset("/volume/labels", data = labels, compression='gzip')
    trainfeaturesfile = fout.create_dataset("/volume/trainfeatures", shape = oldfeaturestrain.shape, compression='gzip')
    
    for i, x in enumerate(xmin):
        for j, y in enumerate(ymin):
            print "training, processing part ", i, j
            trainfeaturesfile[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = \
                                oldfeaturestrain[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :]
                                #featurecachetrain.outputs["Output"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
            print "features for part done"

            pmapspart = opPredict.outputs["PMaps"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
            print "predictions for part done"
            predout[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = pmapspart[:]
            
    fout.close()
    f.close()
    
    #rf.writeHDF5(rf, rfout, "/RF")


def runContext(outputfile, outfilenew, tempfile, tempfilenew, rffile, opernames, radii, use3d):
    #graphfile = "/home/akreshuk/data/context/50slices_down2_graph_1.h5"
    #outputfile = "/home/akreshuk/data/context/TEM_results/50slices_down2_templ_all.ilp"
    #outfilenew = "/home/akreshuk/data/context/TEM_results/50slices_down2_var_i1.ilp"

    #tempfile = "/home/akreshuk/data/context/50slices_down2_all_iter0.h5"
    #tempfilenew = "/home/akreshuk/data/context/50slices_down2_var_iter1.h5"

    #numIter = 4

    print "will write to old ilastik project:", outfilenew
    print "will read from a temp file:", tempfile
    print "will write to a temp file:", tempfilenew


    #for blockwise final prediction
    nxcut = 12
    nycut = 12

    sys.setrecursionlimit(10000)
    #g = Graph(numThreads = 1, softMaxMem = 18000*1024**2)
    
    #create the random forest
    #RF = Train(tempfile, tempfilenew, opernames, radii, use3d)
    print "rffile:", rffile
    #rffile = "/home/akreshuk/data/context/bock_1024_2048_51_81_all_3dfeat_iter1_rf.h5"
    #rfout = h5py.File(rffile, "r")
    #RF = rfout["/RF"]

    RF = vigra.learning.RandomForest(rffile, "RF")
    gc.collect()
    
    print "Random forest done"
    g = Graph()

    f = h5py.File(tempfile, "r")
    pmaps = numpy.array(f["/volume/pmaps"])
    pmapsva = vigra.VigraArray(pmaps, axistags=vigra.VigraArray.defaultAxistags(4))
    if numpy.max(pmaps)>2:
        pmapsva = pmapsva/255.
    
    oldfeaturestest = numpy.array(f["/volume/testfeatures"])
    testfeaturesva = vigra.VigraArray(oldfeaturestest, axistags=vigra.VigraArray.defaultAxistags(4))

    print "READ FROM FILE, PMAPS:", pmapsva.shape, "FEATURES:", testfeaturesva.shape
    

    #prepare the features for test dataset, we have everything
    pmapslicer = operators.OpMultiArraySlicer(g)
    pmapslicer.inputs["Input"].setValue(pmapsva)
    pmapslicer.inputs["AxisFlag"].setValue('z')
   
    opMultiStest = createContextFeatureOperators(g, testfeaturesva, pmapslicer, opernames, radii, use3d)
    stackertest = operators.OpMultiArrayStacker(g)
    stackertest.inputs["AxisFlag"].setValue('c')
    stackertest.inputs["AxisIndex"].setValue(3)
    stackertest.inputs["Images"].connect(opMultiStest.outputs["Outputs"])

    print "STACKERTEST:", stackertest.outputs["Output"].shape

    featurecachetest = operators.OpBlockedArrayCache(g)
    featurecachetest.inputs["innerBlockShape"].setValue((16,16,16,120))
    featurecachetest.inputs["outerBlockShape"].setValue((64,64,64,120))
    featurecachetest.inputs["Input"].connect(stackertest.outputs["Output"])
    featurecachetest.inputs["fixAtCurrent"].setValue(False)  
    
    print "FEATURECACHETEST:", featurecachetest.outputs["Output"].shape

    opPredict2=operators.OpPredictRandomForest(g)
    #opPredict2.inputs['Classifier'].connect(acache2.outputs['Output'])
    opPredict2.inputs['Classifier'].setValue(RF)
    opPredict2.inputs['Image'].connect(featurecachetest.outputs["Output"])
    opPredict2.inputs['LabelsCount'].setValue(pmaps.shape[-1])

    print "OPPREDICT2:", opPredict2.outputs["PMaps"].shape

    size = pmaps.shape
    xmin = [i*size[0]/nxcut for i in range(nxcut)]
    ymin = [i*size[1]/nycut for i in range(nycut)]
    xmax = [i*size[0]/nxcut for i in range(1, nxcut+1)]
    ymax = [i*size[1]/nycut for i in range(1, nycut+1)]

    print size
    print xmin, ymin, xmax, ymax
    
    import shutil
    shutil.copy2(outputfile, outfilenew)
    outfile = h5py.File(outfilenew, "r+")
    
    temp = h5py.File(tempfilenew, "a")
    
    predfile = outfile["/DataSets/dataItem00/prediction"]   
    labelsfile = outfile["/DataSets/dataItem00/labels/data"]
    labelsfile[:] = numpy.zeros(labelsfile.shape)
    try:
        temppredfile = temp.create_dataset("/volume/pmaps", shape = size, dtype = opPredict2.outputs["PMaps"].dtype, compression='gzip')
    except:
        temppredfile = temp["/volume/pmaps"]
    
    try:
        testfeaturesfile = temp.create_dataset("/volume/testfeatures", oldfeaturestest.shape, compression='gzip')
    except:
        testfeaturesfile = temp["/volume/testfeatures"]
        
    for i, x in enumerate(xmin):
        for j, y in enumerate(ymin):
            print "processing part ", i, j
            testfeaturesfile[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = \
                                oldfeaturestest[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :]
             
            print "features for part done"

            pmapspart = opPredict2.outputs["PMaps"][xmin[i]:xmax[i], ymin[j]:ymax[j], :, :].allocate().wait()
            print "predictions for part done"
            predfile[0, xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = pmapspart[:]
            temppredfile[xmin[i]:xmax[i], ymin[j]:ymax[j], :, :] = pmapspart[:]
    
    print "all done!"
    f.close()
    outfile.close()
    temp.close()

def createContextFeatureOperators(g, featuresva, pmapslicer, opernames, radii, use3d):
    contOps = []
    contOpStackers = []
    shifterOps = []
    nclasses = pmapslicer.outputs["Slices"][0].shape[-1]
    for name in opernames:
        contOps = []
        if name=="var":
            contOp = operators.OpVarianceContext2D(g)
            contOp.inputs["PMaps"].connect(pmapslicer.outputs["Slices"])
            #contOpAv.inputs["Radii"].setValue([1, 3, 5, 10, 15, 20])
            contOp.inputs["Radii"].setValue(radii)
            contOp.inputs["LabelsCount"].setValue(nclasses)
            contOps.append(contOp)
        elif name=="hist":
            contOp = operators.OpContextHistogram(g)
            contOp.inputs["PMaps"].connect(pmapslicer.outputs["Slices"])
            contOp.inputs["Radii"].setValue(radii)
            contOp.inputs["LabelsCount"].setValue(nclasses)
            contOp.inputs["BinsCount"].setValue(4)
            contOps.append(contOp)
        
        
        for contOp in contOps:
            stacker_cont = operators.OpMultiArrayStacker(g)
            stacker_cont.inputs["Images"].connect(contOp.outputs["Output"])
            stacker_cont.inputs["AxisFlag"].setValue('z')
            stacker_cont.inputs["AxisIndex"].setValue(2)
            contOpStackers.append(stacker_cont)
            
            #use the features from a number (use3d) slices from above and below
            if use3d>0:
                for i in range(use3d):
                    zshift = i+1
                    shifter_plus = operators.OpFlipArrayShifter(g)
                    shifter_plus.inputs["Input"].connect(stacker_cont.outputs["Output"])
                    shifter_plus.inputs["Shift"].setValue((0, 0, zshift, 0))
                    shifterOps.append(shifter_plus)
                    shifter_minus = operators.OpFlipArrayShifter(g)
                    shifter_minus.inputs["Input"].connect(stacker_cont.outputs["Output"])
                    shifter_minus.inputs["Shift"].setValue((0, 0, -zshift, 0))
                    shifterOps.append(shifter_minus)

    #print "Stacker context output shape:", stacker_cont.outputs["Output"].shape

    #combine the image and context features
    opMultiS = operators.Op50ToMulti(g)
    opMultiS.inputs["Input00"].setValue(featuresva)
    #opMultiS.inputs["Input1"].connect(stacker_cont.outputs["Output"])
    for ns, stacker in enumerate(contOpStackers):
        opMultiS.inputs["Input%02d"%(ns+1)].connect(stacker.outputs["Output"])
    nold = len(contOpStackers)+1
    for ns, shifter in enumerate(shifterOps):
        opMultiS.inputs["Input%02d"%(ns+nold)].connect(shifter.outputs["Output"])
        
    return opMultiS



if __name__=="__main__":
    #outputfile = "/home/akreshuk/data/context/TEM_results/50slices_down2_templ_all.ilp"
    #outfilenew = "/home/akreshuk/data/context/TEM_results/50slices_down2_var_i1.ilp"

    #tempfile = "/home/akreshuk/data/context/50slices_down2_all_iter0.h5"
    #tempfilenew = "/home/akreshuk/data/context/50slices_down2_var_iter1.h5"
    
    outputfile = "/home/akreshuk/data/context/TEM_results/bock_testing_1024_2048_51_81.ilp"
    outfilenew_pref = "/home/akreshuk/data/context/TEM_results/bock_testing_1024_2048_51_81_anis_"
    #outfilenew_pref = "/tmp/temp"
    #tempfile_pref = "/home/akreshuk/data/context/50slices_down2_var_hist_gaus_3d1_iter"
    tempfile_pref = "/home/akreshuk/data/context/bock_1024_2048_51_81_all_3d_anis_feat_iter"
    #tempfile_pref = "/tmp/temp"
    
    opernames = ["var"]
    #radii = [1, 3, 5, 10, 15, 20]
    radii = [5, 10, 15, 20, 30, 40]
    
    niter = 1
    for i in range(3, 4):
        gc.collect()
        outfilenew = outfilenew_pref + opernames[0] + "_iter"+str(i+1)+".ilp"
        if i==0:
            #tempfile = "/home/akreshuk/data/context/50slices_down2_gaus_float_iter0.h5"
            #tempfile = "/home/akreshuk/data/context/50slices_down2_temp_iter1.h5"
            tempfile = "/home/akreshuk/data/context/bock_1024_2048_51_81_all_3dfeat_anis_iter0.h5"
        else:
            tempfile = tempfile_pref + str(i) + ".h5"
        tempfilenew = tempfile_pref + str(i+1) + ".h5"
        rffile = tempfile_pref + str(i+1) + "_rf.h5"
        Train(tempfile, tempfilenew, rffile, opernames, radii, use3d=0)
        #runContext(outputfile, outfilenew, tempfile, tempfilenew, rffile, opernames, radii, use3d=0)
        gc.collect()
