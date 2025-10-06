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

import vigra
from vigra.analysis import extractRegionFeatures

from lazyflow.base import SPATIAL_AXES


class Neighborhood(IntEnum):
    """
    Connectivity paradigm describing the search space for neighbors of a block.

    The value corresponds to the number of hops, as in the connectivity parameter
    for skimage.measure.label (see their docs for more context).

    Example for 2d, for the centerpixel P, N is considered part of the neighborhood:

    . . .    . N .      N N N
    . P .    N P N      N P N
    . . .    . N .      N N N

    NONE     SINGLE     NDIM

    """

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


BoundaryDescrRelative = Dict[SpatialAxesKeys, BlockBoundary]
BoundaryDescr = Dict[SpatialAxesKeys, Union[int, None]]


class RelativeBoundaries:
    """
    This class contains only boundaries that can be reached by a positive increment
    along at least one axis.

    For 2D, where B is the "current", and N denotes neighboring blocks.

    . . .    . . .      . . N
    . B .    . B N      . B N
    . . .    . N .      N N N

    NONE     SINGLE     NDIM

    Boundary descriptions here are used to access these neighboring blocks.
    """

    @staticmethod
    def positive_boundaries(
        spatial_axes: List[SpatialAxesKeys], neighborhood: Neighborhood
    ) -> Iterator[BoundaryDescrRelative]:

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

        _Boundaries = {
            (Neighborhood.NONE, 2): (),
            (Neighborhood.NONE, 3): (),
            (Neighborhood.SINGLE, 2): _Boundaries2D_SINGLE,
            (Neighborhood.SINGLE, 3): _Boundaries3D_SINGLE,
            (Neighborhood.NDIM, 2): _Boundaries2D_NDIM,
            (Neighborhood.NDIM, 3): _Boundaries3D_NDIM,
        }

        n_spatial = len(spatial_axes)
        assert n_spatial in (2, 3)

        boundary_iter = _Boundaries[(neighborhood, n_spatial)]

        for boundary in boundary_iter:
            assert not all(
                x == BlockBoundary.NONE for x in boundary
            ), f"Unexpected, nonsensical BlockBoundary value {boundary}."

            yield dict(zip(spatial_axes, boundary))


_INVERTED_BOUNDARIES: dict[BlockBoundary, BlockBoundary] = {
    BlockBoundary.NONE: BlockBoundary.NONE,
    BlockBoundary.START: BlockBoundary.STOP,
    BlockBoundary.STOP: BlockBoundary.START,
}


@dataclass(frozen=True)
class Region:
    """
    Representation of the bounding box belonging to a certain label
    """

    axistags: Sequence[str]
    slices: Tuple[slice, ...]
    label: int

    __slots__ = "axistags", "slices", "label"

    def __post_init__(self):
        if len(self.axistags) != len(self.slices):
            raise ValueError(f"{self.axistags=} and {self.slices=} not matching in length")

        if any(_is_unbound(sl) for sl in self.slices):
            raise ValueError("Cannot construct region with unbound slicing")

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

    def with_slices(self, tagged_slices: Dict[str, slice]) -> "Region":
        axistags = [k for k in tagged_slices]
        slices = tuple([v for v in tagged_slices.values()])
        return Region(axistags=axistags, slices=slices, label=self.label)


@dataclass(frozen=True)
class Block:
    """
    Single block, as part of a larger blocking (knows about neighbors starting points)

    Args:
      axistags: up to 5D (tzyxc)
      slices: Block position. Neighbors are expected to start at block stops
      regions: Block-local regions (as in slices be within limits of block size)
      neighborhood: Neighborhood to consider for finding neighboring blocks
    """

    axistags: Sequence[str]
    slices: Tuple[slice, ...]
    regions: Sequence[Region]
    neighborhood: Neighborhood = Neighborhood.NDIM

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
        if self.neighborhood == Neighborhood.NONE:
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
            if label is None:
                return True
            else:
                return region_label == label

        for region in self.regions:
            if region.is_at_boundary(tagged_boundary) and _labelmatch(region.label):
                yield region

    def boundary_regions_positive(self) -> Iterator[Tuple[BoundaryDescrRelative, Region]]:
        for boundary in RelativeBoundaries.positive_boundaries(self.spatial_axes, self.neighborhood):
            for boundary_region in self.boundary_regions(boundary):
                yield boundary, boundary_region

    def neighbor_start_coordinates(self, boundary: BoundaryDescrRelative) -> Tuple[int, ...]:
        tagged_slices = self.tagged_slices

        neighbor_start: dict[str, int] = {}
        for k, sl in tagged_slices.items():
            if k not in SPATIAL_AXES:
                neighbor_start[k] = sl.start
                continue

            ks = SpatialAxesKeys(k)
            b = boundary[ks]
            if b == BlockBoundary.NONE:
                neighbor_start[k] = sl.start
            elif b == BlockBoundary.START:
                neighbor_start[k] = sl.start - (sl.stop - sl.start)
            elif b == BlockBoundary.STOP:
                neighbor_start[k] = sl.stop
            else:
                # unreachable
                raise NotImplementedError()

        return tuple(neighbor_start[k] for k in self.axistags)

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

        return region.with_slices(world_sl)


def add_tagged_coords(t1: Dict[str, float], t2: Dict[str, float]) -> Dict[str, float]:
    if not set(t1.keys()).issubset(set(t2.keys())):
        raise ValueError(
            f"First argument keys {list(t1.keys())=} must be a subset of second argument keys {list(t2.keys())=}!"
        )
    return {k: t1[k] + t2[k] for k in t1.keys()}


def _is_unbound(sl: slice) -> bool:
    return sl.start is None or sl.stop is None


def extract_annotations(labels_data: vigra.VigraArray) -> Tuple[Region, ...]:
    """Wrap connected components in a label array in Regions

    Args:
      labels_data: integer valued VigraArray with axistags. Note: only spatial
        axistags (x, y, z) are allowed. 0 values are considered background. Arrays
        are casted to`uint32` for labeling, potentially lossy coming from `uint64`.

    Returns:
      Tuple of connected components wrapped in Region objects
    """
    axistags = [a.key for a in labels_data.axistags]
    assert len(axistags) in [2, 3]
    assert all(k in SPATIAL_AXES for k in axistags)

    if len(axistags) == 3:
        connected_components = vigra.analysis.labelVolumeWithBackground(
            labels_data.astype("uint32"),
            neighborhood=26,
        )
    else:
        connected_components = vigra.analysis.labelImageWithBackground(
            labels_data.astype("uint32"),
            neighborhood=8,
        )
    feats = extractRegionFeatures(
        labels_data.astype("float32"),
        connected_components,
        ignoreLabel=0,
        features=["RegionCenter", "Coord<Maximum>", "Coord<Minimum>", "Minimum"],
    )

    # shape: (n_objs, ndim), we +1 the maximum bounding box value to make it
    # compatible with slice objects, where the stop is exclusive
    # first object is ignored -> background object.
    max_bb = feats["Coord<Maximum>"][1:].astype("uint32") + 1
    min_bb = feats["Coord<Minimum>"][1:].astype("uint32")

    slices: list[Tuple[slice, ...]] = []
    for min_, max_ in zip(min_bb, max_bb):
        slices.append(tuple(slice(mi, ma) for mi, ma in zip(min_, max_)))

    # we pass the label image as "image", so minimum will be the same label
    labels = feats["Minimum"][1:].astype("uint32")

    spatial_at = [at for at in axistags if at in SPATIAL_AXES]
    regions = tuple(Region(axistags=spatial_at, slices=sl, label=label) for sl, label in zip(slices, labels))

    return regions


def connect_regions(block_dict: Dict[Tuple[int, ...], Block]) -> Dict[Region, Region]:
    """
    Connect regions between a sparse blocking
    """
    regions_dict: Dict[Region, Region] = {}  # region_world: region_world, updated with anchor as value

    def get_anchor(region):
        """An anchor is the representative for a connected region.

        Currently it is the first already seen region connected to `region` through
        any number of other regions.
        """
        if region not in regions_dict:
            return region

        current = region
        while True:
            anchor = regions_dict[current]
            if anchor == current:
                return anchor
            current = anchor

    for block in block_dict.values():
        for region in block.regions:
            region_world = block.region_in_world(region)
            if region_world not in regions_dict:
                regions_dict[region_world] = region_world

        for boundary, region in block.boundary_regions_positive():
            region_world = block.region_in_world(region)
            block_start = block.neighbor_start_coordinates(boundary)
            if block_start not in block_dict:
                continue

            neighbor_block = block_dict[block_start]
            boundary_in_neighbor = {k: _INVERTED_BOUNDARIES[v] for k, v in boundary.items()}
            for reg in neighbor_block.boundary_regions(boundary_in_neighbor, label=region.label):
                neighbor_region_world = neighbor_block.region_in_world(reg)
                if check_overlap(region_world, neighbor_region_world):
                    anchor_neighbor = get_anchor(neighbor_region_world)
                    anchor_reg = get_anchor(region_world)

                    regions_dict[anchor_neighbor] = anchor_reg

    return regions_dict


def check_overlap(region_a: Region, region_b: Region) -> bool:
    """Check bounding box overlap"""
    assert region_a.axistags == region_b.axistags

    overlap = True
    for k, v in region_a.tagged_slicing.items():

        if k not in SPATIAL_AXES:
            continue
        if not (v.stop >= region_b.tagged_slicing[k].start and region_b.tagged_slicing[k].stop >= v.start):
            return False

    return overlap
