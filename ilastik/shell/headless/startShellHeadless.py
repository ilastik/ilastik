#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Logging configuration
import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
ilastik.ilastik_logging.startUpdateInterval(10) # 10 second periodic refresh

from ilastik.shell.headless.headlessShell import HeadlessShell

def startShellHeadless(workflowClass):
    """
    Start the ilastik shell in "headless" mode with the given workflow type.
    
    workflowClass - the type of workflow to instantiate for the shell.
    
    Returns the shell and workflow instance.
    """
    # Create workflow
    workflow = workflowClass()
    
    # Create the shell and populate it
    shell = HeadlessShell()
    for app in workflow.applets:
        shell.addApplet(app)

    # For now, headless shell doesn't do anything that requires knowledge of image names.
    #shell.setImageNameListSlot( workflow.imageNameListSlot )

    return (shell, workflow)
