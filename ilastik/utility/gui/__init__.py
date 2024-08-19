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
from PyQt5.QtWidgets import QApplication


from .roi import roi2rect
from .threadRouter import ThreadRouter, threadRouted, threadRoutedWithRouter
from .thunkEvent import ThunkEvent, ThunkEventHandler
from .widgets import enable_when_ready, silent_qobject


def is_qt_dark_mode() -> bool:
    """
    One of the methods reported working to determine dark/light mode during runtime
    with Qt5.

    ref: https://stackoverflow.com/questions/75457687/detect-dark-application-style

    Note: This might break users using custom themes.

    Returns True if in dark mode, False if light mode
    """
    return QApplication.palette().windowText().color().value() > QApplication.palette().window().color().value()
