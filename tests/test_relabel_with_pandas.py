import nose
import numpy as np
from lazyflow.utility import relabel_with_pandas

try:
    import pandas as pd
    _pandas_available = True
except ImportError:
    _pandas_available = False

###
### Oracle function, for verifying results
###
def relabel_via_vectorize(labels, mapping):
    vectorized_relabel = np.vectorize(mapping.__getitem__)
    return vectorized_relabel( labels )    

# def relabel_via_indexarray(labels, mapping):
#     """
#     This is an alternative pure-python function,
#     way faster than the 'vectorize' version for small mappings,
#     but slower for really huge maps.
#     """
#     from itertools import chain
#     sorted_mapping = np.fromiter( chain(mapping.iterkeys(), mapping.itervalues()), dtype=labels.dtype )
#     sorted_mapping.shape = (2, -1)
#     sorted_mapping.sort(axis=0)
#     consecutivized_labels = np.searchsorted( sorted_mapping[0], labels )
#     return sorted_mapping[1][consecutivized_labels]

class Test_relabel_with_pandas(object):
    
    def setUp(self):
        if not _pandas_available:
            raise nose.SkipTest("pandas not available")
    
    def test_inplace(self):
        labels = np.random.randint(0,256, (100,100)).astype(np.uint32)
        mapping = { x : (x+100)%256 for x in range(256) }
    
        expected = relabel_via_vectorize(labels, mapping)
        relabel_with_pandas(labels, mapping, out=labels)
        assert (labels == expected).all()

    def test_not_inplace(self):
        labels = np.random.randint(0,256, (100,100)).astype(np.uint32)
        mapping = { x : (x+100)%256 for x in range(256) }
    
        expected = relabel_via_vectorize(labels, mapping)
        labels = relabel_with_pandas(labels, mapping)
        assert (labels == expected).all()

    def test_different_outparam(self):
        labels = np.random.randint(0,256, (100,100)).astype(np.uint32)
        mapping = { x : (x+100)%256 for x in range(256) }
    
        out = np.empty_like(labels)
        expected = relabel_via_vectorize(labels, mapping)
        newlabels = relabel_with_pandas(labels, mapping, out)
        assert newlabels is out
        assert (newlabels == expected).all()

    def test_bigger_output_dtype(self):
        # labels is uint16, result is uint32,
        # and mapping requires the bigger output dtype
        labels = np.random.randint(0,256, (100,100)).astype(np.uint16)
        mapping = { x : x+1000000 for x in range(256) }
    
        out = np.empty_like(labels, dtype=np.uint32)
        expected = labels.astype(np.uint32) + 1000000
        newlabels = relabel_with_pandas(labels, mapping, out)
        assert newlabels is out
        assert (newlabels == expected).all()

    def test_smaller_output_dtype(self):
        # labels is uint32, result is uint16,
        # and mapping requires the bigger input dtype
        labels = np.random.randint(1000000,1000256, (100,100)).astype(np.uint32)
        mapping = { x : x-1000000 for x in range(1000000,1000256) }
    
        out = np.empty_like(labels, dtype=np.uint16)
        expected = labels - 1000000
        newlabels = relabel_with_pandas(labels, mapping, out)
        assert newlabels is out
        assert (newlabels == expected).all()

    def test_noncontiguous_output(self):
        labels = np.random.randint(0,256, (100,100)).astype(np.uint32)
        mapping = { x : (x+100)%256 for x in range(256) }
    
        out = np.zeros( shape=(101, 101), dtype=np.uint32 )[:100,:100]
        assert not out.flags.contiguous
        expected = relabel_via_vectorize(labels, mapping)
        newlabels = relabel_with_pandas(labels, mapping, out)
        assert newlabels is out
        assert (newlabels == expected).all()

    def test_noncontiguous_input(self):
        labels = np.random.randint(0,256, (100,100)).astype(np.uint32)
        labels = labels[:90, :90]
        assert not labels.flags.contiguous
        mapping = { x : (x+100)%256 for x in range(256) }
    
        out = np.empty_like(labels)
        expected = relabel_via_vectorize(labels, mapping)
        newlabels = relabel_with_pandas(labels, mapping, out)
        assert newlabels is out
        assert (newlabels == expected).all()

    def test_noncontiguous_input_and_output(self):
        labels = np.random.randint(0,256, (100,100)).astype(np.uint32)
        labels = labels[:90, :90]
        assert not labels.flags.contiguous
        mapping = { x : (x+100)%256 for x in range(256) }
    
        out = np.zeros( shape=(101, 101), dtype=np.uint32 )[:90,:90]
        assert not out.flags.contiguous
        expected = relabel_via_vectorize(labels, mapping)
        newlabels = relabel_with_pandas(labels, mapping, out)
        assert newlabels is out
        assert (newlabels == expected).all()

    def test_disallow_incompatible_dtypes(self):
        labels = np.random.randint(0,256, (100,100)).astype(np.uint32)
        mapping = { x : (x+100)%256 for x in range(256) }
    
        out = np.empty_like(labels, dtype=np.float32)
        try:
            relabel_with_pandas(labels, mapping, out)
        except AssertionError:
            pass
        else:
            assert False, "relabel should have failed: outparam has an incompatible dtype"
        
    def test_disallow_incompatible_shapes(self):
        labels = np.random.randint(0,256, (100,100)).astype(np.uint32)
        mapping = { x : (x+100)%256 for x in range(256) }
    
        out = np.zeros((50,50), dtype=np.uint32)
        try:
            relabel_with_pandas(labels, mapping, out)
        except AssertionError:
            pass
        else:
            assert False, "relabel should have failed: out param has an incompatible shape"
        

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
