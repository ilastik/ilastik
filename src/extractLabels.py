import numpy
import vigra
import os
import glob

newdir = "/home/akreshuk/data/Luca/labels/"
olddir = "/home/akreshuk/Desktop/Labeled/"
dirnames = os.listdir(olddir)
#dirnames = [dirnames[0]]
for d in dirnames:
    if '.DS_Store' in d:
            continue
    files = os.listdir(olddir + "/" + d)
    for f in files:
        if '.DS_Store' in f:
            continue
        print olddir + "/" + d + "/" +f
        im = vigra.impex.readImage(olddir + "/" + d + "/" +f)
        if im.shape[2]!=3:
            continue
        
        redind = numpy.where(im[:, :, 0]==255)
        notredind = numpy.where(im[:, :, 2]!=0)
        
        greenind = numpy.where(im[:, :, 1]==255)
        
        
        #imdiff = im[:, :, 0] + im[:,:,1] + im[:, :, 2]
        #redstuffind = numpy.where(imdiff==255)
        #greenstuffind = numpy.where(imdiff == 255+255)
        #tempind = numpy.where(im[:, :, 0]==255)
        #print tempind
        newim = numpy.zeros((im.shape[0], im.shape[1]), dtype = numpy.uint8)
        newim[redind]=255
        newim[greenind]=255
        newim[notredind]=0
        newname = newdir + f
        vigra.impex.writeImage(newim.swapaxes(0, 1), newname)
        