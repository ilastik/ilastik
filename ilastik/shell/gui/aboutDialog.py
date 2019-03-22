###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2019, the ilastik developers
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
import sys
import os
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout
)
from PyQt5.QtCore import Qt
from functools import partial


import ilastik


about_text = f"""
    <p>ilastik version {ilastik.__version__}</p>
    <p>ilastik is developed by the ilastik development team in
    the Kreshuk Group at the European Molecular Biology Laboratory Heidelberg.
    More information can be found at
    <a href=https://ilastik.org/about.html>www.ilastik.org</a>.</p>

    <p>For a list of contributors visit our main repositories:
    <ul>
        <li><a href="https://github.com/ilastik/ilastik/graphs/contributors">
        ilastik contributors</a>
        </li>
        <li><a href="https://github.com/ilastik/lazyflow/graphs/contributors">
        lazyflow contributors</a></li>
        <li><a href="https://github.com/ilastik/volumina/graphs/contributors">
        volumina contributors</a></li>
    </ul>
    </p>
"""


class AboutDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_layout()

    def setup_layout(self):
        main_layout = QVBoxLayout()
        content_layout = QHBoxLayout()
        splash_path = os.path.join(
            os.path.split(ilastik.__file__)[0], 'ilastik-splash.png'
        )
        splash_pixmap = QPixmap(splash_path)
        logo_label = QLabel()
        logo_label.setPixmap(splash_pixmap)
        content_layout.addWidget(logo_label)

        text_label = QLabel()
        text_label.setWordWrap(True)
        text_label.setTextFormat(Qt.RichText)
        text_label.setOpenExternalLinks(True)
        text_label.setText(about_text)
        content_layout.addWidget(text_label)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(self.accept)

        main_layout.addLayout(content_layout)
        main_layout.addWidget(btn_box)

        self.setLayout(main_layout)
        self.setStyleSheet("background-color: white;")
        self.setFixedSize(splash_pixmap.width() * 2.5, splash_pixmap.height() * 1.05)


def showAboutDialog(parent=None):
    dialog = AboutDialog(parent=parent)
    dialog.setWindowTitle('About ilastik')
    dialog.exec()
