import numpy
from lazyflow.roi import determineBlockShape

class Test_determineBlockShape(object):
    
    def testBasic(self):
        max_shape = (1000,1000,1000,1)
        block_shape = determineBlockShape( max_shape, 1e6 )
        assert block_shape == (100,100,100,1), "Got {}, expected (100,100,100,1)".format(block_shape)
        
    def testBasic2(self):
        max_shape = (1,100,5,200,3)
        block_shape = determineBlockShape( max_shape, 1000 )
        assert block_shape == (1,8,5,8,3)


    def testSmallMax(self):
        # In this case, the target size is too large for the given max_shape
        # Therefore, block_shape == max_shape
        max_shape = (1,2,3,2,1)
        block_shape = determineBlockShape( max_shape, 1000 )
        assert block_shape == max_shape

    def testInvalidMax(self):
        try:
            max_shape =  (1,2,3,2,0)
            determineBlockShape( max_shape, 1000 )
        except AssertionError:
            pass
        except Exception as e:
            assert False, "Wrong type of exception.  Expected AssertionError, but got {}".format( e )
        else:
            assert False, "Expected assertion in determineBlockShape() due to invalid inputs"


if __name__ == "__main__":
    # Run nose
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
