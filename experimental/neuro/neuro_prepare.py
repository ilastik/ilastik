import h5py
import vigra
import glob
import numpy
import os

#rawdir = "/home/akreshuk/data/knott_2D/stretched/cropped/"
#labdir = "/home/akreshuk/data/knott_2D/stretched/cropped/labeled/"

rawdir = "/home/akreshuk/data/dbock/stack/"
labdir = "/home/akreshuk/data/context/TEM_labels/bock_training/from_ilastik_more_labels/"

nslices = 50

nfirst = 5 #z3308, training
#nfirst = 51 #z3362, testing
nlast = 28 #z3331, training
#nlast = 81 #z3396, testing

nslices = nlast-nfirst


rawfiles = glob.glob(rawdir+"*.tif")
rawfiles = sorted(rawfiles, key=str.lower)

#for i in range(len(rawfiles)):
    #print i, rawfiles[i]

#import sys
#sys.exit(1)

labfilescolor = glob.glob(labdir+"*.tif")
labfilescolor = sorted(labfilescolor, key=str.lower)

for i in range(len(labfilescolor)):
    print i, labfilescolor[i]
    
#import sys
#sys.exit(1)

im0 = vigra.readImage(rawfiles[0])
shape3d = ((im0.shape[0], im0.shape[1], nslices))


shape3d = ((1024, 1024, nslices))

data = numpy.zeros(shape = shape3d, dtype = numpy.uint8)
labels = numpy.zeros(shape = shape3d, dtype = numpy.uint8)


for i in range(nfirst, nlast):
    fDir, fFile = os.path.split(rawfiles[i])
    im = vigra.readImage(rawfiles[i])
    print i, rawfiles[i], im.shape
    #print "image:", im.shape
    #print "data:", data[:, :, i].shape
    #data[:, :, i-nfirst] = im.squeeze()
    data[:, :, i-nfirst] = im[1024:2048, 1024:2048, 0]
    
    templabname = labdir + fFile
    if templabname in labfilescolor:
        #this slice is labeled, add to the labels array
        print
        print
        print "adding labels for slice", i
        print
        print
        filebw = os.path.splitext(fFile)[0]+"_bw"+os.path.splitext(fFile)[1]
        labim = vigra.readImage(labdir + filebw)
        labim = labim.swapaxes(0, 1)
        labels[:, :, i-nfirst] = labim.squeeze()
        
#fraw = h5py.File("/home/akreshuk/data/context/TEM_raw/"+str(nslices)+"slices.h5", "w")
#flabels = h5py.File("/home/akreshuk/data/context/TEM_labels/"+str(nslices)+"slices.h5", "w")
fraw = h5py.File("/home/akreshuk/data/context/TEM_raw/bock_training_1024_2048_"+str(nfirst)+"_"+str(nlast)+"_slices.h5", "w")
flabels = h5py.File("/home/akreshuk/data/context/TEM_labels/bock_training_1024_2048_"+str(nfirst)+"_"+str(nlast)+"_more_labels_from_ilastik.h5", "w")

dr = fraw.create_dataset("/volume/data", data.shape, data.dtype, data=data)
dl = flabels.create_dataset("/volume/data", labels.shape, labels.dtype, data=labels)
fraw.close()
flabels.close()
    

