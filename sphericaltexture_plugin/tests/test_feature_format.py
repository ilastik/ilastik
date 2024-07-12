import random
from typing import Dict, List, Tuple

import numpy as np
import numpy.typing as npt
import pytest
import vigra
from sphericaltexture_plugin.objfeat_sphericaltexture import ObjFeatSphericalTexture


def image_data_2d():
    return vigra.taggedView(np.random.randint(0, 256, (128, 256, 1, 1)), axistags="xyzc")


def image_data_3d():
    return vigra.taggedView(np.random.randint(0, 256, (128, 256, 32, 1)), axistags="xyzc")


def image_data_2d_multichannel():
    return vigra.taggedView(np.random.randint(0, 256, (128, 256, 1, 6)), axistags="xyzc")


def image_data_3d_multichannel():
    return vigra.taggedView(np.random.randint(0, 256, (128, 256, 32, 7)), axistags="xyzc")


def bbox_coords_2d():
    return np.array([[2, 2, 0], [50, 20, 0]]), np.array([[5, 5, 1], [60, 80, 1]])


def bbox_coords_3d():
    return np.array([[4, 2, 2], [50, 20, 10]]), np.array([[8, 5, 5], [60, 80, 20]])


def label_data_2d():
    labels = vigra.taggedView(np.zeros((128, 256, 1), dtype="uint32"), axistags="xyz")
    for i, (minc, maxc) in enumerate(zip(*bbox_coords_2d())):
        labels[tuple(slice(mi, ma) for mi, ma in zip(minc, maxc))] = i + 1
    return labels


def label_data_3d():
    labels = vigra.taggedView(np.zeros((128, 256, 32), dtype="uint32"), axistags="xyz")
    for i, (minc, maxc) in enumerate(zip(*bbox_coords_3d())):
        coords = tuple(slice(mi, ma) for mi, ma in zip(minc, maxc))
        labels[coords] = i + 1
    return labels


def objects_with_margin_2d(image):
    # margin is 2, 2
    margin = 2
    labels = label_data_2d()

    min_coords, max_coords = bbox_coords_2d()
    min_coords[:, 0:2] -= margin
    max_coords[:, 0:2] += margin

    objects = []

    for i, (minc, maxc) in enumerate(zip(min_coords, max_coords)):
        img = image[tuple(slice(mi, ma) for mi, ma in zip(minc, maxc))]
        binbb = labels[tuple(slice(mi, ma) for mi, ma in zip(minc, maxc))] == i + 1
        objects.append((img, binbb))

    return objects


def objects_with_margin_3d(image):
    # margin is 2, 2, 2
    margin = 2
    labels = label_data_3d()

    min_coords, max_coords = bbox_coords_3d()
    min_coords -= margin
    max_coords += margin

    objects = []

    for i, (minc, maxc) in enumerate(zip(min_coords, max_coords)):
        img = image[tuple(slice(mi, ma) for mi, ma in zip(minc, maxc))]
        binbb = labels[tuple(slice(mi, ma) for mi, ma in zip(minc, maxc))] == i + 1
        objects.append((img, binbb))

    return objects


@pytest.mark.parametrize(
    "image, labels, axes",
    [
        (image_data_2d(), label_data_2d(), "xyzc"),
        (image_data_2d_multichannel(), label_data_2d(), "xyzc"),
        (image_data_3d(), label_data_3d(), "xyzc"),
        (image_data_3d_multichannel(), label_data_3d(), "xyzc"),
    ],
    ids=["2D", "2D-multichannel", "3D", "3D-multichannel"],
)
class TestGlobalFeatureFormat:
    def test_features_can_be_computed_global(self, image, labels, axes):
        """Test if all features can be computed"""
        feature_plugin = ObjFeatSphericalTexture()
        available = feature_plugin.availableFeatures(image, labels)

        computed_features_global = feature_plugin.compute_global(image, labels, available, axes)

        expected_global_features = {k: v for k, v in available.items() if "margin" not in v}

        assert computed_features_global.keys() == expected_global_features.keys()

    def test_features_shape(self, image, labels, axes):
        """Check that each feature returns an array of shape (n_objs, n_feat_val)

        often n_feat_val is 1, but can be more.
        """
        feature_plugin = ObjFeatSphericalTexture()
        available = feature_plugin.availableFeatures(image, labels)
        computed_features_global = feature_plugin.compute_global(image, labels, available, axes)

        # in ilastik we expect that 0 will be ignored by feature computation
        n_objs = len([x for x in np.unique(labels) if x != 0])
        failures = []
        for k, v in computed_features_global.items():
            if len(v.shape) != 2:
                failures.append((k, f"Dimension mismatch, expected two dimensions, got {v.shape}."))
                continue

            if v.shape[0] != n_objs:
                failures.append((k, f"Expected features for {n_objs} objects, got {v.shape[0]}."))

        if failures:
            msg = "\n".join([f"{k}: {msg}" for k, msg in failures])
            raise AssertionError(msg)

    def test_fill_properties(self, image, labels, axes):
        feature_plugin = ObjFeatSphericalTexture()
        available = feature_plugin.availableFeatures(image, labels)

        rnd_feature_names = random.sample(list(available.keys()), k=min(len(available) - 1, 3))

        props = feature_plugin.fill_properties({k: available[k] for k in rnd_feature_names})

        assert len(props) == len(rnd_feature_names)

        assert all(x in props for x in rnd_feature_names)


@pytest.mark.parametrize(
    "objects, margin, axes",
    [
        (objects_with_margin_2d(image_data_2d()), (2, 2), "xyzc"),
        (objects_with_margin_2d(image_data_2d_multichannel()), (2, 2), "xyzc"),
        (objects_with_margin_3d(image_data_3d()), (2, 2, 2), "xyzc"),
        (objects_with_margin_3d(image_data_3d_multichannel()), (2, 2, 2), "xyzc"),
    ],
    ids=["2D", "2D-multichannel", "3D", "3D-multichannel"],
)
class TestLocalFeatureFormat:

    def test_local_features(self, objects, margin, axes):
        """Test if all features can be computed"""
        feature_plugin = ObjFeatSphericalTexture()
        available = feature_plugin.availableFeatures(objects[0][0], objects[0][1])

        expected_local_features = {k: v for k, v in available.items() if "margin" in v}

        # HACK: need to set margin to non-zero value - in our tests we use 2
        for k in available:
            if "margin" in available[k]:
                available[k]["margin"] = margin

        computed_features = []
        for obj_img, obj_mask in objects:
            feats_object = feature_plugin.compute_local(obj_img, obj_mask, available, axes)
            computed_features.append(feats_object)

        stacked = {}
        for k in expected_local_features.keys():
            stacked[k] = np.vstack(list(v[k].reshape(1, -1) for v in computed_features))

        assert stacked.keys() == expected_local_features.keys()

        n_objs = len(objects)
        failures = []
        for k, v in stacked.items():
            if len(v.shape) != 2:
                failures.append((k, f"Dimension mismatch, expected two dimensions, got {v.shape}."))
                continue

            if v.shape[0] != n_objs:
                failures.append((k, f"Expected features for {n_objs} objects, got {v.shape[0]}."))

        if failures:
            msg = "\n".join([f"{k}: {msg}" for k, msg in failures])
            raise AssertionError(msg)
