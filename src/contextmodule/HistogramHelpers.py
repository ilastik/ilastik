import numpy
import vigra
#"""
#def getHistOfRegion(upperLeft,lowerRight,H):
    #""""""
    #This function extracts the actual histogram of 
    #a region from the integral histogram
    #""""""
    
    #h,w,nc=H.shape    
    #p1m,p2m=upperLeft
    #p1p,p2p=lowerRight
    #p1p-=1
    #p2p-=1
    #print p1p,p2p,H.shape
    #res=H[p1p,p2p,:].copy()#-H[p1m,p2p]-H[p1p,p2m]+H[p1m,p2m] 
    ##print "here",res
    ##res+=H[0,p2p,:]+H[p1p,0,:]-H[p1m,0,:]-H[p1m,0,:]+H[0,0]
    #if p1m >0 and p2m>0:
        #res=H[p1p,p2p,:]-H[p1m-1,p2p,:]-H[p1p,p2m-1,:]+H[p1m-1,p2m-1,:] 
            
    
    #return res.astype(numpy.uint32)
#"""

def getHistOfRegion(upperLeft,lowerRight,H):
    """This function extracts the actual histogram of 
    a region from the integral histogram. The range is exlusive on lowerRight"""
    
    H = H.view(numpy.ndarray)
    p1x, p1y = upperLeft
    p2x, p2y = lowerRight
    
    nx = p2x-p1x
    ny = p2y-p2x
    res = numpy.zeros(H[p1x, p1y, :].shape, H.dtype)
    
    lr = H[p2x-1, p2y-1, :]
    ll = H[p1x-1, p2y-1, :] if p1x>0 else numpy.zeros((H.shape[2],))
    ur = H[p2x-1, p1y-1, :] if p1y>0 else numpy.zeros((H.shape[2],))
    ul = H[p1x-1, p1y-1, :] if p1x>0 and p1y>0 else numpy.zeros((H.shape[2],))
    
    res[:] = lr[:]-ll[:]-ur[:]+ul[:]
    
    return res.astype(numpy.uint32)


def histContext(radii,H):
    
    #Ginven histograms and radii return the context feature
    
    
    assert len(radii)%2==0, "Please even number of radii"
    
    h,w,c=H.shape
    
    res=numpy.zeros((h,w,(len(radii)-1)*c),dtype=numpy.uint32)
    
    for y in range(h):
        for x in range(w):
            for i in range(len(radii)-1):
                radiusp=radii[i+1]
                radiusm=radii[i]
                
                upleftp=(y-radiusp,x-radiusp)
                lowrightp=(y+radiusp+1,x+radiusp+1)
                
                upleftm=(y-radiusm,x-radiusm)
                lowrightm=(y+radiusm+1,x+radiusm+1)
                
                if x==10 and y==10:
                    print "here",upleftm,lowrightm,upleftp,lowrightp
                
                                
                res[y,x,i*c:(i+1)*c]=getHistOfRegion(upleftp,lowrightp,H)-getHistOfRegion(upleftm,lowrightm,H)
                if x==10 and y==10:
                    print "here",res[y,x,i*c:(i+1)*c]
                    print "larger ", getHistOfRegion(upleftp,lowrightp,H)
                    print "lower " , getHistOfRegion(upleftm,lowrightm,H)
                
    return res


