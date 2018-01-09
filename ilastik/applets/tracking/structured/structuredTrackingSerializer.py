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
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot, SerialPickleableSlot

class StructuredTrackingSerializer(AppletSerializer):

    def __init__(self, topLevelOperator, projectFileGroupName):
        self.VERSION = 1  # Make sure to bump the version in case you make any changes in the serialization
        try:
            slots = [ SerialDictSlot(topLevelOperator.Parameters, selfdepends=True),
                      SerialDictSlot(topLevelOperator.FilteredLabels, transform=str, selfdepends=True),
                      SerialPickleableSlot(topLevelOperator.ExportSettings, version=self.VERSION),
                      SerialPickleableSlot(topLevelOperator.HypothesesGraph, version=self.VERSION),
                      SerialPickleableSlot(topLevelOperator.LearningHypothesesGraph, version=self.VERSION),
                      SerialPickleableSlot(topLevelOperator.ResolvedMergers, version=self.VERSION),
                      SerialSlot(topLevelOperator.DivisionWeight),
                      SerialSlot(topLevelOperator.DetectionWeight),
                      SerialSlot(topLevelOperator.TransitionWeight),
                      SerialSlot(topLevelOperator.AppearanceWeight),
                      SerialSlot(topLevelOperator.DisappearanceWeight),
                      SerialSlot(topLevelOperator.MaxNumObjOut)
            ]
        except:
            slots = [ SerialDictSlot(topLevelOperator.Parameters, selfdepends=True),
                      SerialDictSlot(topLevelOperator.FilteredLabels, transform=str, selfdepends=True),
                      SerialPickleableSlot(topLevelOperator.ExportSettings, version=self.VERSION),
                      SerialPickleableSlot(topLevelOperator.ResolvedMergers, version=self.VERSION),
                      SerialSlot(topLevelOperator.DivisionWeight),
                      SerialSlot(topLevelOperator.DetectionWeight),
                      SerialSlot(topLevelOperator.TransitionWeight),
                      SerialSlot(topLevelOperator.AppearanceWeight),
                      SerialSlot(topLevelOperator.DisappearanceWeight),
                      SerialSlot(topLevelOperator.MaxNumObjOut)
            ]

        super(StructuredTrackingSerializer, self ).__init__(projectFileGroupName, slots=slots, operator=topLevelOperator)
