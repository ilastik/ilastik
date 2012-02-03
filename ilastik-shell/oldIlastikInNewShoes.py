from ilastikShell import IlastikShell
from applets.pixelClassification import PixelClassificationApplet

pc = PixelClassificationApplet()
shell = IlastikShell()
shell.addApplet(pc)
