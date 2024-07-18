import os

import ilastik
import platform
import sys
import webbrowser
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QSizePolicy
from urllib.parse import quote


def _get_log_since_last_startup() -> str:
    """
    Reads the log up to maximum 1 MB from the end and returns the text since the last startup, or the entire 1 MB.
    We don't want people emailing us more than 1MB of log...
    """
    log_path = ilastik.ilastik_logging.default_config.get_logfile_path()
    marker = b"Starting ilastik"
    text_size_limit = 1048576  # 1 MB
    file_size = int(os.path.getsize(log_path))
    with open(log_path, "rb") as log_file:
        position = max(0, file_size - text_size_limit)
        log_file.seek(position)
        log_text = log_file.read()
    if marker in log_text:
        return b"".join(log_text.rpartition(marker)[1:]).decode()
    else:
        return log_text.decode()


class ReportIssueDialog(QDialog):
    def __init__(self, parent=None, workflow_report_text=""):
        super().__init__(parent=parent)

        self.setWindowTitle("Report issue")
        self.setFixedSize(600, 300)

        main_layout = QVBoxLayout()

        # Create and add the instruction label
        instruction_label = QLabel()
        instruction_label.setText(
            "<p>Sorry you ran into a problem! Please copy the information below, and include it when you "
            "report your issue.</p>"
            '<p>The best place to get help is the community forum, using the "ilastik" tag '
            '(<a href="https://forum.image.sc/tag/ilastik">https://forum.image.sc/tag/ilastik</a>).<br>'
            "Alternatively, you can report the issue on GitHub ("
            '<a href="https://github.com/ilastik/ilastik/issues/">https://github.com/ilastik/ilastik/issues/</a>'
            ') or email us at <a href="mailto:team@ilastik.org">team@ilastik.org</a>.</p>'
        )
        instruction_label.setOpenExternalLinks(True)
        instruction_label.setWordWrap(True)
        main_layout.addWidget(instruction_label)

        report = (
            f"ilastik version: {ilastik.__version__}\n"
            f"OS: {platform.platform()}\n"
            f"{workflow_report_text}"
            "Log since last startup:\n"
            f"```\n{_get_log_since_last_startup()}\n```"
        )
        self.report_text = QTextEdit()
        self.report_text.setPlainText(report)
        self.report_text.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        main_layout.addWidget(self.report_text)

        button_layout = QHBoxLayout()
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_button)
        email_button = QPushButton("Open in Email App")
        email_button.clicked.connect(self.open_in_email_app)
        button_layout.addWidget(email_button)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

        # Set the layout to the dialog
        self.setLayout(main_layout)
        self.show()

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.report_text.toPlainText())

    def open_in_email_app(self):
        body = (
            "Please describe the issue you are experiencing and adapt the email subject.\n"
            "\n\n--\nAuto-generated report:\n"
        )
        body += self.report_text.toPlainText()
        subject = "ilastik issue report"
        mailto_url = f"mailto:team@ilastik.org?subject={subject}&body={quote(body)}"
        webbrowser.open(mailto_url)
