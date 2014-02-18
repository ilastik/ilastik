# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

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
    
    