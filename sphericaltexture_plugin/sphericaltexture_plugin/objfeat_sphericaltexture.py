from typing import Dict, List

from typing_extensions import NotRequired, TypedDict

import numpy
import numpy.typing as numpyt
import vigra
from ilastik.plugins.types import ObjectFeaturesPlugin

from sphericaltexture import SphericalTextureGenerator


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


class ObjFeatSphericalTexture(ObjectFeaturesPlugin):
    """Plugins of this class calculate object features."""

    name = "Spherical Texture"

    _feature_dict: Dict[str, FeatureDescription] = {
        "Spectrum": {
            "displaytext": "Spherical Texture",
            "detailtext": (
                "Maps each object to a sphere/circle by mean intensity projection,"
                "and quantifies the distribution of the intensity signal in the projection "
                "through Spherical Harmonics/Fourier decomposition. "
                "It thus gives a quantification of variance per angular wavelength in 20 values."
            ),
            "tooltip": "Spherical/Circular Texture",
            "advanced": False,
            "margin": 0,
        },
        "Polarization Direction": {
            "displaytext": "Polarization Direction",
            "detailtext": (
                "Maps each object to a sphere/circle by mean intensity projection, and returns "
                "the angle in rad with the max intensity in the angular projection."
            ),
            "tooltip": "Spherical/Circular Polarization Direction",
            "advanced": False,
            "margin": 0,
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selectedFeatures = []
        self.stg = None

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

        ndim = 2
        if is_3d:
            ndim = 3
        return {f"{ndim}D_{k}": v for k, v in self._feature_dict.items() if is_compatible(v)}

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
        # for "reasons", there will be always a margin around the object in the
        # local calculations, so get a tight bounding array:
        non_zero_indices = numpy.argwhere(binary_bbox)
        min_idx = non_zero_indices.min(axis=0)
        max_idx = non_zero_indices.max(axis=0)

        tight_slicing = tuple([slice(mmin, mmax + 1) for mmin, mmax in zip(min_idx, max_idx)])
        tight_bbox = binary_bbox[tight_slicing]

        # wrap naming and initialization of
        output_types = []
        stg_to_feat = {}
        ndim = None
        for feature in features:
            if "Spectrum" in feature:
                output_types.append("Condensed Spectrum")
                ndim = int(feature[0])
                stg_to_feat["Intensity Condensed Spectrum"] = feature
            if "Polarization Direction" in feature:
                output_types.append("Polarization Direction")
                ndim = int(feature[0])
                stg_to_feat["Intensity Polarization Direction"] = feature

        if self.stg == None:
            self.stg = SphericalTextureGenerator(projections=["Intensity"], output_types=output_types)
        return self.do_channels(self._do_extract, image, tight_bbox=tight_bbox, stg_to_feat=stg_to_feat, axes=axes)

    def _do_extract(self, image, axes, tight_bbox, stg_to_feat):

        if self.stg is None:
            raise Exception("SphericalTextureGenerator was not initialized")
        stg_results = self.stg.process_image(image, tight_bbox)
        for key in list(stg_results.keys()):  # rename keys to ilastik feature names
            stg_results[key] = numpy.nan_to_num(stg_results[key], nan=0.0).astype(numpy.float64)
            stg_results[stg_to_feat[key]] = stg_results.pop(key)
        return stg_results

    def do_channels(self, fn, image: vigra.VigraArray, axes, **kwargs):
        """Helper for features that only take one channel.

        :param fn: function that computes features

        """
        results = []
        slc = [slice(None)] * 4
        channel_index = image.channelIndex
        for channel in range(image.shape[channel_index]):
            slc[channel_index] = channel
            # a dictionary for the channel
            result = fn(image[slc], axes, **kwargs)
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
