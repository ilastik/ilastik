import logging
import time

from pathos import multiprocessing
import numpy as np

logger = logging.getLogger(__name__)


def timeit(method):
    def timed(*args, **kw):
        ts = time.perf_counter()
        result = method(*args, **kw)
        t = time.perf_counter() - ts
        logger.info(f"{method.__name__} took {t:.2f} ms")
        return result

    return timed


@timeit
def get_supervoxel_features(featuresMatrix, supervoxel_mask):

    N_voxels = np.max(supervoxel_mask) + 1
    N_features = featuresMatrix.shape[-1]

    supervoxel_features = np.ndarray((N_voxels, N_features))
    # Parallelize by mapping over supervoxels

    for v in range(N_voxels):
        supervoxel_features[v, :N_features] = np.mean(featuresMatrix[supervoxel_mask[:, :, :, 0] == v, :], axis=0)

    return supervoxel_features


@timeit
def get_supervoxel_labels(labels, supervoxel_mask):
    supervoxel_mask = supervoxel_mask[:, :, :, 0]

    N_supervoxels = np.max(supervoxel_mask) + 1
    supervoxel_labels = np.ndarray((N_supervoxels,))

    for supervoxel in range(N_supervoxels):
        counts = np.bincount(labels[supervoxel_mask == supervoxel].ravel())

        # Little trick to avoid labelling a supervoxel as unlabelled if only a small part of it has been labelled
        if len(counts) == 1:  # or max(counts[1:]) == 0:
            # If there's only unlabelled pixels, label 0 (=unlabeled)
            label = 0
        else:
            # Else, return the label which has the most pixels (excluding label 0)
            label = counts[1:].argmax() + 1

        supervoxel_labels[supervoxel] = label
    return supervoxel_labels


@timeit
def slic_to_mask(slic_segmentation, supervoxel_values):
    num_cores = multiprocessing.cpu_count()

    slices = np.array_split(slic_segmentation, num_cores * 16)

    @timeit
    def compute(slice_):
        shape = slice_.shape + (supervoxel_values.shape[-1],)
        slice_out = np.zeros(shape, dtype=supervoxel_values.dtype)
        for (i, v) in enumerate(supervoxel_values):
            slice_out[slice_ == i, :] = v[:]
        return slice_out

    pool = multiprocessing.Pool(num_cores * 4)

    slices_out = pool.map(compute, slices)
    pool.close()
    return np.concatenate(slices_out)
