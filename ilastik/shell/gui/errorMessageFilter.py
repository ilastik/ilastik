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
        