import logging
from functools import partial
import cPickle as pickle
import tempfile


from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.adaptors import Op5ifyer
from lazyflow.stype import Opaque
from lazyflow.rtype import SubRegion
from lazyflow.request import Request, RequestPool

import numpy as np
import numpy as np

import vigra

############################
############################           
############################
###                      ###
###  Top Level Operator  ###
###                      ###
############################
############################
############################

loggerName = __name__ 
logger = logging.getLogger(loggerName)


class OpInterpMissingData(Operator):
    name = "OpInterpMissingData"

    InputVolume = InputSlot()
    InputSearchDepth = InputSlot(value=3)
    PatchSize = InputSlot(value=128)
    HaloSize = InputSlot(value=30)
    DetectionMethod = InputSlot(value='svm')
    InterpolationMethod = InputSlot(value='cubic')
    OverloadDetector = InputSlot(value='')
      
    Output = OutputSlot()
    Missing = OutputSlot()
    Detector = OutputSlot(stype=Opaque)
    
    _requiredMargin = {'cubic': 2, 'linear': 1, 'constant': 0}
    
    def __init__(self, *args, **kwargs):
        super(OpInterpMissingData, self).__init__(*args, **kwargs)
        
        
        self.detector = OpDetectMissing(parent=self)
        self.interpolator = OpInterpolate(parent=self)
        
        self.detector.InputVolume.connect(self.InputVolume)
        self.detector.PatchSize.connect(self.PatchSize)
        self.detector.HaloSize.connect(self.HaloSize)
        self.detector.DetectionMethod.connect(self.DetectionMethod)
        
        self.interpolator.InputVolume.connect(self.InputVolume)
        self.interpolator.Missing.connect(self.detector.Output) 
        self.interpolator.InterpolationMethod.connect(self.InterpolationMethod) 
        
        self.Missing.connect(self.detector.Output)

    def dumps(self):
        return self.detector.dumps()
    
    def loads(self, s):
        self.detector.loads(s)

    def setupOutputs(self):
        # Output has the same shape/axes/dtype/drange as input
        self.Output.meta.assignFrom( self.InputVolume.meta )

        # Check for errors
        taggedShape = self.InputVolume.meta.getTaggedShape()
        
        # this assumption is important!
        if 't' in taggedShape:
            assert taggedShape['t'] == 1, "Non-spatial dimensions must be of length 1"
        if 'c' in taggedShape:
            assert taggedShape['c'] == 1, "Non-spatial dimensions must be of length 1"
            
        self.Detector.meta.shape = (1,)

    def execute(self, slot, subindex, roi, result):
        '''
        execute
        '''
        
        if slot == self.Detector:
            result = self.dumps()
            return result
        
        method = self.InterpolationMethod.value
        
        assert method in self._requiredMargin.keys(), "Unknown interpolation method {}".format(method)
        
        def roi2slice(roi):
            out = []
            for start, stop in zip(roi.start, roi.stop):
                out.append(slice(start, stop))
            return tuple(out)

        
        oldStart = np.asarray([k for k in roi.start])
        oldStop = np.asarray([k for k in roi.stop])

        z_index = self.InputVolume.meta.axistags.index('z')
        nz = self.InputVolume.meta.getTaggedShape()['z']
        
        # check if more input is needed, and how many
        z_offsets = self._extendRoi(roi)
        
        
        # get extended interpolation
        roi.start[z_index] -= z_offsets[0]
        roi.stop[z_index] += z_offsets[1]
        
        a = self.interpolator.Output.get(roi).wait()
        
        # reduce to original roi
        roi.stop = roi.stop - roi.start
        roi.start *= 0
        roi.start[z_index] += z_offsets[0]
        roi.stop[z_index] -= z_offsets[1]
        key = roi2slice(roi)
        
        result[:] = a[key]
        
        
        return result
    
    
    def propagateDirty(self, slot, subindex, roi):
        # TODO: This implementation of propagateDirty() isn't correct.
        if slot == self.InputVolume:
            self.Output.setDirty(roi)
        
        if slot == self.OverloadDetector:
            s = self.OverloadDetector.value
            self.loads(s)
        
        
        
    
    def _extendRoi(self, roi):
        
        
        origStart = np.copy(roi.start)
        origStop = np.copy(roi.stop)
        
        
        offset_top = 0
        offset_bot = 0
        
        z_index = self.InputVolume.meta.axistags.index('z')
        
        depth = self.InputSearchDepth.value
        nRequestedSlices = roi.stop[z_index] - roi.start[z_index]
        nNeededSlices = self._requiredMargin[self.InterpolationMethod.value]
        
        missing = vigra.taggedView(self.detector.Output.get(roi).wait(), axistags=self.InputVolume.meta.axistags).withAxes(*'zyx')
        
        nGoodSlicesTop = 0
        # go inside the roi
        for k in range(nRequestedSlices):
            if np.all(missing[k,...]==0): #clean slice
                nGoodSlicesTop += 1
            else:
                break
        
        # are we finished yet?
        if nGoodSlicesTop >= nRequestedSlices:
            return (0,0)
        
        # looks like we need more slices on top
        while nGoodSlicesTop < nNeededSlices and offset_top < depth and roi.start[z_index] > 0:
            roi.stop[z_index] = roi.start[z_index] 
            roi.start[z_index] -= 1
            offset_top += 1
            topmissing = self.detector.Output.get(roi).wait()
            if np.all(topmissing==0): # clean slice
                nGoodSlicesTop += 1
            else: # need to start again
                nGoodSlicesTop = 0
        
        
        nGoodSlicesBot = 0
        # go inside the roi
        for k in range(1,nRequestedSlices+1):
            if np.all(missing[-k,...]==0): #clean slice
                nGoodSlicesBot += 1
            else:
                break
        
        
        roi.start = np.copy(origStart)
        roi.stop = np.copy(origStop)
        
        
        # looks like we need more slices on bottom
        while nGoodSlicesBot < nNeededSlices and offset_bot < depth and roi.stop[z_index] < self.InputVolume.meta.getTaggedShape()['z']:
            roi.start[z_index] = roi.stop[z_index] 
            roi.stop[z_index] += 1
            offset_bot += 1
            botmissing = self.detector.Output.get(roi).wait()
            if np.all(botmissing==0): # clean slice
                nGoodSlicesBot += 1
            else: # need to start again
                nGoodSlicesBot = 0
                
        
        roi.start = np.copy(origStart)
        roi.stop = np.copy(origStop)
        
        return (offset_top,offset_bot)
        
        
### HISTOGRAM EXTRACTION FUNCTION ###

def extractHistograms(volume, labels, patchSize = 64, nBins=30, intRange=(0,255)):
    '''
    extracts histograms from 3d-volume 
     - labels are
        0       ignore
        1       positive
        2       negative
     - histogram extraction is attempted to be done in parallel
     - patches that intersect with the volume border are discarded
     - volume and labels must be 3d, and in order 'zyx' (if not VigraArrays)
     - returns: np.ndarray, shape: (nSamples,nBins+1), last column is the label
    '''
    
    # sanity checks
    assert len(volume.shape) == 3, "Volume must be 3d data"
    assert volume.shape == labels.shape, "Volume and labels must have the same shape"
    
    try:
        volumeZYX = volume.withAxes(*'zyx')
        labelsZYX = labels.withAxes(*'zyx')
    except AttributeError:
        # can't blame me
        volumeZYX = volume
        labelsZYX = labels
        pass
    
    
    # fill list of patch centers (VigraArray does not support bitwise_or)
    ind_z, ind_y, ind_x = np.where((labelsZYX==1).view(np.ndarray) | (labelsZYX==2).view(np.ndarray))
    index = np.arange(len(ind_z))
    
    # prepare chunking of histogram centers
    chunkSize = 1000 #FIXME magic number??
    nChunks = len(index)//chunkSize + (1 if len(index) % chunkSize > 0 else 0)
    s = [slice(k*chunkSize,min((k+1)*chunkSize,len(index))) for k in range(nChunks)]
    histoList = [None]*nChunks
    
    # prepare subroutine for parallel extraction
    
    #BEGIN subroutine
    def _extract(index):
        
        out = []
        
        for z,y,x in zip(ind_z[index], ind_y[index],ind_x[index]):
            ymin = y - patchSize//2
            ymax = ymin + patchSize
            xmin = x - patchSize//2
            xmax = xmin + patchSize
            
            if not (xmin < 0 or ymin < 0 or xmax > volumeZYX.shape[2] or ymax > volumeZYX.shape[1]):
                # valid patch, add it to the output
                hist = np.zeros((nBins+1,))
                (hist[:nBins], _) = np.histogram(volumeZYX[z,ymin:ymax,xmin:xmax], bins=nBins, range=intRange, \
                                            density = True)
                hist[nBins] = 1 if labelsZYX[z,y,x] == 1 else 0
                out.append(hist)
            
        return np.vstack(out) if len(out) > 0 else np.zeros((0,nBins+1))

    def partFun(i):
        histoList[i] = _extract(index[s[i]])
    #END subroutine
    
    # pool the extraction requests
    pool = RequestPool()
    
    for i in range(nChunks):
        req = Request(partial(partFun, i))
        pool.add(req)
    
    pool.wait()
    pool.clean()
    
    return np.vstack(histoList)
    
    


################################
################################           
################################
###                          ###
###  Interpolation Operator  ###
###                          ###
################################
################################
################################

from vigra.analysis import labelVolumeWithBackground

def _cubic_mat(n=1):
    n = float(n)
    x = -1/(n+1)
    y = (n+2)/(n+1)
    
    A = [[1, x, x**2, x**3],\
        [1, 0, 0, 0],\
        [1, 1, 1, 1],\
        [1, y, y**2, y**3]]
    
    #TODO we could implement the direct inverse here, but it's a bit lengthy
    # compare to http://www.wolframalpha.com/input/?i=invert+matrix%28[1%2Cx%2Cx^2%2Cx^3]%2C[1%2C0%2C0%2C0]%2C[1%2C1%2C1%2C1]%2C[1%2Cy%2Cy^2%2Cy^3]%29
    
    return np.linalg.inv(A)



class OpInterpolate(Operator):
    InputVolume = InputSlot()
    Missing = InputSlot()
    InterpolationMethod = InputSlot(value='cubic')
    
    Output = OutputSlot()
    
    _requiredMargin = {'cubic': 2, 'linear': 1, 'constant': 0}
    _maxInterpolationDistance = {'cubic': 1, 'linear': np.inf, 'constant': np.inf}
    _fallbacks = {'cubic': 'linear', 'linear': 'constant', 'constant': None}
    
    def propagateDirty(self, slot, subindex, roi):
        # TODO
        self.Output.setDirty(roi)
    
    def setupOutputs(self):
        # Output has the same shape/axes/dtype/drange as input
        self.Output.meta.assignFrom( self.InputVolume.meta )
        
        try:
            self._iinfo = np.iinfo(self.InputVolume.meta.dtype)
        except ValueError:
            # not integer type, no casting needed
            self._iinfo = None

        assert self.InputVolume.meta.getTaggedShape() == self.Missing.meta.getTaggedShape(), \
                "InputVolume and Missing must have the same shape ({} vs {})".format(\
                self.InputVolume.meta.getTaggedShape(), self.Missing.meta.getTaggedShape())
            
        

    def execute(self, slot, subindex, roi, result):
        
        # prefill result
        result[:] = self.InputVolume.get(roi).wait()
        
        resultZYXCT = vigra.taggedView(result,self.InputVolume.meta.axistags).withAxes(*'zyxct')
        missingZYXCT = vigra.taggedView(self.Missing.get(roi).wait(),self.Missing.meta.axistags).withAxes(*'zyxct')
                
        for t in range(resultZYXCT.shape[4]):
            for c in range(resultZYXCT.shape[3]):
                missingLabeled = labelVolumeWithBackground(missingZYXCT[...,c,t])
                maxLabel = missingLabeled.max()
                for i in range(1,maxLabel+1):
                    self._interpolate(resultZYXCT[...,c,t], missingLabeled==i)
        
        
        
        return result
    
    def _cast(self, x):
        '''
        casts the array to expected range (i.e. 0..255 for uint8 types, ...)
        '''
        if not self._iinfo is None:
            x = np.where(x>self._iinfo.max, self._iinfo.max, x)
            x = np.where(x<self._iinfo.min, self._iinfo.min, x)
        return x
        
        
    def _interpolate(self,volume, missing, method = None):
        '''
        interpolates in z direction
        :param volume: 3d block with axistags 'zyx'
        :type volume: array-like
        :param missing: True where data is missing
        :type missing: bool, 3d block with axistags 'zyx'
        :param method: 'cubic' or 'linear' or 'constant' (see class documentation)
        :type method: str
        '''
        
        method = self.InterpolationMethod.value if method is None else method
        # sanity checks
        assert method in self._requiredMargin.keys(), "Unknown method '{}'".format(method)

        assert volume.axistags.index('z') == 0 \
            and volume.axistags.index('y') == 1 \
            and volume.axistags.index('x') == 2 \
            and len(volume.shape) == 3, \
            "Data must be 3d with z as first axis."
        
        # number and z-location of missing slices (z-axis is at zero)
        black_z_ind, black_y_ind, black_x_ind = np.where(missing)
        
        if len(black_z_ind) == 0: # no need for interpolation
            return 
            
        if black_z_ind.max() - black_z_ind.min() + 1 > self._maxInterpolationDistance[method]:
            self._interpolate(volume, missing, self._fallbacks[method])
            return
        
        # indices with respect to the required margin around the missing values
        minZ = black_z_ind.min() - self._requiredMargin[method]
        maxZ = black_z_ind.max() + self._requiredMargin[method]
        
        
        n = maxZ-minZ-2*self._requiredMargin[method]+1
        
        if not (minZ>-1 and maxZ < volume.shape[0]):
            # this method is not applicable, try another one
            logger.warning("Margin not big enough for interpolation (need at least {} pixels for '{}')".format(self._requiredMargin[method], method))
            if self._fallbacks[method] is not None:
                logger.warning("Falling back to method '{}'".format(self._fallbacks[method]))
                self._interpolate(volume, missing, self._fallbacks[method])
                return
            else:
                assert False, "Margin not big enough for interpolation (need at least {} pixels for '{}') and no fallback available".format(self._requiredMargin[method], method)
                
        minY, maxY = (black_y_ind.min(), black_y_ind.max())
        minX, maxX = (black_x_ind.min(), black_x_ind.max())
        
        if method == 'linear':
            # do a convex combination of the slices to the left and to the right
            xs = np.linspace(0,1,n+2)
            left = volume[minZ,minY:maxY+1,minX:maxX+1]
            right = volume[maxZ,minY:maxY+1,minX:maxX+1]

            for i in range(n):
                # interpolate every slice
                volume[minZ+i+1,minY:maxY+1,minX:maxX+1] =  self._cast((1-xs[i+1])*left + xs[i+1]*right)
                
        elif method == 'cubic': 
            # interpolation coefficients
            
            D = np.rollaxis(volume[[minZ,minZ+1,maxZ-1,maxZ],minY:maxY+1,minX:maxX+1],0,3)
            F = np.tensordot(D,_cubic_mat(n),([2,],[1,]))
            
            xs = np.linspace(0,1,n+2)
            for i in range(n):
                # interpolate every slice
                x = xs[i+1]
                volume[minZ+i+2,minY:maxY+1,minX:maxX+1] = self._cast(F[...,0] + F[...,1]*x + F[...,2]*x**2 + F[...,3]*x**3 )
                
        else: #constant
            if minZ > 0:
                # fill right hand side with last good slice
                for i in range(maxZ-minZ+1):
                    volume[minZ+i,minY:maxY+1,minX:maxX+1] = volume[minZ-1,minY:maxY+1,minX:maxX+1]
            elif maxZ < volume.shape[0]-1:
                # fill left hand side with last good slice
                for i in range(maxZ-minZ+1):
                    volume[minZ+i,minY:maxY+1,minX:maxX+1] = volume[maxZ+1,minY:maxY+1,minX:maxX+1]
            else:
                # nothing to do for empty block
                logger.warning("Not enough data for interpolation, leaving slice as is ...")
            
            
############################
############################           
############################
###                      ###
###  Detection Operator  ###
###                      ###
############################
############################
############################


try:
    from sklearn.svm import SVC
    havesklearn = True
except ImportError:
    logger.warning("Could not import dependency 'sklearn' for SVMs")
    havesklearn = False
    
class PseudoSVC(object):
    '''
    pseudo SVM 
    '''
    
    def __init__(self, *args, **kwargs):
        pass
    
    def fit(self, *args, **kwargs):
        pass
        
    def predict(self,*args, **kwargs):
        X = args[0]
        out = np.zeros(len(X))
        for k, patch in enumerate(X):
            out[k] = 1 if np.all(patch[1:] == 0) else 0
        return out
    
    
class NotTrainedError(Exception):
    pass

class SVMManager(object):
    '''
    manages our SVMs for multiple bin numbers
    '''
    
    _svms = {'version': 1}
    
    def get(self, n):
        try:
            return self._svms[n]
        except KeyError:
            raise NotTrainedError("Detector for bin size {} not trained.".format(n))
    
    def add(self, svm, n, overwrite=False):
        if not n in self._svms.keys() or overwrite:
            self._svms[n] = svm
    
    def remove(self, n):
        try:
            del self._svms[n]
        except KeyError:
            raise NotTrainedError("Detector for bin size {} not trained.".format(n))
    
    def has(self, n):
        return n in self._svms
    
    def extract(self):
        return self._svms
    
    def overload(self, obj):
        if 'version' in obj and obj['version'] == self._svms['version']:
            self._svms = obj
            return
        else:
            try:
                for n in obj['svm'].keys():
                    for svm in obj['svm'][n].values():
                        self.add(svm, n, overwrite=True)
            except KeyError:
                raise ValueError("Format not recognized.")


def _chooseRandomSubset(data, n):
    choice = np.random.permutation(len(data))
    return (data[choice[:n]], choice[:n], data[choice[n:]], choice[n:]) 


def _patchify(data, patchSize, haloSize):
    '''
    data must be 2D y-x
    
    returns (patches, slices)
    '''
    
    patches = []
    slices = []
    nPatchesX = data.shape[1]/patchSize + (1 if data.shape[1]%patchSize > 0 else 0)
    nPatchesY = data.shape[0]/patchSize + (1 if data.shape[0]%patchSize > 0 else 0)
    
    for y in range(nPatchesY):
        for x in range(nPatchesX):
            
            left = max(x*patchSize - haloSize, 0)
            top = max(y*patchSize - haloSize, 0)
            right = min((x+1)*patchSize + haloSize, data.shape[1])
            bottom = min((y+1)*patchSize + haloSize, data.shape[0])
            patches.append(data[top:bottom, left:right])
            slices.append( (slice(patchSize*y, min( patchSize*(y+1), data.shape[0] )), \
                slice(patchSize*x, min( patchSize*(x+1), data.shape[1] ))) )
            
    return (patches, slices)


def _histogramIntersectionKernel(X,Y):
    '''
    implements the histogram intersection kernel in a fancy way
    (standard: k(x,y) = sum(min(x_i,y_i)) )
    '''

    A = X.reshape( (X.shape[0],1,X.shape[1]) )
    B = Y.reshape( (1,) + Y.shape )
    
    return np.sum(np.minimum(A,B), axis=2)


_defaultBinSize = 30

def _defaultTrainingHistograms():
    '''
    produce a standard training set with black regions
    '''
    
    nHists = 100
    n = _defaultBinSize+1
    hists = np.zeros((nHists, n))
    
    # generate nHists/2 positive sets
    for i in range(nHists/2):
        (hists[i,:n-1],_) = np.histogram(np.zeros((64,64), dtype=np.uint8), bins=_defaultBinSize, range=(0,255), density=True)
        hists[i,n-1] = 1
    
    for i in range(nHists/2,nHists):
        (hists[i,:n-1],_) = np.histogram(np.random.random_integers(60,180,(64,64)), bins=_defaultBinSize, range=(0,255), density=True)
    
    return hists


class OpDetectMissing(Operator):
    '''
    Sub-Operator for detection of missing image content
    '''
    
    InputVolume = InputSlot()
    PatchSize = InputSlot(value=128)
    HaloSize = InputSlot(value=30)
    DetectionMethod = InputSlot(value='classic')
    NHistogramBins = InputSlot(value=_defaultBinSize)
    
    #histograms: ndarray, shape: nHistograms x (NHistogramBins.value + 1)
    # the last column holds the label, i.e. {0: negative, 1: positive}
    TrainingHistograms = InputSlot(value = _defaultTrainingHistograms())
    
    
    Output = OutputSlot()
    
    
    
    ### PRIVATE class attributes ###
    _manager = SVMManager()
    _inputRange = (0,255)
    _needsTraining = True
    
    
    def __init__(self, *args, **kwargs):
        super(OpDetectMissing, self).__init__(*args, **kwargs)
        
        
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.InputVolume:
            self.Output.setDirty(roi)
        if slot == self.TrainingHistograms:
            OpDetectMissing._needsTraining = True
            
        if slot == self.NHistogramBins:
            OpDetectMissing._needsTraining = OpDetectMissing._manager.has(self.NHistogramBins.value)
        
    
    def setupOutputs(self):
        self.Output.meta.assignFrom( self.InputVolume.meta )
        self.Output.meta.dtype = np.uint8
        
        # determine range of input
        if self.InputVolume.meta.dtype == np.uint8:
            r = (0,255) 
        elif self.InputVolume.meta.dtype == np.uint16:
            r = (0,65535) 
        else:
            #FIXME hardcoded range, use np.iinfo
            r = (0,255)
        self._inputRange = r


    def execute(self, slot, subindex, roi, result):
        
        # sanity check
        assert self.DetectionMethod.value in ['svm', 'classic'], \
            "Unknown detection method '{}'".format(self.DetectionMethod.value)
        
        # prefill result
        result[:] = 0
        resultZYXCT = vigra.taggedView(result,self.InputVolume.meta.axistags).withAxes(*'zyxct')
            
        # acquire data
        data = self.InputVolume.get(roi).wait()
        dataZYXCT = vigra.taggedView(data,self.InputVolume.meta.axistags).withAxes(*'zyxct')
        
        # walk over time and channel axes
        for t in range(dataZYXCT.shape[4]):
            for c in range(dataZYXCT.shape[3]):
                resultZYXCT[...,c,t] = self._detectMissing(slot, dataZYXCT[...,c,t])

        return result
    
    
    def dumps(self):
        return pickle.dumps(OpDetectMissing._manager.extract())
    
    
    def loads(self, s):
        OpDetectMissing._manager.overload(pickle.loads(s))
        OpDetectMissing._needsTraining = OpDetectMissing._manager.has(self.NHistogramBins.value)
    

    def _detectMissing(self, slot, data):
        '''
        detects missing regions and labels each missing region with 
        its own integer value
        :param origData: 3d data 
        :type origData: array-like
        '''
        
        assert data.axistags.index('z') == 0 \
            and data.axistags.index('y') == 1 \
            and data.axistags.index('x') == 2 \
            and len(data.shape) == 3, \
            "Data must be 3d with axis 'zyx'."
        
        if not OpDetectMissing._manager.has(self.NHistogramBins.value):
            self._train()
        
        result = vigra.VigraArray(data)*0
        
        patchSize = self.PatchSize.value
        haloSize = self.HaloSize.value
        
        if patchSize is None or not patchSize>0:
            raise ValueError("PatchSize must be a positive integer")
        if haloSize is None or haloSize<0:
            raise ValueError("HaloSize must be a non-negative integer")
        
        #if np.any(patchSize>np.asarray(data.shape[1:])):
            #logger.debug("Ignoring small region (shape={})".format(dict(zip([k.key for k in data.axistags], data.shape))))
            #maxZ=0
        #else:
        maxZ = data.shape[0]
            
        #from pdb import set_trace;set_trace()
        # pixels in patch
        nPatchElements = (patchSize+haloSize)**2
            
        # walk over slices
        for z in range(maxZ):
            patches, slices = _patchify(data[z,:,:], patchSize, haloSize)
            hists = []
            # walk over patches
            for patch in patches:
                (hist, _) = np.histogram(patch, bins=self.NHistogramBins.value, range=self._inputRange, density=True)
                hists.append(hist)
            
            pred = self._predict(hists)
            
            for i, p in enumerate(pred):
                if p > 0: 
                    #patch is classified as missing
                    result[z, slices[i][0], slices[i][1]] = 1
         
        return result
        
        
    def _train(self, force=False):
        '''
        trains with samples drawn from slot TrainingHistograms
        (retrains only if bin size is currently untrained or force is True)
        '''
        
        #FIXME unneccessary force input        
        
        # return early if unneccessary
        if not OpDetectMissing._needsTraining and OpDetectMissing._manager.has(self.NHistogramBins.value):
            return
        
        logger.debug("Training for {} histogram bins ...".format(self.NHistogramBins.value))
        
        if self.DetectionMethod.value == 'classic' or not havesklearn:
            # no need to train this
            return
        
        histograms = self.TrainingHistograms[:].wait()
        
        logger.debug("Finished loading histogram data of shape {}.".format(histograms.shape))
        
        assert histograms.shape[1] == self.NHistogramBins.value+1 and \
            len(histograms.shape) == 2, \
            "Training data has wrong shape (expected: (n,{}), got: {}.".format(self.NHistogramBins.value+1, histograms.shape)
        
        labels = histograms[:,-1]
        histograms = histograms[:,:self.NHistogramBins.value]
        
        neg_inds = np.where(labels==0)[0]
        pos_inds = np.setdiff1d(np.arange(len(labels)), neg_inds)
        
        pos = histograms[pos_inds]
        neg = histograms[neg_inds]
        npos = len(pos)
        nneg = len(neg)

        #prepare for 10-fold cross-validation
        nfolds = 10
        cfp = np.zeros((nfolds,))
        cfn = np.zeros((nfolds,))
        cprec = np.zeros((nfolds,))
        crec = np.zeros((nfolds,))
        pos_random = np.random.permutation(len(pos))
        neg_random = np.random.permutation(len(neg))

        with tempfile.NamedTemporaryFile(suffix='.txt', prefix='crossvalidation_', delete=False) as templogfile:
            for i in range(nfolds):
                logger.debug("starting cross validation fold {}".format(i))
                
                # partition the set in training and test data, use i-th for testing
                posTest=pos[pos_random[i*npos/nfolds:(i+1)*npos/nfolds],:]
                posTrain = np.vstack((pos[pos_random[0:i*npos/nfolds],:], pos[pos_random[(i+1)*npos/nfolds:],:]))
                
                negTest=neg[neg_random[i*nneg/nfolds:(i+1)*nneg/nfolds],:]
                negTrain = np.vstack((neg[neg_random[0:i*nneg/nfolds],:], neg[neg_random[(i+1)*nneg/nfolds:],:]))
                
                logger.debug("positive training shape {}, negative training shape {}, positive testing shape {}, negative testing shape {}".format(posTrain.shape, negTrain.shape, posTest.shape, negTest.shape))

                #FIXME do we need a minimum training set size??
                
                logger.debug("Starting training with {} negative patches and {} positive patches...".format( len(neg), len(pos)))
                self._felzenszwalbTraining(negTrain, posTrain)
            

                predNeg = self._predict(negTest)
                predPos = self._predict(posTest)

            
                fp = (predNeg.sum())/float(predNeg.size); cfp[i] = fp
                fn = (predPos.size - predPos.sum())/float(predPos.size); cfn[i] = fn
                
                prec = predPos.sum()/float(predPos.sum()+predNeg.sum()); cprec[i] = prec
                recall = 1-fn; crec[i] = recall
            
                logger.debug(" Finished training. Results of cross validation: FPR=%.5f, FNR=%.5f (recall=%.5f, precision=%.5f)." % (fp, fn, recall, prec))
                templogfile.write(str(fp)+" "+str(fn)+" "+str(1-fn)+" "+str(prec)+"\n")
            
            fp = np.mean(cfp)
            fn = np.mean(cfn)
            recall = np.mean(crec)
            prec = np.mean(cprec)
            logger.info(" Finished training. Averaged results of cross validation: FPR=%.5f, FNR=%.5f (recall=%.5f, precision=%.5f)." % (fp, fn, recall, prec))
            logger.info(" Wrote training results to '{}'.".format(templogfile.name))
        
        OpDetectMissing._needsTraining = False
            
        
            
    def _felzenszwalbTraining(self, negative, positive):
        '''
        we want to train on a 'hard' subset of the non-defective training data, see
        FELZENSZWALB ET AL.: OBJECT DETECTION WITH DISCRIMINATIVELY TRAINED PART-BASED MODELS (4.4), PAMI 32/9
        '''
        
        #TODO sanity checks
        
        n = (self.PatchSize.value + self.HaloSize.value)**2
        
        #FIXME arbitrary
        firstSamples = 200
        maxRemovePerStep = 0
        maxAddPerStep = 300
        maxSamples = 1500
        nTrainingSteps = 4
        
        # initial choice of training samples
        (initNegative,choiceNegative, _, _) = _chooseRandomSubset(negative, min(firstSamples, len(negative)))
        (initPositive,choicePositive, _, _) = _chooseRandomSubset(positive, min(firstSamples, len(positive)))
        
        # setup for parallel training
        samples = [negative,positive]
        choice = [choiceNegative, choicePositive]
        S_t = [initNegative, initPositive]
        
        finished = [False, False]
        
        ### BEGIN SUBROUTINE ###
        def felzenstep(x, cache, ind):
            
            case = ("positive" if ind>0 else "negative") + " set"
            pred = self._predict(x)
            
            hard = np.where(pred != ind)[0]
            easy = np.setdiff1d(range(len(x)), hard)
            logger.debug(" {}: currently {} hard and {} easy samples".format(\
                case, len(hard), len(easy)))

            # shrink the cache
            easyInCache = np.intersect1d(easy, cache) if len(easy)>0 else []
            if len(easyInCache)>10: #FIXME arbitrary
                (removeFromCache, _, _, _) = _chooseRandomSubset(easyInCache, min(len(easyInCache), maxRemovePerStep))
                cache = np.setdiff1d(cache, removeFromCache)
                logger.debug(" {}: shrunk the cache by {} elements".format(case, len(removeFromCache)))
                
            # grow the cache
            temp = len(cache)
            addToCache = _chooseRandomSubset(hard, min(len(hard), maxAddPerStep))[0]
            cache = np.union1d(cache, addToCache)
            addedHard = len(cache)-temp
            logger.debug(" {}: grown the cache by {} elements".format(case, addedHard))
            
            if len(cache) > maxSamples:
                logger.debug(" {}: Cache to big, removing elements.".format(case))
                (cache,_,_,_) = _chooseRandomSubset(cache, maxSamples)
            
            # apply the cache
            C = x[cache]
            #logger.debug(" {}: expanded set to {} elements".format(case, len(C)))
            
            return (C,cache,addedHard==0)
        ### END SUBROUTINE ###
        
        ### BEGIN PARALLELIZATION FUNCTION ###
        def partFun(i):
            (C, newChoice, newFinished) = felzenstep(samples[i], choice[i], i)
            S_t[i] = C
            choice[i] = newChoice
            finished[i] = newFinished
        ### END PARALLELIZATION FUNCTION ###
        
        for k in range(nTrainingSteps): #just count iterations

            logger.debug("Felzenszwalb Training (step {}/{}): {} hard negative samples, {} hard positive samples.".format(k+1,nTrainingSteps, len(S_t[0]), len(S_t[1])))
            self._fit(S_t[0], S_t[1])
            
            pool = RequestPool()

            for i in range(len(S_t)):
                req = Request(partial(partFun, i))
                pool.add(req)
            
            pool.wait()
            pool.clean()
            
            if np.all(finished): 
                #already have all hard examples in training set
                break

        self._fit(S_t[0], S_t[1])
        
        logger.debug(" Finished Felzenszwalb Training.")
    
    
    def _fit(self, negative, positive):
        '''
        train the underlying SVM
        '''
        
        if self.DetectionMethod.value == 'classic' or not havesklearn:
            return
        
        labels = [0]*len(negative) + [1]*len(positive)
        samples = np.vstack( (negative,positive) )
        
        svm = SVC(C=1000, kernel=_histogramIntersectionKernel)
        
        svm.fit(samples, labels)
        
        OpDetectMissing._manager.add(svm, self.NHistogramBins.value, overwrite=True)
        
        
    def _predict(self, X):
        '''
        predict if the histograms in X correspond to missing regions
        do this for subsets of X in parallel
        '''
        
        if self.DetectionMethod.value == 'classic' or not havesklearn:
            svm = PseudoSVC()
        else:
            svm = OpDetectMissing._manager.get(self.NHistogramBins.value)
        
        y = np.zeros((len(X),))*np.nan
        
        pool = RequestPool()

        chunkSize = 1000 #FIXME magic number??
        nChunks = len(X)/chunkSize + (1 if len(X) % chunkSize > 0 else 0)
        
        s = [slice(k*chunkSize,min((k+1)*chunkSize,len(X))) for k in range(nChunks)]
        
        def partFun(i):
            y[s[i]] = svm.predict(X[s[i]])
        
        for i in range(nChunks):
            req = Request(partial(partFun, i))
            pool.add(req)
        
        pool.wait()
        pool.clean()
        
        assert not np.any(np.isnan(y))
        return np.asarray(y)


if __name__ == "__main__":
    
    import argparse
    import os.path
    
    from lazyflow.graph import Graph
    
    from lazyflow.operators.opInterpMissingData import _histogramIntersectionKernel, PseudoSVC
    
    parser = argparse.ArgumentParser(description='Train a missing slice detector')
    parser.add_argument('file', nargs='*', action='store', help="volume and labels (if omitted, '-f' must be given)")
    parser.add_argument('-f', action='store', default=None, dest='histfile', help='pickled histograms (if not existing, histograms get calculated from volume and label files and stored there.')
    parser.add_argument('-d', dest='detfile', action='store', default=None, help='Output file for detector (will be a temporary file if omitted)')
    parser.add_argument('--patch', dest='patchSize', action='store', default='64', help='patch size')
    parser.add_argument('--halo', dest='haloSize', action='store', default='64', help='halo size')
    parser.add_argument('--bins', dest='binSize', action='store', default='30', help='number of histogram bins')
    
    
    args = parser.parse_args()
    patchSize = int(args.patchSize)
    haloSize = int(args.haloSize)
    binSize = int(args.binSize)
    
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
    
    startFromLabels = args.histfile is None or not os.path.exists(args.histfile)
    
    logger.debug("Gathering histograms...")
    
    if startFromLabels:
        assert len(args.file) == 2, "If there are no histograms available, volume and labels must be provided."
        logger.debug("Computing histograms (this could take a while)...")
        volume = vigra.impex.readHDF5(args.file[0], '/volume/data').withAxes(*'zyx')
        labels = vigra.impex.readHDF5(args.file[1], '/volume/data').withAxes(*'zyx')
        histograms = extractHistograms(volume, labels, patchSize = patchSize+haloSize, nBins=binSize, intRange=(0,255))
        
        if args.histfile is not None:
            vigra.impex.writeHDF5(histograms, args.histfile, '/volume/data')
            logger.debug("Dumped training data with shape {} to '{}'.".format(histograms.shape, args.histfile))
        
    else:
        histograms = vigra.impex.readHDF5(args.histfile, '/volume/data')
        logger.debug("Loaded training data from '{}'.".format(args.histfile))
    
    
    
    logger.debug("Training...")
    
    op = OpDetectMissing(graph=Graph())

    op.PatchSize.setValue(patchSize)
    op.HaloSize.setValue(haloSize)
    op.DetectionMethod.setValue('svm')
    op.NHistogramBins.setValue(binSize)
    
    op.TrainingHistograms.setValue(histograms)
    
    op._train(force=True)
    
    try:
        if args.detfile is None:
            with tempfile.NamedTemporaryFile(suffix='.pkl', prefix='detector_', delete=False) as f:
                logger.debug("Detector written to {}".format(f.name))
                f.write(op.dumps())
        else:
            with open(args.detfile,'w') as f:
                logger.debug("Detector written to {}".format(f.name))
                f.write(op.dumps())
    except Exception as e:
        print(e)
        print(op.dumps())
    
