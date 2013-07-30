import os

import numpy
import vigra

from lazyflow.graph import Operator, InputSlot
from lazyflow.roi import TinyVector

class OpExport2DImage(Operator):
    """
    Export a 2D image using vigra.impex.writeImage()
    """
    Input = InputSlot() # Allowed to have more than 2 dimensions as long as the others are singletons.
    Filepath = InputSlot()
    
    def setupOutputs(self):
        # Check for errors...
        shape = TinyVector(self.Input.meta.shape)
        assert sum(shape > 1) <= 2, "Image must have no more than 2 non-singleton dimensions."

        # Ask vigra which extensions are supported.
        # If vigra was compiled with libpng, libjpeg, etc.,
        #  then 'png', 'jpeg', etc. will be in this list.
        # Otherwise, they aren't supported.        
        extension = os.path.splitext(self.Filepath.value)[1][1:]
        if extension not in vigra.impex.listExtensions().split():
            msg = "Unknown export format: '{}' "\
                  "is not a recognized 2D image extension.".format( extension )
            raise Exception(msg)
        

    # No Output slots...
    def execute(self, slot, subindex, roi, result): pass
    def propagateDirty(self, slot, subindex, roi): pass
    
    def run_export(self):
        """
        Requests all of the input and saves the output file.
        SYNCHRONOUSLY.
        """
        data = self.Input[:].wait()
        data = data.squeeze()
        if len(data.shape) == 1:
            data = data[numpy.newaxis, :]
        assert len(data.shape) == 2, "Image has shape {}".format(data.shape)
        
        vigra.impex.writeImage(data, self.Filepath.value)

if __name__ == "__main__":
    a = numpy.random.random((1, 100, 1, 100, 1)) * 255
    a = a.astype( numpy.uint8 )
    a = vigra.taggedView(a, vigra.defaultAxistags('txyzc'))
    
    from lazyflow.graph import Graph
    op = OpExport2DImage(graph=Graph())
    op.Input.setValue(a)
    op.Filepath.setValue('/tmp/test.png')
    
    op.run_export()

