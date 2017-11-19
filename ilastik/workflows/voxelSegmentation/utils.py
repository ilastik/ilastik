import logging

import numpy as np

from . import features

logger = logging.getLogger('default')


def log(s):
    logger.info(s)


def get_supervoxel_features(featuresMatrix, image, supervoxel_mask):

    N_voxels = np.max(supervoxel_mask) + 1
    N_features = 2

    supervoxel_features = np.ndarray((N_voxels, N_features))  # +8 is for the 3 features that are  3-dimensional
    print("svf shape {}".format(supervoxel_features.shape))
    print("featm shape {}".format(featuresMatrix.shape))
    # Parallelize by mapping over supervoxels

    filters = []

    for ffilter in features.FASTFILTERS:
        for params in ffilter["params"]:
            filters.append(
                {
                    "function": ffilter["function"],
                    "name": ffilter["name"],
                    "params": params,
                }
            )

    def build_feature(filter):
        #         log("feature: {}".format(filter["name"]))
        feature = filter["function"](image, window_size=3.5, **filter['params'])
        return feature

    voxelfeatures = []

    for f in filters:
        feature = build_feature(f)
        if len(feature.shape) == 4:
            for dimension in range(feature.shape[3]):
                voxelfeatures.append(feature[:, :, :, dimension])
        else:
            voxelfeatures.append(feature)

    voxelfeatures = np.stack(voxelfeatures)

    for v in range(N_voxels):
        # print(voxelfeatures.shape)
        # print(supervoxel_features.shape)
        # print(supervoxel_mask[:, :, :, 0].shape)
        supervoxel_features[v, :N_features] = np.mean(voxelfeatures[:, supervoxel_mask[:, :, :, 0] == v], axis=1)
        return supervoxel_features


def get_supervoxel_labels(labels, supervoxel_mask):
    supervoxel_mask = supervoxel_mask[:, :, :, 0]
    print("labels {}".format(labels.shape))
    return [np.bincount(labels[supervoxel_mask == v].ravel()).argmax() for v in range(np.max(supervoxel_mask) + 1)]


def slic_to_mask(slic_segmentation, supervoxel_values):
    out = np.zeros(slic_segmentation.shape, dtype=supervoxel_values.dtype)
    for (i, v) in enumerate(supervoxel_values):
        if v:
            out[slic_segmentation == i] = v
    return out
