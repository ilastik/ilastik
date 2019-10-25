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
from ilastik.applets.dataExport.opDataExport import DataExportPathFormatter


class PathFormatterFactory:
    def __init__(self, op):
        self._op = op

    def for_lane(self, lane_index: int) -> DataExportPathFormatter:
        return DataExportPathFormatter(
            dataset_info=self._op.RawDatasetInfo[lane_index].value,
            working_dir=self._op.WorkingDirectory.value,
        )


class ObjectClassificationDataExportApplet(DataExportApplet):
    """
    This a specialization of the generic data export applet that
    provides a special viewer for object classification predictions.
    """

    def __init__(self, *args, table_exporter, **kwargs):
        super(ObjectClassificationDataExportApplet, self).__init__(*args, **kwargs)
        self._tableExporter = table_exporter
        self._tableExporter.set_path_formatter_factory(PathFormatterFactory(self.topLevelOperator))

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
        # FIXME: Even in non-headless mode, we can't show the gui because we're running in a non-main thread.
        #        That's not a huge deal, because there's still a progress bar for the overall export.
        req = self._tableExporter.export_object_data(lane_index, show_gui=False).wait()
