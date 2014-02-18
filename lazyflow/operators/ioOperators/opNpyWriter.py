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

import numpy
from lazyflow.graph import Operator, InputSlot

import logging
logger = logging.getLogger(__name__)

class OpNpyWriter(Operator):
    Input = InputSlot()
    Filepath = InputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNpyWriter, self ).__init__(*args, **kwargs)
    
    def setupOutputs(self):
        pass
    
    def execute(self, *args):
        pass
    
    def propagateDirty(self, *args):
        pass
    
    def write(self):
        """
        Requests the entire input and saves it to the file.
        This function executes synchronously.
        """
        # TODO: Use a lazyflow.utility.BigRequestStreamer to split up 
        #       this giant request into a series of streamed subrequests.
        
        logger.warn("The current implementation of NPY-format data export computes the entire dataset at once, which requires lots of RAM.")
        path = self.Filepath.value
        data = self.Input[:].wait()
        numpy.save(path, data)
    