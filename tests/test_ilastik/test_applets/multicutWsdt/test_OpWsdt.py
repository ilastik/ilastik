###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2026, the ilastik developers
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
from typing import Iterator

import numpy
import pytest
import vigra

from ilastik.applets.wsdt.opWsdt import OpCachedWsdt
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.utility.pipeline import Pipeline


@pytest.fixture
def data() -> vigra.VigraArray:
    shape = (36, 64, 128, 1)
    return vigra.taggedView(numpy.random.random(numpy.prod(shape)).astype("float32").reshape(shape), axistags="zyxc")


@pytest.fixture
def op_cached_wsdt(graph, data: vigra.VigraArray) -> Iterator[OpCachedWsdt]:
    with Pipeline(graph=graph) as pipeline:
        pipeline.add(OpArrayPiper, Input=data)
        op = pipeline.add(OpCachedWsdt, FreezeCache=False)

        yield op


def test_threshold_not_dirty_when_threshold_doesnt_change(op_cached_wsdt: OpCachedWsdt):
    threshold_expected_count = [(0.5, 0), (0.5, 0), (0.1, 1), (0.1, 1), (0.9, 2), (0.9, 2)]
    dirty_probs = 0

    def _inc_dirty_probps(*_, **__):
        nonlocal dirty_probs
        dirty_probs += 1

    op_cached_wsdt.ThresholdedInput.notifyDirty(_inc_dirty_probps)

    for threshold, expected_dirty_probs in threshold_expected_count:
        op_cached_wsdt.Threshold.setValue(threshold)
        assert dirty_probs == expected_dirty_probs


def test_threshold_not_dirty_when_other_inputs_change(op_cached_wsdt: OpCachedWsdt):
    dirty_probs = 0

    def _inc_dirty_probps(*_, **__):
        nonlocal dirty_probs
        dirty_probs += 1

    op_cached_wsdt.ThresholdedInput.notifyDirty(_inc_dirty_probps)

    slot_values = [
        (op_cached_wsdt.Alpha, 0.1),
        (op_cached_wsdt.Alpha, 0.2),
        (op_cached_wsdt.ApplyNonmaxSuppression, False),
        (op_cached_wsdt.ApplyNonmaxSuppression, True),
        (op_cached_wsdt.MinSize, 10),
        (op_cached_wsdt.MinSize, 42),
        (op_cached_wsdt.Sigma, 5.0),
        (op_cached_wsdt.Sigma, 1.0),
        (op_cached_wsdt.PixelPitch, [0, 1, 3]),
        (op_cached_wsdt.PixelPitch, [10, 44, 2]),
        (op_cached_wsdt.EnableDebugOutputs, True),
        (op_cached_wsdt.EnableDebugOutputs, False),
    ]

    for slot, value in slot_values:
        slot.setValue(value)
        assert dirty_probs == 0
