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
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy
import vigra


DEFAULT_LOWEST_SCALE_KEY = ""


@dataclass
class Multiscale:
    """
    Metadata for a single scale of a multiscale dataset as required for the GUI.
    This is stored in `Slot.meta` dicts, so must be serializable.

    :param key: Key-string used by the MultiscaleStore internally to identify this scale.
    :param dimensions: (xyz) Metadata of the dataset at this scale, to inform the user's choice.
        E.g. resolution (Precomputed) or size (OME-Zarr).
    """

    key: str
    dimensions: List[int]


class MultiscaleStore(metaclass=ABCMeta):
    """Base class for adapter classes that handle communication with a web source serving a multiscale dataset.
    Specifies the minimum interface required for GUI interaction, image computations and project file storage."""

    def __init__(
        self,
        dtype: numpy.dtype,
        axistags: vigra.AxisTags,
        multiscales: Dict[str, Multiscale],
        lowest_resolution_key: str,
        highest_resolution_key: str,
    ):
        """
        :param dtype: The dataset's numpy dtype.
        :param axistags: vigra.AxisTags describing the dataset's axes.
        :param multiscales: Dict of scale metadata for GUI interaction and storage in the project file.
            Keys should be human-readable absolute identifiers for each scale as found in the dataset.
        :param lowest_resolution_key: Key of the lowest-resolution scale within the multiscales dict.
            This acts as the default scale after load until the user selects a different one.
        :param highest_resolution_key: Used to infer the maximum dataset size, and for legacy HBP-mode projects.
        """
        self.dtype = dtype
        self.axistags = axistags
        self.multiscales = multiscales
        self.lowest_resolution_key = lowest_resolution_key
        self.highest_resolution_key = highest_resolution_key

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
    def URL_HINT(self) -> str:
        """
        User-facing description how to recognize URLs of this format.
        Subclasses should implement this as a class string constant like:
        class OMEZarrStore(MultiscaleStore):
            URL_HINT = 'URL contains .zarr'
        """
        ...

    @staticmethod
    @abstractmethod
    def is_url_compatible(url: str) -> bool:
        """Check if the dataset at this URL might be compatible with this adapter.
        All adapters are asked to check in turn, so need to avoid slow operations like web requests here."""
        ...
