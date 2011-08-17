import numpy
from contextcpp import *
from HistogramHelpers import *



def HaarWaveletFirstOrder(scale,H):   
    
    
    scale=list(scale)
    
    h,w,c=H.shape
    
    if len(scale)==2:
        v,o=tuple(numpy.array(scale)/2)
    else:
        v=o=scale/2   
    
    res=numpy.zeros((h,w,c),dtype=numpy.uint32)
    
    for y in range(h):
        for x in range(w):    
                
            upleftp=(y-v,x-o)
            lowrightp=(y+v+1,x)    
            upleftm=(y-v,x)
            lowrightm=(y+v+1,x+o+1)
            
            print "HERE", upleftp,lowrightp,upleftm,lowrightm
                                
            res[y,x,:]=getHistOfRegion(upleftp,lowrightp,H)-getHistOfRegion(upleftm,lowrightm,H)
            
            print "HERE", getHistOfRegion(upleftp,lowrightp,H)
            print "fakfdjkh", getHistOfRegion(upleftp,lowrightp,H)
            
            
            
    return res



def HaarWaveletSecondOrder(scale,H):   
    
    
    scale=list(scale)
    
    h,w,c=H.shape
    
    if len(scale)==2:
        v,o=tuple(numpy.array(scale)/2)
    else:
        v=o=scale/2   
    
    res=numpy.zeros((h,w,c),dtype=numpy.uint32)
    
    for y in range(h):
        for x in range(w):    
                
            upleftp=(y-v,x-o+1)
            lowrightp=(y+1,x+o+1)    
            upleftm=(y,x-o+1)
            lowrightm=(y+v+1,x+o+1)
                                
            res[y,x,:]=getHistOfRegion(upleftp,lowrightp,H)-getHistOfRegion(upleftm,lowrightm,H)

    return res




    
def HaarWaveletThirdOrder(scale,H):   
    scale=list(scale)
    
    h,w,c=H.shape
    
    if len(scale)==2:
        v,o=tuple(numpy.array(scale))
        o=o/3
        v=v/2
    else:
        v=scale/2
        o=scale/3  
    
    res=numpy.zeros((h,w,c),dtype=numpy.uint32)
    
    for y in range(h):
        for x in range(w):    
                
            upleftp1=(y-v,x-o-o/2)
            lowrightp1=(y+v+1,x-o/2+1)    
            
            upleftm=(y-v,x-o/2)
            lowrightm=(y+v+1,x+o/2+1)
            
            upleftp2=(y-v,x+o/2)
            lowrightp2=(y+v+1,x+o+o/2+1)    
            
                                
            res[y,x,:]=getHistOfRegion(upleftp1,lowrightp1,H)+getHistOfRegion(upleftp2,lowrightp2,H)-getHistOfRegion(upleftm,lowrightm,H)

    return res


def HaarWaveletForthOrder(scale,H):   
    scale=list(scale)
    
    h,w,c=H.shape
    
    if len(scale)==2:
        v,o=tuple(numpy.array(scale)/2)
    else:
        v=o=scale/2 
    
    res=numpy.zeros((h,w,c),dtype=numpy.uint32)
    
    for y in range(h):
        for x in range(w):    
                
            upleftp1=(y-v,x-o)
            lowrightp1=(y+1,x+1)    
            
            upleftm1=(y-v,x)
            lowrightm1=(y+1,x+o+1)
            
            upleftm2=(y,x-o)
            lowrightm2=(y+v+1,x+1)
            
            
            upleftp2=(y,x)
            lowrightp2=(y+v+1,x+o+1)    
            
                                
            res[y,x,:]=getHistOfRegion(upleftp1,lowrightp1,H)+getHistOfRegion(upleftp2,lowrightp2,H)-getHistOfRegion(upleftm1,lowrightm1,H)-getHistOfRegion(upleftm2,lowrightm2,H)

    return res