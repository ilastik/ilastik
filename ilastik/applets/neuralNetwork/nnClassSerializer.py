###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2021, the ilastik developers
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
import json
import logging

import numpy as np

# Note: bioimageio imports are delayed as to prevent https request to
# github and bioimage.io on ilastik startup

from ilastik.applets.base.appletSerializer import (
    AppletSerializer,
    SerialBlockSlot,
    SerialListSlot,
    SerialSlot,
    jsonSerializerRegistry,
)
from ilastik.applets.neuralNetwork.opNNclass import OpNNTrainingClassification

from .tiktorchController import BIOModelData, ModelInfo

logger = logging.getLogger(__name__)


@jsonSerializerRegistry.register_serializer(ModelInfo)
class ModelInfoSerializer(jsonSerializerRegistry.IDictSerializer):
    def serialize(self, obj: ModelInfo):
        return {
            "name": obj.name,
            "hasTraining": obj.hasTraining,
            "knownClasses": obj.knownClasses,
        }

    def deserialize(self, dct) -> ModelInfo:
        return ModelInfo(
            name=dct["name"],
            knownClasses=dct["knownClasses"],
            hasTraining=dct["hasTraining"],
        )


class BinarySlot(SerialSlot):
    """
    Implements the logic for serializing a binary slot.

    wraps value with numpy.void to avoid the following error:
    ValueError: VLEN strings do not support embedded NULLs
    """

    @staticmethod
    def _saveValue(group, name, value):
        if value:
            group.create_dataset(name, data=np.void(value))

    @staticmethod
    def _getValue(subgroup, slot):
        val = subgroup[()]
        slot.setValue(val.tobytes())


class BioimageIOModelSlot(SerialSlot):
    """ """

    @staticmethod
    def _saveValue(group, name, value):
        assert isinstance(value, BIOModelData)
        if value:
            ds = group.create_dataset(name, data=np.void(value.binary))
            ds.attrs["name"] = value.name
            ds.attrs["modelUri"] = value.modelUri
            ds.attrs["hashVal"] = value.hashVal

    @staticmethod
    def _getValue(subgroup, slot):
        from ilastik.utility.bioimageio_utils import get_model_descr_from_model_bytes

        binary = subgroup[()].tobytes()
        model_uri = subgroup.attrs["modelUri"]
        try:
            model = BIOModelData(
                modelUri=model_uri,
                binary=binary,
                rawDescription=get_model_descr_from_model_bytes(binary),
                hashVal=subgroup.attrs["hashVal"],
            )
        except KeyError as e:
            logger.debug(f"Could not deserialize model {e}")
            return

        slot.setValue(model)


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
            BioimageIOModelSlot(topLevelOperator.BIOModel),
        ]

        super().__init__(projectFileGroupName, slots)


class NNTrainingClassificationSerializer(AppletSerializer):
    def __init__(self, topLevelOperator: OpNNTrainingClassification, projectFileGroupName):
        self.VERSION = 1

        # todo: serialize unet config

        slots = [
            # SerialSlot(topLevelOperator.UnetConfig),
        ]

        super().__init__(projectFileGroupName, slots)
