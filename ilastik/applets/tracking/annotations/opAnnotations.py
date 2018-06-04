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
from builtins import range
from ilastik.applets.base.applet import DatasetConstraintError

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import List, SubRegion
from lazyflow.stype import Opaque

import numpy as np
import vigra

import logging
logger = logging.getLogger(__name__)

class OpAnnotations(Operator):
    name = "Training"
    category = "other"
    
    BinaryImage = InputSlot()
    LabelImage = InputSlot()    
    RawImage = InputSlot()
    ActiveTrack = InputSlot(stype='int', value=0)
    ObjectFeatures = InputSlot(stype=Opaque, rtype=List)
    DivisionProbabilities = InputSlot(stype=Opaque, rtype=List)
    DetectionProbabilities = InputSlot(stype=Opaque, rtype=List)
    MaxNumObj = InputSlot()
    ComputedFeatureNames = InputSlot(rtype=List, stype=Opaque)

    TrackImage = OutputSlot()
    Labels = OutputSlot(stype=Opaque, rtype=List)
    Divisions = OutputSlot(stype=Opaque, rtype=List)
    Appearances = OutputSlot(stype=Opaque)
    Disappearances = OutputSlot(stype=Opaque)
    UntrackedImage = OutputSlot()

    Annotations = OutputSlot(stype=Opaque)

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
        super(OpAnnotations, self).__init__(parent=parent, graph=graph)
        self.labels = {}
        self.divisions = {}
        self.appearances = {}
        self.disappearances = {}

        self.Annotations.setValue(dict())
        self.Labels.setValue({})
        self.Divisions.setValue({})
        self.Appearances.setValue({})
        self.Disappearances.setValue({})

        self.RawImage.notifyReady( self._checkConstraints )
        self.BinaryImage.notifyReady( self._checkConstraints )

        self.export_progress_dialog = None
        self.ExportSettings.setValue( (None, None) )

    def setupOutputs(self):
        self.TrackImage.meta.assignFrom(self.LabelImage.meta)
        self.UntrackedImage.meta.assignFrom(self.LabelImage.meta)

        for t in range(self.LabelImage.meta.shape[0]):
            if t not in list(self.labels.keys()):
                self.labels[t]={}

        self.Annotations.meta.dtype = object
        self.Annotations.meta.shape = (1,)

        self.Labels.meta.dtype = object
        self.Labels.meta.shape = (1,)

        self.Divisions.meta.dtype = object
        self.Divisions.meta.shape = (1,)

        self.Appearances.meta.dtype = object
        self.Appearances.meta.shape = (1,)

        self.Disappearances.meta.dtype = object
        self.Disappearances.meta.shape = (1,)

    def initOutputs(self):
        self.TrackImage.meta.assignFrom(self.LabelImage.meta)
        self.UntrackedImage.meta.assignFrom(self.LabelImage.meta)

        for t in range(self.LabelImage.meta.shape[0]):
            if t not in list(self.labels.keys()):
                self.labels[t]={}
            if t not in list(self.appearances.keys()):
                self.appearances[t]={}
            if t not in list(self.disappearances.keys()):
                self.disappearances[t]={}

    def _checkConstraints(self, *args):
        if self.RawImage.ready():
            rawTaggedShape = self.RawImage.meta.getTaggedShape()
            if rawTaggedShape['t'] < 2:
                raise DatasetConstraintError(
                     "Tracking",
                     "For tracking, the dataset must have a time axis with at least 2 images.   "\
                     "Please load time-series data instead. See user documentation for details." )

        if self.LabelImage.ready():
            segmentationTaggedShape = self.LabelImage.meta.getTaggedShape()        
            if segmentationTaggedShape['t'] < 2:
                raise DatasetConstraintError(
                     "Tracking",
                     "For tracking, the dataset must have a time axis with at least 2 images.   "\
                     "Please load time-series data instead. See user documentation for details." )

        if self.RawImage.ready() and self.LabelImage.ready():
            rawTaggedShape['c'] = None
            segmentationTaggedShape['c'] = None
            if dict(rawTaggedShape) != dict(segmentationTaggedShape):
                raise DatasetConstraintError("Tracking",
                     "For tracking, the raw data and the prediction maps must contain the same "\
                     "number of timesteps and the same shape.   "\
                     "Your raw image has a shape of (t, x, y, z, c) = {}, whereas your prediction image has a "\
                     "shape of (t, x, y, z, c) = {}"\
                     .format( self.RawImage.meta.shape, self.BinaryImage.meta.shape ) )
            
            
    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        if slot is self.Divisions:
            result = {}
            for trackid in list(self.divisions.keys()):
                (children, t_parent) = self.divisions[trackid] 
                result[trackid] = (children, t_parent)
            return result
         
        if slot is self.Labels:
            result = {}
            for t in list(self.labels.keys()):
                result[t] = self.labels[t]
                
        elif slot is self.TrackImage:
            for t in range(roi.start[0],roi.stop[0]):
                if t not in list(self.labels.keys()):
                    result[t-roi.start[0],...][:] = 0
                    return result

                result[t-roi.start[0],...] = self.LabelImage.get(roi).wait()[t-roi.start[0],...]
                result[t-roi.start[0], ..., 0] = self._relabel(result[t-roi.start[0], ..., 0], self.labels[t])        
        
        elif slot is self.UntrackedImage:
            for t in range(roi.start[0],roi.stop[0]):
                result[t-roi.start[0],...] = self.LabelImage.get(roi).wait()[t-roi.start[0],...]
                labels_at = {}
                if t in list(self.labels.keys()):
                    labels_at = self.labels[t]
                result[t-roi.start[0],...,0] = self._relabelUntracked(result[t-roi.start[0],...,0], labels_at)

        if slot.name == 'Annotations':
            annotations = self.Annotations[key].wait()
            result[...] = annotations
        elif slot.name =='Appearances':
            appearances = self.Appearances[key].wait()
            result[...] = appearances
        elif slot.name == 'Disappearances':
            disappearances = self.Disappearances[key].wait()
            result[...] = disappearances


        return result
        
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.LabelImage:
            self.labels = {}
            self.divisions = {}
            self.appearances = {}
            self.disappearances = {}
        elif slot.name == "Annotations":
            self.Annotations.setDirty( roi )
        elif slot.name == "Labels":
            self.Labels.setDirty( roi )
        elif slot.name == "Divisions":
            self.Divisions.setDirty( roi )
        elif slot.name == "Appearances":
            self.Appearances.setDirty( roi )
        elif slot.name == "Disappearances":
            self.Disappearances.setDirty( roi )
        # else:
        #     self.Labels.setDirty( slice(None) )
        #     self.Divisions.setDirty( slice(None) )
        #     self.Annotations.setDirty( slice(None) )

    def _relabel(self, volume, replace):
        mp = np.arange(0, np.amax(volume) + 1, dtype=volume.dtype)
        mp[1:] = 0
        labels = np.sort(vigra.analysis.unique(volume)).tolist()
        if 0 in labels:
            labels.remove(0)
        for label in labels:
            if label in replace and len(replace[label]) > 0:
                l = list(replace[label])[-1]
                if l == -1:
                    mp[label] = 2**16-1
                else:
                    mp[label] = l 
        return mp[volume]
    
    def _relabelUntracked(self, volume, tracked_at):
        mp = np.arange(0, np.amax(volume) + 1, dtype=volume.dtype)
        mp[1:] = 1
        labels = np.sort(vigra.analysis.unique(volume)).tolist()
        if 0 in labels:
            labels.remove(0)
        for label in labels:
            if (label in list(tracked_at.keys())) and (len(tracked_at[label]) > 0):                
                mp[label] = 0
        return mp[volume]
    
    def _getObjects(self, trange, misdet_idx):                  
        filtered_labels = {}
        oid2tids = {}
        alltids = set()
        for t in range(trange[0],trange[1]):
            count = 0
            filtered_labels[t] = []
            oid2tids[t] = {}
            troi = SubRegion(self.LabelImage, start=[t,] + [0,] * len(self.LabelImage.meta.shape[1:]), 
                             stop=[t+1,] + list(self.LabelImage.meta.shape[1:]))            
            max_oid = np.max(self.LabelImage.get(troi).wait())
            for idx in range(max_oid + 1):
                oid = int(idx) + 1                
                if t in list(self.labels.keys()) and oid in list(self.labels[t].keys()):
                    if misdet_idx not in self.labels[t][oid]:
                        oid2tids[t][oid] = self.labels[t][oid]
                        for l in self.labels[t][oid]:
                            alltids.add(l)   
                        count += 1
                         
            logger.info( "at timestep {}, {} traxels found".format( t, count ) )
            
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
        for oid, tids in mapping.items():
            if tid in tids:
                return oid
        raise ValueError("TID {} at t={} not found!".format(tid, t))

    def do_export(self, settings, selected_features, progress_slot, lane_index, filename_suffix=""):
        """
        Implements ExportOperator.do_export(settings, selected_features, progress_slot
        Most likely called from ExportOperator.export_object_data
        :param settings: the settings for the exporter, see
        :param selected_features:
        :param progress_slot:
        :param lane_index: Ignored. (This is a single-lane operator. It is the caller's responsibility to make sure he's calling the right lane.)
        :param filename_suffix: If provided, appended to the filename (before the extension).
        :return:
        """

        obj_count = list(objects_per_frame(self.LabelImage))  # slow
        divisions = self.divisions
        t_range = (0, self.LabelImage.meta.shape[self.LabelImage.meta.axistags.index("t")])
        oid2tid, _ = self._getObjects(t_range, None)  # slow
        tracks = [0 if list(map(len, list(i.values())))==[] else max(list(map(len, list(i.values())))) for i in list(oid2tid.values())]
        if tracks==[]:
            max_tracks = 0
        else:
            max_tracks = max(tracks)
        ids = ilastik_ids(obj_count)

        file_path = settings["file path"]
        if filename_suffix:
            path, ext = os.path.splitext(file_path)
            file_path = path + "-" + filename_suffix + ext

        export_file = ExportFile(file_path)
        export_file.ExportProgress.subscribe(progress_slot)
        export_file.InsertionProgress.subscribe(progress_slot)

        export_file.add_columns("table", list(range(sum(obj_count))), Mode.List, Default.KnimeId)
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
                    for key, value in sorted(iter(divisions.items()), key=itemgetter(0))]
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

