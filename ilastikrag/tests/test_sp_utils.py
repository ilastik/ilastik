import numpy as np
import nose

from lazyflow.utility.sp_utils import label_vol_mapping

def test_label_vol_mapping():
    # 1 2
    # 3 4    
    vol1 = np.zeros((20,20), dtype=np.uint8)
    vol1[ 0:10,  0:10] = 1
    vol1[ 0:10, 10:20] = 2
    vol1[10:20,  0:10] = 3
    vol1[10:20, 10:20] = 4

    # 2 3
    # 4 5
    vol2 = vol1.copy() + 1
    
    assert (label_vol_mapping(vol1, vol2) == [0,2,3,4,5]).all()
    assert (label_vol_mapping(vol1[3:], vol2[:-3]) == [0,2,3,4,5]).all()
    assert (label_vol_mapping(vol1[6:], vol2[:-6]) == [0,2,3,2,3]).all()
    
    # 7 7
    # 4 5
    vol2[( vol2 == 2 ).nonzero()] = 7
    vol2[( vol2 == 3 ).nonzero()] = 7

    assert (label_vol_mapping(vol1, vol2) == [0,7,7,4,5]).all()

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
