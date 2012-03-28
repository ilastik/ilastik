import numpy, vigra
from roi import roiToSlice, sliceToRoi
from helpers import warn_deprecated

class SlotType( object ):
    def __init__( self, slot):
        self.slot = slot

    def allocateDestination( self, roi ):
      pass

    def writeIntoDestination( self, destination, value, roi ):
      pass

    def isCompatible(self, value):
      """
      Slot types must implement this method.

      this method should check wether the supplied value
      is compatible with this type trait and should return true
      if this is the case.
      """
      pass

    def setupMetaForValue(self, value):
      """
      Slot types must implement this method.

      this method should extract valuable meta information
      from the provided value and set up the self.slot.meta
      MetaDict accordingly
      """
      pass


    def isConfigured(self):
      """
      Slot types must implement this method.

      it should analyse the .meta property of the slot
      and return wether the neccessary meta information
      is available.
      """
      return False

    def connect(self,slot):
      pass
      

class ArrayLike( SlotType ):
    def allocateDestination( self, roi ):
        shape = roi.stop - roi.start if roi else self.slot.meta.shape
        storage = numpy.ndarray(shape, dtype=self.slot.meta.dtype)
        # if axistags is True:
        #     storage = vigra.VigraArray(storage, storage.dtype, axistags = copy.copy(s))elf.axistags))
        #     #storage = storage.view(vigra.VigraArray)
        #     #storage.axistags = copy.copy(self.axistags)
        return storage

    def writeIntoDestination( self, destination, value, roi ):
        if not isinstance(destination, list):
         assert(roi.dim == destination.ndim), "%r ndim=%r, shape=%r" % (roi.toSlice(), destination.ndim, destination.shape)
        sl = roiToSlice(roi.start, roi.stop)
        try:
            destination[:] = value[sl]
        except TypeError:
            warn_deprecated("old style slot encountered: non array-like value set -> change SlotType from ArrayLike to proper SlotType")
            destination[:] = value
        return destination

    def isCompatible(self, value):
        warn_deprecated("FIXME here")
        return True


    def setupMetaForValue(self, value):
      if hasattr(value,"__getitem__")  and hasattr(value,"shape") and hasattr(value,"dtype"):
        self.slot.meta.shape = value.shape
        self.slot.meta.dtype = value.dtype
        if hasattr(value,"axistags"):
          self.slot.meta.axistags = value.axistags
        else:
          self.slot.meta.axistags = vigra.defaultAxistags(len(value.shape))
      else:
        self.slot.meta.shape = (1,)
        self.slot.meta.dtype = object

    def isConfigured(self):
      meta = self.slot.meta
      if meta.shape is not None and meta.dtype is not None:
        return True
      else:
        return False


class Struct( SlotType ):
    
    """
    Sublass this type and define some class
    variables of type Slot. Example:

    class GraphType(Struct):
      nodes = Slot(stype = ArrayLike)
      edges = Slot(stype = ArrayLike)

    
    slots with stype=GraphType
    will now have instance
    InputSlot/OutputSlot instance 
    attributes corresponding to these
    names which behave like normal slots.
    """

    def __init__(self, slot):
      SlotType.__init__(self, slot)
      self._subSlots = {}
      if slot.operator is not None:
        self.graph = slot.operator.graph
      else:
        self.graph = None
      for k,v in self.__class__.__dict__.items():
        if hasattr(v,"_subSlots") and v != slot: #FIXME: really bad detection of type
          v._type = slot._type
          si = v.getInstance(operator=self)
          self._subSlots[k] = si
          setattr(slot,k,si)

    def isConfigured(self):
      configured = True
      for k,v in self._subSlots.items():
        if v._optional is False and v.connected() is False:
          configured = False
          break
      return configured

    def connect(self, slot):
      for k,v in self._subSlots.items():
        if hasattr(slot,k):
          self._subSlots[k].connect(getattr(slot,k))
          print "subslot ", k, "connected:", self._subSlots[k].partner,self._subSlots[k].connected(),self._subSlots[k].shape, self._subSlots[k].graph, self.slot.operator

    
    def execute(self,slot,roi,destination):
      return self.slot.operator.execute(slot,roi,destination)

    def _notifyDisconnect(self,slot):
      pass

    def _notifyConnect(self,slot):
      pass



class Opaque( SlotType ):
    def allocateDestination( self, roi ):
        return None

    def writeIntoDestination( self, destination, value,roi ):
        print "FIXME: roi cant be applied here"
        destination = value
        return destination

    def isCompatible(self, value):
      return True
   
    def setupMetaForValue(self, value):
      self.slot.meta.shape = (1,)
      self.slot.meta.dtype = object
      self.slot.meta.axistags = vigra.defaultAxistags(1)

    def isConfigured(self):
      return True
