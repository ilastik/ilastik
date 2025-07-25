###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Dict, Iterator, List, Optional, Sequence, Tuple, Union

from lazyflow.utility.io_util.write_ome_zarr import SPATIAL_AXES


class Neighbourhood(IntEnum):
    NONE = 0
    SINGLE = 1  # Axis aligned, 2D: 4, 3D: 6
    NDIM = 2  # Full block, 2D: 8, 3D: 26


class BlockBoundary(IntEnum):
    NONE = 0
    START = 1
    STOP = 2


class SpatialAxesKeys(StrEnum):
    x = "x"
    y = "y"
    z = "z"


_Boundaries2D_SINGLE = ((BlockBoundary.NONE, BlockBoundary.STOP), (BlockBoundary.STOP, BlockBoundary.NONE))
_Boundaries2D_NDIM = _Boundaries2D_SINGLE + ((BlockBoundary.STOP, BlockBoundary.STOP),)


_Boundaries3D_SINGLE = (
    (BlockBoundary.NONE, BlockBoundary.NONE, BlockBoundary.STOP),
    (BlockBoundary.NONE, BlockBoundary.STOP, BlockBoundary.NONE),
    (BlockBoundary.STOP, BlockBoundary.NONE, BlockBoundary.NONE),
)
_Boundaries3D_NDIM = _Boundaries3D_SINGLE + (
    (BlockBoundary.NONE, BlockBoundary.STOP, BlockBoundary.STOP),
    (BlockBoundary.STOP, BlockBoundary.NONE, BlockBoundary.STOP),
    (BlockBoundary.STOP, BlockBoundary.STOP, BlockBoundary.NONE),
    (BlockBoundary.STOP, BlockBoundary.STOP, BlockBoundary.STOP),
)


BoundaryDescrRelative = Dict[SpatialAxesKeys, BlockBoundary]
BoundaryDescr = Dict[SpatialAxesKeys, Union[int, None]]

_INVERTED_BOUNDARIES: dict[BlockBoundary, BlockBoundary] = {
    BlockBoundary.NONE: BlockBoundary.NONE,
    BlockBoundary.START: BlockBoundary.STOP,
    BlockBoundary.STOP: BlockBoundary.START,
}

_Boundaries = {
    (Neighbourhood.NONE, 2): (),
    (Neighbourhood.NONE, 3): (),
    (Neighbourhood.SINGLE, 2): _Boundaries2D_SINGLE,
    (Neighbourhood.SINGLE, 3): _Boundaries3D_SINGLE,
    (Neighbourhood.NDIM, 2): _Boundaries2D_NDIM,
    (Neighbourhood.NDIM, 3): _Boundaries3D_NDIM,
}


@dataclass(slots=True, frozen=True)
class Region:
    """
    Representation of the bounding box belonging to a certain label
    """

    axistags: Sequence[str]
    slices: Tuple[slice, ...]
    label: int

    def __post_init__(self):
        if len(self.axistags) != len(self.slices):
            raise ValueError(f"{self.axistags=} and {self.slices=} not matching in length")

        if any(_is_unbound(sl) for sl in self.slices):
            raise ValueError(f"Cannot construct region with unbound slicing")

    @property
    def tagged_slicing(self) -> Dict[str, slice]:
        return dict(zip(self.axistags, self.slices))

    @property
    def tagged_center(self) -> Dict[str, float]:
        """Returns the center of the interval defined by slicing

        Stop element is assumed to be exclusive.
        """
        return {k: (sl.stop - 1 - sl.start) / 2 + sl.start for k, sl in self.tagged_slicing.items()}

    def is_at_boundary(self, boundary: BoundaryDescr) -> bool:
        """Return True if any bounding box coordinates match given integer in boundary description

        only exact matches at boundary. Bounding box intersecting the boundary is considered False.
        """
        if all(b is None for b in boundary.values()):
            return False

        is_at_boundary = True
        for k, coord in boundary.items():
            if coord is not None:
                sl = self.tagged_slicing[k]
                if sl.start == coord or sl.stop == coord:
                    continue
                else:
                    return False

        return is_at_boundary

    def __hash__(self):
        """
        Hash based on volume defined by slicing.
        In our setting regions cannot overlap in start and stop coordinates
        -> result in a unique key.
        """
        return hash(tuple((sl.start, sl.stop) for sl in self.slices))

    @classmethod
    def with_slices(cls, reg: "Region", tagged_slices: Dict[str, slice]) -> "Region":
        axistags = [k for k in tagged_slices]
        slices = tuple([v for v in tagged_slices.values()])
        return Region(axistags=axistags, slices=slices, label=reg.label)


@dataclass(frozen=True)
class Block:
    """
    Single block, as part of a larger blocking (knows about neighbors starting points)

    Args:
      axistags: up to 5D (tzyxc)
      slices: Block position. Neighbours are expected to start at block stops
      regions: Block-local regions (as in slices be within limits of block size)
      neighborhood: Neighborhood to consider for finding neighboring blocks
    """

    axistags: Sequence[str]
    slices: Tuple[slice, ...]
    regions: Sequence[Region]
    neigbourhood: Neighbourhood = Neighbourhood.NDIM

    @property
    def block_start(self) -> Tuple[int, ...]:
        return tuple(sl.start for sl in self.slices)

    @property
    def tagged_slices(self) -> dict[str, slice]:
        return {tag: sl for tag, sl in zip(self.axistags, self.slices)}

    @property
    def spatial_axes(self) -> List[SpatialAxesKeys]:
        return [SpatialAxesKeys(x) for x in self.axistags if x in SPATIAL_AXES]

    @property
    def tagged_start(self) -> dict[str, slice]:
        return {tag: sl.start for tag, sl in zip(self.axistags, self.slices)}

    def boundary_regions(self, boundary: BoundaryDescrRelative, label: Optional[int] = None) -> Iterator[Region]:
        if self.neigbourhood == Neighbourhood.NONE:
            return

        def _boundary_index_from_slice(sl: slice, boundary: BlockBoundary) -> Union[int, None]:
            if boundary == BlockBoundary.NONE:
                return None
            if boundary == BlockBoundary.START:
                return 0
            if boundary == BlockBoundary.STOP:
                return sl.stop - sl.start

        tagged_boundary: dict[SpatialAxesKeys, Union[int, None]] = {}
        for at, bd in boundary.items():
            tagged_boundary[at] = _boundary_index_from_slice(self.tagged_slices[at], bd)

        def _labelmatch(region_label: Union[int, None]) -> bool:
            if label == None:
                return True
            else:
                return region_label == label

        for region in self.regions:
            if region.is_at_boundary(tagged_boundary) and _labelmatch(region.label):
                yield region

    def boundaries_positive(self) -> Iterator[BoundaryDescrRelative]:
        n_spatial = len(self.spatial_axes)
        assert n_spatial in (2, 3)

        boundary_iter = _Boundaries[(self.neigbourhood, n_spatial)]

        for boundary in boundary_iter:
            if all(x == BlockBoundary.NONE for x in boundary):
                continue

            yield dict(zip(self.spatial_axes, boundary))

    def boundary_regions_positive(self) -> Iterator[Tuple[BoundaryDescrRelative, Region]]:
        for boundary in self.boundaries_positive():
            for boundary_region in self.boundary_regions(boundary):
                yield boundary, boundary_region

    def neighbour_start_coordinates(self, boundary: BoundaryDescrRelative) -> Tuple[int, ...]:
        tagged_slices = self.tagged_slices

        neighbour_start: dict[str, int] = {}
        for k, sl in tagged_slices.items():
            if k not in SPATIAL_AXES:
                neighbour_start[k] = sl.start
                continue

            ks = SpatialAxesKeys(k)
            b = boundary[ks]
            if b == BlockBoundary.NONE:
                neighbour_start[k] = sl.start
            elif b == BlockBoundary.START:
                neighbour_start[k] = sl.start - (sl.stop - sl.start)
            elif b == BlockBoundary.STOP:
                neighbour_start[k] = sl.stop
            else:
                # unreachable
                raise NotImplemented()

        return tuple(neighbour_start[k] for k in self.axistags)

    def region_in_world(self, region: Region) -> Region:
        tagged_region_sl = region.tagged_slicing
        tagged_block_sl = self.tagged_slices
        world_sl = {}
        for k in self.axistags:
            if k in SPATIAL_AXES:
                sl = tagged_region_sl[k]
                world_sl[k] = slice(sl.start + self.tagged_start[k], sl.stop + self.tagged_start[k])
            else:
                world_sl[k] = tagged_block_sl[k]

        return region.with_slices(region, world_sl)


def add_tagged_coords(t1: Dict[str, float], t2: Dict[str, float]) -> Dict[str, float]:
    assert set(t1.keys()).issubset(set(t2.keys())), f"{list(t1.keys())=}, {list(t2.keys())=}"
    return {k: t1[k] + t2[k] for k in t1.keys()}


def _is_unbound(sl: slice) -> bool:
    return sl.start is None or sl.stop is None
