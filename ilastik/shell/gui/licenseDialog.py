# -*- coding: utf8 -*-
###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
#		   http://ilastik.org/license.html
###############################################################################
import os
from PyQt4.QtGui import  QMessageBox, QPixmap
from PyQt4.QtCore import Qt

import platform
import ilastik
ilastik_path = os.path.split(ilastik.__file__)[0]
def get_buildem_license():
    """
    Check if ilastik is run from a binary install created by BuildEM and
    return path to the license file from the binary distribution.

    Looks up the names of the directories from the base of the binary
    install up to the ilastik Python module source.
    """
    system = platform.system()
    if system == "Windows":
        dir_names = ['ilastik', 'ilastik', 'ilastik']
    else:
        dir_names = ['src', 'ilastik', 'ilastik', 'ilastik']
    global ilastik_path
    path_components = ilastik_path.split(os.sep)
    if path_components[-len(dir_names):] == dir_names:
        # this is safer than
        # os.path.join(path_components[:-len(dir_names)]
        new_components = [ilastik_path] + len(dir_names)*['..'] + \
                ['COPYING' + ('.txt' if system == "Windows" else '')]
        license_path = os.path.join(*new_components)
        if os.path.isfile(license_path):
            return license_path
    return None


class LicenseDialog(QMessageBox):
    LICENSE_SHORT = u"""<p>Copyright © 2011-2014, the ilastik developers <team@ilastik.org></p>
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
<p>See the <a href="http://ilastik.org/license.html">license page on the ilastik web site</a> for details.</p>
"""
    LICENSE_ERROR = u"""Cannot find LICENSE file in ilastik sources.

Please report this problem to ilastik-devel@ilastik.org.

License information is available on the the ilastik web site at http://ilastik.org/license.html.
"""

    def __init__(self, parent=None):
        super(LicenseDialog, self).__init__(parent=parent)

        self.setText(self.LICENSE_SHORT)

        global ilastik_path
        logo_path = os.path.join(ilastik_path, 'shell', 'gui',
                'ilastik-logo-alternate-colors.png')

        logo_image = QPixmap(logo_path).scaled(125, 200, Qt.KeepAspectRatio)
        self.setIconPixmap(logo_image)

        license_path = os.path.join(ilastik_path, '..', 'LICENSE')
        # if ilastik is run from a binary
        # use the COPYING file in the distribution
        license_path_dist = get_buildem_license()
        if license_path_dist:
            license_long = open(license_path_dist, 'r').read()
        elif os.path.isfile(license_path):
            license_long = open(license_path, 'r').read()
        else:
            license_long = self.LICENSE_ERROR

        self.setDetailedText(license_long)

        self.setWindowModality(Qt.NonModal)
        self.open()

    def closeEvent(self, event):
        """
        Emulate accept signal to close the window.

        Using the window close button does not close a QMessageBox.
        """
        self.accept()
        super(LicenseDialog, self).closeEvent(event)
