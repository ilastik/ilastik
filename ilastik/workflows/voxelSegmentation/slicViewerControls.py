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
# Built-in
from functools import partial
import os

# Third-party
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

from volumina.widgets.exportHelper import get_settings_and_export_layer


# Modified from widgets.ViewerControls
class SlicViewerControls(QWidget):
    def __init__(self, parent=None, model=None):
        QWidget.__init__(self, parent)
        localDir = os.path.split(__file__)[0]
        uic.loadUi(os.path.join(localDir, "slicViewerControls.ui"), self)
