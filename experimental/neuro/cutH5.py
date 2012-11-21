import h5py
import glob
import numpy
from numpy.testing import assert_array_equal

def cut(cutX, cutY, overlapX, overlapY):
    infile = h5py.File("/home/akreshuk/data/training_old/dbock/substack_05_41_aligned_elastic.h5")
    dd = infile["/volume/data"]
    rangeX = dd.shape[0]
    rangeY = dd.shape[1]
    rangeZ = dd.shape[2]
    
    nnew = cutX*cutY
    newfiles = []
    for i in range(nnew):
        newfile = "/home/akreshuk/data/training_old/dbock/substack_05_41_cut/%02d.h5"%i
        newfiles.append(newfile)
        
    for x in range(cutX):
        for y in range(cutY):
            #compute the shape
            xmin = max(0, x*rangeX/cutX-overlapX)
            xmax = min(rangeX, (x+1)*rangeX/cutX+overlapX)
            ymin = max(0, y*rangeY/cutY-overlapY)
            ymax = min(rangeY, (y+1)*rangeY/cutY+overlapY)
            
            print newfiles[x*cutY+y]
            print xmin, xmax, ymin, ymax
            print
            
            outf = h5py.File(newfiles[ x*cutY+y ], "w")
            d = outf.create_dataset("/volume/data", shape=(xmax-xmin, ymax-ymin, rangeZ, 1), dtype=dd.dtype)
            d[:] = dd[xmin:xmax, ymin:ymax, :, :]
            outf.close()

def reconstruct(cutX, cutY, overlapX, overlapY):
    infiles = glob.glob("/home/akreshuk/data/training_old/dbock/substack_05_41_cut/*.h5")
    infiles = sorted(infiles, key=str.lower)
    rangeX=0
    rangeY=0
    rangeZ = 0
    rangeC = 0
    type=None
    for ix in range(cutX):
        f = h5py.File(infiles[ix])
        d = f["/volume/data"]
        rangeX = rangeX+d.shape[0]-overlapX
        rangeZ = d.shape[2]
        rangeC = d.shape[3]
        type=d.dtype
        
    for iy in range(cutY):
        f = h5py.File(infiles[cutY*iy])
        d = f["/volume/data"]
        rangeY = rangeY+d.shape[1]-overlapY
    
    print rangeX, rangeY
    outfile = h5py.File("/home/akreshuk/data/training_old/dbock/substack_05_41_rec.h5", "w")
    dd = outfile.create_dataset("/volume/data", shape=(rangeX, rangeY, rangeZ, rangeC), dtype=type)
    for x in range(cutX):
        for y in range(cutY):
            f = h5py.File(infiles[ x*cutY+y ])
            d = f["/volume/data"]
            
            #position in the big file
            xmin = max(0, x*rangeX/cutX)
            xmax = min(rangeX, (x+1)*rangeX/cutX)
            ymin = max(0, y*rangeY/cutY)
            ymax = min(rangeY, (y+1)*rangeY/cutY)
            
            #print "position in big file:", xmin, xmax, ymin, ymax
            
            #position in the small file
            xxmin = 0 if x==0 else overlapX
            xxmax = d.shape[0] if x==cutX-1 else d.shape[0]-overlapX
            yymin = 0 if y==0 else overlapY
            yymax = d.shape[1] if y==cutY-1 else d.shape[1]-overlapY
            
            #print "position in small file:", xxmin, xxmax, yymin, yymax
            
            dd[xmin:xmax, ymin:ymax, :, :] = d[xxmin:xxmax, yymin:yymax, :, :]
            f.close()
    outfile.close()
    
def compare():
    original = h5py.File("/home/akreshuk/data/training_old/dbock/substack_05_41_aligned_elastic.h5")
    reconstructed = h5py.File("/home/akreshuk/data/training_old/dbock/substack_05_41_rec.h5")
    
    dorig = numpy.asarray(original["/volume/data"])
    drec = numpy.asarray(reconstructed["/volume/data"])
    
    assert dorig.shape==drec.shape
    assert dorig.dtype==drec.dtype
    
    assert_array_equal(dorig, drec)
    print "all done!"
    
    
    
    
if __name__ == "__main__":
    cutX = 4
    cutY = 4
    overlapX = 200
    overlapY = 200

    cut(cutX, cutY, overlapX, overlapY)
    reconstruct(cutX, cutY, overlapX, overlapY)
    compare()