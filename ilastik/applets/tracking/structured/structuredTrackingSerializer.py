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
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot, deleteIfPresent,\
    getOrCreateGroup, SerialHdf5BlockSlot, SerialPickleableSlot, SerialPickledValueSlot
from ilastik.applets.tracking.base.trackingSerializer import TrackingSerializer

import pgmlink

class SerialDivisionsSlot(SerialSlot):
    def serialize(self, group):
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        for i, op in enumerate(innerops):
            dset = []
            for trackid in op.divisions.keys():
                (children, t_parent) = op.divisions[trackid]
                dset.append([trackid, children[0], children[1], t_parent])
            if len(dset) > 0:
                group.create_dataset(name=str(i), data=dset)
        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        opgroup = group[self.name]
        for inner in opgroup.keys():
            dset = opgroup[inner]            
            op = innerops[int(inner)]
            divisions = {}
            for row in dset:
                divisions[row[0]] = ([row[1],row[2]], row[3])
            op.divisions = divisions
        self.dirty = False
        
class SerialLabelsSlot(SerialSlot):
    def serialize(self, group):
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        for i, op in enumerate(innerops):
            gr = getOrCreateGroup(group, str(i))
            for t in op.labels.keys():
                t_gr = getOrCreateGroup(gr, str(t))
                for oid in op.labels[t].keys():
                    l = op.labels[t][oid]
                    dset = list(l)
                    if len(dset) > 0:
                        t_gr.create_dataset(name=str(oid), data=dset)
        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        opgroup = group[self.name]
        for inner in opgroup.keys():
            gr = opgroup[inner]
            op = innerops[int(inner)]
            labels = {}
            for t in gr.keys():
                labels[int(t)] = {}
                t_gr = gr[str(t)]
                for oid in t_gr.keys():
                    labels[int(t)][int(oid)] = set(t_gr[oid])
            op.labels = labels
        self.dirty = False
        
class StructuredTrackingSerializer(AppletSerializer):

    def __init__(self, topLevelOperator, projectFileGroupName):
        slots = [ SerialDictSlot(topLevelOperator.Parameters, selfdepends=True),
                  SerialDictSlot(topLevelOperator.EventsVector, transform=str, selfdepends=True),
                  SerialDictSlot(topLevelOperator.FilteredLabels, transform=str, selfdepends=True),
                  SerialPickledValueSlot(topLevelOperator.ExportSettings),
                  SerialSlot(topLevelOperator.DivisionWeight),
                  SerialSlot(topLevelOperator.DetectionWeight),
                  SerialSlot(topLevelOperator.TransitionWeight),
                  SerialSlot(topLevelOperator.AppearanceWeight),
                  SerialSlot(topLevelOperator.DisappearanceWeight),
                  SerialSlot(topLevelOperator.MaxNumObjOut)
        ]

        if 'CoordinateMap' in topLevelOperator.outputs:
            slots.append(SerialPickleableSlot(topLevelOperator.CoordinateMap, 1, pgmlink.TimestepIdCoordinateMap()))

        super(StructuredTrackingSerializer, self ).__init__(projectFileGroupName, slots=slots, operator=topLevelOperator)
