__author__ = 'fabian'

import sys
from PyQt4.QtGui import QDialog
from PyQt4.QtCore import pyqtRemoveInputHook, pyqtRestoreInputHook
import os
from PyQt4 import uic
# import IPython

class FeatureSelectionDlg(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        localDir = os.path.split(os.path.abspath(__file__))[0]
        uic.loadUi(localDir+"/selectFeaturesDlg.ui", self)

        self.cancel.clicked.connect(self.reject)
        self.ok.clicked.connect(self.accept)

        self.__feat_selection_methods = {
            0: "Gini",
            1: "Filter",
            2: "Wrapper"
        }



    @property
    def selectedMethod(self):
        return self.__feat_selection_methods[self.comboBox.currentIndex()]

if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)

    #app.setStyle("windows")
    #app.setStyle("motif")
    #app.setStyle("cde")
    #app.setStyle("plastique")
    #app.setStyle("macintosh")
    #app.setStyle("cleanlooks")

    ex = FeatureSelectionDlg()
    ex.setWindowTitle("FeatureTest")
    ex.exec_()

    pyqtRemoveInputHook()
    IPython.embed()
    pyqtRestoreInputHook()

    app.exec_()

