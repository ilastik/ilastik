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
                                     promotedSlotNames=set(['RawData', 'Inputs', 'RawDatasetInfo', 'ConstraintDataset']) )
        self._gui = None
        self._title = title
        self._serializers = [ DataExportSerializer(self._topLevelOperator, title) ]

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

    def prepareExportObjectCountsToCsv(self, csv_path):
        """
        Prepare a request to calculate the total object count in each lane and export the results to csv.
        The prepared request is returned, but not submitted yet.
        
        If the export fails, the exception will be logged.  
        Additional failure handling can be provided by calling notify_failed on the returned request before submitting it.
        """
        opCounting = self.opCounting
        self.busy = True
        self.appletStateUpdateRequested.emit()

        def _export_object_counts():
            num_files = len(self.topLevelOperator.RawDatasetInfo)

            with open(csv_path, 'w') as export_file:
                for lane_index, (info_slot, sum_slot) in enumerate(zip(self.topLevelOperator.RawDatasetInfo, opCounting.OutputSum)):
                    self.progressSignal.emit(100.0*lane_index/num_files)
                    nickname = info_slot.value.nickname
                    object_count = sum_slot[:].wait()[0]
                    export_file.write(nickname + "," + str(object_count) + "\n")

            self.busy = False
            self.progressSignal.emit(100)
            self.appletStateUpdateRequested.emit()

        def _handle_object_count_export_failure( exception, exception_info ):
            msg = "Failed to export object counts:\n{}".format( exception )
            log_exception( logger, msg, exception_info )

        req = Request(_export_object_counts)
        req.notify_failed( _handle_object_count_export_failure )
        
        # Caller must submit the request.
        #req.submit()
        return req
