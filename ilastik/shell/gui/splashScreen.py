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
