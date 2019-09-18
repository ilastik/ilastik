from __future__ import absolute_import

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
# 		   http://ilastik.org/license.html
###############################################################################
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet


class ObjectClassificationDataExportApplet(DataExportApplet):
    """
    This a specialization of the generic data export applet that
    provides a special viewer for object classification predictions.
    """

    def __init__(self, *args, table_exporter, **kwargs):
        super(ObjectClassificationDataExportApplet, self).__init__(*args, **kwargs)
        self._tableExporter = table_exporter

    def getMultiLaneGui(self):
        if self._gui is None:
            # Gui is a special subclass of the generic gui
            from .objectClassificationDataExportGui import ObjectClassificationDataExportGui

            self._gui = ObjectClassificationDataExportGui(self, self.topLevelOperator)
            self._gui.set_exporting_operator(self._tableExporter)
        return self._gui

    def post_process_lane_export(self, lane_index):
        # FIXME: This probably only works for the non-blockwise export slot.
        #        We should assert that the user isn't using the blockwise slot.
        settings, selected_features = self._tableExporter.get_table_export_settings()
        if settings:
            raw_dataset_info = self.topLevelOperator.RawDatasetInfo[lane_index].value
            if raw_dataset_info.is_in_filesystem():
                filename_suffix = raw_dataset_info.nickname
            else:
                filename_suffix = str(lane_index)
            req = self._tableExporter.export_object_data(
                lane_index,
                # FIXME: Even in non-headless mode, we can't show the gui because we're running in a non-main thread.
                #        That's not a huge deal, because there's still a progress bar for the overall export.
                show_gui=False,
                filename_suffix=filename_suffix,
            )
            req.wait()
