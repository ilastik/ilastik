import functools

from ilastik.shell.headless.headlessShell import HeadlessShell
from ilastik.workflows.pixelClassification.pixelClassificationWorkflow import PixelClassificationWorkflow

if __name__ == "__main__":
    shell = HeadlessShell( functools.partial(PixelClassificationWorkflow, appendBatchOperators=False) )
    shell.createBlankProjectFile("/tmp/testproject.ilp")
    workflow = shell.workflow 
    
    d = {a.name : a for a in workflow.applets}
    
    d["Project Metadata"].projectName = "Test project"
    d["Project Metadata"].labeler     = "Mr. Labeler"
    d["Project Metadata"].description = "Automatically generated"
    
    shell.projectManager.saveProject() 
    
    