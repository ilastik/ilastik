from lazyflow.graph import Graph

import numpy as np
from lazyflow.operators.opInterpMissingData import OpInterpMissingData

class TestInterpMissingData(object):
    def setUp(self):
        
        #Large Block + 1 Layer is missing
        self.d1=np.ones((10,10,100))
        for i in range(100): self.d1[:,:,i]*=(i+1)
        self.d1[:,:,30:50]=0
        self.d1[:,:,70]=0
        

        #Fist Block is missing
        self.d2=np.ones((10,10,100))
        for i in range(100): self.d2[:,:,i]*=(i+1)
        self.d2[:,:,0:10]=0

        #Last Layer is missing
        self.d3=np.ones((10,10,100))
        for i in range(100): self.d3[:,:,i]*=(i+1)
        self.d3[:,:,99]=0



    def testStuff(self):

        Ones=np.ones((10,10))
        g=Graph()
        op = OpInterpMissingData(graph = g)


        op.InputVolume.setValue( self.d1 )
        
        #Layer in center of large black Block
        assert np.any(op.Output[:].wait()[:,:,40]==Ones*41)==True

        #Single Layer
        assert np.any(op.Output[:].wait()[:,:,70]==Ones*71)==True
    

        #First Layers 
        op.InputVolume.setValue( self.d2 )
        assert np.any(op.Output[:].wait()[:,:,4]==Ones*11)==True

        #Last Layer
        op.InputVolume.setValue( self.d3 )
        assert np.any(op.Output[:].wait()[:,:,99]==Ones*99)==True
      
      
      
          
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
