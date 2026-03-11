import shutil
from pathlib import Path
import configparser
from qtpy.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFormLayout


def _get_creds_path():
    return Path.home() / ".aws" / "credentials"


class AwsCredentialsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AWS Credentials Editor")
        self.setMinimumWidth(400)

        self.profile_input = QLineEdit()
        self.access_key_input = QLineEdit()
        self.secret_key_input = QLineEdit()

        self.setup_ui()
        self.load_existing_credentials()
        self.show()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        warning_label = QLabel(
            "<p>Warning: This modifies your user-wide AWS credentials file at <br>"
            f"<b>{_get_creds_path()}</b>"
            "</p><p>If something goes wrong, look for .bak files in the same folder.</p>"
        )
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)

        form = QFormLayout()
        form.addRow(QLabel("Profile:"), self.profile_input)
        form.addRow(QLabel("Access Key ID:"), self.access_key_input)
        form.addRow(QLabel("Secret Access Key:"), self.secret_key_input)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        buttons.addWidget(self.ok_button)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)

        self.ok_button.clicked.connect(self.on_ok)
        self.cancel_button.clicked.connect(self.reject)

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
            profile = next(iter(config.sections())) if config.sections() else "default"

        self.profile_input.setText(profile)
        self.access_key_input.setText(config.get(profile, "aws_access_key_id", fallback=""))
        self.secret_key_input.setText(config.get(profile, "aws_secret_access_key", fallback=""))

    def on_ok(self):
        profile = self.profile_input.text().strip()
        access_key = self.access_key_input.text().strip()
        secret_key = self.secret_key_input.text().strip()

        if not profile or not access_key or not secret_key:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        creds_path = _get_creds_path()
        backup_path = Path.home() / ".aws" / "credentials.bak"
        i = 1
        while backup_path.exists():
            backup_path = Path.home() / ".aws" / f"credentials.bak{i}"
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
