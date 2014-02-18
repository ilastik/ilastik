# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

import os
from PyQt4.QtGui import  QSplashScreen, QPixmap 
from PyQt4.QtCore import Qt

import ilastik

splashScreen = None
def showSplashScreen():
    splash_path = os.path.join(os.path.split(ilastik.__file__)[0], 'ilastik-splash.png')
    splashImage = QPixmap(splash_path)
    global splashScreen
    splashScreen = QSplashScreen(splashImage)    
    splashScreen.showMessage( ilastik.__version__, Qt.AlignBottom | Qt.AlignRight )
    splashScreen.show()

def hideSplashScreen():
    import startShellGui
    global splashScreen
    splashScreen.finish(startShellGui.shell)
