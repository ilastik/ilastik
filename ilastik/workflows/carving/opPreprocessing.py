from __future__ import absolute_import
from __future__ import division
###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
#Python
from builtins import range
from past.utils import old_div
import sys

#SciPy
import numpy
import vigra

#lazyflow
from lazyflow.roi import roiFromShape
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpBlockedArrayCache

from lazyflow.request import Request

from lazyflow.utility.timer import Timer
from ilastik.applets.base.applet import DatasetConstraintError

#carving backend in ilastiktools
from .watershed_segmentor import WatershedSegmentor

from .carvingTools import simple_parallel_ws

import logging
logger = logging.getLogger(__name__)

class OpFilter(Operator):
    HESSIAN_BRIGHT = 0
    HESSIAN_DARK = 1
    STEP_EDGES = 2
    RAW = 3
    RAW_INVERTED = 4

    Input = InputSlot()
    Filter = InputSlot(value=HESSIAN_BRIGHT)
    Sigma = InputSlot(value=1.6)
    
    Overlay = InputSlot(optional=True) # GUI-only.  Shown over raw data if available.
    
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
        
        logger.info( "input volume shape: %r" %  (volume.shape,) )
        logger.info( "input volume size: %r MB", (old_div(volume.nbytes, 1024**2),) )
        fvol = numpy.asarray(volume, numpy.float32)

        #Choose filter selected by user
        volume_filter = self.Filter.value

        logger.info( "applying filter on shape = %r" % (fvol.shape,) )
        with Timer() as filterTimer:        
            if fvol.shape[2] > 1:
                # true 3D volume
                if volume_filter == OpFilter.HESSIAN_BRIGHT:
                    logger.info( "lowest eigenvalue of Hessian of Gaussian" )
                    options = vigra.blockwise.BlockwiseConvolutionOptions3D()
                    options.stdDev = (sigma, )*3 
                    result_view[...] = vigra.blockwise.hessianOfGaussianLastEigenvalue(fvol,options)[:,:,:]
                    result_view[:] = numpy.max(result_view) - result_view
                
                elif volume_filter == OpFilter.HESSIAN_DARK:
                    logger.info( "greatest eigenvalue of Hessian of Gaussian" )
                    options = vigra.blockwise.BlockwiseConvolutionOptions3D()
                    options.stdDev = (sigma, )*3 
                    result_view[...] = vigra.blockwise.hessianOfGaussianFirstEigenvalue(fvol,options)[:,:,:]
                     
                elif volume_filter == OpFilter.STEP_EDGES:
                    logger.info( "Gaussian Gradient Magnitude" )
                    result_view[...] = vigra.filters.gaussianGradientMagnitude(fvol,sigma)
                    
                elif volume_filter == OpFilter.RAW:
                    logger.info( "Gaussian Smoothing" )
                    result_view[...] = vigra.filters.gaussianSmoothing(fvol,sigma)
                    
                elif volume_filter == OpFilter.RAW_INVERTED:
                    logger.info( "negative Gaussian Smoothing" )
                    result_view[...] = vigra.filters.gaussianSmoothing(-fvol,sigma)

                logger.info( "Filter took {} seconds".format( filterTimer.seconds() ) )
            else:
                # 2D Image
                fvol = fvol[:,:,0]
                if volume_filter == OpFilter.HESSIAN_BRIGHT:
                    logger.info( "lowest eigenvalue of Hessian of Gaussian" )
                    volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,1]
                    volume_feat[:] = numpy.max(volume_feat) - volume_feat
                
                elif volume_filter == OpFilter.HESSIAN_DARK:
                    logger.info( "greatest eigenvalue of Hessian of Gaussian" )
                    volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,0]
                     
                elif volume_filter == OpFilter.STEP_EDGES:
                    logger.info( "Gaussian Gradient Magnitude" )
                    volume_feat = vigra.filters.gaussianGradientMagnitude(fvol,sigma)
                    
                elif volume_filter == OpFilter.RAW:
                    logger.info( "Gaussian Smoothing" )
                    volume_feat = vigra.filters.gaussianSmoothing(fvol,sigma)
                    
                elif volume_filter == OpFilter.RAW_INVERTED:
                    logger.info( "negative Gaussian Smoothing" )
                    volume_feat = vigra.filters.gaussianSmoothing(-fvol,sigma)

                result_view[:,:,0] = volume_feat
                logger.info( "Filter took {} seconds".format( filterTimer.seconds() ) )
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))

class OpNormalize255(Operator):
    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom( self.Input.meta )
    
    def execute(self, slot, subindex, roi, result):
        # Save memory: use result as a temporary
        self.Input( roi.start, roi.stop ).writeInto(result).wait()
        volume_max = numpy.max(result)
        volume_min = numpy.min(result)

        # result[...] = (result - volume_min) * 255.0 / (volume_max-volume_min)
        # Avoid temporaries...
        result[:] -= volume_min
        result[:] *= 255.0
        result[:] /= (volume_max - volume_min)
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(roi.start, roi.stop)

class OpSimpleWatershed(Operator):
    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.uint32

    def execute(self, slot, subindex, roi, result):
        assert roi.stop - roi.start == self.Output.meta.shape, "Watershed must be run on the entire volume."
        input_image = self.Input(roi.start, roi.stop).wait()
        volume_feat = input_image[0,...,0]
        result_view = result[0,...,0]
        with Timer() as watershedTimer:
            if self.Input.meta.getTaggedShape()['z'] > 1:
                sys.stdout.write("Watershed..."); sys.stdout.flush()
                #result_view[...] = vigra.analysis.watersheds(volume_feat[:,:])[0].astype(numpy.int32)
                result_view[...] = vigra.analysis.watershedsNew(volume_feat[:,:].astype(numpy.uint8))[0]
                logger.info( "done {}".format(numpy.max(result[...]) ) )
            else:
                sys.stdout.write("Watershed..."); sys.stdout.flush()
                
                labelVolume = vigra.analysis.watershedsNew(volume_feat[:,:,0])[0]#.view(dtype=numpy.int32)
                result_view[...] = labelVolume[:,:,numpy.newaxis]
                logger.info( "done {}".format(numpy.max(labelVolume)) )

        logger.info( "Watershed took {} seconds".format( watershedTimer.seconds() ) )
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))

class OpSimpleBlockwiseWatershed(Operator):
    Input = InputSlot()
    Output = OutputSlot()

    DoAgglo           = InputSlot(value = 1)
    SizeRegularizer   = InputSlot(value = 0.5)
    ReduceTo          = InputSlot(value = 0.2)


    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.uint32

    def execute(self, slot, subindex, roi, result):
        assert roi.stop - roi.start == self.Output.meta.shape, "Blockwise Watershed must be run on the entire volume."
        input_image = self.Input(roi.start, roi.stop).wait()
        volume_feat = input_image[0,...,0]
        result_view = result[0,...,0]
        with Timer() as watershedTimer:
            if self.Input.meta.getTaggedShape()['z'] > 1:
                sys.stdout.write("Blockwise Watershed 3D..."); sys.stdout.flush()

                if not self.DoAgglo.value:
                    result_view[...] = vigra.analysis.watersheds(volume_feat[...])[0].astype(numpy.int32)

                else:
                    result_view[...] = simple_parallel_ws(
                        volume_feat,
                        max_workers=Request.global_thread_pool.num_workers,
                        size_regularizer=self.SizeRegularizer.value,
                        reduce_to=self.ReduceTo.value)
                logger.info( "done {}".format(numpy.max(result[...]) ) )
            else:
                if not self.DoAgglo.value:
                    result_view[...] = vigra.analysis.watersheds(volume_feat[:,:,0])[0].astype(numpy.int32)
                else:
                    sys.stdout.write("Blockwise Watershed..."); sys.stdout.flush()
                    labelVolume = simple_parallel_ws(
                        volume_feat[:, :, 0],
                        max_workers=Request.global_thread_pool.num_workers,
                        size_regularizer=self.SizeRegularizer.value,
                        reduce_to=self.ReduceTo.value)
                    result_view[...] = labelVolume[:,:,numpy.newaxis]
                logger.info( "done {}".format(numpy.max(labelVolume)) )

        logger.info( "Blockwise Watershed took {} seconds".format( watershedTimer.seconds() ) )
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
        self.applet.progressSignal(-1)
        try:
            volume_feat = self.Image( *roiFromShape( self.Image.meta.shape ) ).wait()
            labelVolume = self.LabelImage( *roiFromShape( self.LabelImage.meta.shape ) ).wait()

            self.applet.progress = 0
            def updateProgressBar(x):
                #send signal iff progress is significant
                if x-self.applet.progress>1 or x==100:
                    self.applet.progressSignal(x)
                    self.applet.progress = x

           #mst= MSTSegmentor(labelVolume[0,...,0],
           #                  numpy.asarray(volume_feat[0,...,0], numpy.float32),
           #                  edgeWeightFunctor = "minimum",
           #                  progressCallback = updateProgressBar)
           ##mst.raw is not set here in order to avoid redundant data storage
           #mst.raw = None

            newMst = WatershedSegmentor(labelVolume[0,...,0],numpy.asarray(volume_feat[0,...,0], numpy.float32),
                              edgeWeightFunctor = "minimum",progressCallback = updateProgressBar)

            #Output is of shape 1
            #result[0] = mst
            newMst.raw = None
            result[0] = newMst
            return result

        finally:
            self.applet.progressSignal(100)

    def propagateDirty(self, slot, subindex, roi):
        self.MST.setDirty(slice(None))

class OpPreprocessing(Operator):
    """
    The top-level operator for the pre-procession applet
    """
    name = "Preprocessing"
    
    #Image before preprocess
    OverlayData = InputSlot(optional=True)
    InputData = InputSlot()
    Sigma = InputSlot(value = 1.6)
    Filter = InputSlot(value = 0)
    WatershedSource = InputSlot(value="filtered") # Choices: "raw", "input", "filtered"
    InvertWatershedSource = InputSlot(value=False)
    
    DoAgglo           = InputSlot(value = 1)
    SizeRegularizer   = InputSlot(value = 0.5)
    ReduceTo          = InputSlot(value = 0.2)

    #Image after preprocess 
    PreprocessedData = OutputSlot()
    
    # Display outputs
    FilteredImage = OutputSlot()
    WatershedImage = OutputSlot()
    WatershedSourceImage = OutputSlot()

    # OverlayData ---- opOverlayFilter* -----> opOverlayNormalize ------                                                                  --> WatershedImage
    #                                                                   \                                                                /
    # InputData --> -- opInputFilter*--------> opInputNormalize -------> (SELECT by WatershedSource) --> opWatershed --> opWatershedCache --> opMstProvider --> [via execute()] --> PreprocessedData
    #              \                                                    /                                                                    /
    # Sigma ------> opFilter --> opFilterNormalize --> opFilterCache --> --------------------------------------------------------------------
    #              /                                                \
    # Filter ------                                                  --> FilteredImage

    # *note: Raw/Input filters used for inversion and smoothing only.
    
    def __init__(self, *args, **kwargs):
        super(OpPreprocessing, self).__init__(*args, **kwargs)
        self._prepData = [None]
        self.applet = self.parent.parent.preprocessingApplet
        
        self._unsavedData = False # set to True if data is not yet saved
        self._dirty = False       # set to True if any Input is dirty
         
         
        self.initialSigma = None  # save settings of last preprocess
        self.initialFilter = None # applied to gui by pressing reset
        self.initialDoAgglo = None
        self.initialSizeRegularizer = None
        self.initialReduceTo = None
        
        self._opFilter = OpFilter(parent=self)
        self._opFilter.Input.connect( self.InputData )
        self._opFilter.Sigma.connect( self.Sigma )
        self._opFilter.Filter.connect( self.Filter )

        self._opFilterNormalize = OpNormalize255( parent=self )
        self._opFilterNormalize.Input.connect( self._opFilter.Output )
        
        self._opFilterCache = OpBlockedArrayCache( parent=self )
        
        self._opWatershed = OpSimpleBlockwiseWatershed( parent=self )
        self._opWatershed.DoAgglo.connect( self.SizeRegularizer )
        self._opWatershed.ReduceTo.connect( self.ReduceTo )
        self._opWatershed.SizeRegularizer.connect( self.SizeRegularizer )
        
        self._opWatershedCache = OpBlockedArrayCache( parent=self )
        
        self._opOverlayFilter = OpFilter( parent=self )
        self._opOverlayFilter.Input.connect( self.OverlayData )
        self._opOverlayFilter.Sigma.connect( self.Sigma )
        
        self._opOverlayNormalize = OpNormalize255( parent=self )
        self._opOverlayNormalize.Input.connect( self._opOverlayFilter.Output )
        
        self._opInputFilter = OpFilter( parent=self )
        self._opInputFilter.Input.connect( self.InputData )
        self._opInputFilter.Sigma.connect( self.Sigma )

        self._opInputNormalize = OpNormalize255( parent=self )
        self._opInputNormalize.Input.connect( self._opInputFilter.Output )
        
        self._opMstProvider = OpMstSegmentorProvider( self.applet, parent=self )
        self._opMstProvider.Image.connect( self._opFilterCache.Output )
        self._opMstProvider.LabelImage.connect( self._opWatershedCache.Output )

        self._opWatershedSourceCache = OpBlockedArrayCache( parent=self )

        #self.PreprocessedData.connect( self._opMstProvider.MST )
        
        # Display slots
        self.FilteredImage.connect( self._opFilterCache.Output )
        self.WatershedImage.connect( self._opWatershedCache.Output )
        
        self.InputData.notifyReady( self._checkConstraints )
        
    def _checkConstraints(self, *args):
        slot = self.InputData
        numChannels = slot.meta.getTaggedShape()['c']
        if numChannels != 1:
            raise DatasetConstraintError(
                "Carving",
                "Input image must have exactly one channel.  " +
                "You attempted to add a dataset with {} channels".format( numChannels ) )
        
        sh = slot.meta.shape
        ax = slot.meta.axistags
        if len(slot.meta.shape) != 5:
            # Raise a regular exception.  This error is for developers, not users.
            raise RuntimeError("was expecting a 5D dataset, got shape=%r" % (sh,))
        if slot.meta.getTaggedShape()['t'] != 1:
            raise DatasetConstraintError(
                "Carving",
                "Input image must not have more than one time slice.  " +
                "You attempted to add a dataset with {} time slices".format( slot.meta.getTaggedShape()['t'] ) )
        
        for i in range(1,4):
            if not ax[i].isSpatial():
                # This is for developers.  Don't need a user-friendly error.
                raise RuntimeError("%d-th axis %r is not spatial" % (i, ax[i]))

            
    def setupOutputs(self):
        self.PreprocessedData.meta.shape = (1,)
        self.PreprocessedData.meta.dtype = object

        self._opFilterCache.BlockShape.setValue( self.InputData.meta.shape )
        self._opFilterCache.Input.connect( self._opFilterNormalize.Output )

        # If the user's boundaries are dark, then invert the special watershed sources
        if self.InvertWatershedSource.value:
            self._opOverlayFilter.Filter.setValue( OpFilter.RAW_INVERTED )
            self._opInputFilter.Filter.setValue( OpFilter.RAW_INVERTED )
        else:
            self._opOverlayFilter.Filter.setValue( OpFilter.RAW )
            self._opInputFilter.Filter.setValue( OpFilter.RAW )

        ws_source = self.WatershedSource.value
        if ws_source == 'raw':
            if self.OverlayData.ready():
                self._opWatershed.Input.connect( self._opOverlayNormalize.Output )
            else:
                self._opWatershed.Input.connect( self._opInputNormalize.Output )
        elif ws_source == 'input':
            self._opWatershed.Input.connect( self._opInputNormalize.Output )
        elif ws_source == 'filtered':
            self._opWatershed.Input.connect( self._opFilterCache.Output )
        else:
            assert False, "Unknown Watershed source option: {}".format( ws_source )

        self._opWatershedSourceCache.BlockShape.setValue( self.InputData.meta.shape )
        self._opWatershedSourceCache.Input.connect( self._opWatershed.Input )

        self.WatershedSourceImage.connect( self._opWatershedSourceCache.Output )

        self._opWatershedCache.BlockShape.setValue( self._opWatershed.Output.meta.shape )
        self._opWatershedCache.Input.connect( self._opWatershed.Output )


    def execute(self,slot,subindex,roi,result):
        assert slot == self.PreprocessedData, "Invalid output slot"
        if self._prepData[0] is not None and not self._dirty:
            return self._prepData
        
        mst = self._opMstProvider.MST.value
        
        #save settings for reloading them if asked by user
        self.initialSigma = self.Sigma.value
        self.initialFilter = self.Filter.value
        self.initalDoAgglo = self.DoAgglo.value
        self.initalReduceTo = self.ReduceTo.value
        self.initalSizeRegularizer = self.SizeRegularizer.value

        self.enableReset(False)
        self._unsavedData = True
        self._dirty = False
        self.enableDownstream(True)
        
        # copy over seeds, and saved objects
        if self._prepData[0] is not None:
            #mst.seeds[:] = self._prepData[0].seeds[:]
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

    
    def AreSettingsInitial(self):
        '''analyse settings for sigma and filter
        return True if they are equal to those of last preprocess'''
        if self.initialFilter is None:
            return False        
        if self.Filter.value != self.initialFilter:
            return False
        if self.DoAgglo.value != self.initialDoAgglo:
            return False
        if abs(self.Sigma.value - self.initialSigma)>0.005:
            return False
        if abs(self.ReduceTo.value - self.initialReduceTo)>0.005:
            return False
        if abs(self.SizeRegularizer.value - self.initalSizeRegularizer)>0.005:
            return False
        return True
    
    def propagateDirty(self,slot,subindex,roi):
        if slot == self.InputData:
            #complete restart
            #No values will be reused any more
            self.initialSigma = None
            self.initialFilter = None
            self.initialDoAgglo = None
            self.initialSizeRegularizer = None
            self.initialReduceTo = None
            self._prepData = [None]
        
        ws_source_changed = False
        if slot == self.WatershedSource or \
          (slot == self.Filter and self.WatershedSource.value == 'filtered') or \
           slot == self.InvertWatershedSource:
            self._opWatershed.Input.setDirty(slice(None))
            ws_source_changed = True
        
        if not ws_source_changed and self.AreSettingsInitial():
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

    

