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
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot, deleteIfPresent, getOrCreateGroup

class SerialAnnotationsSlot(SerialSlot):
    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        for i, op in enumerate(innerops):
            gr = getOrCreateGroup(group, str(i))
            labels_gr = getOrCreateGroup(gr, str("labels"))
            if "labels" in op.Annotations.value.keys():
                for t in op.Annotations.value["labels"].keys():
                    t_gr = getOrCreateGroup(labels_gr, str(t))
                    for oid in op.Annotations.value["labels"][t].keys():
                        l = op.Annotations.value["labels"][t][oid]
                        dset = list(l)
                        if len(dset) > 0:
                            t_gr.create_dataset(name=str(oid), data=dset)

            divisions_gr = getOrCreateGroup(gr, str("divisions"))
            dset = []
            if "divisions" in op.Annotations.value.keys():
                for trackid in op.Annotations.value["divisions"].keys():
                    (children, t_parent) = op.Annotations.value["divisions"][trackid]
                    dset.append([trackid, children[0], children[1], t_parent])
            if len(dset) > 0:
                divisions_gr.create_dataset(name=str(i), data=dset)
        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        opgroup = group[self.name]
        for inner in list(opgroup.keys()):
            gr = opgroup[inner]
            op = innerops[int(inner)]
            annotations = {}

            if "labels" in gr.keys():
                labels_gr = gr["labels"]
                annotations["labels"] = {}
                for t in labels_gr.keys():
                    annotations["labels"][int(t)] = {}
                    t_gr = labels_gr[str(t)]
                    for oid in t_gr.keys():
                        annotations["labels"][int(t)][int(oid)] = set(t_gr[oid])

            if "divisions" in gr.keys():
                divisions_gr = gr["divisions"]
                annotations["divisions"] = {}
                for divKey in divisions_gr.keys():
                    dset = divisions_gr[divKey]
                    annotations["divisions"] = {}
                    for row in dset:
                        annotations["divisions"][row[0]] = ([row[1],row[2]], row[3])

        op.Annotations.setValue(annotations)
        self.dirty = False

class SerialDivisionsSlot(SerialSlot):
    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        for i, op in enumerate(innerops):
            dset = []
            for trackid in list(op.divisions.keys()):
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
        for inner in list(opgroup.keys()):
            dset = opgroup[inner]
            op = innerops[int(inner)]
            divisions = {}
            for row in dset:
                divisions[row[0]] = ([row[1],row[2]], row[3])
            op.divisions = divisions
        self.dirty = False

class SerialLabelsSlot(SerialSlot):
    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        for i, op in enumerate(innerops):
            gr = getOrCreateGroup(group, str(i))
            for t in list(op.labels.keys()):
                t_gr = getOrCreateGroup(gr, str(t))
                for oid in list(op.labels[t].keys()):
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
        for inner in list(opgroup.keys()):
            gr = opgroup[inner]
            op = innerops[int(inner)]
            labels = {}
            for t in list(gr.keys()):
                labels[int(t)] = {}
                t_gr = gr[str(t)]
                for oid in list(t_gr.keys()):
                    labels[int(t)][int(oid)] = set(t_gr[oid])
            op.labels = labels
        self.dirty = False
        
class SerialAppearancesSlot(SerialSlot):
    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        for i, op in enumerate(innerops):
            gr = getOrCreateGroup(group, str(i))
            for t in list(op.appearances.keys()):
                t_gr = getOrCreateGroup(gr, str(t))
                for oid in list(op.appearances[t].keys()):
                    oid_gr = getOrCreateGroup(t_gr, str(oid))
                    for track in list(op.appearances[t][oid].keys()):
                        app = op.appearances[t][oid][track]
                        if app:
                            oid_gr.create_dataset(name=str(track), data=app)
        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        opgroup = group[self.name]
        for inner in list(opgroup.keys()):
            gr = opgroup[inner]
            op = innerops[int(inner)]
            appearances = {}
            for t in list(gr.keys()):
                appearances[int(t)] = {}
                t_gr = gr[str(t)]
                for oid in list(t_gr.keys()):
                    appearances[int(t)][int(oid)] = {}
                    oid_gr = t_gr[str(oid)]
                    for track in list(oid_gr.keys()):
                        appearances[int(t)][int(oid)][int(track)] = True
            op.appearances = appearances
            op.Appearances.setValue(appearances)
        self.dirty = False

class SerialDisappearancesSlot(SerialSlot):
    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        for i, op in enumerate(innerops):
            gr = getOrCreateGroup(group, str(i))
            for t in list(op.disappearances.keys()):
                t_gr = getOrCreateGroup(gr, str(t))
                for oid in list(op.disappearances[t].keys()):
                    oid_gr = getOrCreateGroup(t_gr, str(oid))
                    for track in list(op.disappearances[t][oid].keys()):
                        app = op.disappearances[t][oid][track]
                        if app:
                            oid_gr.create_dataset(name=str(track), data=app)
        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        mainOperator = self.slot.getRealOperator()
        innerops = mainOperator.innerOperators
        opgroup = group[self.name]
        for inner in list(opgroup.keys()):
            gr = opgroup[inner]
            op = innerops[int(inner)]
            disappearances = {}
            for t in list(gr.keys()):
                disappearances[int(t)] = {}
                t_gr = gr[str(t)]
                for oid in list(t_gr.keys()):
                    disappearances[int(t)][int(oid)] = {}
                    oid_gr = t_gr[str(oid)]
                    for track in list(oid_gr.keys()):
                        disappearances[int(t)][int(oid)][int(track)] = True
            op.disappearances = disappearances
            op.Disappearances.setValue(disappearances)
        self.dirty = False

class AnnotationsSerializer(AppletSerializer):
    
    def __init__(self, operator, projectFileGroupName):
        slots = [ SerialAnnotationsSlot(operator.Annotations),
                  SerialDivisionsSlot(operator.Divisions),
                  SerialLabelsSlot(operator.Labels),
                  SerialAppearancesSlot(operator.Appearances),
                  SerialDisappearancesSlot(operator.Disappearances)]
    
        super(AnnotationsSerializer, self ).__init__(projectFileGroupName, slots=slots)
