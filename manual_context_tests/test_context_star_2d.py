import vigra
import h5py
import numpy
import time
from vigra import context



trfile = h5py.File("/home/akreshuk/data/context/slice0_408_f_and_l.h5")
trfeatures = trfile["/volume/features"][:]
print "tr features shape: ", trfeatures.shape
trlabels = trfile["/volume/labels"][:]
print "tr labels shape: ", trlabels.shape
trindices = trfile["/volume/indices"][:]
print "tr indices shape: ", trindices.shape

ffile = h5py.File("/home/akreshuk/data/context/slice0_408_all_features.h5")
feat0 = ffile["/volume/data_0"][:]
feat1 = ffile["/volume/data_1"][:]

print "all features shape: ", feat0.shape, feat1.shape

if not trlabels.dtype==numpy.uint32:
    trlabels = trlabels.astype(numpy.uint32)
if not trfeatures.dtype==numpy.float32:
    trfeatures = trfeatures.astype(numpy.float32)
if not feat0.dtype==numpy.float32:
    feat0 = feat0.astype(numpy.float32)
if not feat1.dtype==numpy.float32:
    feat1 = feat1.astype(numpy.float32)

#build the forest
rf = vigra.learning.RandomForest(treeCount = 100)
oob = rf.learnRF(trfeatures, trlabels)
print oob

imshape = (feat0.shape[2], feat0.shape[3])
#predict first image
pred0 = rf.predictProbabilities(feat0.reshape(feat0.shape[2]*feat0.shape[3], feat0.shape[4]))
#predict second image
pred1 = rf.predictProbabilities(feat1.reshape(feat1.shape[2]*feat1.shape[3], feat1.shape[4]))

print "old predictions shape: ", pred0.shape
nclasses = pred0.shape[1]
pred0 = pred0.reshape((imshape[0], imshape[1], nclasses))
pred1 = pred1.reshape((imshape[0], imshape[1], nclasses))
print "new predictions shape: ", pred0.shape

if not pred0.dtype == numpy.float32:
    pred0 = pred0.astype(numpy.float32)
if not pred1.dtype == numpy.float32:
    pred1 = pred1.astype(numpy.float32)

#radii = numpy.array([5, 7, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 125, 150, 175, 200], dtype=numpy.uint32)
radii = numpy.array([5,10,15,20,25,35,45,55,100],dtype=numpy.uint32)

nnew = 8*2*nclasses*radii.shape[0]

res0 = numpy.zeros(shape=(imshape[0], imshape[1], nnew), dtype=numpy.float32)
res1 = numpy.zeros(shape=(imshape[0], imshape[1], nnew), dtype=numpy.float32)
print "res shape: ", res0.shape
tic = time.clock()
vigra.context.starContext2Dmulti(radii, pred0, res0)
vigra.context.starContext2Dmulti(radii, pred1, res1)
toc = time.clock()
print "time = ", toc-tic

newfeatures0 = res0.reshape(feat0.shape[2]*feat0.shape[3], nnew)
newfeatures1 = res1.reshape(feat1.shape[2]*feat1.shape[3], nnew)
print "after reshaping new features: ", newfeatures0.shape
newfeaturesfull0 = numpy.hstack((feat0.reshape(feat0.shape[2]*feat0.shape[3], feat0.shape[4]), newfeatures0))
newfeaturesfull1 = numpy.hstack((feat1.reshape(feat1.shape[2]*feat1.shape[3], feat1.shape[4]), newfeatures1))

#because we know the labels are in the second image...
newfeaturestr = newfeatures1[numpy.squeeze(trindices)]
print "shape of new training features: ", newfeaturestr.shape
rf2 = vigra.learning.RandomForest(treeCount=100)
oob2, varimp = rf2.learnRFWithFeatureSelection(newfeaturestr, trlabels)
print oob2
print varimp.shape
gini = varimp[:, -1]
indsort = numpy.argsort(gini)
print "not important vars:"
print indsort[0:10]
print gini[indsort[0:10]]
print "important vars:"
print indsort[-10:-1]
print gini[indsort[-10:-1]]

fimp = open("/home/akreshuk/data/context/varimp_full_r.txt", "w")

for i, ind in enumerate(indsort):
    strtowrite = "%d    %f\n"%(ind, gini[indsort[i]]
    fimp.write(strtowrite)
fimp.close()



pred0 = rf2.predictProbabilities(newfeaturesfull0)
pred1 = rf2.predictProbabilities(newfeaturesfull1)

print "second prediction done..."

#lab0 = rf2.predictLabels(newfeaturesfull0)
#lab1 = rf2.predictLabels(newfeaturesfull1)



outfile = h5py.File("/home/akreshuk/data/context/slice0_408_results_full_r.ilp", "r+")

predfile0 = outfile["/DataSets/dataItem00/prediction"]
predfile0[:] = pred0.reshape((1, 1, imshape[0], imshape[1], nclasses))[:]
predfile1 = outfile["/DataSets/dataItem01/prediction"]
predfile1[:] = pred1.reshape((1, 1, imshape[0], imshape[1], nclasses))[:]
outfile.close()




#compare...
#print "predictions:"
#print pred0[0:3, 0:3, 0]
#print "new features:"
#print res[1, 1, 0:8]


#print "done!"
