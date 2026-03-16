import configparser
from unittest.mock import patch

import pytest
from qtpy.QtCore import Qt

from ilastik.shell.gui.awsCredentialsDialog import AwsCredentialsDialog


@pytest.fixture
def dialog(qtbot):
    dlg = AwsCredentialsDialog()
    qtbot.addWidget(dlg)
    qtbot.waitExposed(dlg)
    return dlg


@pytest.fixture
def aws_dir(tmp_path):
    aws_dir = tmp_path / ".aws"
    aws_dir.mkdir()
    return aws_dir


def test_dialog_runs(dialog):
    assert dialog.isVisible()
    assert dialog.profile_input is not None
    assert dialog.access_key_input is not None
    assert dialog.secret_key_input is not None


def test_loads_existing_credentials(dialog, tmp_path, aws_dir):
    creds_path = aws_dir / "credentials"
    config = configparser.ConfigParser()
    config["default"] = {
        "aws_access_key_id": "test_key",
        "aws_secret_access_key": "test_secret",
    }
    with open(creds_path, "w") as f:
        config.write(f)

    with patch("pathlib.Path.home", return_value=tmp_path):
        dialog.load_existing_credentials()
        assert dialog.profile_input.text() == "default"
        assert dialog.access_key_input.text() == "test_key"
        assert dialog.secret_key_input.text() == "test_secret"


def test_on_ok_creates_backup_and_writes_credentials(dialog, qtbot, tmp_path, aws_dir):
    creds_path = aws_dir / "credentials"
    config = configparser.ConfigParser()
    config["default"] = {
        "aws_access_key_id": "old_key",
        "aws_secret_access_key": "old_secret",
    }
    with open(creds_path, "w") as f:
        config.write(f)

    with patch("pathlib.Path.home", return_value=tmp_path):
        dialog.profile_input.setText("test_profile")
        dialog.access_key_input.setText("new_key")
        dialog.secret_key_input.setText("new_secret")

        qtbot.mouseClick(dialog.ok_button, Qt.MouseButton.LeftButton)

        backup_files = list(aws_dir.glob("credentials.bak*"))
        assert len(backup_files) == 1

        new_config = configparser.ConfigParser()
        new_config.read(creds_path)
        assert new_config["test_profile"]["aws_access_key_id"] == "new_key"
        assert new_config["test_profile"]["aws_secret_access_key"] == "new_secret"


def test_modify_alternative_profile(dialog, qtbot, tmp_path, aws_dir):
    creds_path = aws_dir / "credentials"
    config = configparser.ConfigParser()
    default_config = {
        "aws_access_key_id": "default_key",
        "aws_secret_access_key": "default_secret",
    }
    config["default"] = default_config
    config["alt_profile"] = {
        "aws_access_key_id": "old_alt_key",
        "aws_secret_access_key": "old_alt_secret",
    }
    with open(creds_path, "w") as f:
        config.write(f)

    with patch("pathlib.Path.home", return_value=tmp_path):
        dialog.load_existing_credentials()
        dialog.profile_input.setText("alt_profile")
        dialog.access_key_input.setText("new_alt_key")
        dialog.secret_key_input.setText("new_alt_secret")

        qtbot.mouseClick(dialog.ok_button, Qt.MouseButton.LeftButton)

        new_config = configparser.ConfigParser()
        new_config.read(creds_path)
        assert new_config["default"] == default_config
        assert new_config["alt_profile"]["aws_access_key_id"] == "new_alt_key"
        assert new_config["alt_profile"]["aws_secret_access_key"] == "new_alt_secret"


@pytest.mark.parametrize(
    "text_input",
    [
        "profile_input",
        "access_key_input",
        "secret_key_input",
    ],
)
def test_validation_disables_on_any_empty_field(dialog, qtbot, tmp_path, text_input):
    input_widget = getattr(dialog, text_input)
    input_widget.clear()

    assert not dialog.ok_button.isEnabled()
    assert "red" in input_widget.styleSheet()

    qtbot.mouseClick(dialog.ok_button, Qt.MouseButton.LeftButton)
    is_accepted = bool(dialog.result())
    assert not is_accepted
