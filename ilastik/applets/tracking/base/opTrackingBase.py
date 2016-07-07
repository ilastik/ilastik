# ##############################################################################
# ilastik: interactive learning and segmentation toolkit
#
# Copyright (C) 2011-2014, the ilastik developers
# <team@ilastik.org>
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
# http://ilastik.org/license.html
# ##############################################################################
import os
from functools import partial
import logging

import numpy as np

from lazyflow.graph import Operator, InputSlot, OutputSlot
from ilastik.utility.exportingOperator import ExportingOperator
from lazyflow.rtype import List
from lazyflow.stype import Opaque
try:
    import pgmlink
except:
    import pgmlinkNoIlpSolver as pgmlink
from ilastik.applets.tracking.base.trackingUtilities import relabel, \
    get_dict_value
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key
from ilastik.applets.objectExtraction import config
from ilastik.applets.base.applet import DatasetConstraintError
from lazyflow.operators.opCompressedCache import OpCompressedCache
from lazyflow.operators.valueProviders import OpZeroDefault
from lazyflow.roi import sliceToRoi


logger = logging.getLogger(__name__)


class OpTrackingBase(Operator, ExportingOperator):
    name = "Tracking"
    category = "other"

    LabelImage = InputSlot()
    ObjectFeatures = InputSlot(stype=Opaque, rtype=List)
    ObjectFeaturesWithDivFeatures = InputSlot(optional=True, stype=Opaque, rtype=List)
    ComputedFeatureNames = InputSlot(rtype=List, stype=Opaque)
    ComputedFeatureNamesWithDivFeatures = InputSlot(optional=True, rtype=List, stype=Opaque)
    EventsVector = InputSlot(value={})
    FilteredLabels = InputSlot(value={})
    RawImage = InputSlot()
    Parameters = InputSlot(value={})

    # for serialization
    InputHdf5 = InputSlot(optional=True)
    CleanBlocks = OutputSlot()
    AllBlocks = OutputSlot()
    OutputHdf5 = OutputSlot()
    CachedOutput = OutputSlot()  # For the GUI (blockwise-access)

    Output = OutputSlot()

    # Use a slot for storing the export settings in the project file.
    ExportSettings = InputSlot()

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
        super(OpTrackingBase, self).__init__(parent=parent, graph=graph)
        self.label2color = []
        self.mergers = []
        self.resolvedto = []

        self.track_id = None
        self.extra_track_ids = None
        self.divisions = None

        self._opCache = OpCompressedCache(parent=self)
        self._opCache.InputHdf5.connect(self.InputHdf5)
        self._opCache.Input.connect(self.Output)
        self.CleanBlocks.connect(self._opCache.CleanBlocks)
        self.OutputHdf5.connect(self._opCache.OutputHdf5)
        self.CachedOutput.connect(self._opCache.Output)

        self.zeroProvider = OpZeroDefault(parent=self)
        self.zeroProvider.MetaInput.connect(self.LabelImage)

        # As soon as input data is available, check its constraints
        self.RawImage.notifyReady(self._checkConstraints)
        self.LabelImage.notifyReady(self._checkConstraints)

        self.export_progress_dialog = None
        self.ExportSettings.setValue( (None, None) )

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.LabelImage.meta)

        # cache our own output, don't propagate from internal operator
        chunks = list(self.LabelImage.meta.shape)
        # FIXME: assumes t,x,y,z,c
        chunks[0] = 1  # 't'        
        self._blockshape = tuple(chunks)
        self._opCache.BlockShape.setValue(self._blockshape)

        self.AllBlocks.meta.shape = (1,)
        self.AllBlocks.meta.dtype = object


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
        if slot is self.Output:
            result[:] = self.LabelImage.get(roi).wait()
            if not self.Parameters.ready():
                raise Exception("Parameter slot is not ready")
            parameters = self.Parameters.value

            t_start = roi.start[0]
            t_end = roi.stop[0]
            for t in range(t_start, t_end):
                if ('time_range' in parameters and t <= parameters['time_range'][-1] and t >= parameters['time_range'][
                    0]) and len(self.label2color) > t:
                    result[t - t_start, ..., 0] = relabel(result[t - t_start, ..., 0], self.label2color[t])
                else:
                    result[t - t_start, ...] = 0
            return result
        elif slot == self.AllBlocks:
            # if nothing was computed, return empty list
            if len(self.label2color) == 0:
                result[0] = []
                return result

            all_block_rois = []
            shape = self.Output.meta.shape
            # assumes t,x,y,z,c
            slicing = [slice(None), ] * 5
            for t in range(shape[0]):
                slicing[0] = slice(t, t + 1)
                all_block_rois.append(sliceToRoi(slicing, shape))

            result[0] = all_block_rois
            return result


    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.LabelImage:
            self.Output.setDirty(roi)
        elif inputSlot is self.EventsVector:
            self._setLabel2Color()
            try:
                self._setLabel2Color(export_mode=True)
            except:
                logger.debug("Warning: some label information might be wrong...")


    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.InputHdf5, "Invalid slot for setInSlot(): {}".format(slot.name)

    def _setLabel2Color(self, successive_ids=True, export_mode=False):
        if not self.EventsVector.ready() or not self.Parameters.ready() \
                or not self.FilteredLabels.ready():
            return

        if export_mode:
            assert successive_ids, "Export mode only works for successive ids"

        events = self.EventsVector.value
        parameters = self.Parameters.value
        
        time_min = 0
        time_max = self.RawImage.meta.shape[0] - 1 # Assumes t,x,y,z,c
        if 'time_range' in parameters:
            time_min, time_max = parameters['time_range']
        time_range = range(time_min, time_max)

        filtered_labels = self.FilteredLabels.value

        label2color = []
        label2color.append({})
        mergers = []
        resolvedto = []

        maxId = 2  # misdetections have id 1

        # handle start time offsets
        for i in range(time_range[0]):
            label2color.append({})
            mergers.append({})
            resolvedto.append({})

        extra_track_ids = {}
        if export_mode:
            multi_move = {}
            multi_move_next = {}
            divisions = []

        for i in time_range:
            app = get_dict_value(events[str(i - time_range[0] + 1)], "app", [])
            div = get_dict_value(events[str(i - time_range[0] + 1)], "div", [])
            mov = get_dict_value(events[str(i - time_range[0] + 1)], "mov", [])
            merger = get_dict_value(events[str(i - time_range[0])], "merger", [])
            res = get_dict_value(events[str(i - time_range[0])], "res", {})

            logger.debug(" {} app at {}".format(len(app), i))
            logger.debug(" {} div at {}".format(len(div), i))
            logger.debug(" {} mov at {}".format(len(mov), i))
            logger.debug(" {} merger at {}".format(len(merger), i))

            label2color.append({})
            mergers.append({})
            moves_at = []
            resolvedto.append({})

            if export_mode:
                moves_to = {}

            for e in app:
                if successive_ids:
                    label2color[-1][int(e[0])] = maxId  # in export mode, the label color is used as track ID
                    maxId += 1
                else:
                    label2color[-1][int(e[0])] = np.random.randint(1, 255)

            for e in mov:
                if export_mode:
                    if e[1] in moves_to:
                        multi_move.setdefault(i, {})
                        multi_move[i][e[0]] = e[1]
                        if len(moves_to[e[1]]) == 1:  # if we are just setting up this multi move
                            multi_move[i][moves_to[e[1]][0]] = e[1]
                        multi_move_next[(i, e[1])] = 0
                    moves_to.setdefault(e[1], [])
                    moves_to[e[1]].append(e[0])  # moves_to[target] contains list of incoming object ids

                # alternative way of appearance
                if not label2color[-2].has_key(int(e[0])):
                    if successive_ids:
                        label2color[-2][int(e[0])] = maxId
                        maxId += 1
                    else:
                        label2color[-2][int(e[0])] = np.random.randint(1, 255)

                # assign color of parent
                label2color[-1][int(e[1])] = label2color[-2][int(e[0])]
                moves_at.append(int(e[0]))

                if export_mode:
                    key = i - 1, e[0]
                    if key in multi_move_next:  # captures mergers staying connected over longer time spans
                        multi_move_next[key] = e[1]  # redirects output of last merger to target in this frame
                        multi_move_next[(i, e[1])] = 0  # sets current end to zero (might be changed by above line in the future)

            for e in div:  # event(parent, child, child)
                # if not label2color[-2].has_key(int(e[0])):
                if not int(e[0]) in label2color[-2]:
                    if successive_ids:
                        label2color[-2][int(e[0])] = maxId
                        maxId += 1
                    else:
                        label2color[-2][int(e[0])] = np.random.randint(1, 255)
                ancestor_color = label2color[-2][int(e[0])]
                if export_mode:
                    label2color[-1][int(e[1])] = maxId
                    label2color[-1][int(e[2])] = maxId + 1
                    divisions.append((i, int(e[0]), ancestor_color,
                                      int(e[1]), maxId,
                                      int(e[2]), maxId + 1
                    ))
                    maxId += 2
                else:
                    label2color[-1][int(e[1])] = ancestor_color
                    label2color[-1][int(e[2])] = ancestor_color

            for e in merger:
                mergers[-1][int(e[0])] = int(e[1])

            for o, r in res.iteritems():
                resolvedto[-1][int(o)] = [int(c) for c in r[:-1]]
                # label the original object with the false detection label
                mergers[-1][int(o)] = len(r[:-1])

                if export_mode:
                    extra_track_ids.setdefault(i, {})
                    extra_track_ids[i][int(o)] = [int(c) for c in r[:-1]]

        # last timestep
        merger = get_dict_value(events[str(time_range[-1] - time_range[0] + 1)], "merger", [])
        mergers.append({})
        for e in merger:
            mergers[-1][int(e[0])] = int(e[1])

        res = get_dict_value(events[str(time_range[-1] - time_range[0] + 1)], "res", {})
        resolvedto.append({})
        if export_mode:
            extra_track_ids[time_range[-1] + 1] = {}
        for o, r in res.iteritems():
            resolvedto[-1][int(o)] = [int(c) for c in r[:-1]]
            mergers[-1][int(o)] = len(r[:-1])

            if export_mode:
                    extra_track_ids[time_range[-1] + 1][int(o)] = [int(c) for c in r[:-1]]

        # mark the filtered objects
        for i in filtered_labels.keys():
            if int(i) + time_range[0] >= len(label2color):
                continue
            fl_at = filtered_labels[i]
            for l in fl_at:
                assert l not in label2color[int(i) + time_range[0]]
                label2color[int(i) + time_range[0]][l] = 0

        if export_mode:  # don't set fields when in export_mode
            self.track_id = label2color
            self.divisions = divisions
            self.extra_track_ids = extra_track_ids
            return label2color, extra_track_ids, divisions

        self.track_id = label2color
        self.extra_track_ids = extra_track_ids
        self.label2color = label2color
        self.resolvedto = resolvedto
        self.mergers = mergers

        self.Output._value = None
        self.Output.setDirty(slice(None))

        if 'MergerOutput' in self.outputs:
            self.MergerOutput._value = None
            self.MergerOutput.setDirty(slice(None))

    def export_track_ids(self):
        return self._setLabel2Color(export_mode=True)

    def track_children(self, track_id, start=0):
        if start in self.divisions:
            for t, _, track, _, child_track1, _, child_track2 in self.divisions[start:]:
                if track == track_id:
                    children_of = partial(self.track_children, start=t)
                    return [child_track1, child_track2] + \
                           children_of(child_track1) + children_of(child_track2)
        return []

    def track_parent(self, track_id):
        if not self.divisions == {}:
            for t, oid, track, _, child_track1, _, child_track2 in self.divisions[:-1]:
                if track_id in (child_track1, child_track2):
                    return [track] + self.track_parent(track)
        return []

    def track_family(self, track_id):
        return self.track_children(track_id), self.track_parent(track_id)


    def _generate_traxelstore(self,
                              time_range,
                              x_range,
                              y_range,
                              z_range,
                              size_range,
                              x_scale=1.0,
                              y_scale=1.0,
                              z_scale=1.0,
                              with_div=False,
                              with_local_centers=False,
                              median_object_size=None,
                              max_traxel_id_at=None,
                              with_opt_correction=False,
                              with_coordinate_list=False,
                              with_classifier_prior=False):

        if not self.Parameters.ready():
            raise Exception("Parameter slot is not ready")

        parameters = self.Parameters.value
        parameters['scales'] = [x_scale, y_scale, z_scale]
        parameters['time_range'] = [min(time_range), max(time_range)]
        parameters['x_range'] = x_range
        parameters['y_range'] = y_range
        parameters['z_range'] = z_range
        parameters['size_range'] = size_range

        logger.info("generating traxels")
        logger.info("fetching region features and division probabilities")
        feats = self.ObjectFeatures(time_range).wait()

        if with_div:
            if not self.DivisionProbabilities.ready() or len(self.DivisionProbabilities([0]).wait()[0]) == 0:
                msgStr = "\nDivision classifier has not been trained! " + \
                         "Uncheck divisible objects if your objects don't divide or " + \
                         "go back to the Division Detection applet and train it."
                raise DatasetConstraintError ("Tracking",msgStr)
            divProbs = self.DivisionProbabilities(time_range).wait()

        if with_local_centers:
            localCenters = self.RegionLocalCenters(time_range).wait()

        if with_classifier_prior:
            if not self.DetectionProbabilities.ready() or len(self.DetectionProbabilities([0]).wait()[0]) == 0:
                msgStr = "\nObject count classifier has not been trained! " + \
                         "Go back to the Object Count Classification applet and train it."
                raise DatasetConstraintError ("Tracking",msgStr)
            detProbs = self.DetectionProbabilities(time_range).wait()

        logger.info("filling traxelstore")
        ts = pgmlink.TraxelStore()
        fs = pgmlink.FeatureStore()

        max_traxel_id_at = pgmlink.VectorOfInt()
        filtered_labels = {}
        obj_sizes = []
        total_count = 0
        empty_frame = False

        for t in feats.keys():
            rc = feats[t][default_features_key]['RegionCenter']
            lower = feats[t][default_features_key]['Coord<Minimum>']
            upper = feats[t][default_features_key]['Coord<Maximum>']
            if rc.size:
                rc = rc[1:, ...]
                lower = lower[1:, ...]
                upper = upper[1:, ...]

            if with_opt_correction:
                try:
                    rc_corr = feats[t][config.features_vigra_name]['RegionCenter_corr']
                except:
                    raise Exception, 'Can not consider optical correction since it has not been computed before'
                if rc_corr.size:
                    rc_corr = rc_corr[1:, ...]

            ct = feats[t][default_features_key]['Count']
            if ct.size:
                ct = ct[1:, ...]

            logger.debug("at timestep {}, {} traxels found".format(t, rc.shape[0]))
            count = 0
            filtered_labels_at = []
            for idx in range(rc.shape[0]):
                # for 2d data, set z-coordinate to 0:
                if len(rc[idx]) == 2:
                    x, y = rc[idx]
                    z = 0
                elif len(rc[idx]) == 3:
                    x, y, z = rc[idx]
                else:
                    raise DatasetConstraintError ("Tracking", "The RegionCenter feature must have dimensionality 2 or 3.")
                size = ct[idx]
                if (x < x_range[0] or x >= x_range[1] or
                            y < y_range[0] or y >= y_range[1] or
                            z < z_range[0] or z >= z_range[1] or
                            size < size_range[0] or size >= size_range[1]):
                    filtered_labels_at.append(int(idx + 1))
                    continue
                else:
                    count += 1
                tr = pgmlink.Traxel()
                tr.set_feature_store(fs)
                tr.set_x_scale(x_scale)
                tr.set_y_scale(y_scale)
                tr.set_z_scale(z_scale)
                tr.Id = int(idx + 1)
                tr.Timestep = int(t)

                # pgmlink expects always 3 coordinates, z=0 for 2d data
                tr.add_feature_array("com", 3)
                for i, v in enumerate([x, y, z]):
                    tr.set_feature_value('com', i, float(v))

                tr.add_feature_array("CoordMinimum", 3)
                for i, v in enumerate(lower[idx]):
                    tr.set_feature_value("CoordMinimum", i, float(v))
                tr.add_feature_array("CoordMaximum", 3)
                for i, v in enumerate(upper[idx]):
                    tr.set_feature_value("CoordMaximum", i, float(v))

                if with_opt_correction:
                    tr.add_feature_array("com_corrected", 3)
                    for i, v in enumerate(rc_corr[idx]):
                        tr.set_feature_value("com_corrected", i, float(v))
                    if len(rc_corr[idx]) == 2:
                        tr.set_feature_value("com_corrected", 2, 0.)

                if with_div:
                    tr.add_feature_array("divProb", 1)
                    # idx+1 because rc and ct start from 1, divProbs starts from 0
                    tr.set_feature_value("divProb", 0, float(divProbs[t][idx + 1][1]))

                if with_classifier_prior:
                    tr.add_feature_array("detProb", len(detProbs[t][idx + 1]))
                    for i, v in enumerate(detProbs[t][idx + 1]):
                        val = float(v)
                        if val < 0.0000001:
                            val = 0.0000001
                        if val > 0.99999999:
                            val = 0.99999999
                        tr.set_feature_value("detProb", i, float(val))


                # FIXME: check whether it is 2d or 3d data!
                if with_local_centers:
                    tr.add_feature_array("localCentersX", len(localCenters[t][idx + 1]))
                    tr.add_feature_array("localCentersY", len(localCenters[t][idx + 1]))
                    tr.add_feature_array("localCentersZ", len(localCenters[t][idx + 1]))
                    for i, v in enumerate(localCenters[t][idx + 1]):
                        tr.set_feature_value("localCentersX", i, float(v[0]))
                        tr.set_feature_value("localCentersY", i, float(v[1]))
                        tr.set_feature_value("localCentersZ", i, float(v[2]))

                tr.add_feature_array("count", 1)
                tr.set_feature_value("count", 0, float(size))
                if median_object_size is not None:
                    obj_sizes.append(float(size))

                ts.add(fs, tr)

            if len(filtered_labels_at) > 0:
                filtered_labels[str(int(t) - time_range[0])] = filtered_labels_at
            logger.debug("at timestep {}, {} traxels passed filter".format(t, count))
            max_traxel_id_at.append(int(rc.shape[0]))
            if count == 0:
                empty_frame = True

            total_count += count

        if median_object_size is not None:
            median_object_size[0] = np.median(np.array(obj_sizes), overwrite_input=True)
            logger.info('median object size = ' + str(median_object_size[0]))

        self.FilteredLabels.setValue(filtered_labels, check_changed=True)

        return fs, ts, empty_frame, max_traxel_id_at

    def save_export_progress_dialog(self, dialog):
        """
        Implements ExportOperator.save_export_progress_dialog
        Without this the progress dialog would be hidden after the export
        :param dialog: the ProgressDialog to save
        """
        self.export_progress_dialog = dialog

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

        with_divisions = self.Parameters.value["withDivisions"] if self.Parameters.ready() else False
        if with_divisions:
            object_feature_slot = self.ObjectFeaturesWithDivFeatures
        else:
            object_feature_slot = self.ObjectFeatures

        self._do_export_impl(settings, selected_features, progress_slot, object_feature_slot, self.LabelImage, lane_index, filename_suffix)


    def _do_export_impl(self, settings, selected_features, progress_slot, object_feature_slot, label_image_slot, lane_index, filename_suffix=""):
        from ilastik.utility.exportFile import objects_per_frame, ExportFile, ilastik_ids, Mode, Default, \
            flatten_dict, division_flatten_dict

        selected_features = list(selected_features)
        with_divisions = self.Parameters.value["withDivisions"] if self.Parameters.ready() else False
        obj_count = list(objects_per_frame(label_image_slot))
        track_ids, extra_track_ids, divisions = self.export_track_ids()
        self._setLabel2Color()
        lineage = flatten_dict(self.label2color, obj_count)
        multi_move_max = self.Parameters.value["maxObj"] if self.Parameters.ready() else 2
        t_range = self.Parameters.value["time_range"] if self.Parameters.ready() else (0, 0)
        ids = ilastik_ids(obj_count)

        file_path = settings["file path"]
        if filename_suffix:
            path, ext = os.path.splitext(file_path)
            file_path = path + "-" + filename_suffix + ext

        export_file = ExportFile(file_path)
        export_file.ExportProgress.subscribe(progress_slot)
        export_file.InsertionProgress.subscribe(progress_slot)

        export_file.add_columns("table", range(sum(obj_count)), Mode.List, Default.KnimeId)
        export_file.add_columns("table", list(ids), Mode.List, Default.IlastikId)
        export_file.add_columns("table", lineage, Mode.List, Default.Lineage)
        export_file.add_columns("table", track_ids, Mode.IlastikTrackingTable,
                                {"max": multi_move_max, "counts": obj_count, "extra ids": extra_track_ids,
                                 "range": t_range})

        export_file.add_columns("table", object_feature_slot, Mode.IlastikFeatureTable,
                                {"selection": selected_features})

        if with_divisions:
            if divisions:
                div_lineage = division_flatten_dict(divisions, self.label2color)
                zips = zip(*divisions)
                divisions = zip(zips[0], div_lineage, *zips[1:])
                export_file.add_columns("divisions", divisions, Mode.List, Default.DivisionNames)
            else:
                logger.debug("No divisions occurred. Division Table will not be exported!")

        if settings["file type"] == "h5":
            export_file.add_rois(Default.LabelRoiPath, label_image_slot, "table", settings["margin"], "labeling")
            if settings["include raw"]:
                export_file.add_image(Default.RawPath, self.RawImage)
            else:
                export_file.add_rois(Default.RawRoiPath, self.RawImage, "table", settings["margin"])
        export_file.write_all(settings["file type"], settings["compression"])

        export_file.ExportProgress.unsubscribe(progress_slot)
        export_file.InsertionProgress.unsubscribe(progress_slot)
