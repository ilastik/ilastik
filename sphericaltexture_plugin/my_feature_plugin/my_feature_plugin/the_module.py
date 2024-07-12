from typing import Dict, List

from typing_extensions import NotRequired, TypedDict

import numpy
import numpy.typing as npt
import vigra
from ilastik.plugins.types import ObjectFeaturesPlugin


class FeatureDescription(TypedDict):
    displaytext: str
    detailtext: str
    tooltip: str
    advanced: bool
    group: str
    margin: NotRequired[int]
    # features are assumed to be able to do 2D and 3D. If your feature
    # cannot do one of them, you can mark those accordingly by setting
    # one of those keys in the feature description
    no_3D: NotRequired[bool]
    no_2D: NotRequired[bool]
    # if raw data is accessed for your feature, the most of the
    channel_aware: NotRequired[bool]


class MyObjectFeatures(ObjectFeaturesPlugin):
    """Plugins of this class calculate object features."""

    name = "my_feature_plugin"

    _feature_dict: Dict[str, FeatureDescription] = {
        "example_global_feature": {
            "displaytext": "Area of the object",
            "detailtext": "Area of the region i.e. number of pixels of the region.",
            "tooltip": "area",
            "advanced": False,
            "group": "Shape",
        },
        "example_local_feature": {
            "displaytext": "bbox to obj ratio",
            "detailtext": "Ratio of pixels in the region to pixels in the bounding box.",
            "tooltip": "bbox2obj",
            "advanced": False,
            "group": "Shape",
            "margin": 0,
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selectedFeatures = []

    def availableFeatures(self, image: vigra.VigraArray, labels: vigra.VigraArray):
        """Reports which features this plugin can compute on a
        particular image and label image.

        often plugins may return a slightly different feature set depending
        on the image being 2D or 3D.

        Args:
            image: tagged vigra array
            labels: tagged vigra array

        Returns:
            a nested dictionary, where dict[feature_name] is a
            dictionary of parameters.

        """
        is_3d = all(ax > 1 for ax in labels.withAxes("zyx").shape)

        def is_compatible(fdict):
            if not is_3d:
                return not fdict.get("no_2D", False)

            return not fdict.get("no_3D", False)

        return {k: v for k, v in self._feature_dict.items() if is_compatible(v)}

    def compute_global(
        self, image: vigra.VigraArray, labels: vigra.VigraArray, features: Dict[str, Dict], axes
    ) -> Dict[str, npt.ArrayLike]:
        """calculate the requested features.

        Object id 0 should be excluded from feature computation here.
        (ilastik expects it that way.)

        Args;
            image: VigraArray of the image with axistags, always xyzc, full image
            labels: VigraArray of the labels with axistags, always xyz, full label
                image with all objects having unique pixel values.
                ObjectID 0 is considered background, object ids are positive integers
            features: list of feature names; which features to compute
            axes: axis tags, DEPRECATED; use `.axistags` attribute of image/labels

        Returns
            dictionary with one entry per feature. dict[feature_name] is a
            numpy.ndarray with shape (n_objs, n_featvals), where featvals is
            the number of elements for a single object for the particular feature
        """
        # ilastik will give all features here, so we need to exclude the local ones
        global_features = {k: v for k, v in features.items() if "margin" not in v}

        _ids, counts = numpy.unique(labels, return_counts=True)

        if 0 in _ids:
            assert _ids[0] == 0
            counts = counts[1:]

        # since in this example, counts is only 1d, but requirement is a 2d output for each feature
        ret = {"example_global_feature": counts[:, numpy.newaxis]}
        return ret

    def compute_local(self, image: vigra.VigraArray, binary_bbox: vigra.VigraArray, features: Dict[str, Dict], axes):
        """Calculate features on a single object.

        Args:
            image: VigraArray of the image with axistags, always xyzc, for one object, includes margin around
            binary_bbox: VigraArray of the image with axistags, always xyz, for one object, includes margin around
            features: which features to compute
            axes: axis tags, DEPRECATED; use `.axistags` attribute of image/labels

        Returns:
            a dictionary with one entry per feature.
            dict[feature_name] is a numpy.ndarray with ndim=1

        """
        # call parent class method if local features are not needed
        feature_dict = {}

        local_features = {k: v for k, v in features.items() if "margin" in v}

        # for "reasons", there will be always a margin around the object in the
        # local calculations, so get a tight bounding array:
        non_zero_indices = numpy.argwhere(binary_bbox)
        min_idx = non_zero_indices.min(axis=0)
        max_idx = non_zero_indices.max(axis=0)

        tight_slicing = tuple([slice(mmin, mmax + 1) for mmin, mmax in zip(min_idx, max_idx)])

        tight_bbox = binary_bbox[tight_slicing]

        feature_dict["example_local_feature"] = tight_bbox.sum() / tight_bbox.size

        return feature_dict

    def do_channels(self, fn, image: vigra.VigraArray, labels: vigra.VigraArray, axes, **kwargs):
        """Helper for features that only take one channel.

        :param fn: function that computes features

        """
        results = []
        slc = [slice(None)] * 4
        channel_index = image.channelIndex
        for channel in range(image.shape[channel_index]):
            slc[channel_index] = channel
            # a dictionary for the channel

            result = fn(image[slc], labels, axes, **kwargs)
            results.append(result)

        return self.combine_dicts_with_numpy(results)

    def fill_properties(self, feature_dict):
        """Augment die feature dictionary with additional fields

        For every feature in the feature dictionary, fill in its properties,
        such as 'detailtext', which will be displayed in help, or 'displaytext'
        which will be displayed instead of the feature name

        Only necessary if these keys are not present to begin with.

        Args:
            feature_dict: list of feature names

        Returns:
            same dictionary, with additional fields filled for each feature

        """
        return super().fill_properties(feature_dict)
