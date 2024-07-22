import os
import platform
import re
import webbrowser
from ilastik import __version__ as ilastik_version
from ilastik import ilastik_logging
from ilastik.app import STARTUP_MARKER
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QSizePolicy
from urllib.parse import quote

FORUM_URI = "https://forum.image.sc/tag/ilastik"
TEAM_EMAIL = "team@ilastik.org"
FILE_PATH_MASK = "(file path masked)"


def _mask_file_paths(text: str) -> str:
    """Replace file paths with a placeholder for privacy."""
    windows_pattern = r"""       # Windows path or file-URI with Windows path (could be with double-backslash)
        [a-zA-Z]:[/\\]\\?        # Drive and first slash
        (?!/)                    # Not immediately followed by another slash (avoid matching schema://)
        ([^/\\\n]+[/\\]\\?)*     # Any number of directories
        \S*
    """
    unix_pattern = r"""          # Unix path or other URI
            /[^/\n]+/            # at least two slashes, but not double-slash
            \S*
    """
    combined_pattern = re.compile(f"({windows_pattern}|{unix_pattern})", re.X)
    masked = re.sub(combined_pattern, FILE_PATH_MASK, text)
    return masked


def _get_log_since_last_startup(text_size_limit=65536, pre_marker_padding=512) -> str:
    """
    Reads the log up to maximum `text_size_limit` from the end (64 KiB).
    Returns the text since the last startup plus `pre_marker_padding`, or the entire text if the marker is not found.
    We don't want people posting or emailing us huge amounts of log...
    """
    log_path = ilastik_logging.default_config.get_logfile_path()
    file_size = int(os.path.getsize(log_path))
    with open(log_path, "rb") as log_file:
        position = max(0, file_size - text_size_limit)
        log_file.seek(position)
        log_text = log_file.read().decode()
    # Go back a bit further than the marker to catch pre-startup log messages
    before_marker = max(0, log_text.rfind(STARTUP_MARKER) - pre_marker_padding)
    return log_text[before_marker:]


class ReportIssueDialog(QDialog):
    def __init__(self, parent=None, workflow_report_text=""):
        super().__init__(parent=parent)

        self.setWindowTitle("Report issue")
        self.setMinimumSize(600, 300)

        main_layout = QVBoxLayout()

        # Create and add the instruction label
        instruction_label = QLabel()
        instruction_label.setText(
            "<p>Sorry you ran into a problem! Please include the information below when you report your issue.</p>"
            f'<p>The best place to get help is the <a href="{FORUM_URI}">community forum</a>. '
            "Most posts get responses very quickly there, and others can benefit from the advice you receive!</p>"
            f'<p>Alternatively, you can email us at <a href="mailto:{TEAM_EMAIL}">{TEAM_EMAIL}</a>. '
            "We'll do our best to get back to you quickly.</p>"
        )
        instruction_label.setOpenExternalLinks(True)
        instruction_label.setWordWrap(True)
        instruction_label.setMaximumHeight(150)
        main_layout.addWidget(instruction_label)

        report = (
            f"ilastik version: {ilastik_version}\n"
            f"OS: {platform.platform()}\n"
            f"{workflow_report_text}"
            "Log since last startup (please shorten to relevant parts if this seems very long):\n"
            f"```\n{_mask_file_paths(_get_log_since_last_startup())}\n```"
        )
        self.report_text = QTextEdit()
        self.report_text.setPlainText(report)
        self.report_text.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        main_layout.addWidget(self.report_text)

        button_layout = QHBoxLayout()
        copy_button = QPushButton("Copy and open forum")
        copy_button.clicked.connect(self.copy_and_go_to_forum)
        button_layout.addWidget(copy_button)
        email_button = QPushButton("Open in email app")
        email_button.clicked.connect(self.open_in_email_app)
        button_layout.addWidget(email_button)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

        # Set the layout to the dialog
        self.setLayout(main_layout)
        self.show()

    def copy_and_go_to_forum(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.report_text.toPlainText())
        webbrowser.open(FORUM_URI)

    def open_in_email_app(self):
        subject = "[Bugreport] --Summarise your issue here--"
        body = (
            "Please describe the issue you are experiencing and adapt the email subject.\n"
            "\n\n--\nAuto-generated report:\n"
        )
        body += self.report_text.toPlainText()
        mailto_url = f"mailto:{TEAM_EMAIL}?subject={subject}&body={quote(body)}"
        webbrowser.open(mailto_url)
