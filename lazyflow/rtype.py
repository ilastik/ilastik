from roi import sliceToRoi, roiToSlice

class Roi(object):
  def __init__(self, slot):
    self.slot = slot
    pass
  pass

class SubRegion(Roi):
  def __init__(self, slot, start = None, stop = None, pslice = None):
    super(SubRegion,self).__init__(slot)
    if pslice != None:
      self.start, self.stop = sliceToRoi(pslice,self.slot.meta.shape)
    else:
      self.start = start
      self.stop = stop
