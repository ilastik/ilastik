from lazyflow.graph import Graph

import numpy as np
import vigra
from lazyflow.operators.opInterpMissingData import OpInterpMissingData

class TestInterpMissingData(object):

    def setUp(self):

        #Large block and one single Layer is empty
        d1 = vigra.VigraArray( np.ones((10,10,100)), axistags=vigra.defaultAxistags('xyz') )
        for i in range(100): d1[:,:,i]*=(i+1)
        d1[:,:,30:50]=0
        d1[:,:,70]=0
        
        #Fist block is empty
        d2=np.ones((10,10,100))
        for i in range(100): d2[:,:,i]*=(i+1)
        d2[:,:,0:10]=0

        #Last layer is empty
        d3=np.ones((10,10,100))
        for i in range(100): d3[:,:,i]*=(i+1)
        d3[:,:,99]=0

        #Second layer is empty
        d4=np.ones((10,10,100))
        for i in range(100): d4[:,:,i]*=(i+1)
        d4[:,:,1]=0

        #First layer is empty
        d5=np.ones((10,10,100))
        for i in range(100): d5[:,:,i]*=(i+1)
        d5[:,:,0]=0

        #Last layer empty
        d6=np.ones((10,10,100))
        for i in range(100): d6[:,:,i]*=(i+1)
        d6[:,:,99]=0

        #all layers are empty
        d7=np.zeros((10,10,100))

        #next to the layer is empty
        d8=np.ones((10,10,100))
        for i in range(100): d8[:,:,i]*=(i+1)
        d8[:,:,98]=0

        self.d1 = d1
        self.d2 = d2
        self.d3 = d3
        self.d4 = d4
        self.d5 = d5
        self.d6 = d6
        self.d7 = d7
        self.d8 = d8

    def testBasic(self):
        d1 = self.d1
        d2 = self.d2
        d3 = self.d3
        d4 = self.d4
        d5 = self.d5
        d6 = self.d6
        d7 = self.d7
        d8 = self.d8

        Ones=np.ones((10,10))
        g=Graph()
        op = OpInterpMissingData(graph = g)
        op.InputVolume.setValue( d1 )
        
        assert np.any(op.Output[:].wait()[:,:,40]==Ones*41)==True

        assert np.any(op.Output[:].wait()[:,:,70]==Ones*71)==True
    
        op.InputVolume.setValue( d2 )
        assert np.any(op.Output[:].wait()[:,:,4]==Ones*11)==True

        op.InputVolume.setValue( d3 )
        assert np.any(op.Output[:].wait()[:,:,99]==Ones*99)==True

        op.InputVolume.setValue( d4 )
        assert np.any(op.Output[:].wait()[:,:,1]==Ones*2)==True

        op.InputVolume.setValue( d5 )
        assert np.any(op.Output[:].wait()[:,:,0]==Ones*2)==True

        op.InputVolume.setValue( d6 )
        assert np.any(op.Output[:].wait()[:,:,99]==Ones*99)==True

        op.InputVolume.setValue( d7 )
        assert np.any(op.Output[:].wait()[:,:,50]==Ones*0)==True

        op.InputVolume.setValue( d8 )
        assert np.any(op.Output[:].wait()[:,:,98]==Ones*99)==True

    def testAxesReversed(self):
        d1 = self.d1.transpose()
        d2 = self.d2.transpose()
        d3 = self.d3.transpose()        
        d4 = self.d4.transpose()
        d5 = self.d5.transpose()
        d6 = self.d6.transpose()        
        d7 = self.d7.transpose()        
        d8 = self.d8.transpose()        



        Ones=np.ones((10,10))
        g=Graph()
        op = OpInterpMissingData(graph = g)
        op.InputVolume.setValue( d1 )
        
        assert np.any(op.Output[:].wait()[40,:,:]==Ones*41)==True

        assert np.any(op.Output[:].wait()[70,:,:]==Ones*71)==True
    
        op.InputVolume.setValue( d2 )
        assert np.any(op.Output[:].wait()[4,:,:]==Ones*11)==True

        op.InputVolume.setValue( d3 )
        assert np.any(op.Output[:].wait()[99,:,:]==Ones*99)==True

        op.InputVolume.setValue( d4 )
        assert np.any(op.Output[:].wait()[1,:,:]==Ones*2)==True

        op.InputVolume.setValue( d5 )
        assert np.any(op.Output[:].wait()[0,:,:]==Ones*2)==True

        op.InputVolume.setValue( d6 )
        assert np.any(op.Output[:].wait()[99,:,:]==Ones*99)==True

        op.InputVolume.setValue( d7 )
        assert np.any(op.Output[:].wait()[50,:,:]==Ones*0)==True

        op.InputVolume.setValue( d8 )
        assert np.any(op.Output[:].wait()[98,:,:]==Ones*99)==True
         
          
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
