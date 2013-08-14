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
    