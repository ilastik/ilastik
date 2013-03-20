from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators.ioOperators import OpStreamingHdf5Reader, OpInputDataReader
from ilastik.utility.operatorSubView import OperatorSubView

from ilastik.shell.gui.ilastikShell import ProgressDisplayManager

from lazyflow.operators import Op5ifyer
from lazyflow.request import Request
from ilastik.applets.base.applet import ControlCommand

from cylemon.segmentation import MSTSegmentor
import vigra
import numpy
import uuid

class OpPreprocessing(Operator):
    """
    The top-level operator for the pre-procession applet
    """
    name = "Preprocessing"
    
    #Image before preprocess
    RawData = InputSlot()
    Sigma = InputSlot(value = 1.6)
    Filter = InputSlot(value = 0)
    
    #Image after preprocess
    PreprocessedData = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpPreprocessing, self).__init__(*args, **kwargs)
        self._prepData = [None]
        self.applet = self.parent.parent.preprocessingApplet
        
        self._unsavedData = False # set to True if data is not yet saved
        self._dirty = False       # set to True if any Input is dirty
         
         
        self.initialSigma = None  # save settings of last preprocess
        self.initialFilter = None # applied to gui by pressing reset
    
    def setupOutputs(self):
        self.PreprocessedData.meta.shape = (1,)
        self.PreprocessedData.meta.dtype = object
    
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
            self.enableReset(True)
            self.enableDownstream(False)
    
    def AreSettingsInitial(self):
        '''analyse settings for sigma and filter
        return True if they are equal to those of last preprocess'''
        if self.initialFilter is None:
            return False        
        if self.Filter.value != self.initialFilter:
            return False
        print self.Sigma.value
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
        
        #temp - temp - temp - temp - temp - temp - temp - temp
        if self.applet.ThorbenGraph is not None:
            result[0] = self.applet.ThorbenGraph
            self._prepData = result
            return result
        #/temp - temp - temp - temp - temp - temp - temp - temp 
        
        volume5d = self.RawData.value
        sigma = self.Sigma.value
        
        #Hack: Remove Channel
        volume = numpy.add.reduce(volume5d,3)
        
        print "input volume shape: ", volume.shape
        print "input volume size: ", volume.nbytes / 1024**2, "MB"
        fvol = volume.astype(numpy.float32)

        #Choose filter selected by user
        volume_filter = self.Filter.value
        
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
        print "Watershed..."
        self.applet.progressSignal.emit(0)
        labelVolume = vigra.analysis.watersheds(volume_feat)[0].astype(numpy.int32)
        
        
        self.applet.progress = 0
        def updateProgressBar(x):
            #send signal iff progress is significant
            if x-self.applet.progress>1 or x==100:
                self.applet.progressSignal.emit(x)
                self.applet.progress = x
        
        mst= MSTSegmentor(labelVolume, volume_feat.astype(numpy.float32), edgeWeightFunctor = "minimum",progressCallback = updateProgressBar)
        mst.raw = volume
        
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
