#Python
import sys

#SciPy
import numpy
import vigra

#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot

#carving Cython module
from cylemon.segmentation import MSTSegmentor

class OpPreprocessing(Operator):
    """
    The top-level operator for the pre-procession applet
    """
    name = "Preprocessing"
    
    #Image before preprocess
    RawData = InputSlot()
    Sigma = InputSlot(value = 1.6)
    Filter = InputSlot(value = 0)
    
    #Image after preprocess as cylemon.MST
    PreprocessedData = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpPreprocessing, self).__init__(*args, **kwargs)
        self._prepData = [None]
        self.applet = self.parent.parent.preprocessingApplet
        
        self._unsavedData = False # set to True if data is not yet saved
        self._dirty = False       # set to True if any Input is dirty
         
         
        self.initialSigma = None  # save settings of last preprocess
        self.initialFilter = None # applied to gui by pressing reset
        
    def _checkMeta(self, slot):
        sh = slot.meta.shape
        ax = slot.meta.axistags
        if len(ax) != 5:
            raise RuntimeError("was expecting a 5D dataset, got shape=%r" % (sh,))
        if sh[0] != 1:
            raise RuntimeError("0th axis has length %d != 1" % (sh[0],))
        if sh[4] != 1:
            raise RuntimeError("4th axis has length %d != 1" % (sh[4],))
        for i in range(1,4):
            if not ax[i].isSpatial():
                raise RuntimeError("%d-th axis %r is not spatial" % (i, ax[i]))
    
    def setupOutputs(self):
        self._checkMeta(self.RawData)
        self.PreprocessedData.meta.shape = (1,)
        self.PreprocessedData.meta.dtype = object
        self.enableDownstream(False)
        
    def propagateDirty(self,slot,subindex,roi):
        if slot == self.RawData:
            #complete restart
            #No values will be reused any more
            self.initialSigma = None
            self.initialFilter = None
            self._prepData = [None]
        
        if self.AreSettingsInitial():
            #if settings are the same as with last preprocess
            #enable carving, as the graph is still stored
            self._dirty = False
            self.enableReset(False)
            self.enableDownstream(True)
        else:
            self._dirty = True
            self.enableDownstream(False)
            # is there a stored preprocessed graph?
            if self._prepData[0] is not None:
                self.enableReset(True)
    
    def AreSettingsInitial(self):
        '''analyse settings for sigma and filter
        return True if they are equal to those of last preprocess'''
        if self.initialFilter is None:
            return False        
        if self.Filter.value != self.initialFilter:
            return False
        if abs(self.Sigma.value - self.initialSigma)>0.005:
            return False
        return True
    
    def enableReset(self,er):
        '''set enabled of resetButton to er'''
        self.applet.enableReset(er)
    
    def enableDownstream(self,ed):
        '''set enable of carving applet to ed'''
        self.applet.enableDownstream(ed)

    def reset(self):
        '''reset sigma and filter to values of last preprocess'''
        self.applet._gui.setSigma(self.initialSigma)
        self.applet._gui.setFilter(self.initialFilter)
    
    def execute(self,slot,subindex,roi,result):
        if self._prepData[0] is not None and not self._dirty:
            return self._prepData
        
        #first thing, show the user that we are waiting for computations to finish        
        self.applet.progressSignal.emit(0)
       
        #make sure raw data is 5D: t,{x,y,z},c 
        ax = self.RawData.meta.axistags
        sh = self.RawData.meta.shape
        assert len(ax) == 5
        assert ax[0].key == "t" and sh[0] == 1
        for i in range(1,4):
            assert ax[i].isSpatial()
        assert ax[4].key == "c" and sh[4] == 1
        
        volume5d = self.RawData.value
        sigma = self.Sigma.value
        volume = volume5d[0,:,:,:,0]
        
        print "input volume shape: ", volume.shape
        print "input volume size: ", volume.nbytes / 1024**2, "MB"
        fvol = volume.astype(numpy.float32)

        #Choose filter selected by user
        volume_filter = self.Filter.value
        
        self.applet.progressSignal.emit(0)
        print "applying filter",
        if volume_filter == 0:
            print "lowest eigenvalue of Hessian of Gaussian"
            volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,:,0]
        
        elif volume_filter == 1:
            print "greatest eigenvalue of Hessian of Gaussian"
            volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,:,2]
             
        elif volume_filter == 2:
            print "Gaussian Gradient Magnitude"
            volume_feat = vigra.filters.gaussianGradientMagnitude(fvol,sigma)
            
        elif volume_filter == 3:
            print "Gaussian Smoothing"
            volume_feat = vigra.filters.gaussianSmoothing(fvol,sigma)
            
        elif volume_filter == 4:
            print "negative Gaussian Smoothing"
            volume_feat = vigra.filters.gaussianSmoothing(-fvol,sigma)
        
        volume_ma = numpy.max(volume_feat)
        volume_mi = numpy.min(volume_feat)
        volume_feat = (volume_feat - volume_mi) * 255.0 / (volume_ma-volume_mi)
        sys.stdout.write("Watershed..."); sys.stdout.flush()
        labelVolume = vigra.analysis.watersheds(volume_feat)[0].astype(numpy.int32)
        sys.stdout.write("done"); sys.stdout.flush()
        
        
        self.applet.progress = 0
        def updateProgressBar(x):
            #send signal iff progress is significant
            if x-self.applet.progress>1 or x==100:
                self.applet.progressSignal.emit(x)
                self.applet.progress = x
        
        mst= MSTSegmentor(labelVolume, volume_feat.astype(numpy.float32), edgeWeightFunctor = "minimum",progressCallback = updateProgressBar)
        #mst.raw is not set here in order to avoid redundant data storage 
        mst.raw = None
        
        #Output is of shape 1
        result[0] = mst
        
        #save settings for reloading them if asked by user
        self.initialSigma = sigma
        self.initialFilter = volume_filter
        self.enableReset(False)
        self._unsavedData = True
        self._dirty = False
        self.enableDownstream(True)
        
        
        #Cache result
        self._prepData = result
        
        #Wonder why this is set?
        #The preprocess is only called by the run button.
        #By setting the output dirty, this event is propagated to the
        #carving-Operator, who copies the result just calculated.
        #This is to gain control over when the preprocess is executed.
        self.PreprocessedData.setDirty()
        
        return result
