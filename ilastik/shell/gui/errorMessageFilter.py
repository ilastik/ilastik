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
        for caption, text in self.messages.iteritems():
            QMessageBox.critical(self.parent(), caption, text)
        self.messages = {}
        