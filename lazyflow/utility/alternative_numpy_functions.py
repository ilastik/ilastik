import vigra
import numpy as np
    
def vigra_bincount(labels):
    """
    A RAM-efficient implementation of numpy.bincount() when you're dealing with uint32 labels.
    If your data isn't int64, numpy.bincount() will copy it internally -- a huge RAM overhead.
    (This implementation may also need to make a copy, but it prefers uint32, not int64.)
    """
    labels = labels.astype(np.uint32, copy=False)
    labels = np.ravel(labels, order='K').reshape((-1, 1), order='A')
    # We don't care what the 'image' parameter is, but we have to give something
    image = labels.view(np.float32)
    counts = vigra.analysis.extractRegionFeatures(image, labels, ['Count'])['Count']
    return counts.astype(np.int64)

if __name__ == "__main__":
    a = np.random.randint(0,100, size=(100,100))
    assert (np.bincount(a.flat) == vigra_bincount(a)).all()
    print "DONE."
