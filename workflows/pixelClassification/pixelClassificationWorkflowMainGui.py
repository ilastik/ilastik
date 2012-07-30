import ilastik.utility.monkey_patches # Must be the first import

from ilastik.shell.gui.startShellGui import startShellGui
from pixelClassificationWorkflow import PixelClassificationWorkflow

startShellGui( PixelClassificationWorkflow ) # Pass the class, not an instance
