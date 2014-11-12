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
import copy

from PyQt4 import QtCore
from PyQt4.QtCore import QObject, QTimer
from PyQt4.QtGui import QMessageBox

class ErrorMessageFilter(QObject):
    """
    In a parallel program, the same error may occur in several threads in close succession.
    For example, all slice views will notice a "filter too large" error simultaneously.
    This class collects error messages for a certain time (currently: 1000ms) and then
    displays each unique message only once.
    """
    def __init__(self, parent):
        super(QObject, self).__init__(parent)
        self.messages = {}
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(1000)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timeout)
        
    def showErrorMessage(self, caption, text):
        if not self.timer.isActive():
            self.timer.start()
        self.messages[caption] = text
        
    def timeout(self):
        # Must copy now because the eventloop is allowed to run during QMessageBox.critical, below.
        # That is, self.messages might change while the loop is executing (not allowed).
        messages = copy.copy(self.messages)
        for caption, text in messages.iteritems():
            QMessageBox.critical(self.parent(), caption, text)
        self.messages = {}
        