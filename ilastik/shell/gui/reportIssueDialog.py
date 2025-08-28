import pathlib
import platform
import re
import webbrowser
from functools import partial

from qtpy.QtCore import QUrl, Qt
from qtpy.QtGui import QDesktopServices

from ilastik import __version__ as ilastik_version
from ilastik import ilastik_logging
from qtpy.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QSizePolicy
from urllib.parse import quote

FORUM_URI = "https://forum.image.sc/tag/ilastik"
TEAM_EMAIL = "team@ilastik.org"
FILE_PATH_MASK = "(file path masked)"
LOG_LENGTH_THRESHOLD = 5000  # Maximum we are happy to have people email or post in the forum


def _mask_file_paths(text: str) -> str:
    """Replace file paths with a placeholder for privacy."""
    windows_pattern = r"""       # Windows path or file-URI with Windows path (could be with double-backslash)
        [a-zA-Z]:[/\\]\\?        # Drive and first slash
        (?!/)                    # Not immediately followed by another slash (avoid matching schema://)
        ([^/\\\n]+[/\\]\\?)*     # Any number of directories
        \S*
    """
    unix_pattern = r"""          # Unix path or other URI
        /[^/\s]+/                # at least two slashes, but not double-slash
        \S*
    """
    combined_pattern = re.compile(f"({windows_pattern}|{unix_pattern})", re.X)
    masked = re.sub(combined_pattern, FILE_PATH_MASK, text)
    return masked


def _get_current_session_log_or_hint() -> str:
    log_path = ilastik_logging.get_session_logfile_path()
    if not log_path:
        return 'Could not find session log file. Please use the "Open log folder" button to locate the log.'
    with open(log_path, "r") as log_file:
        log_text = log_file.read()
    if len(log_text) > LOG_LENGTH_THRESHOLD:
        return (
            "Session log is too long to include here. "
            'Please use the "Open log folder" button to locate the log file '
            "and attach it to your forum thread or email."
        )
    return log_text


class ReportIssueDialog(QDialog):
    def __init__(self, parent=None, workflow_report_text=""):
        super().__init__(parent=parent)

        self.setWindowTitle("Report issue")
        self.setMinimumSize(600, 300)

        main_layout = QVBoxLayout()

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
            "Session log (please shorten to relevant parts if possible):\n"
            f"```\n{_mask_file_paths(_get_current_session_log_or_hint())}\n```"
        )
        self.report_text = QTextEdit()
        self.report_text.setPlainText(report)
        self.report_text.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.report_text.setFocusPolicy(Qt.ClickFocus)
        main_layout.addWidget(self.report_text)

        log_path = ilastik_logging.get_logfile_path()
        if log_path:
            log_button_layout = QHBoxLayout()  # To align this with the button_layout underneath
            log_url = QUrl(pathlib.Path(log_path).parent.as_uri())
            log_button = QPushButton("Open log folder")
            log_button.clicked.connect(partial(QDesktopServices.openUrl, log_url))
            log_button_layout.addWidget(log_button, alignment=Qt.AlignRight)
            main_layout.addLayout(log_button_layout)

        button_layout = QHBoxLayout()
        copy_button = QPushButton("Copy and open forum")
        copy_button.clicked.connect(self.copy_and_go_to_forum)
        button_layout.addWidget(copy_button)
        email_button = QPushButton("Open in email app")
        email_button.clicked.connect(self.open_in_email_app)
        button_layout.addWidget(email_button)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def showEvent(self, event):
        super().showEvent(event)
        # This doesn't work when called in __init__ after self.report_text.setFocusPolicy(Qt.ClickFocus)
        self.close_button.setDefault(True)
        self.close_button.setFocus()

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
        mailto_url = f"mailto:{TEAM_EMAIL}?subject={quote(subject)}&body={quote(body)}"
        webbrowser.open(mailto_url)

    @classmethod
    def createAndShowModal(cls, parent=None, workflow_report_text=""):
        dialog = cls(parent=parent, workflow_report_text=workflow_report_text)
        dialog.exec()
