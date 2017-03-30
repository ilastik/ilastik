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
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot, \
    SerialHdf5BlockSlot, SerialPickleableSlot, SerialPickledValueSlot

try:
    import hytra
    WITH_HYTRA = True
except ImportError as e:
    WITH_HYTRA = False

class StructuredTrackingSerializer(AppletSerializer):

    def __init__(self, topLevelOperator, projectFileGroupName):

        if WITH_HYTRA:
            slots = [ SerialDictSlot(topLevelOperator.Parameters, selfdepends=True),
                      SerialDictSlot(topLevelOperator.FilteredLabels, transform=str, selfdepends=True),
                      SerialPickledValueSlot(topLevelOperator.ExportSettings),
                      SerialPickledValueSlot(topLevelOperator.HypothesesGraph),
                      SerialPickledValueSlot(topLevelOperator.ResolvedMergers),
                      SerialSlot(topLevelOperator.DivisionWeight),
                      SerialSlot(topLevelOperator.DetectionWeight),
                      SerialSlot(topLevelOperator.TransitionWeight),
                      SerialSlot(topLevelOperator.AppearanceWeight),
                      SerialSlot(topLevelOperator.DisappearanceWeight),
                      SerialSlot(topLevelOperator.MaxNumObjOut)
            ]
        else:
            try:
                import pgmlink
            except:
                import pgmlinkNoIlpSolver as pgmlink

            slots = [ SerialDictSlot(topLevelOperator.Parameters, selfdepends=True),
                        SerialHdf5BlockSlot(topLevelOperator.OutputHdf5,
                                         topLevelOperator.InputHdf5,
                                         topLevelOperator.CleanBlocks,
                                         name="CachedOutput"),
                        SerialDictSlot(topLevelOperator.EventsVector, transform=str, selfdepends=True),
                        SerialDictSlot(topLevelOperator.FilteredLabels, transform=str, selfdepends=True),
                        SerialSlot(topLevelOperator.DivisionWeight),
                        SerialSlot(topLevelOperator.DetectionWeight),
                        SerialSlot(topLevelOperator.TransitionWeight),
                        SerialSlot(topLevelOperator.AppearanceWeight),
                        SerialSlot(topLevelOperator.DisappearanceWeight),
                        SerialSlot(topLevelOperator.MaxNumObjOut)
            ]

            if 'MergerOutput' in topLevelOperator.outputs:
                slots.append(SerialHdf5BlockSlot(topLevelOperator.MergerOutputHdf5,
                                         topLevelOperator.MergerInputHdf5,
                                         topLevelOperator.MergerCleanBlocks,
                                         name="MergerCachedOutput"),
                              )


            if 'CoordinateMap' in topLevelOperator.outputs:
                slots.append(SerialPickleableSlot(topLevelOperator.CoordinateMap, 1, pgmlink.TimestepIdCoordinateMap()))

        super(StructuredTrackingSerializer, self ).__init__(projectFileGroupName, slots=slots, operator=topLevelOperator)
