from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import SubRegion
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader

import numpy

class OpTracking(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpTracking"
    category = "other"
    
    #InputImage = InputSlot()
    #MinValue = InputSlot(stype='int')
    #MaxValue = InputSlot(stype='int')
    
    Output = OutputSlot()
    RawData = OutputSlot()
    Objects = InputSlot()

    def __init__( self, parent = None, graph = None, register = True ):
        super(OpTracking, self).__init__(parent=parent,graph=graph,register=register)
        self._rawReader = OpInputDataReader( graph )
        self._rawReader.FilePath.setValue('/home/bkausler/src/ilastik/tracking/relabeled-stack/objects.h5/raw')
        self.RawData.connect( self._rawReader.Output )

        #self._trackingReader = OpInputDataReader( graph )
        #self._trackingReader.FilePath.setValue('/home/bkausler/src/ilastik/tracking/relabeled-stack/labeledtracking.h5/labeledtracking')
        #self.Output.connect( self._trackingReader.Output )

        self._objectsReader = OpInputDataReader( graph )
        self._objectsReader.FilePath.setValue('/home/bkausler/src/ilastik/tracking/relabeled-stack/objects.h5/objects')

        print self.Objects.meta
        assert( self._objectsReader.Output.ready() )

        self.Objects.connect( self._objectsReader.Output )
        assert( self.Objects.ready() )
        assert( self.Objects.configured() )
        self._initialized = True
        assert(self.configured() )
        print self.Objects.meta
        print self.Output.meta
        
        #self.Output.connect( self._reader.Output )

    
    def setupOutputs(self):
        print "tracking: setupOutputs"
        # Copy the input metadata to both outputs
        #self.Output.meta.assignFrom( self.InputImage.meta )
        #self.InvertedOutput.meta.assignFrom( self.InputImage.meta )
        #self.RawData.meta.assignFrom(self._reader.Output.meta )
        self.Output.meta.assignFrom(self.Objects.meta )
    
    def execute(self, slot, roi, result):
        if slot is self.Output:
            #self.Objects.get(roi, destination=result).wait()
            al = self.Objects.get( SubRegion( self.Objects ) ).wait()
            print type(al), al.shape

    def propagateDirty(self, inputSlot, roi):
        print "tracking: propagateDirty"
        if inputSlot is self.Objects:
            self.Output.setDirty(roi)
        # if inputSlot.name == "InputImage":
        #     self.Output.setDirty(roi)
        #     self.InvertedOutput.setDirty(roi)
        # if inputSlot.name == "MinValue" or inputSlot.name == "MaxValue":
        #     self.Output.setDirty( slice(None) )
        #     self.InvertedOutput.setDirty( slice(None) )
