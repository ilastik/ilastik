import numpy
from lazyflow.roi import determineBlockShape, getIntersection

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

class Test_getIntersection(object):
    
    def testBasic(self):
        roiA = [(10,10,10), (20,20,20)]
        roiB = [(15,16,17), (25,25,25)]
        intersection = getIntersection( roiA, roiB ) 
        assert (numpy.array(intersection) == ( [15,16,17], [20,20,20] )).all()

    def testAssertNonIntersect(self):
        roiA = [(10,10,10), (20,20,20)]
        roiB = [(15,26,27), (16,30,30)]
        try:
            intersection = getIntersection( roiA, roiB )
        except AssertionError:
            pass
        else: 
            assert False, "getIntersection() was supposed to assert because the parameters don't intersect!"

    def testNoAssertNonIntersect(self):
        roiA = [(10,10,10), (20,20,20)]
        roiB = [(15,26,27), (16,30,30)]
        intersection = getIntersection( roiA, roiB , assertIntersect=False)
        assert intersection is None, "Expected None because {} doesn't intersect with {}".format(  )

if __name__ == "__main__":
    # Run nose
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
