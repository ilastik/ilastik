from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import os


class MultiProgressDialog(QDialog):
    finished = pyqtSignal()
    def __init__(self, max_steps, parent=None):
        super(MultiProgressDialog, self).__init__(parent)
        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/multiProgressDialog.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)

        self.max_steps = max_steps
        self.current_step = 1
        self._has_finished = False

        self.ui.progressBar.reset()
        self._update_label()
        self.ui.finished.setEnabled(False)

        self._isready = False

    #slot
    def finish_step(self):
        if not self._has_finished:
            if self.current_step < self.max_steps:
                self.ui.progressBar.reset()
                self.current_step += 1
                self._update_label()
            else:
                self.ui.finished.setEnabled(True)
                self.ui.steps.setText("Finished")
                self.ui.progressBar.setValue(100)
                self.finished.emit()

    #slot
    def update_step(self, progress):
        self.ui.progressBar.setValue(progress)

    def _update_label(self):
        self.ui.steps.setText("step {} of {}".format(self.current_step, self.max_steps))

    def showEvent(self, event):
        self._isready = True

    def is_ready(self):
        return self._isready

if __name__ == "__main__":
    import sys, time
    app = QApplication(sys.argv)

    d = MultiProgressDialog(3)
    d.show()
    for j in xrange(3):
        for i in xrange(1, 21):
            d.update_step(i*5)
            time.sleep(.05)
        d.finish_step()



    sys.exit(app.exec_())