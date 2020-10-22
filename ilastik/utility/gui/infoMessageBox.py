from pathlib import Path

from PyQt5.QtWidgets import QCheckBox, QMessageBox

from volumina.utility import preferences
from ilastik.utility.info import InfoMessageData


class InfoMessageBox(QMessageBox):
    def __init__(self, parent_window, message_data: InfoMessageData):
        content = Path(message_data.filename).read_text()
        super().__init__(parent=parent_window)

        self.setWindowTitle(message_data.title)
        self.setText(content)

        self.message_id = message_data.message_id
        self.preferences_group = "suppress-message"

        suppress_in_future = QCheckBox("Don't show this message again.", parent=self)
        self.setCheckBox(suppress_in_future)

        def update_prefs():
            preferences.set(self.preferences_group, self.message_id, bool(suppress_in_future.checkState()))

        self.setModal(False)
        self.setIcon(QMessageBox.Information)
        self.finished.connect(update_prefs)

    def show(self):
        if not preferences.get(self.preferences_group, self.message_id):
            super().show()

    def exec(self):
        raise NotImplementedError("Please use .show")

    def open(self):
        raise NotImplementedError("Please use .show")
