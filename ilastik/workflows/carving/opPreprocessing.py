#Python
import sys

#SciPy
import numpy
import vigra

#lazyflow
from lazyflow.roi import roiFromShape
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpArrayCache

#carving Cython module
from cylemon.segmentation import MSTSegmentor

class OpFilter(Operator):
    Input = InputSlot()
    Filter = InputSlot(value=0)
    Sigma = InputSlot(value=1.6)
    
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.dtype = numpy.float32
    
    def execute(self, slot, subindex, roi, result):
        #make sure raw data is 5D: t,{x,y,z},c 
        ax = self.Input.meta.axistags
        sh = self.Input.meta.shape
        assert len(ax) == 5
        assert ax[0].key == "t" and sh[0] == 1
        for i in range(1,4):
            assert ax[i].isSpatial()
        assert ax[4].key == "c" and sh[4] == 1
        
        volume5d = self.Input.value
        sigma = self.Sigma.value
        volume = volume5d[0,:,:,:,0]
        result_view = result[0,:,:,:,0]
        
        print "input volume shape: ", volume.shape
        print "input volume size: ", volume.nbytes / 1024**2, "MB"
        fvol = volume.astype(numpy.float32)

        #Choose filter selected by user
        volume_filter = self.Filter.value
        
        print "applying filter", fvol.shape
        if fvol.shape[2] > 1:
            # true 3D volume
            if volume_filter == 0:
                print "lowest eigenvalue of Hessian of Gaussian"
                result_view[...] = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,:,2]
                result_view[:] = numpy.max(result_view) - result_view
            
            elif volume_filter == 1:
                print "greatest eigenvalue of Hessian of Gaussian"
                result_view[...] = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,:,0]
                 
            elif volume_filter == 2:
                print "Gaussian Gradient Magnitude"
                result_view[...] = vigra.filters.gaussianGradientMagnitude(fvol,sigma)
                
            elif volume_filter == 3:
                print "Gaussian Smoothing"
                result_view[...] = vigra.filters.gaussianSmoothing(fvol,sigma)
                
            elif volume_filter == 4:
                print "negative Gaussian Smoothing"
                result_view[...] = vigra.filters.gaussianSmoothing(-fvol,sigma)

            volume_ma = numpy.max(result_view[...])
            volume_mi = numpy.min(result_view[...])
            result_view[...] = (result_view - volume_mi) * 255.0 / (volume_ma-volume_mi)

        else:
            # 2D Image
            fvol = fvol[:,:,0]
            if volume_filter == 0:
                print "lowest eigenvalue of Hessian of Gaussian"
                volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,1]
                result_view[:] = numpy.max(result_view) - result_view
            
            elif volume_filter == 1:
                print "greatest eigenvalue of Hessian of Gaussian"
                volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,0]
                 
            elif volume_filter == 2:
                print "Gaussian Gradient Magnitude"
                volume_feat = vigra.filters.gaussianGradientMagnitude(fvol,sigma)
                
            elif volume_filter == 3:
                print "Gaussian Smoothing"
                volume_feat = vigra.filters.gaussianSmoothing(fvol,sigma)
                
            elif volume_filter == 4:
                print "negative Gaussian Smoothing"
                volume_feat = vigra.filters.gaussianSmoothing(-fvol,sigma)
        
            fvol = fvol[:,:,numpy.newaxis]
            volume_feat = volume_feat[:,:,numpy.newaxis]
            volume_ma = numpy.max(volume_feat)
            volume_mi = numpy.min(volume_feat)
            volume_feat = (volume_feat - volume_mi) * 255.0 / (volume_ma-volume_mi)
            result_view[...] = volume_feat
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))

class OpSimpleWatershed(Operator):
    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.int32

    def execute(self, slot, subindex, roi, result):
        assert roi.stop - roi.start == self.Output.meta.shape, "Watershed must be run on the entire volume."
        input_image = self.Input(roi.start, roi.stop).wait()
        volume_feat = input_image[0,...,0]
        result_view = result[0,...,0]
        if self.Input.meta.getTaggedShape()['z'] > 1:
            sys.stdout.write("Watershed..."); sys.stdout.flush()
            result_view[...] = vigra.analysis.watersheds(volume_feat[:,:])[0].astype(numpy.int32)
            print "done" ,numpy.max(result[...])
        else:
            sys.stdout.write("Watershed..."); sys.stdout.flush()
            labelVolume = vigra.analysis.watersheds(volume_feat[:,:,0])[0].astype(numpy.int32)
            result_view[...] = labelVolume[:,:,numpy.newaxis]
            print "done" ,numpy.max(labelVolume)
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))
    
class OpMstSegmentorProvider(Operator):
    Image = InputSlot()
    LabelImage = InputSlot()
    
    MST = OutputSlot(stype='object')
    
    def __init__(self, applet, *args, **kwargs):
        super( OpMstSegmentorProvider, self ).__init__(*args, **kwargs)
        self.applet = applet
    
    def setupOutputs(self):
        self.MST.meta.shape = (1,)
        self.MST.meta.dtype = object

    def execute(self,slot,subindex,roi,result):
        assert slot == self.MST, "Invalid output slot: {}".format(slot.name)
        #first thing, show the user that we are waiting for computations to finish        
        self.applet.progressSignal.emit(0)
        
        volume_feat = self.Image( *roiFromShape( self.Image.meta.shape ) ).wait()
        labelVolume = self.LabelImage( *roiFromShape( self.LabelImage.meta.shape ) ).wait()

        self.applet.progress = 0
        def updateProgressBar(x):
            #send signal iff progress is significant
            if x-self.applet.progress>1 or x==100:
                self.applet.progressSignal.emit(x)
                self.applet.progress = x
        
        mst= MSTSegmentor(labelVolume[0,...,0], volume_feat[0,...,0].astype(numpy.float32), edgeWeightFunctor = "minimum",progressCallback = updateProgressBar)
        #mst.raw is not set here in order to avoid redundant data storage 
        mst.raw = None
        
        #Output is of shape 1
        result[0] = mst
        
        return result        

    def propagateDirty(self, slot, subindex, roi):
        self.MST.setDirty(slice(None))

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
    
    # Display outputs
    FilteredImage = OutputSlot()
    WatershedImage = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpPreprocessing, self).__init__(*args, **kwargs)
        self._prepData = [None]
        self.applet = self.parent.parent.preprocessingApplet
        
        self._unsavedData = False # set to True if data is not yet saved
        self._dirty = False       # set to True if any Input is dirty
         
         
        self.initialSigma = None  # save settings of last preprocess
        self.initialFilter = None # applied to gui by pressing reset
        
        self._opFilter = OpFilter(parent=self)
        self._opFilter.Input.connect( self.RawData )
        self._opFilter.Sigma.connect( self.Sigma )
        self._opFilter.Filter.connect( self.Filter )
        
        self._opFilterCache = OpArrayCache( parent=self )
        
        self._opWatershed = OpSimpleWatershed( parent=self )
        self._opWatershed.Input.connect( self._opFilterCache.Output )
        
        self._opWatershedCache = OpArrayCache( parent=self )

        self._opMstProvider = OpMstSegmentorProvider( self.applet, parent=self )
        self._opMstProvider.Image.connect( self._opFilterCache.Output )
        self._opMstProvider.LabelImage.connect( self._opWatershedCache.Output )

        #self.PreprocessedData.connect( self._opMstProvider.MST )
        
        # Display slots
        self.FilteredImage.connect( self._opFilterCache.Output )
        self.WatershedImage.connect( self._opWatershedCache.Output )
        
    def setupOutputs(self):
        self._checkMeta(self.RawData)
        self.PreprocessedData.meta.shape = (1,)
        self.PreprocessedData.meta.dtype = object

        self._opFilterCache.blockShape.setValue( self.RawData.meta.shape )
        self._opFilterCache.Input.connect( self._opFilter.Output )

        self._opWatershedCache.blockShape.setValue( self._opWatershed.Output.meta.shape )
        self._opWatershedCache.Input.connect( self._opWatershed.Output )

    def execute(self,slot,subindex,roi,result):
        assert slot == self.PreprocessedData, "Invalid output slot"
        if self._prepData[0] is not None and not self._dirty:
            return self._prepData
        
        mst = self._opMstProvider.MST.value
        
        #save settings for reloading them if asked by user
        self.initialSigma = self.Sigma.value
        self.initialFilter = self.Filter.value
        self.enableReset(False)
        self._unsavedData = True
        self._dirty = False
        self.enableDownstream(True)
        
        # copy over seeds, and saved objects
        if self._prepData[0] is not None:
            mst.seeds[:] = self._prepData[0].seeds[:]
            mst.object_lut = self._prepData[0].object_lut
            mst.object_names = self._prepData[0].object_names
            mst.object_seeds_bg_voxels = self._prepData[0].object_seeds_bg_voxels
            mst.object_seeds_fg_voxels = self._prepData[0].object_seeds_fg_voxels
            mst.bg_priority = self._prepData[0].bg_priority
            mst.no_bias_below = self._prepData[0].no_bias_below
            
        
        #Cache result
        self._prepData = result
        
        #Wonder why this is set?
        #The preprocess is only called by the run button.
        #By setting the output dirty, this event is propagated to the
        #carving-Operator, who copies the result just calculated.
        #This is to gain control over when the preprocess is executed.
        #self.PreprocessedData.setDirty()
        
        result[0] = mst
        return result

    
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
    

