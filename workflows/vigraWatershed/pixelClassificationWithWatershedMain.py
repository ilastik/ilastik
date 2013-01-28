from ilastik.shell.gui.startShellGui import startShellGui
from pixelClassificationWithWatershedWorkflow import PixelClassificationWithVigraWatershedWorkflow

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
    #info.filePath = '/magnetic/singleslice.h5'
    opDataSelection = workflow.dataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(info)
    
    # Set some features
    import numpy
    featApplet = workflow.applets[2]
    featureGui = featApplet.gui
    opFeatures = featApplet.topLevelOperator
    #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
    selections = numpy.array( [[True, False, False,  False, False, False, False],
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
    from optparse import OptionParser
    usage = "%prog [options] filename"
    parser = OptionParser(usage)

    (options, args) = parser.parse_args()
    # Start the GUI
    if len(args) == 1:
        def loadProject(shell):
            shell.openProjectFile(args[0])
        startShellGui( PixelClassificationWithVigraWatershedWorkflow, loadProject )
    elif len(args) == 0:
        startShellGui( PixelClassificationWithVigraWatershedWorkflow )
    else:
        parser.error("incorrect number of arguments")
