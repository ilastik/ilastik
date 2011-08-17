import h5py
import vigra
import glob
import numpy
import os

rawdir = "/home/akreshuk/data/knott_2D/stretched/cropped/"
labdir = "/home/akreshuk/data/knott_2D/stretched/cropped/labeled/"

nslices = 50

rawfiles = glob.glob(rawdir+"*.tif")
rawfiles = sorted(rawfiles, key=str.lower)

labfilescolor = glob.glob(labdir+"*.tif")
labfilescolor = sorted(labfilescolor, key=str.lower)

#labfilesbw = glob.glob(labdir+"*_bw.tif")
#labfilesbw = sorted(labfiles, key=str.lower)

im0 = vigra.readImage(rawfiles[0])
shape3d = ((im0.shape[0], im0.shape[1], nslices))

data = numpy.zeros(shape = shape3d, dtype = numpy.uint8)
labels = numpy.zeros(shape = shape3d, dtype = numpy.uint8)


for i in range(nslices):
    fDir, fFile = os.path.split(rawfiles[i])
    im = vigra.readImage(rawfiles[i])
    #print "image:", im.shape
    #print "data:", data[:, :, i].shape
    data[:, :, i] = im.squeeze()
    
    templabname = labdir + fFile
    if templabname in labfilescolor:
        #this slice is labeled, add to the labels array
        filebw = os.path.splitext(fFile)[0]+"_bw"+os.path.splitext(fFile)[1]
        labim = vigra.readImage(labdir + filebw)
        labels[:, :, i] = labim.squeeze()
        
fraw = h5py.File("/home/akreshuk/data/context/TEM_raw/"+str(nslices)+"slices.h5", "w")
flabels = h5py.File("/home/akreshuk/data/context/TEM_labels/"+str(nslices)+"slices.h5", "w")
dr = fraw.create_dataset("/volume/data", data.shape, data.dtype, data=data)
dl = flabels.create_dataset("/volume/data", labels.shape, labels.dtype, data=labels)
fraw.close()
flabels.close()
    

