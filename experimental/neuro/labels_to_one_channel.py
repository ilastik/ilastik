import numpy
import vigra
import glob
import os

#ldir = "/home/akreshuk/data/knott_2D/stretched/cropped/labeled/"

ldir = "/home/akreshuk/data/context/TEM_labels/bock_training/from_ilastik/"

lfiles = glob.glob(ldir+"*.tif")
lfiles = sorted(lfiles, key=str.lower)



for fname in lfiles:
    
    if 'bw' in fname:
        continue
    im = vigra.readImage(fname)
    im = im.astype(numpy.uint32)
    imnew = numpy.zeros((im.shape[0], im.shape[1]), dtype = numpy.uint8)
    
    print im.shape, im.dtype
    
    imflat = im[:, :, 0] + 1000*im[:, :, 1] + 1000000*im[:, :, 2]
    indred = numpy.where(imflat[:, :]==255)
    indgreen = numpy.where(imflat[:, :]==255000)
    indblue = numpy.where(imflat[:, :]==255000000)
    indyellow = numpy.where(imflat[:, :]==255255)
    indmagenta = numpy.where(imflat[:, :]==255000255)
    
    #imarray = numpy.array(im)
    
    #values = numpy.unique(imflat)
    #print values
    #for v in values:
        #print "%d"%v
    #values_ch1 = numpy.unique(imarray[:, :, 0])
    #print values_ch1
    #values_ch2 = numpy.unique(imarray[:, :, 1])
    #print values_ch2
    #values_ch3 = numpy.unique(imarray[:, :, 2])
    #print values_ch3
    #for i in range(im.shape[0]):
        #for j in range(im.shape[1]):
            #if im[i, j, 0]==255 and im[i, j, 2]==255 and im[i, j, 1]!=255:
                #print im[i, j, :]
                
    print "red labels:", len(indred[0])
    print "green labels:", len(indgreen[0])
    print "blue labels:", len(indblue[0])
    print "yellow labels:", len(indyellow[0])
    print "magenta labels:", len(indmagenta[0])
    
    
    imnew[indred]=1
    imnew[indgreen]=2
    imnew[indblue]=3
    imnew[indyellow]=4
    imnew[indmagenta]=5
    
    fDir, fFile = os.path.split(fname)
    fBase, fExt = os.path.splitext(fFile)
    fnamenew = fDir + "/" + fBase + "_bw" + fExt
    vigra.impex.writeImage(imnew, fnamenew)
    
    
    
    