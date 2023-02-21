# -*- coding: utf8 -*-
###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2022, the ilastik developers
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
import os
import webbrowser
from functools import partial
from pathlib import Path
from textwrap import dedent

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

import ilastik


class LicenseDialog(QDialog):
    LICENSE_SHORT = dedent(
        """
        <p>Copyright © 2011-2022, the ilastik developers <team@ilastik.org></p>
        <p>
        This program is free software; you can redistribute it and/or
        modify it under the terms of the GNU General Public License
        as published by the Free Software Foundation; either version 2
        of the License, or (at your option) any later version.
        </p>
        <p>
        In addition, as a special exception, the copyright holders of
        ilastik give you permission to combine ilastik with applets,
        workflows and plugins which are not covered under the GNU
        General Public License.
        </p>
        <p>See the <a href="https://ilastik.org/license.html">license page on the ilastik web site</a> for details.</p>
        """
    )
    LICENSE_ERROR = dedent(
        """
        Cannot find LICENSE file in ilastik sources.

        Please report this problem to team@ilastik.org.

        License information is available on the the ilastik web site at https://ilastik.org/license.html.
        """
    )
    LICENSE_3RD_PARTY_ERROR = dedent(
        """
        Cannot find third party license file. This is expected when running ilastik from source in conda.

        If you are seeing this in a release binary, please report this problem to team@ilastik.org.
        """
    )

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        ilastik_path = Path(ilastik.__file__).parent

        # files copied during release process
        license_path = ilastik_path / "LICENSE.txt"
        license_3rd_party_path = ilastik_path / "THIRDPARTY_LICENSES.txt"

        logo_path = ilastik_path / "ilastik-fist.png"

        logo_image = QPixmap(str(logo_path)).scaled(125, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo = QLabel()
        logo.setPixmap(logo_image)

        short_license_label = QLabel(self.LICENSE_SHORT)
        short_license_label.setWordWrap(True)
        short_license_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        short_license_label.setMinimumSize(600, 50)

        header_layout = QHBoxLayout()
        header_layout.addWidget(logo)
        header_layout.addWidget(short_license_label, 1)

        def show_license(_checked, license_path: Path, error_message: str):
            if license_path.is_file():
                webbrowser.open(license_path.as_uri())
            else:
                # parent, title, text
                QMessageBox.warning(self, "License file not found!", error_message)

        show_details_btn = QPushButton("Show full license")
        show_details_btn.clicked.connect(
            partial(show_license, license_path=license_path, error_message=self.LICENSE_ERROR)
        )
        self._show_details_btn = show_details_btn
        show_3rd_party_btn = QPushButton("Show third party licenses")
        show_3rd_party_btn.clicked.connect(
            partial(show_license, license_path=license_3rd_party_path, error_message=self.LICENSE_3RD_PARTY_ERROR)
        )
        self._show_3rd_party_btn = show_3rd_party_btn
        btnbox = QHBoxLayout()
        btnbox.addStretch()
        btnbox.addWidget(show_details_btn)
        btnbox.addWidget(show_3rd_party_btn)
        close_btn = QPushButton("Close")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        btnbox.addWidget(close_btn)
        layout = QVBoxLayout(self)
        layout.addLayout(header_layout)
        layout.addLayout(btnbox)

        self.setLayout(layout)
        self.setTabOrder(close_btn, show_details_btn)
        self.setTabOrder(show_details_btn, show_3rd_party_btn)

        self.setWindowModality(Qt.NonModal)
        self.show()
