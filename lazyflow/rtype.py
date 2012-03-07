from roi import sliceToRoi, roiToSlice
import vigra,numpy
from lazyflow.roi import TinyVector

class Roi(object):
    def __init__(self, slot):
        self.slot = slot
        pass
    pass

class SubRegion(Roi):
    def __init__(self, slot, start = None, stop = None, pslice = None):
        super(SubRegion,self).__init__(slot)
        if pslice != None or start is not None and stop is None and pslice is None:
            if pslice is None:
                pslice = start
            assert self.slot.meta.shape is not None
            self.start, self.stop = sliceToRoi(pslice,self.slot.meta.shape)
        elif start is None and pslice is None:
            self.start, self.stop = sliceToRoi(slice(None,None,None),self.slot.meta.shape)
        else:
            self.start = start
            self.stop = stop
        self.axistags = None
        self.dim = len(self.start)
    
    def __str__( self ):
        return "".join(("Subregion: start '", str(self.start), "' stop '", str(self.stop), "'"))
    
    def setAxistags(self,axistags):
        assert type(axistags) == vigra.vigranumpycore.AxisTags
        self.axistags = axistags
    
    def expandByShape(self,shape):
        """
        extend a roi by a given in shape
        """
        #TODO: make sure its bounded
        if type(shape == int):
            tmp = shape
            shape = numpy.zeros(self.dim).astype(int)
            shape[:] = tmp
            shape[self.axistags.channelIndex] = 0
        self.start = TinyVector([x-s for x,s in zip(self.start,shape)])
        self.stop = TinyVector([x+s for x,s in zip(self.stop,shape)])
    
    def decreaseByShape(self,shape):
        """
        extend a roi by a given in shape
        """
        #TODO: make sure its bounded
        if type(shape == int):
            tmp = shape
            shape = numpy.zeros(self.dim).astype(int)
            shape[:] = tmp
            shape[self.axistags.channelIndex] = 0
        self.start = TinyVector([x+s for x,s in zip(self.start,shape)])
        self.stop = TinyVector([x-s for x,s in zip(self.stop,shape)])
    
    def popAxis(self,axis):
        for tag,i in zip(self.axistags,range(len(self.axistags))):
            if tag.key == axis:
                self.axistags.__delitem__(i)
                popKey = i
        self.start.pop(popKey)
        self.stop.pop(popKey)
    
    def changeCoordinateSystemTo(self,shape):
        pass
            
    def toSlice(self, hardBind = False):
        return roiToSlice(self.start,self.stop, hardBind)
