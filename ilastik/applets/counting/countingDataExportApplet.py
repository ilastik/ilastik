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
from opCountingDataExport import OpCountingDataExport
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.applets.dataExport.dataExportSerializer import DataExportSerializer
from ilastik.applets.base.appletSerializer import SerialSlot

from ilastik.utility import OpMultiLaneWrapper, log_exception
from lazyflow.request import Request 

import logging
logger = logging.getLogger(__name__)

class CountingDataExportApplet( DataExportApplet ):
    """
    This a specialization of the generic data export applet that
    provides a special viewer for pixel classification predictions.
    """
    def __init__( self, workflow, title, opCounting, isBatch=False ):
        # Our operator is a subclass of the generic data export operator
        self._topLevelOperator = OpMultiLaneWrapper( OpCountingDataExport, parent=workflow,
                                     promotedSlotNames=set(['RawData', 'Inputs', 'RawDatasetInfo']) )
        self._gui = None
        self._title = title
        self._serializers = [ DataExportSerializer(self._topLevelOperator,
                                                   title,
                                                   [ SerialSlot(self._topLevelOperator.CsvFilepath) ]) ]

        self.opCounting = opCounting

        # Base class init
        super(CountingDataExportApplet, self).__init__(workflow, title, isBatch)
        
    @property
    def dataSerializers(self):
        return self._serializers

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    def getMultiLaneGui(self):
        if self._gui is None:
            # Gui is a special subclass of the generic gui
            from countingDataExportGui import CountingDataExportGui
            self._gui = CountingDataExportGui( self, self.topLevelOperator )
        return self._gui

    def write_csv_results(self, export_file, lane_index):
        """
        Write the counting sum for the given lane to the 
        given export file object (which must be open already).
        """
        info_slot = self.topLevelOperator.getLane(lane_index).RawDatasetInfo
        sum_slot = self.opCounting.getLane(lane_index).OutputSum
        nickname = info_slot.value.nickname
        object_count = sum_slot[:].wait()[0]
        export_file.write(nickname + "," + str(object_count) + "\n")
