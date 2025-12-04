###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
# 		   http://ilastik.org/license.html
###############################################################################
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from typing import Literal, Tuple

import numpy
import vigra

# See MultiscaleStore docstring for details
Multiscale = OrderedDict[str, OrderedDict[Literal["t", "c", "z", "y", "x"], int]]
DEFAULT_SCALE_KEY = ""


class MultiscaleStore(metaclass=ABCMeta):
    """
    Base class for adapter classes that handle communication with a web source serving a multiscale dataset.
    Specifies the minimum interface required for GUI interaction, image computations and project file storage.

    Terminology around this subject is not standardised, in particular "scale" and "resolution" are used
    somewhat interchangeably. We aim to stick with "scale" as the term for a level of scaling of the dataset,
    synonymously to "pyramid level" or "multiscale" in some communities. "Resolution" for image detail,
    i.e. "high res" = more pixels.
    """

    def __init__(
        self,
        uri: str,
        dtype: numpy.dtype,
        axistags: vigra.AxisTags,
        multiscale: Multiscale,
        lowest_resolution_key: str,
        highest_resolution_key: str,
    ):
        """
        :param uri: Location where this store was initialized (as passed to __init__).
        :param dtype: The dataset's numpy dtype.
        :param axistags: vigra.AxisTags describing the dataset's axes.
        :param multiscale: Dict of scales for GUI and OME-Zarr export, {key: tagged shape}
            Order from highest to lowest resolution (i.e. largest to smallest shape).
            Keys: absolute identifiers for each scale as found in the dataset.
            Values: tagged shape dicts ({axis: size}) of the image at each scale.
            Axis order in shape dicts must match axistags.
        :param lowest_resolution_key: Key of the lowest-resolution scale within the multiscale dict.
            This acts as the default scale after load until the user selects a different one.
        :param highest_resolution_key: Used to infer the maximum dataset size, and for legacy HBP-mode projects.
        """
        self.uri = uri
        self.dtype = dtype
        self.axistags = axistags
        self.multiscale = multiscale
        self.lowest_resolution_key = lowest_resolution_key
        self.highest_resolution_key = highest_resolution_key
        scale_keys = list(self.multiscale.keys())
        assert (
            self.highest_resolution_key == scale_keys[0] and self.lowest_resolution_key == scale_keys[-1]
        ), "Multiscale dict must be ordered from highest to lowest resolution (i.e. largest to smallest shape)"
        assert all(
            list(scale_shape.keys()) == axistags.keys() for scale_shape in self.multiscale.values()
        ), "Multiscale values must be shape dicts for the given axistags"

    @abstractmethod
    def get_shape(self, scale_key: str) -> Tuple[int]:
        """Shape of the dataset at the given scale."""
        ...

    @abstractmethod
    def get_chunk_size(self, scale_key: str) -> Tuple[int]:
        """Preferred download/computation chunk size of the dataset at the given scale."""
        ...

    @property
    @abstractmethod
    def NAME(self) -> str:
        """
        User-facing name of the data format the store handles, e.g. "OME-Zarr" or "Precomputed".
        Subclasses should implement this as a class string constant like:
        class OMEZarrStore(MultiscaleStore):
            NAME = 'OME-Zarr'
        """
        ...

    @property
    @abstractmethod
    def URI_HINT(self) -> str:
        """
        User-facing description how to recognize URIs of this format.
        Note we aim to use "URI" in code but "URL" in user-facing text.
        Subclasses should implement this as a class string constant like:
        class OMEZarrStore(MultiscaleStore):
            URI_HINT = 'URL contains .zarr'
        """
        ...

    @staticmethod
    @abstractmethod
    def is_uri_compatible(uri: str) -> bool:
        """Check if the dataset at this URI might be compatible with this adapter.
        All adapters are asked to check in turn, so need to avoid slow operations like web requests here."""
        ...
