###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
import pickle
import json

import numpy as np
import typing

from tiktorch.types import Model, ModelState

from ilastik.applets.base.appletSerializer import (
    AppletSerializer,
    SerialSlot,
    SerialListSlot,
    SerialBlockSlot,
)


class BinaryStringSlot(SerialSlot):
    """
    Implements the logic for serializing a binary slot.

    Allows to store binary string containing nulls,
    while BinarySlot will fail with following error:
        ValueError: VLEN strings do not support embedded NULLs
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def _saveValue(group, name, value):
        if value:
            group.create_dataset(name, data=np.void(value))

    @staticmethod
    def _getValue(subgroup, slot):
        val = subgroup[()]
        slot.setValue(val.tobytes())


class NNClassificationSerializer(AppletSerializer):
    def __init__(self, topLevelOperator, projectFileGroupName):
        self.VERSION = 1

        slots = [
            SerialListSlot(topLevelOperator.LabelNames),
            SerialListSlot(topLevelOperator.LabelColors, transform=lambda x: tuple(x.flat)),
            SerialListSlot(topLevelOperator.PmapColors, transform=lambda x: tuple(x.flat)),
            SerialBlockSlot(
                topLevelOperator.LabelImages,
                topLevelOperator.LabelInputs,
                topLevelOperator.NonzeroLabelBlocks,
                name="LabelSets",
                subname="labels{:03d}",
                selfdepends=False,
                shrink_to_bb=True,
            ),
            BinaryStringSlot(topLevelOperator.ModelBinary),
            #SerialModelStateSlot(topLevelOperator.ModelState),
            #SerialListModelStateSlot(topLevelOperator.Checkpoints),
        ]

        super().__init__(projectFileGroupName, slots)


def maybe_get_value(dset, key, default=None):
    if key in dset:
        return dset[key][()].tostring()
    else:
        return default


class ModelStateSerializer:
    OPTIMIZER = "optimizer"
    MODEL = "model"
    META = "metadata"

    @classmethod
    def dump_model_state(cls, group, state: ModelState) -> None:
        if not state:
            return

        if state.model_state:
            group.create_dataset(cls.MODEL, data=np.void(state.model_state))

        if state.optimizer_state:
            group.create_dataset(cls.OPTIMIZER, data=np.void(state.optimizer_state))

        metadata = {"loss": state.loss, "epoch": state.epoch}

        group.create_dataset(cls.META, data=np.void(json_dumps_binary(metadata)))

    @classmethod
    def load_model_state(cls, group) -> ModelState:
        model = maybe_get_value(group, cls.MODEL, b"")
        optimizer = maybe_get_value(group, cls.OPTIMIZER, b"")
        metadata = json_loads_binary(maybe_get_value(group, cls.META, b"{}"))

        return ModelState(model_state=bytes(model), optimizer_state=bytes(optimizer), **metadata)


class SerialModelStateSlot(SerialSlot):
    def _saveValue(self, group, name: str, value: ModelState):
        model_group = group.require_group(self.name)
        ModelStateSerializer.dump_model_state(model_group, value)

    def _getValue(self, dset, slot):
        state = ModelStateSerializer.load_model_state(dset)
        slot.setValue(state)


class SerialListModelStateSlot(SerialSlot):
    def _saveValue(self, group, name: str, value: typing.List[ModelState]):
        if value is None:
            return

        model_group = group.require_group(self.name)

        states = value

        for idx, state in enumerate(states):
            state_group = model_group.require_group(str(idx))
            ModelStateSerializer.dump_model_state(state_group, state)

        model_group.attrs["length"] = len(states)

    def _getValue(self, dset, slot):
        states = []

        for idx in range(dset.attrs["length"]):
            state_group = dset[str(idx)]
            model_state = ModelStateSerializer.load_model_state(state_group)
            states.append(model_state)

        slot.setValue(states)
