import numpy, vigra
import time
from lazyflow import graph
import gc
from lazyflow import roi
import sys
import copy

from lazyflow.operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper, OpMultiMultiArrayPiper



from lazyflow.operators import *

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

g = graph.Graph(8,5*2000*1024**2)



fileNames=['scripts/CB_compressed_XY.h5']

reader=OpH5ReaderBigDataset(g)
reader.inputs["Filenames"].setValue(fileNames)
reader.inputs["hdf5Path"].setValue("volume/data")




#sigmas=[0.7,1,1.6,3.5,5]
sigmas = [0.3, 10]
operators=[]
resFolder='/media/96A669B1A6699293/features_knott/'

resultfileNames=[]

print "Connecting the operators"

multi=OpNToMulti(g,50)

count=0
for s in sigmas:
    
    op=OpGaussianSmoothing(g)
    op.inputs['sigma'].setValue(s)
    op.inputs['Input'].connect(reader.outputs['Output'])
    operators.append(op)
    filename=op.name+"_sigma_"+str(s)+'_.h5'
    resultfileNames.append(filename)
    multi.inputs['Input'+str(count)].connect(op.outputs['Output'])
    count+=1
    
    '''
    op=OpHessianOfGaussianEigenvalues(g)
    op.inputs['scale'].setValue(s)
    op.inputs['Input'].connect(reader.outputs['Output'])
    operators.append(op)
    filename=op.name+"_scale_"+str(s)+'_.h5'
    resultfileNames.append(filename)
    multi.inputs['Input'+str(count)].connect(op.outputs['Output'])
    count+=1
    

    op=OpGaussianGradientMagnitude(g)
    op.inputs['sigma'].setValue(s)
    op.inputs['Input'].connect(reader.outputs['Output'])
    operators.append(op)
    filename=op.name+"_sigma_"+str(s)+'_.h5'
    resultfileNames.append(filename)
    multi.inputs['Input'+str(count)].connect(op.outputs['Output'])
    count+=1
    
    
    op=OpLaplacianOfGaussian(g)
    op.inputs['scale'].setValue(s)
    op.inputs['Input'].connect(reader.outputs['Output'])
    operators.append(op)
    filename=op.name+"_scale_"+str(s)+'_.h5'
    resultfileNames.append(filename)
    multi.inputs['Input'+str(count)].connect(op.outputs['Output'])
    count+=1
    
    
    op=OpStructureTensorEigenvalues(g)
    op.inputs['innerScale'].setValue(s)
    op.inputs['outerScale'].setValue(s/2)
    op.inputs['Input'].connect(reader.outputs['Output'])
    operators.append(op)
    filename=op.name+"_innerScale_"+str(s)+"_outerScale_"+str(s/2)+'_.h5'
    resultfileNames.append(filename)
    multi.inputs['Input'+str(count)].connect(op.outputs['Output'])
    count+=1
    
    
    op=OpDifferenceOfGaussians(g)
    op.inputs['sigma0'].setValue(s)
    op.inputs['sigma1'].setValue(s*0.66)
    op.inputs['Input'].connect(reader.outputs['Output'])
    operators.append(op)
    filename=op.name+"_sigma0_"+str(s)+"_sigma1_"+str(s*0.66)+'_.h5'
    resultfileNames.append(filename)
    multi.inputs['Input'+str(count)].connect(op.outputs['Output'])
    count+=1
    '''
#Stack all of them together and put also the stacker in the bunch
'''
op=OpMultiArrayStacker(g)
op.inputs['Images'].connect(multi.outputs['Outputs'])
op.inputs['AxisFlag'].setValue('c')
op.inputs['AxisIndex'].setValue(4)
operators.append(op)
filename=op.name+'_gsm_.h5'
resultfileNames.append(filename)
'''

writerList=[]
for i,op in enumerate(operators):
    writer=OpH5WriterBigDataset(g)
    writer.inputs['Filename'].setValue(resFolder+resultfileNames[i])
    writer.inputs['hdf5Path'].setValue('volume/data')
    #print op.name, op.outputs['Output']
    writer.inputs['Image'].connect(op.outputs['Output'])
    writerList.append(writer)


for w in writerList:
    w.outputs["WriteImage"][0].allocate().wait()
    w.close()
    print "Here - -- - -"

g.finalize()