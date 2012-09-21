import numpy, vigra, h5py
from lazyflow.operators import OpPixelFeaturesPresmoothed, OpBlockedArrayCache, OpArrayPiper, Op5ToMulti, OpBlockedSparseLabelArray, OpArrayCache, \
                               OpTrainRandomForestBlocked, OpPredictRandomForest, OpSlicedBlockedArrayCache

from lazyflow.graph import Operator, InputSlot, OutputSlot
from threading import Lock
import pyximport; pyximport.install()
from cylemon.segmentation import GCSegmentor, MSTSegmentorKruskal, MSTSegmentor, PerturbMSTSegmentor
import json

from json import decoder, scanner

from json.scanner import make_scanner
from _json import scanstring as c_scanstring


class OpSegmentor(Operator):

  image     = InputSlot()

  writeSeeds = InputSlot(optional=True)
  deleteSeed = InputSlot(optional=True)
  update = InputSlot(value = False)
  eraser = InputSlot(value=100)
  algorithm = InputSlot(value="PrioMST")
  parameters = InputSlot(value=dict())
  
  sigma = InputSlot(value=1.6)
  border_indicator = InputSlot(value="hessian_ev_0")
  initial_segmentor = InputSlot(optional = True)

  segmentor = OutputSlot()

  raw = OutputSlot()
  seeds = OutputSlot()
  segmentation = OutputSlot()
  uncertainty = OutputSlot()
  regions = OutputSlot()

  seedNumbers = OutputSlot()
  
  maxUncertainFG = OutputSlot()
  maxUncertainBG = OutputSlot()


  def __init__(self,parent):
    Operator.__init__(self,parent)
    self._dirty   = True
    self._fname = None
    self._algorithm = ""
    self._parameters = {}
    self.seg = None
    self._dirty = True
    self.lock = Lock()
    self.initial_seg = None
    self._dirtySeg = True
    self.initial_segmentor.notifyConnect(self.onInitialSegmentor)
    self.initial_segmentor.notifyMetaChanged(self.onInitialSegmentor)
    self.parameters.notifyMetaChanged(self.onNewParameters)

  def onInitialSegmentor(self, slot):
    if slot.meta.shape is not None:
      print "================= setting initial segmentor"
      seg = slot.value
      if self.initial_seg != seg:
        self.seg = seg
        self._dirtySeg = False
      self.initial_seg = seg

  def onNewParameters(self, slot):
    print "================= setting segmentation to dirty = True"
    self._dirty = True
        
  def updateSeeds(self, oldseg, newseg):
    newseg.seeds.lut[:] = oldseg.seeds.lut[:]

  def setupOutputs(self):  

    self.segmentor.meta.shape = (1,)
    self.segmentor.meta.dtype = object

    self.seedNumbers.meta.shape = (1,)
    self.seedNumbers.meta.dtype = object
    
    self.deleteSeed.meta.shape = (1,)
    self.deleteSeed.meta.dtype = numpy.uint8

    shape = self.raw.meta.shape = self.image.meta.shape
    assert len(shape) == 3
    self.raw.meta.dtype = self.image.meta.dtype

    self.seeds.meta.shape = shape
    self.seeds.meta.dtype = numpy.uint8

    self.segmentation.meta.shape = shape
    self.segmentation.meta.dtype = numpy.uint8
    
    self.uncertainty.meta.shape = shape
    self.uncertainty.meta.dtype = numpy.uint8

    self.regions.meta.shape = shape
    self.regions.meta.dtype = numpy.int32

    self._eraser = self.eraser.value

    self.writeSeeds.meta.shape = shape
    self.writeSeeds.meta.dtype = numpy.uint8

    print "####################################### segmentor setupOutputs ############################"
    
  def setInSlot(self, slot, key, value):
    if self.seg is not None:
      print "  ========================= setInSlot"
      if slot == self.writeSeeds:
        print "  =========================== WriteSeeds"
        key = key[1:-1]
        value = numpy.where(value == self._eraser, 255, value[:])

        self.seg.seeds[key] = value
        self._dirty = True
      
      elif slot == self.deleteSeed:

        lut = self.seg.seeds.lut[:]
        label = value
        print "DELETING SEED", label
        lut = numpy.where(lut == label, 0, lut)
        lut = numpy.where(lut > label, lut - 1, lut)
        self.seg.seeds.lut[:] = lut
        self._dirty = True


  def execute(self, slot, subindex, roi, result):
    key = roi.toSlice()[1:-1]
    if slot == self.raw:
      if self.seg is not None:
        res = self.seg.raw[key]
        result[0,:,:,:,0] = res[:]
    elif slot == self.seeds:
      if self.seg is not None:
        res = self.seg.seeds[key]
        result[0,:,:,:,0] = res[:]
    elif slot == self.regions:
      if self.seg is not None:
        res = self.seg.regionVol[key] % 256
        result[0,:,:,:,0] = res[:]
    elif slot == self.seedNumbers:
      if self.seg is not None:
        result[0] = numpy.unique(self.seg.seeds.lut)
      else:
        result[0] = 0
      return result
    elif slot == self.segmentor:
      if self._dirtySeg:
        volume = self.image[:].wait()
        border_indicator = self.border_indicator.value
        sigma = self.sigma.value

        if border_indicator == "hessian_ev_0":
          print "Preprocessor: Eigenvalues (sigma = %r)" % (sigma,)
          fvol = volume.astype(numpy.float32)[0,:,:,:,0]
          volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,:,0]
        elif border_indicator == "hessian_ev_0_inv":
          print "Preprocessor: Eigenvalues (inverted, sigma = %r)" % (sigma,)
          fvol = (numpy.max(volume) - volume).astype(numpy.float32)[0,:,:,:,0]
          volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,:,0]
        volume_ma = numpy.max(volume_feat)
        volume_mi = numpy.min(volume_feat)
        volume_feat = (volume_feat - volume_mi) * 255.0 / (volume_ma-volume_mi)
        print "Preprocessor: Watershed..."
        labelVolume = vigra.analysis.watersheds(volume_feat)[0].astype(numpy.int32)
        print "Preprocessor: Construct MSTSegmentor..."
        mst = MSTSegmentor(labelVolume, volume_feat.astype(numpy.float32), edgeWeightFunctor = "minimum")
        mst.raw = volume[0,:,:,:,0]
        self.seg = mst
        self._dirtySeg = False
      result[0] = self.seg
      return result

    else:    # segmentation or uncertainty is requested
      self.lock.acquire()
      # get own outputslot
      segmentor = self.segmentor.value

      algorithm = self.algorithm.value
      
      self._parameters = self.parameters.value
      
      labelNumbers = numpy.unique(self.seg.seeds.lut)

      if self._dirty:
        labelCount = len(labelNumbers)
        if not self._parameters.has_key("prios"):
          prios = [1.0] * labelCount
          self._parameters["prios"] = prios
        while labelCount > len(self._parameters["prios"]):
            self._parameters["prios"].append(1.0)
        unaries =  numpy.zeros((self.seg.numNodes,labelCount)).astype(numpy.float32)
        print "parameters", self._parameters
        self.seg.run(unaries, **self._parameters)
        self._dirty = False
      self.lock.release()

      if slot == self.segmentation:
        print " ========== getting segmentation"
        res = self.seg.segmentation[key]
        for l in labelNumbers:
          print "Label=%r, count = %r" % ( l, numpy.sum(numpy.where(res == l, 1, 0)))
      if slot == self.uncertainty:
        res = self.seg.uncertainty[key]
      print res.shape, result.shape
      result[0,:,:,:,0] = res[:]
    return result
  
  def propagateDirty(self, slot, subindex, roi):
    if slot in [self.image, self.sigma, self.border_indicator]:
      print "  ======================= setting segmentor to dirty"
      self._dirty = True
      self._dirtySeg = True
      self.segmentor.setDirty(slice(0,1,None))
      self.segmentation.setDirty(slice(None,None,None))


  def maxUncertainFG(self):
    ufg = numpy.where(self.seg.segmentation.lut > 1, self.seg.uncertainty.lut, 0)
    index = numpy.argmax(ufg)
    return self.seg.regionCenter[index]

  def maxUncertainBG(self):
    ufg = numpy.where(self.seg.segmentation.lut == 1, self.seg.uncertainty.lut, 0)
    index = numpy.argmax(ufg)
    return self.seg.regionCenter[index]
























