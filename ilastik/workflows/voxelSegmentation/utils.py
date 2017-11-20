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


def slic_to_mask(slic_segmentation, supervoxel_values):
    shape = slic_segmentation.shape + (supervoxel_values.shape[-1],)
    out = np.zeros(shape, dtype=supervoxel_values.dtype)
    for (i, v) in enumerate(supervoxel_values):
        out[slic_segmentation == i, :] = v[:]
    return out
