from PyQt4 import uic
from PyQt4.QtGui import QDialog
from os.path import split as split_path


class ProgressDialog(QDialog):
    def __init__(self, steps, parent=None):
        super(ProgressDialog, self).__init__(parent)

        form, _ = uic.loadUiType(split_path(__file__)[0] + "/progressDialog.ui")
        self.ui = form()
        self.ui.setupUi(self)

        self.steps = steps
        self.current = 0

        self._add_pending()

    def update_step(self, progress):
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



if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    from time import sleep
    app = QApplication([])

    p = ProgressDialog(["abc", "def", "ghi"])

    p.show()

    for j in range(3):
        for i in range(11):
            p.update_step(i*10)
            sleep(.1)

    app.exec_()