# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

import warnings

from ilastik.applets.base.appletSerializer import \
  AppletSerializer, SerialSlot, SerialDictSlot, \
  SerialClassifierSlot, SerialListSlot


class ObjectClassificationSerializer(AppletSerializer):
    # FIXME: predictions can only be saved, not loaded, because it
    # would call setValue() on a connected slot

    def __init__(self, topGroupName, operator):
        serialSlots = [
            SerialDictSlot(operator.SelectedFeatures, transform=str),
            SerialListSlot(operator.LabelNames,
                           transform=str),
            SerialListSlot(operator.LabelColors, transform=lambda x: tuple(x.flat)),
            SerialListSlot(operator.PmapColors, transform=lambda x: tuple(x.flat)),
            SerialDictSlot(operator.LabelInputs, transform=int),
            SerialClassifierSlot(operator.Classifier,
                                 operator.classifier_cache,
                                 name="ClassifierForests",
                                 subname="Forest{:04d}"),
            SerialDictSlot(operator.CachedProbabilities,
                           operator.InputProbabilities,
                           transform=int),
        ]

        super(ObjectClassificationSerializer, self ).__init__(topGroupName,
                                                              slots=serialSlots,
                                                              operator=operator)
