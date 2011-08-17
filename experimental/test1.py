import context
import vigra
import os
import glob
import shutil

origdata = "/home/akreshuk/data/Luca/normalized2"
tempfolder = "/home/akreshuk/data/Luca/temprawdata"
tempfolder1 = "/home/akreshuk/data/Luca/templabels"
labeldir = "/home/akreshuk/data/Luca/labels"

labeled = os.listdir(labeldir)
for f in labeled:
    fraw = glob.glob(origdata + "/*/" + f)
    
    print f, fraw
    if len(fraw)>0:
        shutil.copyfile(fraw[0], tempfolder+"/"+f)
        shutil.copyfile(labeldir + "/" + f, tempfolder1+"/"+f)
    