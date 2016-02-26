import numpy as np
from lazyflow.utility import relabel_consecutive

def test_relabel_consecutive():
    labels = np.array([1,1,2,3], dtype=np.uint32)
    relabeled = relabel_consecutive(labels, start_label=1)
    assert (relabeled == [1,1,2,3]).all()
    assert relabeled is not labels
    relabeled = relabel_consecutive(labels, start_label=1, out=labels)
    assert (relabeled == [1,1,2,3]).all()
    assert relabeled is labels
    relabeled = relabel_consecutive(labels, start_label=0)
    assert (relabeled == [0,0,1,2]).all()
    assert relabeled is not labels
    relabeled = relabel_consecutive(labels, start_label=0, out=labels)
    assert (relabeled == [0,0,1,2]).all()
    assert relabeled is labels

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
