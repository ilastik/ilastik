import os
from PyQt5 import uic
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QDialog, QMessageBox
from os.path import split as split_path
import platform
from enum import IntEnum, auto


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


class BarId(IntEnum):
    bar0 = auto()
    bar1 = auto()


class PercentProgressDialog(QDialog):
    class _ProgressEmitter(QObject):
        progress0 = pyqtSignal(int)
        progress1 = pyqtSignal(int)

        def __call__(self, val, bar: BarId = BarId.bar0):
            if bar == BarId.bar0:
                self.progress0.emit(val)
            elif bar == BarId.bar1:
                self.progress1.emit(val)

    def __init__(self, parent=None, *, title=None, secondary_bar=False):
        super().__init__(parent)
        localDir = os.path.split(__file__)[0]
        form, _ = uic.loadUiType(os.path.join(localDir, "percentProgressDialog.ui"))
        self._ui = form()
        self._ui.setupUi(self)
        self._ui.cancel.clicked.connect(self.reject)
        self._emitter = self._ProgressEmitter(parent=self)
        self._emitter.progress0.connect(self._ui.progress0.setValue)
        self._emitter.progress1.connect(self._ui.progress1.setValue)

        if title:
            self.setWindowTitle(title)
            self._ui.progress0.setFormat(f"{title}: %p%")

            # did not manage to show a titlebar on OSX, or progress text on the progress bar
            # added additional label to UI to handle information display on OSX
            if platform.system() == "Darwin":
                self._ui.osxLabel0.setText(title)
                self._ui.osxLabel0.setVisible(True)
                self._emitter.progress0.connect(lambda val: self._ui.osxLabel0.setText(f"{title} {val}%"))

        if secondary_bar:
            self.getBar(BarId.bar1).setVisible(True)
            if platform.system() == "Darwin":
                self._ui.osxLabel1.setVisible(True)

    def updateProgress(self, progress: int, bar: BarId = BarId.bar0):
        # Using emitter to avoid updating UI from non-main thread
        self._emitter(progress, bar)

    def setBusy(self, bar: BarId = BarId.bar0):
        self.getBar(bar).setMaximum(0)

    def getBar(self, bar: BarId):
        if bar == BarId.bar0:
            return self._ui.progress0
        elif bar == BarId.bar1:
            return self._ui.progress1

    def updateBarFormat(self, title: str, bar: BarId = BarId.bar0):
        self.getBar(bar).setFormat(f"{title}: %p%")
        if platform.system() == "Darwin":
            if bar == BarId.bar0:
                self._emitter.progress0.disconnect()
                self._emitter.progress0.connect(lambda val: self._ui.osxLabel0.setText(f"{title} {val}%"))
                self._emitter.progress0.connect(self._ui.progress0.setValue)
            if bar == BarId.bar1:
                self._emitter.progress1.disconnect()
                self._emitter.progress1.connect(lambda val: self._ui.osxLabel1.setText(f"{title} {val}%"))
                self._emitter.progress1.connect(self._ui.progress1.setValue)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    from time import sleep

    app = QApplication([])

    p = ProgressDialog(["abc", "def", "ghi"])

    p.show()

    for j in range(3):
        for i in range(11):
            p.safe_update_step(i * 10)
            sleep(0.01)
    p.safe_popup("information", "lol", "rofl")
    app.exec_()
