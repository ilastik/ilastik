from lazyflow.operators import OpPixelFeaturesPresmoothed, OpBlockedArrayCache, OpArrayPiper, Op5ToMulti, OpBlockedSparseLabelArray, OpArrayCache, \
                               OpTrainRandomForestBlocked, OpPredictRandomForest, OpSlicedBlockedArrayCache

from lazyflow.graph import Operator, InputSlot, OutputSlot
import h5py
import numpy
from threading import Lock
import pyximport; pyximport.install()
from cylemon.segmentation import GCSegmentor, MSTSegmentorKruskal, MSTSegmentor, PerturbMSTSegmentor
import json

from json import decoder, scanner

from json.scanner import make_scanner
from _json import scanstring as c_scanstring

_CONSTANTS = json.decoder._CONSTANTS

py_make_scanner = scanner.py_make_scanner

# Convert from unicode to str
def str_scanstring(*args, **kwargs):
    result = c_scanstring(*args, **kwargs)
    return str(result[0]), result[1]

# Little dirty trick here
json.decoder.scanstring = str_scanstring

class StrJSONDecoder(decoder.JSONDecoder):
    def __init__(self, encoding=None, object_hook=None, parse_float=None,
            parse_int=None, parse_constant=None, strict=True,
            object_pairs_hook=None):
        self.encoding = encoding
        self.object_hook = object_hook
        self.object_pairs_hook = object_pairs_hook
        self.parse_float = parse_float or float
        self.parse_int = parse_int or int
        self.parse_constant = parse_constant or _CONSTANTS.__getitem__
        self.strict = strict
        self.parse_object = decoder.JSONObject
        self.parse_array = decoder.JSONArray
        self.parse_string = str_scanstring
        self.scan_once = py_make_scanner(self)

# And another little dirty trick there    
_default_decoder = StrJSONDecoder(encoding=None, object_hook=None,
                               object_pairs_hook=None)

json._default_decoder = _default_decoder


class Segmentor(Operator):

  fileName = InputSlot()
  writeSeeds = InputSlot(optional=True)
  deleteSeed = InputSlot(optional=True)
  update = InputSlot()
  eraser = InputSlot()
  algorithm = InputSlot()
  parameters = InputSlot()

  raw = OutputSlot()
  seeds = OutputSlot()
  segmentation = OutputSlot()
  uncertainty = OutputSlot()
  regions = OutputSlot()
  
  maxUncertainFG = OutputSlot()
  maxUncertainBG = OutputSlot()


  def __init__(self,parent):
    Operator.__init__(self,parent)
    self._dirty   = True
    self._fname = None
    self._algorithm = ""
    self._parameters = {}
    self.seg = None
    self.lock = Lock()

  def setupOutputs(self):  
    fileName = self.fileName.value
    algorithm = self.algorithm.value
    try:
      parameters = self._parameters = json.loads(self.parameters.value)
    except:
      print "algorithmsOptions not a valid json string: ", self.parameters.value
      parameters = self._parameters = {}

    if self._fname != fileName or algorithm != self._algorithm:
      old = None
      if self._fname == fileName:
        old = self.seg

      if algorithm == "prioMST":
        self.seg = MSTSegmentor.loadH5(fileName,"graph")
      elif algorithm == "prioMSTperturb":
        self.seg = PerturbMSTSegmentor.loadH5(fileName,"graph")

      if old is not None:
        self.seg.seeds.lut[:] = old.seeds.lut[:]

      self._fname = fileName
      self._dirty = True

    shape = self.raw.meta.shape = (1,) + self.seg.raw.shape + (1,)
    self.raw.meta.dtype = self.seg.raw.dtype

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

    self.deleteSeed.meta.shape = (1,)
    self.deleteSeed.meta.dtype = numpy.uint8
    
  def setInSlot(self, slot, key, value):
    if slot == self.writeSeeds:
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


  def execute(self, slot, roi, result):
    key = roi.toSlice()[1:-1]
    if slot == self.raw:
      res = self.seg.raw[key]
    elif slot == self.seeds:
      res = self.seg.seeds[key]
    elif slot == self.regions:
      res = self.seg.regionVol[key] % 256
    else:
      self.lock.acquire()

      if self._dirty and self.update.value == True:
        labelCount = len(numpy.unique(self.seg.seeds.lut))
        prios = [1.0] * labelCount
        if self._parameters.has_key("prioBG"):
          prios[1] = self._parameters["prioBG"]
        print "using labelCount", labelCount
        unaries =  numpy.zeros((self.seg.numNodes,labelCount)).astype(numpy.float32)
        print "parameters", self._parameters
        self.seg.run(unaries, prios = prios, **self._parameters)
        self._dirty = False
      self.lock.release()
      if slot == self.segmentation:
        res = self.seg.segmentation[key]
      if slot == self.uncertainty:
        res = self.seg.uncertainty[key]
    result[0,:,:,:,0] = res[:]
    return result


  def maxUncertainFG(self):
    ufg = numpy.where(self.seg.segmentation.lut > 1, self.seg.uncertainty.lut, 0)
    index = numpy.argmax(ufg)
    return self.seg.regionCenter[index]

  def maxUncertainBG(self):
    ufg = numpy.where(self.seg.segmentation.lut == 1, self.seg.uncertainty.lut, 0)
    index = numpy.argmax(ufg)
    return self.seg.regionCenter[index]

class PixelClassificationLazyflow( object ):
  def __init__( self, graph):
       self.seg =Segmentor(graph) 
       self.seg.update.setValue(False)
        
