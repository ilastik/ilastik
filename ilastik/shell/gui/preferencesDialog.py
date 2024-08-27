###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################

import configparser
import logging
import sys
from typing import Tuple, Union

from annotated_types import Ge, Le
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from pydantic import BaseModel

from ilastik.config import IlastikPreferences, Increment
import ilastik.config as iconfig

logger = logging.getLogger(__name__)


class PreferencesModel(QObject):
    configChanged = pyqtSignal(str, str)  # section_name, option_name

    def __init__(self, config):
        super().__init__()
        self.config: IlastikPreferences = config

    def getSections(self):
        return self.config.model_fields

    def getOptions(self, section):
        return getattr(self.config, section).model_fields

    def getValue(self, section, option):
        return getattr(getattr(self.config, section), option)

    def getOptionField(self, section, option):
        return getattr(self.config, section).model_fields.get(option)

    def setValue(self, section, option, value):
        setattr(getattr(self.config, section), option, value)
        self.configChanged.emit(section, option)

    def resetToDefaults(self):
        self.config = self.config.model_validate({})
        for section in self.getSections():
            for option in self.getOptions(section):
                self.configChanged.emit(section, option)

    def saveConfig(self):
        """
        write config file, but only write values that are different to
        the default config.
        """
        logger.info(f"writing config to {iconfig.cfg_path}")

        pref_dict = self.config.model_dump(exclude_defaults=True)
        cf = configparser.ConfigParser()
        cf.read_dict(pref_dict)
        with open(iconfig.cfg_path, "w") as f:
            cf.write(f)


class PreferencesDialog(QDialog):
    def __init__(self, parent: Union[QWidget, None], model: PreferencesModel):
        super().__init__(parent=parent)
        self.model = model
        self.options2widgets = {}  # {(section_name, option_name): option_widget}
        self.initUI()
        self.model.configChanged.connect(self.updateValue)

    def _widget_for_type(
        self, val: Union[int, str, bool], typehint, section, option
    ) -> Tuple[QLabel, Union[QLineEdit, QSpinBox, QCheckBox]]:

        if isinstance(val, bool):
            widget = QCheckBox()
            widget.setChecked(val)
            widget.stateChanged.connect(
                lambda value, section=section, option=option: self.model.setValue(section, option, bool(value))
            )

        elif isinstance(val, int):
            widget = QSpinBox()
            for arg in typehint:
                if isinstance(arg, Ge):
                    widget.setMinimum(int(arg.ge))
                elif isinstance(arg, Le):
                    widget.setMaximum(int(arg.le))
                elif isinstance(arg, Increment):
                    widget.setSingleStep(arg.increment)

            widget.setValue(val)
            widget.setAlignment(Qt.AlignRight)
            widget.valueChanged.connect(
                lambda value, section=section, option=option: self.model.setValue(section, option, value)
            )

        elif isinstance(val, str):
            widget = QLineEdit(val)
            widget.textChanged.connect(
                lambda value, section=section, option=option: self.model.setValue(section, option, value)
            )

        else:
            raise ValueError(f"Unexpected value type {type(value)=}")

        return widget

    def initUI(self):
        self._main_layout = QVBoxLayout()

        for section_name, section_info in self.model.getSections().items():

            assert issubclass(section_info.annotation, BaseModel)

            groupbox = QGroupBox(section_name)
            layout = QFormLayout()
            layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

            for option_name in self.model.getOptions(section_name):
                value = self.model.getValue(section_name, option_name)
                field_meta = self.model.getOptionField(section_name, option_name)
                val_widget = self._widget_for_type(value, field_meta.metadata, section_name, option_name)
                label = QLabel(option_name)
                val_widget.setToolTip(field_meta.description)
                layout.addRow(label, val_widget)
                self.options2widgets[(section_name, option_name)] = val_widget

            groupbox.setLayout(layout)
            self._main_layout.addWidget(groupbox)

        self._main_layout.addWidget(QLabel("Note: please restart ilastik after modifying any settings."))
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.resetButton = QPushButton("Reset to Defaults")
        self.buttonBox.addButton(self.resetButton, QDialogButtonBox.ResetRole)
        self.buttonBox.accepted.connect(self.model.saveConfig)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.resetButton.clicked.connect(self.model.resetToDefaults)

        self._main_layout.addWidget(self.buttonBox)
        self.setLayout(self._main_layout)
        self.setMinimumWidth(500)

    def updateValue(self, section: str, option: str):
        value = self.model.getValue(section, option)
        widget = self.options2widgets[(section, option)]
        if isinstance(widget, QLineEdit):
            widget.setText(value)
        elif isinstance(widget, QCheckBox):
            widget.setChecked(value)
        if isinstance(widget, QSpinBox):
            widget.setValue(value)

    @classmethod
    def createAndShowModal(cls, parent=None):
        model = PreferencesModel(iconfig.cfg)
        dialog = cls(parent=parent, model=model)
        dialog.exec()


def main():
    app = QApplication(sys.argv)
    PreferencesDialog.createAndShowModal()


if __name__ == "__main__":
    main()
