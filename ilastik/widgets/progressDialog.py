from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QDialog, QMessageBox
from os.path import split as split_path


class ProgressDialog(QDialog):
    cancel = pyqtSignal()
    trigger_popup = pyqtSignal(str, str, object, tuple, bool)
    trigger_update = pyqtSignal(int)

    def __init__(self, steps, parent=None):
        super(ProgressDialog, self).__init__(parent)

        form, _ = uic.loadUiType(split_path(__file__)[0] + "/progressDialog.ui")
        self.ui = form()
        self.ui.setupUi(self)

        self.steps = steps
        self.current = 0

        self._add_pending()

        self.ui.cancel.clicked.connect(self.cancel)
        self.trigger_popup.connect(self.popup)
        self.trigger_update.connect(self.update_step)

    def __call__(self, progress):
        self.safe_update_step(progress)

    def set_busy(self, busy):
        self.ui.progress.setMaximum(0 if busy else 100)

    def safe_update_step(self, progress):
        self.trigger_update.emit(progress)

    def update_step(self, progress):
        self.set_busy(False)
        if self.is_finished:
            return

        if progress == 100:
            self._finish_step()
        else:
            self.ui.progress.setValue(progress)

    @property
    def is_finished(self):
        return len(self.steps) == self.current

    def _add_pending(self):
        self.ui.info.setText("Step {} of {}: {}".format(self.current + 1, len(self.steps), self.steps[self.current]))

    def _finish_step(self):
        if self.is_finished:
            return

        self.current += 1

        if self.is_finished:
            self.ui.progress.setValue(100)
        else:
            self.ui.progress.setValue(0)
            self._add_pending()

    def popup(self, level, title, description, args, close):
        assert level in ("information", "warning", "critical")
        if args is not None:
            description = [description]
            for arg in args:
                if isinstance(arg, Exception):
                    description.append(str(arg))
            description = "\n".join(description)
        getattr(QMessageBox, str(level))(self, title, description)
        if close:
            self.close()

    def safe_popup(self, level, title, description, *args):
        self.trigger_popup.emit(level, title, description, args, True)

    def safe_popup_noclose(self, level, title, description, *args):
        self.trigger_popup.emit(level, title, description, args, False)

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    from time import sleep
    app = QApplication([])

    p = ProgressDialog(["abc", "def", "ghi"])

    p.show()

    for j in range(3):
        for i in range(11):
            p.safe_update_step(i*10)
            sleep(.01)
    p.safe_popup("information", "lol", "rofl")
    app.exec_()