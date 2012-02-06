#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import sys

from PyQt4 import uic
from PyQt4.QtGui import QApplication

class IlastikShell( object ):
    def __init__( self ):
        self.window = uic.loadUi("ui/ilastikShell.ui")


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
from lazyflow.graph import Graph
from applets.pixelClassification import PixelClassificationGui, PixelClassificationPipeline, AppletControl
from PyQt4.QtGui import *

qapp = QApplication(sys.argv)
graph = Graph()

p0 = PixelClassificationPipeline( graph )
p1 = Pipeline()
p2 = Pipeline()

''' wire up p1 and p2 as a workflow here '''
workflow = None

resource = None

p0Gui = PixelClassificationGui( p0, graph )
p0Control = AppletControl()
p1Gui = PipelineGui( p1, resource )
p2Gui = PipelineGui( p2, resource )

shell = IlastikShell()

menuBar = QMenuBar()
shell.window.setMenuBar(menuBar)

def activate_classification_tab():
    shell.window.tabWidget.removeTab(0)
    shell.window.tabWidget.insertTab(0, p0Gui, "Workflow")
    shell.window.tabWidget.setCurrentWidget(p0Gui)

def active_void_tab():
    w = QWidget()
    shell.window.tabWidget.removeTab(0)
    shell.window.tabWidget.insertTab(0, w, "Workflow")
    shell.window.tabWidget.setCurrentWidget( w )
    shell.window.setMenuBar(QMenuBar())

def applet_switcher( index ):
    if index == 1:
        activate_classification_tab()
    else:
        active_void_tab()

shell.window.appletBar.currentChanged.connect(applet_switcher)    



shell.window.appletBar.addItem(p0Control, "Injected Applet" )

layout = QVBoxLayout()
for i in range(30):
    button = QPushButton()
    layout.addWidget(button)

shell.window.appletBar.widget(0).setLayout(layout)

shell.window.show()
#shell.applet_stack.append(p1Gui)
#shell.applet_stack.append(p2Gui)

qapp.exec_()
