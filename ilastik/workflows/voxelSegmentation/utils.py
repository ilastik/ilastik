import logging

import numpy as np


logger = logging.getLogger('default')


def log(s):
    logger.info(s)


def get_supervoxel_features(featuresMatrix, supervoxel_mask):
    N_voxels = np.max(supervoxel_mask) + 1
    N_features = featuresMatrix.shape[1]
    supervoxel_features = np.ndarray((N_voxels, N_features))  # +8 is for the 3 features that are  3-dimensional

    # Parallelize by mapping over supervoxels
    for v in range(N_voxels):
        supervoxel_features[v, :N_features] = np.mean(featuresMatrix[:, supervoxel_mask == v], axis=1)
        return supervoxel_features


def get_supervoxel_labels(labels, supervoxel_mask):
    return [np.average(labels[supervoxel_mask == v]) >= 127 for v in range(np.max(supervoxel_mask) + 1)]


def slic_to_mask(slic_segmentation, supervoxel_values):
    out = np.zeros(slic_segmentation.shape, dtype=np.int)
    for (i, v) in enumerate(supervoxel_values):
        if v:
            out[slic_segmentation == i] = 255
    return out
