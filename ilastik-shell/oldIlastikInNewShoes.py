#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtGui import QApplication

from ilastikshell.ilastikShell import IlastikShell
from applets.pixelClassification import PixelClassificationApplet

app = QApplication([])

g = Graph()
pipeline = PixelClassificationPipeline( g )
pig = PixelClassificationGui( pipeline, graph = g)
pig.show()

pc = PixelClassificationApplet()
shell = IlastikShell()
shell.addApplet(pc)
shell.show()

app.exec_()
