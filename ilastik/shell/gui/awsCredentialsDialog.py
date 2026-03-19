###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2026, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################
import configparser
import os
import shutil
from pathlib import Path

from qtpy.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QFormLayout,
    QDialogButtonBox,
    QCheckBox,
)


def _get_creds_path() -> Path:
    if env_cred_path := os.environ.get("AWS_SHARED_CREDENTIALS_FILE", ""):
        return Path(env_cred_path)
    return Path.home() / ".aws" / "credentials"


class AwsCredentialsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AWS Credentials Editor")
        self.setMinimumWidth(400)

        self.profile_input = QLineEdit()
        self.access_key_input = QLineEdit()
        self.secret_key_input = QLineEdit()

        self._fields = []

        self.setup_ui()
        self.load_existing_credentials()
        self.connect_validation()
        self.validate_inputs()

        self.show()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        if _get_creds_path().exists():
            warning_label = QLabel(
                "<p>Warning: This modifies your user-wide AWS credentials file at <br>"
                f"<b>{_get_creds_path()}</b>"
                "</p><p>If something goes wrong, look for .bak files in the same folder.</p>"
            )
            warning_label.setWordWrap(True)
            layout.addWidget(warning_label)

        form = QFormLayout()

        profile_label = QLabel("Profile")
        access_key_label = QLabel("Access Key ID")
        secret_key_label = QLabel("Secret Access Key")

        form.addRow(profile_label, self.profile_input)
        form.addRow(access_key_label, self.access_key_input)

        self.toggle_secret_button = QCheckBox("Show secret")

        secret_layout = QVBoxLayout()
        secret_layout.addWidget(self.secret_key_input)
        secret_layout.addWidget(self.toggle_secret_button)

        self.secret_key_input.setEchoMode(QLineEdit.Password)
        self.toggle_secret_button.toggled.connect(self._toggle_secret_visibility)
        form.addRow(secret_key_label, secret_layout)

        layout.addLayout(form)

        self._fields = [self.profile_input, self.access_key_input, self.secret_key_input]

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.button_box)
        buttons = QHBoxLayout()
        self.ok_button = self.button_box.button(QDialogButtonBox.Ok)
        layout.addLayout(buttons)

        self.button_box.accepted.connect(self.on_ok)
        self.button_box.rejected.connect(self.reject)

    def connect_validation(self):
        for field in self._fields:
            field.textChanged.connect(self.validate_inputs)

    def _toggle_secret_visibility(self, checked):
        self.secret_key_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def validate_inputs(self):
        all_valid = True
        for field in self._fields:
            valid = bool(field.text().strip())
            if valid:
                field.setStyleSheet("")
            else:
                field.setStyleSheet("border: 1px solid red;")
            all_valid &= valid
        self.ok_button.setEnabled(all_valid)

    def load_existing_credentials(self):
        creds_path = _get_creds_path()
        if not creds_path.exists():
            self.profile_input.setText("default")
            return

        config = configparser.ConfigParser()
        config.read(creds_path)

        if "default" in config:
            profile = "default"
        else:
            profile = next(iter(config.sections()), "default")

        self.profile_input.setText(profile)
        self.access_key_input.setText(config.get(profile, "aws_access_key_id", fallback=""))
        self.secret_key_input.setText(config.get(profile, "aws_secret_access_key", fallback=""))

    def on_ok(self):
        profile = self.profile_input.text().strip()
        access_key = self.access_key_input.text().strip()
        secret_key = self.secret_key_input.text().strip()

        creds_path = _get_creds_path()
        backup_path = creds_path.parent / "credentials.bak"
        i = 1
        while backup_path.exists():
            backup_path = creds_path.parent / f"credentials.bak{i}"
            i += 1

        try:
            if creds_path.exists():
                shutil.copy2(creds_path, backup_path)

            creds_path.parent.mkdir(exist_ok=True)

            config = configparser.ConfigParser()
            if creds_path.exists():
                config.read(creds_path)

            config[profile] = {
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key,
            }

            with open(creds_path, "w") as f:
                config.write(f)

            self.accept()
        except (ValueError, KeyError, RuntimeError) as e:
            QMessageBox.critical(self, "Error", f"Failed to save credentials: {e}")
