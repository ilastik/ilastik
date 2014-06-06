###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
import functools

from ilastik.shell.headless.headlessShell import HeadlessShell
from ilastik.workflows.pixelClassification.pixelClassificationWorkflow import PixelClassificationWorkflow

if __name__ == "__main__":
    shell = HeadlessShell( functools.partial(PixelClassificationWorkflow, appendBatchOperators=False) )
    shell.createBlankProjectFile("/tmp/testproject.ilp")
    workflow = shell.workflow 
    
    d = {a.name : a for a in workflow.applets}
    
    d["Project Metadata"]._projectMetadata.projectName = "Test project"
    d["Project Metadata"]._projectMetadata.labeler     = "Mr. Labeler"
    d["Project Metadata"]._projectMetadata.description = "Automatically generated"
    
    shell.projectManager.saveProject() 
    
    