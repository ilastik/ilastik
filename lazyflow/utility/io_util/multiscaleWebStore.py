from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy
import vigra


@dataclass
class Multiscale:
    """
    Metadata for a single scale of a multiscale dataset as required for the GUI.
    This is stored in `Slot.meta` dicts, so must be serializable.

    :param key: Key-string used by the MultiscaleStore internally to identify this scale.
    :param resolution: xyz list of dataset size at this scale. Used to inform the user's scale choice.
    """

    key: str
    resolution: Optional[List[int]]


class MultiscaleWebStore(metaclass=ABCMeta):
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
        :param axistags: The dataset's axis keys as ordered when loading remote data, e.g. "tczyx"
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
