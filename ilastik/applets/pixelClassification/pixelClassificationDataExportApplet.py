# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

from opPixelClassificationDataExport import OpPixelClassificationDataExport
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.applets.dataExport.dataExportSerializer import DataExportSerializer

from ilastik.utility import OpMultiLaneWrapper

class PixelClassificationDataExportApplet( DataExportApplet ):
    """
    This a specialization of the generic data export applet that
    provides a special viewer for pixel classification predictions.
    """
    def __init__( self, workflow, title, isBatch=False ):
        # Our operator is a subclass of the generic data export operator
        self._topLevelOperator = OpMultiLaneWrapper( OpPixelClassificationDataExport, parent=workflow,
                                     promotedSlotNames=set(['RawData', 'Input', 'RawDatasetInfo', 'ConstraintDataset']) )
        self._gui = None
        self._title = title
        self._serializers = [ DataExportSerializer(self._topLevelOperator, title) ]

        # Base class init
        super(PixelClassificationDataExportApplet, self).__init__(workflow, title, isBatch)
        
    @property
    def dataSerializers(self):
        return self._serializers

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    def getMultiLaneGui(self):
        if self._gui is None:
            # Gui is a special subclass of the generic gui
            from pixelClassificationDataExportGui import PixelClassificationDataExportGui
            self._gui = PixelClassificationDataExportGui( self, self.topLevelOperator )
        return self._gui





