from __future__ import print_function
from builtins import range
import vigra
import numpy as np


def vigra_bincount(labels):
    """
    A RAM-efficient implementation of numpy.bincount() when you're dealing with uint32 labels.
    If your data isn't int64, numpy.bincount() will copy it internally -- a huge RAM overhead.
    (This implementation may also need to make a copy, but it prefers uint32, not int64.)
    """
    labels = labels.astype(np.uint32, copy=False)
    labels = np.ravel(labels, order="K").reshape((-1, 1), order="A")
    # We don't care what the 'image' parameter is, but we have to give something
    image = labels.view(np.float32)
    counts = vigra.analysis.extractRegionFeatures(image, labels, ["Count"])["Count"]
    return counts.astype(np.int64)


def chunked_bincount(labels):
    """
    An even more RAM-efficient bincount.
    The array is processed in small(ish) pieces,
    to avoid copying the whole thing at once.
    """
    labels = np.ravel(labels, order="K").reshape((-1,), order="A")

    global_counts = np.array([]).astype(np.int64)

    CHUNK_SIZE = 100 * (2 ** 20)
    for chunk_start in range(0, len(labels), CHUNK_SIZE):
        chunk_stop = min(chunk_start + CHUNK_SIZE, len(labels))
        chunk_counts = vigra_bincount(labels[chunk_start:chunk_stop])

        if len(chunk_counts) > len(global_counts):
            chunk_counts, global_counts = global_counts, chunk_counts

        global_counts[: len(chunk_counts)] += chunk_counts

    return global_counts


if __name__ == "__main__":
    a = np.random.randint(0, 100, size=(100, 100))
    assert (np.bincount(a.flat) == vigra_bincount(a)).all()
    assert (np.bincount(a.flat) == chunked_bincount(a)).all()
    print("DONE.")
