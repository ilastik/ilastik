import numpy
import vigra
import glob
import os

ldir = "/home/akreshuk/data/knott_2D/stretched/cropped/labeled/"

lfiles = glob.glob(ldir+"*.tif")
lfiles = sorted(lfiles, key=str.lower)



for fname in lfiles:
    im = vigra.readImage(fname)
    imnew = numpy.zeros((im.shape[0], im.shape[1]), dtype = numpy.uint8)
    
    imflat = im[:, :, 0] + 1000*im[:, :, 1] + 1000000*im[:, :, 2]
    indred = numpy.where(imflat[:, :]==255)
    indgreen = numpy.where(imflat[:, :]==255000)
    indblue = numpy.where(imflat[:, :]==255000000)
    indyellow = numpy.where(imflat[:, :]==255255)
    indmagenta = numpy.where(imflat[:, :]==255000255)
    
    imnew[indred]=1
    imnew[indgreen]=2
    imnew[indblue]=3
    imnew[indyellow]=4
    imnew[indmagenta]=5
    
    fDir, fFile = os.path.split(fname)
    fBase, fExt = os.path.splitext(fFile)
    fnamenew = fDir + "/" + fBase + "_bw" + fExt
    vigra.impex.writeImage(imnew, fnamenew)
    
    
    
    