import random
from lazyflow.graph import *
import operators.qcOperators

if __name__ == "__main__":

    random.seed()
    z = 0
     
     
    def compareRequests(op,imgFull,imgPart,start,stop):        

        c = True
        
        global z   
        
        dim = len(stop)
        
        
        diff = []
        for i in range(dim):
            diff.append(stop[i]-start[i])
            
        ld = diff.index(max(diff))    
       
        size = 1
        for i in diff:
            size *= i


        bsize = random.randint(50000,90000)    
    
        if size < bsize:
            for i in range(dim):
                start[i] = int(start[i]+0.5)
                stop[i] = int(stop[i]+0.5)
            
            z +=1            
     
            req = op.outputs["Output"][roiToSlice(start,stop)].writeInto(imgPart[roiToSlice(start,stop)])
            res = req.wait()
            
            #vigra.impex.writeImage(res,"/net/gorgonzola/storage/cripp/lazyflow/lazyflow/examples/tt/result_%05d.jpg" %z)
            
            op.outputs["Output"][roiToSlice(start,stop)].writeInto(imgPart[roiToSlice(start,stop)]).wait()
            #vigra.impex.writeImage(imgPart,"/net/gorgonzola/storage/cripp/lazyflow/lazyflow/examples/tt/resultPart_%05d.jpg" %z)
        
            if not (imgFull[roiToSlice(start,stop)] == res).all():
                c = False
            return c


        p =  random.randint(2,20)
        step = diff[ld]/float(p)
        start[ld] -= step
        for i in range(p):
            start[ld] += step
            stop[ld] = start[ld] + step
            c = compareRequests(op,imgFull, imgPart,start[:],stop[:])    
        
        
        return c
    
    
    
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)


    op = operators.qcOperators.OpLabelToImage(g)

    a = numpy.array([[1,0,1,0,1,0,1,0],[0,1,0,1,0,1,0,1],[1,0,1,0,1,0,1,0],[0,1,0,1,0,1,0,1],[1,0,1,0,1,0,1,0],[0,1,0,1,0,1,0,1],[1,0,1,0,1,0,1,0],[0,1,0,1,0,1,0,1]])

    op.inputs["PatchWidth"].setValue(105)

    op.inputs["Input"].setValue(a)

    imgPart = numpy.zeros((840,840))
    dest = op.outputs["Output"][:].allocate().wait()
    
    #vigra.impex.writeImage(dest,"/net/gorgonzola/storage/cripp/lazyflow/lazyflow/examples/tt/resultFull.jpg")

    if compareRequests(op, dest,imgPart,[0,0],[840,840]):
        print "____________"
        print "operator works correctly"
        print "____________"
    else:
        print "____________"
        print "operator doesn't work correctly"
        print "____________"

    g.finalize()