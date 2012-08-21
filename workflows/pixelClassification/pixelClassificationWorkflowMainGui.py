from ilastik.shell.gui.startShellGui import startShellGui
from pixelClassificationWorkflow import PixelClassificationWorkflow


def debug_with_existing(shell, workflow):
    """
    (Function for debug and testing.)
    """
    projFilePath = '/home/bergs/gigacube.ilp'        
    #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'

    # Open a project
    shell.openProjectFile(projFilePath)

def debug_with_new(shell, workflow):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/magnetic/test_project.ilp"

    # New project
    shell.createAndLoadNewProject(projFilePath)

    # Add a file
    from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
    info = DatasetInfo()
    #info.filePath = '/magnetic/gigacube.h5'
    info.filePath = '/magnetic/synapse_small.npy'
    opDataSelection = workflow.dataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(info)
    
    # Set some features
    import numpy
    featureGui = workflow.featureSelectionApplet.gui
    opFeatures = workflow.featureSelectionApplet.topLevelOperator
    #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
    selections = numpy.array( [[False, False, False,  True, False, False, False],
                               [False, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False], # ST EVs
                               [False, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False],  # GGM
                               [False, False, False, False, False, False, False]] )
    opFeatures.SelectionMatrix.setValue(selections)
    opFeatures.Scales.setValue( featureGui.ScalesList )
    opFeatures.FeatureIds.setValue( featureGui.FeatureIds )

    # Select the labeling drawer
    shell.setSelectedAppletDrawer(3)

    # Save the project
    shell.onSaveProjectActionTriggered()


if __name__ == "__main__":
    # Start the GUI
#    startShellGui( PixelClassificationWorkflow )

    # Start the GUI with a debug project    
    #startShellGui( PixelClassificationWorkflow, debug_with_existing )    
    startShellGui( PixelClassificationWorkflow, debug_with_new )

