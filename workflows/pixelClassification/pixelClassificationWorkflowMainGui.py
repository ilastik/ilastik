from ilastik.shell.gui.startShellGui import startShellGui
from pixelClassificationWorkflow import PixelClassificationWorkflow


def test_existing(shell, workflow):
    """
    (Function for debug and testing.)
    """
    projFilePath = '/home/bergs/gigacube.ilp'        
    #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'

    # Open a project
    shell.openProjectFile(projFilePath)

def test_new(shell, workflow):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/magnetic/test_project.ilp"        

    # New project
    shell.createAndLoadNewProject(projFilePath)

    # Add a file
    from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
    info = DatasetInfo()
    info.filePath = '/magnetic/gigacube.h5'
    opDataSelection = workflow.dataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(info)
    
    # Set some features
    import numpy
    opFeatures = workflow.featureSelectionApplet.topLevelOperator
    #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
    selections = numpy.array( [[False, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False],
                               [False, False, False, False,  True, False, False], # ST EVs
                               [False, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False],  # GGM
                               [False, False, False, False, False, False, False]] )
    opFeatures.SelectionMatrix.setValue(selections)

    # Save the project
    shell.onSaveProjectActionTriggered()


# Start the GUI
startShellGui( PixelClassificationWorkflow )

#startShellGui( PixelClassificationWorkflow, test_existing )    
#startShellGui( PixelClassificationWorkflow, test_new )

