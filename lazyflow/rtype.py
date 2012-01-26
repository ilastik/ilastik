from roi import sliceToRoi, roiToSlice

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
    else:
      self.start = start
      self.stop = stop

  def __str__( self ):
      return "".join(("Subregion: start '", str(self.start), "' stop '", str(self.stop), "'"))


  def toSlice(self, hardBind = False):
    return roiToSlice(self.start,self.stop, hardBind)
