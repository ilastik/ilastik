import vigra
import threading
from lazyflow.graph import *
import copy

from lazyflow import operators


if __name__=="__main__":
    
   
    filename='ostrich.jpg'
    
    
    
    g = Graph()

            
    vimageReader = operators.OpImageReader(g)
    vimageReader.inputs["Filename"].setValue(filename)
    
    subregion = operators.OpSubRegion(g)
    
    subregion.inputs["Input"].connect(vimageReader.outputs["Image"])
    subregion.inputs["Start"].setValue((100,100,0))
    subregion.inputs["Stop"].setValue((200,200,0))
    
    res = subregion.outputs["Output"][:].allocate().wait()
    
    print res.shape
    
    import pylab    
    pylab.imshow(res[:])    
    pylab.show()
    
    g.finalize()
