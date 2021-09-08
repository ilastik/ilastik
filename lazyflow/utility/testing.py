###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#          http://ilastik.org/license/
###############################################################################
import threading
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

import numpy as np
import vigra

from lazyflow.graph import Graph, MetaDict
from lazyflow.operator import InputSlot, Operator, OutputSlot

# Some tools to aid automated testing

# check that two label images have the same meaning
# (label images can differ in the actual labels, but cannot differ in their
# spatial structure)
#
# Examples:
#   Input:
#       1 1 0    250 250 0
#       1 1 0    250 250 0
#       0 0 0    0   0   0
#   Output: None
#
#   Input:
#       1 1 0    250 250 0
#       1 1 0    1   1   0
#       0 0 0    0   0   0
#   Output: AssertionError
#
def assertEquivalentLabeling(labelImage, referenceImage):
    x = labelImage
    y = referenceImage
    assert np.all(x.shape == y.shape), "Shapes do not agree ({} vs {})".format(x.shape, y.shape)

    # identify labels used in x
    labels = set(x.flat)
    for label in labels:
        if label == 0:
            continue
        idx = np.where(x == label)
        refblock = y[idx]
        # check that labels are the same
        corner = [a[0] for a in idx]

        assert np.all(
            refblock == refblock[0]
        ), "Uniformly labeled region at coordinates {} has more than one label in the reference image".format(corner)
        # check that nothing else is labeled with this label
        m = refblock.size
        n = (y == refblock[0]).sum()
        assert m == n, "There are more pixels with (reference-)label {} than pixels with label {}.".format(
            refblock[0], label
        )

    assert len(labels) == len(set(y.flat)), "The number of labels does not agree, perhaps some region was missed"


class OpArrayPiperWithAccessCount(Operator):
    """
    array piper that counts how many times its execute function has been called
    """

    Input = InputSlot(allow_mask=True)
    Output = OutputSlot(allow_mask=True)

    def __init__(self, *args, **kwargs):
        super(OpArrayPiperWithAccessCount, self).__init__(*args, **kwargs)
        self.clear()
        self._lock = threading.Lock()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

    def execute(self, slot, subindex, roi, result):
        with self._lock:
            self.accessCount += 1
            self.requests.append(roi)
        req = self.Input.get(roi)
        req.writeInto(result)
        req.block()

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(roi)

    def clear(self):
        self.requests = []
        self.accessCount = 0


class OpCallWhenDirty(Operator):
    """
    calls the attribute 'function' when Input gets dirty

    The parameters of the dirty call are stored in attributres.
    """

    Input = InputSlot(allow_mask=True)
    Output = OutputSlot(allow_mask=True)

    function = lambda: None
    slot = None
    roi = None

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

    def execute(self, slot, subindex, roi, result):
        req = self.Input.get(roi)
        req.writeInto(result)
        req.block()

    def propagateDirty(self, slot, subindex, roi):
        try:
            self.slot = slot
            self.subindex = subindex
            self.roi = roi
            self.function()
        except:
            raise
        finally:
            self.Output.setDirty(roi)


@dataclass
class SlotDescription:
    dtype: np.dtype = None
    shape: Tuple[int] = (1,)
    axistags: vigra.AxisTags = None
    level: int = 0
    data: Any = None


SLOT_DATA = Mapping[str, SlotDescription]


def build_multi_output_mock_op(slot_data: SLOT_DATA, graph: Graph, n_lanes: int = None):
    """Returns an operator that has outputs as specifier in slot_data

    This is especially useful when testing toplevelOperators, as these usually
    need a lot of diverse inputs, which can be tedious using e.g.
    `OpArrayPiper`. This function can be used to generate an operator that mocks
    all needed output slots, an operator may take as inputs.

    Note: no consistency checking is done with the data provided from SlotDescription

    Currently, data access is not yet supported.

    Args:
      slot_data: Slot metadata will be the same for level 1 slots. If
         slot_data.data is given, it has to be the a sequence of same the same
         length as n_lanes.
      n_lanes: number of lanes - level 1 slots are resized to that number.

    """

    class _OP(Operator):
        def __init__(self, slot_data, *args, **kwargs):
            self._data = slot_data
            self._n_lanes = n_lanes
            super().__init__(*args, **kwargs)
            for name, val in self._data.items():
                meta_dict = MetaDict(dtype=val.dtype, shape=val.shape, axistags=val.axistags)
                if self.outputs[name].level == 0:
                    self.outputs[name].meta.assignFrom(meta_dict)
                elif self.outputs[name].level == 1 and self._n_lanes:
                    if self._data[name].data is not None and not (len(self._data[name].data) == self._n_lanes):
                        raise ValueError(f"Data for slot {name} did not match number of lanes {self._n_lanes}")
                    self.outputs[name].resize(self._n_lanes)
                    for ss in self.outputs[name]:
                        ss.meta.assignFrom(meta_dict)

        def setupOutputs(self):
            pass

        def execute(self, slot, subindex, roi, result):
            raise NotImplementedError("Data access for this mock operator not implemented yet.")
            if self._data[slot.name].data is None:
                raise RuntimeError(f"Slot {slot.name} should not be accessed")
            key = roi.toSlice()
            if slot.level == 0:
                result[...] = self._data[slot.name].data[key]
            elif slot.level == 1:
                result[...] = self._data[slot.name].data[subindex][key]

    assert all(slot_descr.level in [0, 1] for slot_descr in slot_data.values())

    MultiOutputMockOp = type(
        "MultiOutputMockOp",
        (_OP,),
        {slot_name: OutputSlot(level=slot_descr.level) for slot_name, slot_descr in slot_data.items()},
    )
    op = MultiOutputMockOp(slot_data, graph=graph)

    return op
