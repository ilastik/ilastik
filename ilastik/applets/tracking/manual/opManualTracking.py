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
from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.utility.exportingOperator import ExportingOperator
from ilastik.utility.exportFile import objects_per_frame, ExportFile, ilastik_ids, Mode, Default
from operator import itemgetter
from itertools import compress
from functools import partial

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import List, SubRegion
from lazyflow.stype import Opaque

import numpy as np

import logging
logger = logging.getLogger(__name__)


class OpManualTracking(Operator, ExportingOperator):
    name = "Manual Tracking"
    category = "other"

    BinaryImage = InputSlot()
    LabelImage = InputSlot()
    RawImage = InputSlot()
    ActiveTrack = InputSlot(stype='int', value=0)
    ObjectFeatures = InputSlot(stype=Opaque, rtype=List)
    ComputedFeatureNames = InputSlot(rtype=List, stype=Opaque)

    TrackImage = OutputSlot()
    Labels = OutputSlot(stype=Opaque, rtype=List)
    Divisions = OutputSlot(stype=Opaque, rtype=List)
    UntrackedImage = OutputSlot()

    # Use a slot for storing the export settings in the project file.
    ExportSettings = OutputSlot()
    # Override functions ExportingOperator mixin
    def configure_table_export_settings(self, settings, selected_features):
        self.ExportSettings.setValue( (settings, selected_features) )
    def get_table_export_settings(self):
        if self.ExportSettings.ready():
            (settings, selected_features) = self.ExportSettings.value
            return (settings, selected_features)
        else:
            return None, None

    def __init__(self, parent=None, graph=None):
        super(OpManualTracking, self).__init__(parent=parent, graph=graph)
        self.labels = {}
        self.divisions = {}

        # As soon as input data is available, check its constraints
        self.RawImage.notifyReady(self._checkConstraints)
        self.BinaryImage.notifyReady(self._checkConstraints)

        self.export_progress_dialog = None

    def setupOutputs(self):
        self.TrackImage.meta.assignFrom(self.LabelImage.meta)
        self.UntrackedImage.meta.assignFrom(self.LabelImage.meta)

        for t in range(self.LabelImage.meta.shape[0]):
            if t not in self.labels.keys():
                self.labels[t] = {}


    def _checkConstraints(self, *args):
        if self.RawImage.ready():
            rawTaggedShape = self.RawImage.meta.getTaggedShape()
            if rawTaggedShape['t'] < 2:
                raise DatasetConstraintError(
                    "Tracking",
                    "For tracking, the dataset must have a time axis with at least 2 images.   " \
                    "Please load time-series data instead. See user documentation for details.")

        if self.LabelImage.ready():
            segmentationTaggedShape = self.LabelImage.meta.getTaggedShape()
            if segmentationTaggedShape['t'] < 2:
                raise DatasetConstraintError(
                    "Tracking",
                    "For tracking, the dataset must have a time axis with at least 2 images.   " \
                    "Please load time-series data instead. See user documentation for details.")

        if self.RawImage.ready() and self.LabelImage.ready():
            rawTaggedShape['c'] = None
            segmentationTaggedShape['c'] = None
            if dict(rawTaggedShape) != dict(segmentationTaggedShape):
                raise DatasetConstraintError("Tracking",
                                             "For tracking, the raw data and the prediction maps must contain the same " \
                                             "number of timesteps and the same shape.   " \
                                             "Your raw image has a shape of (t, x, y, z, c) = {}, whereas your prediction image has a " \
                                             "shape of (t, x, y, z, c) = {}" \
                                             .format(self.RawImage.meta.shape, self.BinaryImage.meta.shape))


    def execute(self, slot, subindex, roi, result):
        if slot is self.Divisions:
            result = {}
            for trackid in self.divisions.keys():
                (children, t_parent) = self.divisions[trackid]
                result[trackid] = (children, t_parent)
            return result

        if slot is self.Labels:
            result = {}
            for t in self.labels.keys():
                result[t] = self.labels[t]

        elif slot is self.TrackImage:
            for t in range(roi.start[0], roi.stop[0]):
                if t not in self.labels.keys():
                    result[t - roi.start[0], ...][:] = 0
                    return result

                result[t - roi.start[0], ...] = self.LabelImage.get(roi).wait()[t - roi.start[0], ...]
                result[t - roi.start[0], ..., 0] = self._relabel(result[t - roi.start[0], ..., 0], self.labels[t])

        elif slot is self.UntrackedImage:
            for t in range(roi.start[0], roi.stop[0]):
                result[t - roi.start[0], ...] = self.LabelImage.get(roi).wait()[t - roi.start[0], ...]
                labels_at = {}
                if t in self.labels.keys():
                    labels_at = self.labels[t]
                result[t - roi.start[0], ..., 0] = self._relabelUntracked(result[t - roi.start[0], ..., 0], labels_at)

        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot == self.LabelImage:
            self.labels = {}
            self.divisions = {}

    def _relabel(self, volume, replace):
        mp = np.arange(0, np.amax(volume) + 1, dtype=volume.dtype)
        mp[1:] = 0
        labels = np.unique(volume).tolist()
        if 0 in labels:
            labels.remove(0)
        for label in labels:
            if label in replace and len(replace[label]) > 0:
                l = list(replace[label])[-1]
                if l == -1:
                    mp[label] = 2 ** 16 - 1
                else:
                    mp[label] = l
        return mp[volume]

    def _relabelUntracked(self, volume, tracked_at):
        mp = np.arange(0, np.amax(volume) + 1, dtype=volume.dtype)
        mp[1:] = 1
        labels = np.unique(volume).tolist()
        if 0 in labels:
            labels.remove(0)
        for label in labels:
            if (label in tracked_at.keys()) and (len(tracked_at[label]) > 0):
                mp[label] = 0
        return mp[volume]

    def _getObjects(self, trange, misdet_idx):
        filtered_labels = {}
        oid2tids = {}
        alltids = set()
        for t in range(trange[0], trange[1]):
            count = 0
            filtered_labels[t] = []
            oid2tids[t] = {}
            troi = SubRegion(self.LabelImage, start=[t, ] + [0, ] * len(self.LabelImage.meta.shape[1:]),
                             stop=[t + 1, ] + list(self.LabelImage.meta.shape[1:]))
            max_oid = np.max(self.LabelImage.get(troi).wait())
            for idx in range(max_oid + 1):
                oid = int(idx) + 1
                if t in self.labels.keys() and oid in self.labels[t].keys():
                    if misdet_idx not in self.labels[t][oid]:
                        oid2tids[t][oid] = self.labels[t][oid]
                        for l in self.labels[t][oid]:
                            alltids.add(l)
                        count += 1

            logger.info("at timestep {}, {} traxels found".format(t, count))
        return oid2tids, alltids

    def save_export_progress_dialog(self, dialog):
        """
        Implements ExportOperator.save_export_progress_dialog
        Without this the progress dialog would be hidden after the export
        :param dialog: the ProgressDialog to save
        """
        self.export_progress_dialog = dialog

    @staticmethod
    def lookup_oid_for_tid(oid2tid, tid, t):
        mapping = oid2tid[t]
        for oid, tids in mapping.iteritems():
            if tid in tids:
                return oid
        raise ValueError("TID {} at t={} not found!".format(tid, t))

    def do_export(self, settings, selected_features, progress_slot, lane_index):
        """
        Implements ExportOperator.do_export(settings, selected_features, progress_slot
        Most likely called from ExportOperator.export_object_data
        :param settings: the settings for the exporter, see
        :param selected_features:
        :param progress_slot:
        :return:
        """
        assert lane_index == 0, "This has only been tested in tracking workflows with a single image."

        obj_count = list(objects_per_frame(self.LabelImage))  # slow
        divisions = self.divisions
        t_range = (0, self.LabelImage.meta.shape[self.LabelImage.meta.axistags.index("t")])
        oid2tid, _ = self._getObjects(t_range, None)  # slow
        max_tracks = max(max(map(len, i.values())) for i in oid2tid.values())
        ids = ilastik_ids(obj_count)

        export_file = ExportFile(settings["file path"])
        export_file.ExportProgress.subscribe(progress_slot)
        export_file.InsertionProgress.subscribe(progress_slot)

        export_file.add_columns("table", range(sum(obj_count)), Mode.List, Default.KnimeId)
        export_file.add_columns("table", list(ids), Mode.List, Default.IlastikId)
        export_file.add_columns("table", oid2tid, Mode.IlastikTrackingTable,
                                {"max": max_tracks, "counts": obj_count, "extra ids": {},
                                 "range": t_range})
        export_file.add_columns("table", self.ObjectFeatures, Mode.IlastikFeatureTable,
                                {"selection": selected_features})

        if divisions:
            ott = partial(self.lookup_oid_for_tid, oid2tid)
            divs = [(value[1], ott(key, value[1]), key, ott(value[0][0], value[1] + 1), value[0][0],
                     ott(value[0][1], value[1] + 1), value[0][1])
                    for key, value in sorted(divisions.iteritems(), key=itemgetter(0))]
            assert sum(Default.ManualDivMap) == len(divs[0])
            names = list(compress(Default.DivisionNames["names"], Default.ManualDivMap))
            export_file.add_columns("divisions", divs, Mode.List, extra={"names": names})

        if settings["file type"] == "h5":
            export_file.add_rois(Default.LabelRoiPath, self.LabelImage, "table", settings["margin"], "labeling")
            if settings["include raw"]:
                export_file.add_image(Default.RawPath, self.RawImage)
            else:
                export_file.add_rois(Default.RawRoiPath, self.RawImage, "table", settings["margin"])
        export_file.write_all(settings["file type"], settings["compression"])

        export_file.ExportProgress.unsubscribe(progress_slot)
        export_file.InsertionProgress.unsubscribe(progress_slot)

#    def _getObjects(self, time_range, x_range, y_range, z_range, size_range, misdet_idx):
#        trange = range(time_range[0], time_range[1])
#        print 'trange=', trange
#        feats = self.ObjectFeatures(trange).wait()        
#          
#        filtered_labels = {}
#        oid2tids = {}
#        alltids = set()
#        for t in feats.keys():
#            rc = feats[t][0]['RegionCenter']
#            if rc.size:
#                rc = rc[1:, ...]
#                
#            ct = feats[t][0]['Count']
#            if ct.size:
#                ct = ct[1:, ...]
#            mainOperator
#            print "at timestep ", t, rc.shape[0], "traxels found"
#            count = 0
#            filtered_labels[t] = []
#            oid2tids[t] = {}
#            for idx in range(rc.shape[0]):
#                oid = int(idx) + 1
#                x, y, z = rc[idx]
#                size = ct[idx]
#                if (x < x_range[0] or x >= x_range[1] or
#                    y < y_range[0] or y >= y_range[1] or
#                    z < z_range[0] or z >= z_range[1] or                    
#                    size < size_range[0] or size >= size_range[1]):
#                    filtered_labels[t].append(oid)
#                    continue
#                
#                count += 1
#                if t in self.labels.keys() and oid in self.labels[t].keys():
#                    if misdet_idx not in self.labels[t][oid]:
#                        oid2tids[t][oid] = self.labels[t][oid]
#                        for l in self.labels[t][oid]:
#                            alltids.add(l)   
#                         
#            print "at timestep ", t, count, "traxels passed filter"
#            
#        return oid2tids, alltids
    
