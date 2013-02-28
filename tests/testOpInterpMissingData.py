from lazyflow.graph import Graph

import numpy as np
import vigra
from lazyflow.operators.opInterpMissingData import OpInterpMissingData

class TestInterpMissingData(object):

    def setUp(self):
        #Large Block + 1 Layer is missing
        d1 = vigra.VigraArray( np.ones((10,10,100)), axistags=vigra.defaultAxistags('xyz') )
        for i in range(100): d1[:,:,i]*=(i+1)
        d1[:,:,30:50]=0
        d1[:,:,70]=0
        

        #Fist Block is missing
        d2=np.ones((10,10,100))
        for i in range(100): d2[:,:,i]*=(i+1)
        d2[:,:,0:10]=0

        #Last Layer is missing
        d3=np.ones((10,10,100))
        for i in range(100): d3[:,:,i]*=(i+1)
        d3[:,:,99]=0

        self.d1 = d1
        self.d2 = d2
        self.d3 = d3

    def testBasic(self):
        d1 = self.d1
        d2 = self.d2
        d3 = self.d3

        Ones=np.ones((10,10))
        g=Graph()
        op = OpInterpMissingData(graph = g)
        op.InputVolume.setValue( d1 )
        
        #Layer in center of large black Block
        assert np.any(op.Output[:].wait()[:,:,40]==Ones*41)==True

        #Single Layer
        assert np.any(op.Output[:].wait()[:,:,70]==Ones*71)==True
    
        #First Layers 
        op.InputVolume.setValue( d2 )
        assert np.any(op.Output[:].wait()[:,:,4]==Ones*11)==True

        #Last Layer
        op.InputVolume.setValue( d3 )
        assert np.any(op.Output[:].wait()[:,:,99]==Ones*99)==True

    def testAxesReversed(self):
        d1 = self.d1.transpose()
        d2 = self.d2.transpose()
        d3 = self.d3.transpose()        

        Ones=np.ones((10,10))
        g=Graph()
        op = OpInterpMissingData(graph = g)
        op.InputVolume.setValue( d1 )
        
        #Layer in center of large black Block
        assert np.any(op.Output[:].wait()[40,:,:]==Ones*41)==True

        #Single Layer
        assert np.any(op.Output[:].wait()[70,:,:]==Ones*71)==True
    

        #First Layers 
        op.InputVolume.setValue( d2 )
        assert np.any(op.Output[:].wait()[4,:,:]==Ones*11)==True

        #Last Layer
        op.InputVolume.setValue( d3 )
        assert np.any(op.Output[:].wait()[99,:,:]==Ones*99)==True

      
      
          
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
