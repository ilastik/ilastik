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
#		   http://ilastik.org/license.html
###############################################################################
import warnings

from ilastik.applets.base.appletSerializer import \
  AppletSerializer, SerialSlot, SerialDictSlot, \
  SerialClassifierSlot, SerialListSlot, SerialPickleableSlot

class SerialDictSlotWithoutDeserialization(SerialDictSlot):
    
    def __init__(self, slot, mainOperator, **kwargs):
        super(SerialDictSlotWithoutDeserialization, self).__init__(slot, **kwargs)
        self.mainOperator = mainOperator
    
    def serialize(self, group):
        #if self.slot.ready() and self.mainOperator._predict_enabled:
        return SerialDictSlot.serialize(self, group)
    
    def deserialize(self, group):
        # Do not deserialize this slot
        pass


class ObjectClassificationSerializer(AppletSerializer):
    # FIXME: predictions can only be saved, not loaded, because it
    # would call setValue() on a connected slot

    def __init__(self, topGroupName, operator):
        self.VERSION = 1  # Make sure to bump the version in case you make any changes in the serialization
        serialSlots = [
            SerialDictSlot(operator.SelectedFeatures),
            SerialListSlot(operator.LabelNames),
            SerialListSlot(operator.LabelColors, transform=lambda x: tuple(x.flat)),
            SerialListSlot(operator.PmapColors, transform=lambda x: tuple(x.flat)),
            SerialDictSlot(operator.LabelInputs, transform=int),
            SerialClassifierSlot(operator.Classifier,
                                 operator.classifier_cache,
                                 name="ClassifierForests"),
            SerialDictSlot(operator.CachedProbabilities,
                           operator.InputProbabilities,
                           transform=int),
            SerialSlot(operator.MaxNumObj),
            SerialPickleableSlot(operator.ExportSettings, self.VERSION, None)
        ]

        super(ObjectClassificationSerializer, self ).__init__(topGroupName,
                                                              slots=serialSlots,
                                                              operator=operator)
