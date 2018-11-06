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
from ilastik.applets.dataExport.opDataExport import OpDataExport
from lazyflow.graph import InputSlot

class OpTrackingBaseDataExport(OpDataExport):
    # class variable containing the default name of the plugin export source
    PluginOnlyName = 'Plugin'

    # These slots get populated from within ``TrackingBaseDataExportGui``
    # or when parsing the command line in ``TrackingBaseDataExportApplet``
    SelectedPlugin = InputSlot(optional=True)
    SelectedExportSource = InputSlot(value=None)

    # Slot containing plugin specific arguments. Holds a dictionary that can
    # be populated from the `TrackingBaseDataExportGui` or when parsing
    # the command line in `TrackingBaseDataExportApplet`
    AdditionalPluginArguments = InputSlot(value={}, optional=True)

    def __init__(self, *args, **kwargs):
        super(OpTrackingBaseDataExport, self).__init__(*args, **kwargs)

    def run_export(self):
        '''
        We only run the export method of the parent export operator if we are not exporting via a plugin
        '''
        if self.SelectedExportSource.value != self.PluginOnlyName:
            super(OpTrackingBaseDataExport, self).run_export()
