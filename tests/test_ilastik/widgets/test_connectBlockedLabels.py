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
from itertools import zip_longest
from typing import Dict

import numpy
import pytest
import vigra

from ilastik.applets.labeling.connectBlockedLabels import (
    Block,
    BlockBoundary,
    BoundaryDescr,
    BoundaryDescrRelative,
    Neighbourhood,
    Region,
    SpatialAxesKeys,
    add_tagged_coords,
    connect_regions,
    extract_annotations,
)


@pytest.mark.parametrize(
    "c1, c2, res",
    [
        pytest.param({}, {}, {}, id="empty"),
        pytest.param({"a": 1.0}, {"a": 2.0, "b": 5.0}, {"a": 3.0}, id="extra_key_is_fine"),
    ],
)
def test_add_tagged_coordinates(c1: Dict[str, float], c2: Dict[str, float], res: Dict[str, float]):
    ret = add_tagged_coords(c1, c2)
    assert ret == res


def test_add_tagged_coordinates_raises():
    c1 = {"a": 5.0}
    c2 = {"b": 1.0}
    with pytest.raises(ValueError):
        _ret = add_tagged_coords(c1, c2)


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

    block = Block(
        axistags=axistags,
        slices=(slice(10, 20), slice(20, 30)),
        regions=(r_left, r_right, r_top, r_bottom, r_topleft, r_topright, r_bottomleft, r_bottomright),
    )

    assert len(list(block.boundary_regions(boundary, label=label))) == expected_regions


def test_extract_annotations():
    axistags = "yx"

    data = numpy.zeros((100, 100), dtype="uint32")
    data[0:1, :] = 1
    data[3:7, 3:5] = 2
    data[8:9, 8:10] = 1

    labels_data = vigra.taggedView(data, axistags=axistags)

    regions = extract_annotations(labels_data=labels_data)

    assert len(regions) == 3
    assert len([r for r in regions if r.label == 1]) == 2
    assert len([r for r in regions if r.label == 2]) == 1

    r_2 = next((r for r in regions if r.label == 2))
    assert all(a == b for a, b in zip_longest(r_2.axistags, axistags))
    assert r_2.tagged_slicing["x"] == slice(3, 5)
    assert r_2.tagged_slicing["y"] == slice(3, 7)


def test_connect_label_blocks():
    """
     ___ ___
    | a | b |
     --- ---
    |   | c |
     --- ---
    """
    axistags = "yx"
    axistags_s = [SpatialAxesKeys(x) for x in axistags]

    block_a_data = numpy.zeros((100, 80), dtype="uint32")
    block_b_data = numpy.zeros_like(block_a_data)
    block_c_data = numpy.zeros_like(block_a_data)

    block_a_data[0:5, 2:60] = 1  # no connection between block_a_data and block_b_data
    block_b_data[10:, 6:8] = 1  # label to boundary, but not connected to block_c_data
    block_b_data[80:, 48:50] = 2  # label to boundary, with opposing label 1 in block_c_data
    block_c_data[:10, 48:65] = 1  # so no connection
    block_b_data[50:, 63:65] = 1  # label connecting blocks b and c

    block_a_data = vigra.taggedView(block_a_data, axistags=axistags)
    block_b_data = vigra.taggedView(block_b_data, axistags=axistags)
    block_c_data = vigra.taggedView(block_c_data, axistags=axistags)

    block_a = Block(
        axistags=axistags_s,
        slices=(slice(100, 200), slice(80, 160)),
        regions=extract_annotations(block_a_data),
    )
    block_b = Block(
        axistags=axistags_s,
        slices=(slice(100, 200), slice(160, 240)),
        regions=extract_annotations(block_b_data),
    )
    block_c = Block(
        axistags=axistags_s,
        slices=(slice(200, 300), slice(160, 240)),
        regions=extract_annotations(block_c_data),
    )

    block_dict = {bl.block_start: bl for bl in [block_a, block_b, block_c]}

    regions_dict = connect_regions(block_dict)

    assert len(regions_dict) == 5
    assert len([k for k, v in regions_dict.items() if k == v]) == 4

    merged_region = next(k for k, v in regions_dict.items() if k != v)

    parent_region = regions_dict[merged_region]

    assert merged_region.label == parent_region.label == 1
