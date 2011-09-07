import vigra
import h5py
from lazyflow.roi import *
import numpy
import os
from lazyflow import graph
from lazyflow.operators import *

#computes the smoothed datasets

origFile='scripts/CB_compressed_XY.h5'
destFile='scripts/smothedfiletestXY.h5'

if os.path.exists(destFile): os.remove(destFile)

f=h5py.File(origFile,'r')
d=f['volume/data']
start=[0,0,0,0,0]
stop=[1,128,128,20,1]
r=roiToSlice(start,stop)
data=d[r]

data=numpy.require(data,numpy.float32)

sigmas=[0.7,1,1.6,3.5,5]



fres=h5py.File(destFile,'w')
g=fres.create_group('volume')
tmp=g.create_dataset('data',shape=data.shape,data=data)
tmp.attrs['sigma']=0
i=1
for s in sigmas:
    

    d1=vigra.filters.gaussianSmoothing(data[0,:,:,:,0], s)
    d1.shape=(1,)+d1.shape

    d1=g.create_dataset('smoothed_%.2d'%(i),shape=d1.shape,data=d1)
    d1.attrs['sigma']=s
    i+=1
    
    #d1=vigra.filters.gaussianSmoothing(data[0,:,:,:,0], s*0.66)
    #d1.shape=(1,)+d1.shape
    #d1=g.create_dataset('smoothed_%.2d'%(i),shape=d1.shape,data=d1)

    #d1.attrs['sigma']=s*0.66
    #i+=1
    
    #d1=vigra.filters.gaussianSmoothing(data[0,:,:,:,0], s*0.5)
    #d1.shape=(1,)+d1.shape
    #d1=g.create_dataset('smoothed_%.2d'%(i),shape=d1.shape,data=d1)

    #d1.attrs['sigma']=s*0.5
    #i+=1





print 'Checking for sanity'

for el in sorted(fres.keys()):
    print "found group ", el
    g=fres[el]
    for el2 in sorted(g.keys()):
        print "found dataset ", el2
        for at in list(g[el2].attrs):
            print at + " ", g[el2].attrs[at]
            
        
    
f.close()
fres.close()



g=graph.Graph()


op=OpH5ReaderSmoothedDataset(g)
op.inputs['Filename'].setValue(destFile)
op.inputs['hdf5Path'].setValue('volume')
    
for i,out in enumerate(op.outputs['Sigmas']):
    print "sigma = ", op.outputs['Sigmas'][i][:].allocate().wait()
    print "data.shape = ", op.outputs['Outputs'][i][:].allocate().wait().shape
    print "data axistags "
    print "data.shape = ", op.outputs['Outputs'][i].axistags
    print "data.dtype = ", op.outputs['Outputs'][i][:].allocate().wait().dtype
    