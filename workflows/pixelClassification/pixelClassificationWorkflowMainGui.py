import ilastik.utility.monkey_patches # Must be the first import

from ilastik.shell.gui.startShellGui import startShellGui
from pixelClassificationWorkflow import PixelClassificationWorkflow


debug_testing = True
if debug_testing:
    def test(shell):
        import h5py
        projFilePath = '/home/bergs/gigacube.ilp'
        projFile = h5py.File(projFilePath)
        shell.loadProject(projFile, projFilePath)
    
    startShellGui( PixelClassificationWorkflow, test )

else:
    startShellGui( PixelClassificationWorkflow )

