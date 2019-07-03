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

from tiktorch.types import Model, ModelState

from ilastik.applets.base.appletSerializer import (
    AppletSerializer,
    SerialSlot,
    SerialListSlot,
    SerialDictSlot,
    SerialBlockSlot,
    SerialPickleableSlot,
    BinarySlot,
)


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
            SerialModelSlot(topLevelOperator.Model),
            SerialModelStateSlot(topLevelOperator.ModelState),
            SerialPickleableSlot(topLevelOperator.Checkpoints, version=4),
        ]

        super().__init__(projectFileGroupName, slots)


def json_dumps_binary(value):
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def json_loads_binary(value):
    return json.loads(value.decode("utf-8"))


def maybe_get(dset, key, default=None):
    if key in dset:
        return dset[key][()]
    else:
        return default


class SerialModelSlot(SerialSlot):
    def _saveValue(self, group, name: str, value: Model) -> None:
        model_group = group.require_group(self.name)

        if value:
            model_group.create_dataset("code", data=value.code)
            model_group.create_dataset("config", data=json_dumps_binary(value.config))
        else:
            model_group.create_dataset("code", data=b"")
            model_group.create_dataset("config", data=b"")

    def _getValue(self, dset, slot):
        code = maybe_get(dset, "code")

        if not code:
            slot.setValue(Model.Empty)
            return

        model = Model(code=code, config=json.loads(maybe_get(dset, "config", b"")))
        slot.setValue(model)


class SerialModelStateSlot(SerialSlot):
    OPTIMIZER = "optimizer"
    MODEL = "model"

    def _saveValue(self, group, name: str, value: ModelState):
        model_group = group.require_group(self.name)

        if value:
            model_group.create_dataset(self.MODEL, data=value.model_state)
            model_group.create_dataset(self.OPTIMIZER, data=value.optimizer_state)

    def _getValue(self, dset, slot):
        model = maybe_get(dset, self.MODEL, b"")
        optimizer = maybe_get(dset, self.OPTIMIZER, b"")

        state = ModelState(model_state=model, optimizer_state=optimizer)
        slot.setValue(state)
