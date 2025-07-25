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
import pytest

from ilastik.applets.labeling.connectBlockedLabels import (
    Block,
    BlockBoundary,
    BoundaryDescr,
    BoundaryDescrRelative,
    Neighbourhood,
    Region,
    SpatialAxesKeys,
    extract_annotations,
)


def test_region_construction_raises_on_axistags_slices_mismatch():
    with pytest.raises(ValueError):
        _ = Region(axistags="z", slices=(slice(0, 1), slice(1, 2)), label=1)


def test_region_construction_raises_on_unbound_slicing():
    with pytest.raises(ValueError):
        _ = Region(axistags="z", slices=(slice(None, 1),), label=1)


def test_region_center():
    region = Region(axistags="xy", slices=(slice(1, 2), slice(0, 42)), label=1)
    assert region.tagged_center == dict(x=1.0, y=20.5)


def test_region_with_slices():
    region = Region(axistags="xy", slices=(slice(1, 2), slice(0, 42)), label=1)

    new_slices = {"x": slice(5, 6), "y": slice(42, 10)}
    region2 = Region.with_slices(region, tagged_slices=new_slices)
    assert region2.tagged_slicing == new_slices


@pytest.mark.parametrize(
    "boundary_descr, result",
    [
        ({"x": 0, "y": None}, False),
        ({"x": 1, "y": None}, True),
        ({"x": None, "y": 0}, True),
        ({"x": None, "y": 5}, False),
        ({"x": 2, "y": None}, True),
        ({"x": 2, "y": 1}, False),
        ({"x": 2, "y": 0}, True),
        ({"x": 1, "y": 42}, True),
        ({"x": 2, "y": 42}, True),
        ({"x": None, "y": None}, False),
    ],
)
def test_region_at_boundary(boundary_descr: BoundaryDescr, result: bool):
    region = Region(axistags="xy", slices=(slice(1, 2), slice(0, 42)), label=1)
    assert region.is_at_boundary(boundary_descr) == result


@pytest.mark.parametrize(
    "neighbourhood, expected_neighbours",
    [
        (Neighbourhood.NONE, []),
        (
            Neighbourhood.SINGLE,
            [{"y": BlockBoundary.NONE, "x": BlockBoundary.STOP}, {"y": BlockBoundary.STOP, "x": BlockBoundary.NONE}],
        ),
        (
            Neighbourhood.NDIM,
            [
                {"y": BlockBoundary.NONE, "x": BlockBoundary.STOP},
                {"y": BlockBoundary.STOP, "x": BlockBoundary.NONE},
                {"y": BlockBoundary.STOP, "x": BlockBoundary.STOP},
            ],
        ),
    ],
)
def test_block_neighbourhood_types(neighbourhood, expected_neighbours):
    block = Block(
        axistags=("t", "y", "x", "c"),
        slices=(slice(10, 11), slice(100, 200), slice(200, 250), slice(0, 1)),
        regions=(),
        neigbourhood=neighbourhood,
    )

    assert list(block.boundaries_positive()) == expected_neighbours


@pytest.mark.parametrize(
    "boundary",
    [
        {"x": BlockBoundary.START, "y": BlockBoundary.NONE},
        {"x": BlockBoundary.STOP, "y": BlockBoundary.NONE},
        {"x": BlockBoundary.NONE, "y": BlockBoundary.START},
        {"x": BlockBoundary.NONE, "y": BlockBoundary.STOP},
        {"x": BlockBoundary.START, "y": BlockBoundary.START},
        {"x": BlockBoundary.STOP, "y": BlockBoundary.START},
        {"x": BlockBoundary.START, "y": BlockBoundary.STOP},
        {"x": BlockBoundary.STOP, "y": BlockBoundary.STOP},
        {"x": BlockBoundary.NONE, "y": BlockBoundary.NONE},
    ],
    ids=["left", "right", "top", "bottom", "top-left", "top-right", "bottom-left", "bottom_right", "none"],
)
def test_block_no_region_at_boundary_2d(boundary: BoundaryDescrRelative):
    axistags = "yx"
    r1 = Region(axistags=axistags, slices=(slice(1, 8), slice(1, 8)), label=1)
    r2 = Region(axistags=axistags, slices=(slice(1, 2), slice(1, 2)), label=1)
    r3 = Region(axistags=axistags, slices=(slice(5, 9), slice(1, 2)), label=2)

    b = Block(axistags=axistags, slices=(slice(10, 20), slice(20, 30)), regions=(r1, r2, r3))

    assert len(list(b.boundary_regions(boundary))) == 0


@pytest.mark.parametrize(
    "boundary, expected_regions",
    [
        ({"x": BlockBoundary.START, "y": BlockBoundary.NONE}, 3),
        ({"x": BlockBoundary.STOP, "y": BlockBoundary.NONE}, 3),
        ({"x": BlockBoundary.NONE, "y": BlockBoundary.START}, 3),
        ({"x": BlockBoundary.NONE, "y": BlockBoundary.STOP}, 3),
        ({"x": BlockBoundary.START, "y": BlockBoundary.START}, 1),
        ({"x": BlockBoundary.STOP, "y": BlockBoundary.START}, 1),
        ({"x": BlockBoundary.START, "y": BlockBoundary.STOP}, 1),
        ({"x": BlockBoundary.STOP, "y": BlockBoundary.STOP}, 1),
    ],
    ids=["left", "right", "top", "bottom", "top-left", "top-right", "bottom-left", "bottom_right"],
)
def test_block_boundary_regions_2d(boundary: BoundaryDescrRelative, expected_regions):
    # TODO: test that the correct regions are returned!
    axistags = "xy"

    r_left = Region(axistags=axistags, slices=(slice(0, 9), slice(1, 2)), label=1)
    r_right = Region(axistags=axistags, slices=(slice(1, 10), slice(1, 2)), label=1)
    r_top = Region(axistags=axistags, slices=(slice(3, 6), slice(0, 4)), label=2)
    r_bottom = Region(axistags=axistags, slices=(slice(2, 4), slice(1, 10)), label=42)

    r_topleft = Region(axistags=axistags, slices=(slice(0, 3), slice(0, 2)), label=3)
    r_topright = Region(axistags=axistags, slices=(slice(5, 10), slice(0, 4)), label=4)

    r_bottomleft = Region(axistags=axistags, slices=(slice(0, 3), slice(4, 10)), label=6)
    r_bottomright = Region(axistags=axistags, slices=(slice(1, 10), slice(5, 10)), label=7)

    block = Block(
        axistags=axistags,
        slices=(slice(10, 20), slice(20, 30)),
        regions=(r_left, r_right, r_top, r_bottom, r_topleft, r_topright, r_bottomleft, r_bottomright),
    )

    assert len(list(block.boundary_regions(boundary))) == expected_regions


@pytest.mark.parametrize(
    "boundary, label, expected_regions",
    [
        ({"x": BlockBoundary.START, "y": BlockBoundary.NONE}, 1, 1),
        ({"x": BlockBoundary.STOP, "y": BlockBoundary.NONE}, 1, 1),
        ({"x": BlockBoundary.NONE, "y": BlockBoundary.START}, 2, 2),
        ({"x": BlockBoundary.NONE, "y": BlockBoundary.STOP}, 42, 1),
        ({"x": BlockBoundary.START, "y": BlockBoundary.START}, 2, 1),
        ({"x": BlockBoundary.STOP, "y": BlockBoundary.START}, 4, 1),
        ({"x": BlockBoundary.START, "y": BlockBoundary.STOP}, 6, 1),
        ({"x": BlockBoundary.STOP, "y": BlockBoundary.STOP}, 7, 1),
    ],
    ids=["left", "right", "top", "bottom", "top-left", "top-right", "bottom-left", "bottom_right"],
)
def test_block_boundary_regions_per_label_2d(boundary, label, expected_regions):
    # TODO: test that the correct regions are returned!
    axistags = "xy"

    r_left = Region(axistags=axistags, slices=(slice(0, 9), slice(1, 2)), label=1)
    r_right = Region(axistags=axistags, slices=(slice(1, 10), slice(1, 2)), label=1)
    r_top = Region(axistags=axistags, slices=(slice(3, 6), slice(0, 4)), label=2)
    r_bottom = Region(axistags=axistags, slices=(slice(2, 4), slice(1, 10)), label=42)

    r_topleft = Region(axistags=axistags, slices=(slice(0, 3), slice(0, 2)), label=2)
    r_topright = Region(axistags=axistags, slices=(slice(5, 10), slice(0, 4)), label=4)

    r_bottomleft = Region(axistags=axistags, slices=(slice(0, 3), slice(4, 10)), label=6)
    r_bottomright = Region(axistags=axistags, slices=(slice(1, 10), slice(5, 10)), label=7)

    b = Block(
        axistags=axistags,
        slices=(slice(10, 20), slice(20, 30)),
        regions=(r_left, r_right, r_top, r_bottom, r_topleft, r_topright, r_bottomleft, r_bottomright),
    )

    assert len(list(b.boundary_regions(boundary, label=label))) == expected_regions
