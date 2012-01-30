#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import sys

from PyQt4 import uic
from PyQt4.QtGui import QApplication

class IlastikShell( object ):
    def __init__( self ):
        self.window = uic.loadUi("ui/ilastikShell.ui")
        self.appletWindowHook = self.window.tabWidget.workflowTab


### Applet = Pipeline + PipelineGui ###

class PipelineGui( object ):
    def __init__( self, pipeline, resource ):
        self.applet_stack = []
    
    def get_main_widget( self ):
        return None

    def get_status_bar( self ):
        return None

class Pipeline( object ):
    def __init__( self ):
        self.opA = None
        self.opB = None

####
qapp = QApplication(sys.argv)


p1 = Pipeline()
p2 = Pipeline()

''' wire up p1 and p2 as a workflow here '''
workflow = None

resource = None

# make two applet guis; they share a common gui resource like a volumeeditor
p1Gui = PipelineGui( p1, resource )
p2Gui = PipelineGui( p2, resource )

shell = IlastikShell()
shell.window.show()
#shell.applet_stack.append(p1Gui)
#shell.applet_stack.append(p2Gui)

qapp.exec_()
