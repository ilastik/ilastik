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
__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Nov 12, 2014 15:12:47 EST$"



from lazyflow.graph import OutputSlot

from ilastik.applets.dataExport.opDataExport import OpDataExport,OpRawSubRegionHelper, OpFormattedDataExport

from ilastik.applets.nanshe.opMaxProjection import OpMaxProjectionCached
from ilastik.applets.nanshe.opMeanProjection import OpMeanProjectionCached


class OpNansheDataExport( OpDataExport ):
    # Add these additional input slots, to be used by the GUI.
    FormattedMaxProjection = OutputSlot()
    FormattedMeanProjection = OutputSlot()

    def __init__(self,*args,**kwargs):
        super(OpNansheDataExport, self).__init__(*args, **kwargs)


        # We don't export the max projection, but we connect it to it's own op
        # so it can be displayed alongside the data to export in the same viewer.
        # This keeps axis order, shape, etc. in sync with the displayed export data.
        # Note that we must not modify the channels of the raw data, so it gets passed through a helper.
        self._opMax = OpMaxProjectionCached( parent=self )
        self._opMax.InputImage.connect( self.RawData )
        self._opMax.Axis.setValue( 0 )

        self._opMaxHelper = OpRawSubRegionHelper( parent=self )
        self._opMaxHelper.RawImage.connect( self._opMax.Output )
        self._opMaxHelper.ExportStart.connect( self.RegionStart )
        self._opMaxHelper.ExportStop.connect( self.RegionStop )

        self._opFormatMax = OpFormattedDataExport( parent=self )
        self._opFormatMax.TransactionSlot.connect( self.TransactionSlot )
        self._opFormatMax.Input.connect( self._opMax.Output )
        self._opFormatMax.RegionStart.connect( self._opMaxHelper.RawStart )
        self._opFormatMax.RegionStop.connect( self._opMaxHelper.RawStop )
        # Don't normalize the raw data.
        #self._opFormatMax.InputMin.connect( self.InputMin )
        #self._opFormatMax.InputMax.connect( self.InputMax )
        #self._opFormatMax.ExportMin.connect( self.ExportMin )
        #self._opFormatMax.ExportMax.connect( self.ExportMax )
        #self._opFormatMax.ExportDtype.connect( self.ExportDtype )
        self._opFormatMax.OutputAxisOrder.connect( self.OutputAxisOrder )
        self._opFormatMax.OutputFormat.connect( self.OutputFormat )
        self.FormattedMaxProjection.connect( self._opFormatMax.ImageToExport )


        # We don't export the mean projection, but we connect it to it's own op
        # so it can be displayed alongside the data to export in the same viewer.
        # This keeps axis order, shape, etc. in sync with the displayed export data.
        # Note that we must not modify the channels of the raw data, so it gets passed through a helper.
        self._opMean = OpMeanProjectionCached( parent=self )
        self._opMean.InputImage.connect( self.RawData )
        self._opMean.Axis.setValue( 0 )

        self._opMeanHelper = OpRawSubRegionHelper( parent=self )
        self._opMeanHelper.RawImage.connect( self._opMean.Output )
        self._opMeanHelper.ExportStart.connect( self.RegionStart )
        self._opMeanHelper.ExportStop.connect( self.RegionStop )

        self._opFormatMean = OpFormattedDataExport( parent=self )
        self._opFormatMean.TransactionSlot.connect( self.TransactionSlot )
        self._opFormatMean.Input.connect( self._opMean.Output )
        self._opFormatMean.RegionStart.connect( self._opMeanHelper.RawStart )
        self._opFormatMean.RegionStop.connect( self._opMeanHelper.RawStop )
        # Don't normalize the raw data.
        #self._opFormatMean.InputMin.connect( self.InputMin )
        #self._opFormatMean.InputMax.connect( self.InputMax )
        #self._opFormatMean.ExportMin.connect( self.ExportMin )
        #self._opFormatMean.ExportMax.connect( self.ExportMax )
        #self._opFormatMean.ExportDtype.connect( self.ExportDtype )
        self._opFormatMean.OutputAxisOrder.connect( self.OutputAxisOrder )
        self._opFormatMean.OutputFormat.connect( self.OutputFormat )
        self.FormattedMeanProjection.connect( self._opFormatMean.ImageToExport )
