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
import os
import sys
import threading

#SciPy
import numpy
import vigra

#lazyflow
from lazyflow.roi import getIntersectingBlocks, getBlockBounds, roiFromShape, roiToSlice, enlargeRoiForHalo, TinyVector
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpBlockedArrayCache
from lazyflow.operators.opBlockedHdf5Cache import OpBlockedHdf5Cache
from lazyflow.request import RequestLock
from lazyflow.utility.timer import Timer
from lazyflow.utility import Memory

# ilastik
from ilastik.config import cfg as ilastik_config
from ilastik.applets.base.applet import DatasetConstraintError

#carving tools
from watershed_segmentor import WatershedSegmentor

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

        #User selected values
        sigma = self.Sigma.value
        volume_filter = self.Filter.value

        roi_halo, roi_orig = enlargeRoiForHalo(roi.start, roi.stop, self.Input.meta.shape, sigma, return_result_roi=True)

        volume5d = self.Input(*roi_halo).wait()
        volume = volume5d[0,:,:,:,0]
        result_view = result[0,:,:,:,0]
        
        logger.info( "Filter input volume shape: %r, size: %r MB, roi: %s" % (volume.shape, volume.nbytes / 1024**2, roi) )

        fvol = numpy.asarray(volume, numpy.float32)

        logger.info( " applying filter on shape: %r, size: %r MB" % (fvol.shape, fvol.nbytes / 1024**2 ) )
        with Timer() as filterTimer:
            if fvol.shape[2] > 1:
                # true 3D volume
                roi_orig_slice = roiToSlice(*roi_orig)[1:-1]
                if volume_filter == OpFilter.HESSIAN_BRIGHT:
                    logger.info( " lowest eigenvalue of Hessian of Gaussian" )
                    options = vigra.blockwise.BlockwiseConvolutionOptions3D()
                    options.stdDev = (sigma, )*3
                    result_view[...] = vigra.blockwise.hessianOfGaussianLastEigenvalue(fvol,options)[roi_orig_slice]
                    #TODO: fix local inversion; should be global max - result_view
                    result_view[:] = numpy.max(result_view) - result_view
                
                elif volume_filter == OpFilter.HESSIAN_DARK:
                    logger.info( " greatest eigenvalue of Hessian of Gaussian" )
                    options = vigra.blockwise.BlockwiseConvolutionOptions3D()
                    options.stdDev = (sigma, )*3
                    result_view[...] = vigra.blockwise.hessianOfGaussianFirstEigenvalue(fvol,options)[roi_orig_slice]

                elif volume_filter == OpFilter.STEP_EDGES:
                    logger.info( " Gaussian Gradient Magnitude" )
                    result_view[...] = vigra.filters.gaussianGradientMagnitude(fvol,sigma)[roi_orig_slice]
                    
                elif volume_filter == OpFilter.RAW:
                    logger.info( " Gaussian Smoothing" )
                    result_view[...] = vigra.filters.gaussianSmoothing(fvol,sigma)[roi_orig_slice]
                    
                elif volume_filter == OpFilter.RAW_INVERTED:
                    logger.info( " negative Gaussian Smoothing" )
                    result_view[...] = vigra.filters.gaussianSmoothing(-fvol,sigma)[roi_orig_slice]
            else:
                # 2D Image
                roi_orig_slice = roiToSlice(*roi_orig)[1:-2]
                fvol = fvol[:,:,0]
                if volume_filter == OpFilter.HESSIAN_BRIGHT:
                    logger.info( " lowest eigenvalue of Hessian of Gaussian" )
                    volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[roi_orig_slice][:,:,1]
                    #TODO: fix local inversion; should be global max - result_view
                    volume_feat[:] = numpy.max(volume_feat) - volume_feat
                
                elif volume_filter == OpFilter.HESSIAN_DARK:
                    logger.info( " greatest eigenvalue of Hessian of Gaussian" )
                    volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[roi_orig_slice][:,:,0]
                     
                elif volume_filter == OpFilter.STEP_EDGES:
                    logger.info( " Gaussian Gradient Magnitude" )
                    volume_feat = vigra.filters.gaussianGradientMagnitude(fvol,sigma)[roi_orig_slice]
                    
                elif volume_filter == OpFilter.RAW:
                    logger.info( " Gaussian Smoothing" )
                    volume_feat = vigra.filters.gaussianSmoothing(fvol,sigma)[roi_orig_slice]
                    
                elif volume_filter == OpFilter.RAW_INVERTED:
                    logger.info( " negative Gaussian Smoothing" )
                    volume_feat = vigra.filters.gaussianSmoothing(-fvol,sigma)[roi_orig_slice]

                result_view[:, :, 0] = volume_feat

            logger.info( "Filter took {} seconds".format( filterTimer.seconds() ) )

        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))


class OpBlockwiseTotalStats(Operator):
    MINIMUM = 'minimum'
    MAXIMUM = 'maximum'

    Input = InputSlot()
    Output = OutputSlot(stype='object')

    def __init__(self, blockSize, *args, **kwargs):
        super( OpBlockwiseTotalStats, self ).__init__(*args, **kwargs)
        self._lock = RequestLock()
        self._blockSize = blockSize
        self._stats = None

    def setupOutputs(self):
        self.Output.meta.shape = (1,)
        self.Output.meta.dtype = object

    def execute(self, slot, subindex, unused_roi, result):
        assert slot == self.Output, "Invalid output slot: {}".format(slot.name)

        # result was cached
        if self._stats:
            result[0] = self._stats
            return result

        with self._lock:
            if not self._stats:
                # calculate stats
                with Timer() as statsTimer:
                    stats = {self.MINIMUM:sys.float_info.max, self.MAXIMUM:sys.float_info.min}
                    bsz = self._blockSize
                    block_shape = (1,bsz,bsz,bsz,1)
                    block_starts = getIntersectingBlocks( block_shape, roiFromShape(self.Input.meta.shape) )
                    block_count = len(block_starts)
                    for b_id, block in enumerate(block_starts):
                        input_roi = getBlockBounds(self.Input.meta.shape, block_shape, block)
                        inputVolume = self.Input( *input_roi ).wait()

                        stats[self.MINIMUM] = min(stats[self.MINIMUM], numpy.min(inputVolume))
                        stats[self.MAXIMUM] = max(stats[self.MAXIMUM], numpy.max(inputVolume))

                    # stats go live, and are immediately available to all threads
                    self._stats = stats

                    logger.info( "Calculated stats on {} blocks took {} seconds".format( block_count, statsTimer.seconds() ) )
                    logger.info( "  stats: {}: {}, {}: {}".format(
                                self.MINIMUM, self._stats[self.MINIMUM],
                                self.MAXIMUM, self._stats[self.MAXIMUM]) )

        # stats were calculated
        result[0] = self._stats
        return result

    def propagateDirty(self, slot, subindex, unused_roi):
        self._stats = None
        self.Output.setDirty(slice(None))


class OpNormalize255(Operator):
    MINIMUM = 'minimum'
    MAXIMUM = 'maximum'

    Input = InputSlot()
    TotalStats = InputSlot(value={MINIMUM:-128.0, MAXIMUM:127.0})
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom( self.Input.meta )
    
    def execute(self, slot, subindex, roi, result):
        # Save memory: use result as a temporary
        self.Input( roi.start, roi.stop ).writeInto(result).wait()

        stats = self.TotalStats().wait()[0]
        offset = -(stats[self.MINIMUM])
        range = (stats[self.MAXIMUM] - stats[self.MINIMUM])

        # result[...] = (result + offset) * (255.0 / range)
        # Avoid temporaries...
        result[:] += offset
        result[:] *= (255.0 / range)
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))


class OpSimpleWatershed(Operator):
    Input = InputSlot()
    Output = OutputSlot()

    # NOTE: Watershed operator depends on Output being completely cached;
    #       assumes watersheds are only calculated once per region;
    #       does not work with re-calculated blocks.
    #       The vigra.watershedsNew operator correctly calculates
    #       unique local label IDs, but we need globally unique IDs.
    #       When processing blockwise we offset each new local block
    #       by the previous max label ID, producing a contiguous sequence
    #       of globally unique IDs; however, with the usage restrictions
    #       specified above.
    _maxSeedValue = 0 # the largest seed value found so far
    _maxSeedValueLock = threading.Lock()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.uint32

    def execute(self, slot, subindex, roi, result):
        input_image = self.Input(roi.start, roi.stop).wait()
        volume_feat = input_image[0,...,0]
        result_view = result[0,...,0]
        with Timer() as watershedTimer:
            sys.stdout.write("Watershed..."); sys.stdout.flush()

            if self.Input.meta.getTaggedShape()['z'] > 1:
                result_view[...] = vigra.analysis.watershedsNew(volume_feat[:,:].astype(numpy.uint8))[0]
            else:
                labelVolume = vigra.analysis.watershedsNew(volume_feat[:,:,0])[0]
                result_view[...] = labelVolume[:,:,numpy.newaxis]

            result_min = numpy.min(result[...])
            result_max = numpy.max(result[...])
            result_range = (result_max - result_min) + 1

            with self._maxSeedValueLock:
                old_max_seed_value = self._maxSeedValue
                self._maxSeedValue += result_range

            result_view[...] += old_max_seed_value

            logger.info( "Watershed took {} seconds - calculated range {}: {}-{}, offset {}, roi: {}".format(watershedTimer.seconds(), result_range, result_min, result_max, old_max_seed_value, roi))

        return result

    def propagateDirty(self, slot, subindex, roi):
        self._maxSeedValue = 0
        self.Output.setDirty(slice(None))


class OpMstSegmentorProvider(Operator):
    Image = InputSlot()
    LabelImage = InputSlot()
    
    MST = OutputSlot(stype='object')
    
    def __init__(self, applet, blockSize, *args, **kwargs):
        super( OpMstSegmentorProvider, self ).__init__(*args, **kwargs)
        self.applet = applet
        self._blockSize = blockSize

    def setupOutputs(self):
        self.MST.meta.shape = (1,)
        self.MST.meta.dtype = object

    def execute(self, slot, subindex, unused_roi, result):
        assert slot == self.MST, "Invalid output slot: {}".format(slot.name)

        #first thing, show the user that we are waiting for computations to finish
        self.applet.progressSignal.emit(-1)
        self.applet.progress = 0
        def updateProgressBar(blk, max_blk, roi, mst, timer):
            #send signal iff progress is significant
            p = int(((blk + 1) * 100) / max_blk)
            if p-self.applet.progress>=1 or p==100:
                self.applet.progressSignal.emit(p)
                self.applet.progress = p

            gridSeg = mst.gridSegmentor

            logger.info( "Segmentor preprocessed block: {} out of {}, took {} seconds".format( blk + 1, max_blk, timer.seconds() ) )
            logger.info( "  roi: {}".format(roi) )
            logger.info( "  mst: nodes: {} (max id: {}), edges: {} (max id: {})".format(
                        gridSeg.nodeNum(), gridSeg.maxNodeId(),
                        gridSeg.edgeNum(), gridSeg.maxEdgeId()) )
            logger.info( "  memory: used {} out of {} total avail (cache: {}, compute: {})".format(
                        Memory.format(Memory.getMemoryUsage()),
                        Memory.format(Memory.getAvailableRam()),
                        Memory.format(Memory.getAvailableRamCaches()),
                        Memory.format(Memory.getAvailableRamComputation())) )

        bsz = self._blockSize
        halo_size = (False, True, True, True, False)
        block_shape = (1,bsz,bsz,bsz,1)
        block_starts = getIntersectingBlocks( block_shape, roiFromShape(self.Image.meta.shape) )

        mst = WatershedSegmentor(labels=self.LabelImage, blockSize=self._blockSize)

        try:
            block_count = len(block_starts)
            for b_id, block in enumerate(block_starts):
                with Timer() as mstBlockTimer:
                    features_roi = getBlockBounds(self.Image.meta.shape, block_shape, block)
                    labels_roi = getBlockBounds(self.LabelImage.meta.shape, block_shape, block)

                    features_roi_halo = enlargeRoiForHalo(features_roi[0], features_roi[1], self.Image.meta.shape, 1, window=1, enlarge_axes=halo_size)
                    labels_roi_halo = enlargeRoiForHalo(labels_roi[0], labels_roi[1], self.LabelImage.meta.shape, 1, window=1, enlarge_axes=halo_size)

                    # remove halo from bottom
                    features_roi_halo[0] = features_roi[0]
                    labels_roi_halo[0] = labels_roi[0]

                    featureVolume = self.Image( *features_roi_halo ).wait()
                    labelVolume = self.LabelImage( *labels_roi_halo ).wait()

                    block_roi = labels_roi[1]-labels_roi[0]

                    mst.preprocess(labelVolume[0,...,0], numpy.asarray(featureVolume[0,...,0], numpy.float32), TinyVector(block_roi[1:-1]))

                    updateProgressBar(b_id, block_count, labels_roi, mst, mstBlockTimer)

            mst.finalize()

            result[0] = mst
            return result

        finally:
            self.applet.progressSignal.emit(100)


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
    
    #Image after preprocess 
    PreprocessedData = OutputSlot()
    
    # Display outputs
    FilteredImage = OutputSlot()
    WatershedImage = OutputSlot()

    ###########################################################################
    # OverlayData            InputData              Sigma   Filter
    #      \                    \   \-----------------\ \     /
    #      v                    v                     v v    v
    #  opOverlayFilter*      opInputFilter*           opFilter
    #      \    \                \    \                  \   \
    #      \ opOverlayFilterStats \  opInputFilterStats   \ opFilterStats
    #      v    v                  v    v                  v   v
    #  opOverlayNormalize    opInputNormalize       opFilterNormalize
    #          \                   /                  \
    #           \                 /                   v
    #     opOverlayCache    opInputCache       opFilterCache
    #             \             /               /    \    \
    #              \---------->|<--------------/     \     \
    #                          v                     \      v
    #            (SELECT by WatershedSource)         \    FilteredImage
    #                          \                     \
    #  HDF5File                 \                    \
    #      ^                     v                    \
    #       \             opWatershedProvider          \
    #        \--------\          |                       \
    #                  \         |                        \
    #                   v        v                         \
    #               opWatershedHdf5Cache                   \
    #                           /                          \
    #                          v                           \
    #                     opWatershedArrayCache            \
    #                          /          \--------\       \
    #                         v                    v       v
    #                  WatershedImage             opMstProvider
    #                                                  \
    #                                                  v
    #                                              [via execute()]
    #                                                   \
    #                                                   v
    #                                              PreprocessedData

    # *note: Overlay/Input filters used for inversion and smoothing only.
    
    def __init__(self, *args, **kwargs):
        super(OpPreprocessing, self).__init__(*args, **kwargs)
        self._prepData = [None]
        self.applet = self.parent.parent.preprocessingApplet
        
        self._unsavedData = False # set to True if data is not yet saved
        self._dirty = False       # set to True if any Input is dirty

        self._hdf5File = self.parent.parent.shell.projectManager.currentProjectFile
        h5ProjectMetadataGrp = self._hdf5File.require_group('ProjectMetadata')
        # block size is fixed to default on creation of project file
        if "block_size" in h5ProjectMetadataGrp.attrs.keys():
            self._blockSize = h5ProjectMetadataGrp.attrs["block_size"]
        else:
            default_blockSize = os.getenv("ILASTIK_DEFAULT_BLOCKSIZE", None)
            if default_blockSize:
                self._blockSize = int(default_blockSize)
            else:
                self._blockSize = ilastik_config.getint('ilastik', 'default_blocksize')

            self._blockSize = max(self._blockSize, 64)
            logger.info( "Setting BlockSize to: {}".format(self._blockSize))

            h5ProjectMetadataGrp.attrs["block_size"] = self._blockSize

        self.initialSigma = None  # save settings of last preprocess
        self.initialFilter = None # applied to gui by pressing reset

        self._opFilter = OpFilter(parent=self)
        self._opFilter.Input.connect( self.InputData )
        self._opFilter.Sigma.connect( self.Sigma )
        self._opFilter.Filter.connect( self.Filter )

        self._opFilterStats = OpBlockwiseTotalStats(self._blockSize, parent=self)
        self._opFilterStats.Input.connect( self._opFilter.Output )

        self._opFilterNormalize = OpNormalize255( parent=self )
        self._opFilterNormalize.Input.connect( self._opFilter.Output )
        self._opFilterNormalize.TotalStats.connect( self._opFilterStats.Output )

        self._opFilterCache = OpBlockedArrayCache( parent=self )

        self._opOverlayFilter = OpFilter( parent=self )
        self._opOverlayFilter.Input.connect( self.OverlayData )
        self._opOverlayFilter.Sigma.connect( self.Sigma )
        
        self._opOverlayNormalizeStats = OpBlockwiseTotalStats(self._blockSize, parent=self)
        self._opOverlayNormalizeStats.Input.connect( self._opOverlayFilter.Output )

        self._opOverlayNormalize = OpNormalize255( parent=self )
        self._opOverlayNormalize.Input.connect( self._opOverlayFilter.Output )
        self._opOverlayNormalize.TotalStats.connect( self._opOverlayNormalizeStats.Output )

        self._opOverlayCache = OpBlockedArrayCache( parent=self )

        self._opInputFilter = OpFilter( parent=self )
        self._opInputFilter.Input.connect( self.InputData )
        self._opInputFilter.Sigma.connect( self.Sigma )

        self._opInputNormalizeStats = OpBlockwiseTotalStats(self._blockSize, parent=self)
        self._opInputNormalizeStats.Input.connect( self._opInputFilter.Output )

        self._opInputNormalize = OpNormalize255( parent=self )
        self._opInputNormalize.Input.connect( self._opInputFilter.Output )
        self._opInputNormalize.TotalStats.connect( self._opInputNormalizeStats.Output )

        self._opInputCache = OpBlockedArrayCache( parent=self )

        self._opWatershedProvider = OpSimpleWatershed( parent=self )

        self._opWatershedHdf5Cache = OpBlockedHdf5Cache( parent=self )
        self._opWatershedHdf5Cache._opUnblockedHdf5Cache._dataset_kwargs = \
            {'compression':'gzip', 'compression_opts':4}
        self._opWatershedHdf5Cache.Input.connect( self._opWatershedProvider.Output )

        self._opWatershedArrayCache = OpBlockedArrayCache( parent=self )

        self._opMstProvider = OpMstSegmentorProvider( self.applet, self._blockSize, parent=self )
        self._opMstProvider.Image.connect( self._opFilterCache.Output )
        self._opMstProvider.LabelImage.connect( self._opWatershedArrayCache.Output )

        # Display slots
        self.FilteredImage.connect( self._opFilterCache.Output )
        self.WatershedImage.connect( self._opWatershedArrayCache.Output )
        
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

        bsz = self._blockSize
        cacheBlockShape = (1,bsz,bsz,bsz,1)

        self._opFilterCache.fixAtCurrent.setValue(False)
        self._opFilterCache.innerBlockShape.setValue( cacheBlockShape )
        self._opFilterCache.outerBlockShape.setValue( cacheBlockShape )
        self._opFilterCache.Input.connect( self._opFilterNormalize.Output )

        self._opOverlayCache.fixAtCurrent.setValue(False)
        self._opOverlayCache.innerBlockShape.setValue( cacheBlockShape )
        self._opOverlayCache.outerBlockShape.setValue( cacheBlockShape )
        self._opOverlayCache.Input.connect( self._opOverlayNormalize.Output )

        self._opInputCache.fixAtCurrent.setValue(False)
        self._opInputCache.innerBlockShape.setValue( cacheBlockShape )
        self._opInputCache.outerBlockShape.setValue( cacheBlockShape )
        self._opInputCache.Input.connect( self._opInputNormalize.Output )

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
                self._opWatershedProvider.Input.connect( self._opOverlayCache.Output )
            else:
                self._opWatershedProvider.Input.connect( self._opInputCache.Output )
        elif ws_source == 'input':
            self._opWatershedProvider.Input.connect( self._opInputCache.Output )
        elif ws_source == 'filtered':
            self._opWatershedProvider.Input.connect( self._opFilterCache.Output )
        else:
            assert False, "Unknown Watershed source option: {}".format( ws_source )

        # opWatershedCache
        h5PreprocessingGrp = self._hdf5File.require_group('preprocessing')
        h5WatershedGrp = h5PreprocessingGrp.require_group('watershed_labels')

        self._opWatershedHdf5Cache.fixAtCurrent.setValue(not self.is_dirty(h5WatershedGrp))
        self._opWatershedHdf5Cache.innerBlockShape.setValue( cacheBlockShape )
        self._opWatershedHdf5Cache.outerBlockShape.setValue( cacheBlockShape )
        self._hdf5File.file.flush()
        self._opWatershedHdf5Cache.H5CacheGroup.setValue( h5WatershedGrp )

        self._opWatershedArrayCache.fixAtCurrent.setValue(False)
        self._opWatershedArrayCache.innerBlockShape.setValue( cacheBlockShape )
        self._opWatershedArrayCache.outerBlockShape.setValue( cacheBlockShape )
        self._opWatershedArrayCache.Input.connect( self._opWatershedHdf5Cache.Output )


    def execute(self,slot,subindex,unused_roi,result):
        assert slot == self.PreprocessedData, "Invalid output slot"

        h5PreprocessingGrp = self._hdf5File.require_group('preprocessing')
        h5WatershedGrp = h5PreprocessingGrp.require_group('watershed_labels')

        isValid = not self.is_dirty(h5WatershedGrp)

        if self._prepData[0] is not None and isValid:
            return self._prepData

        # invalidate
        if not isValid:
            h5WatershedGrp.attrs['cache_valid'] = False
            h5WatershedGrp.file.flush()
            self._opWatershedHdf5Cache.fixAtCurrent.setValue(False)
            self._opWatershedProvider.Input.setDirty(slice(None))

        with Timer() as mstProviderTimer:
            logger.info( "Creating Segmentor..." )

            self._opMstProvider.MST.ready()
            mst = self._opMstProvider.MST.value

            logger.info( "Created Segmentor in {} seconds".format( mstProviderTimer.seconds() ) )

        # set cache valid
        self._opWatershedHdf5Cache.fixAtCurrent.setValue(True)
        h5WatershedGrp.attrs['cache_valid'] = True
        h5WatershedGrp.file.flush()

        #save settings for reloading them if asked by user
        self.initialSigma = self.Sigma.value
        self.initialFilter = self.Filter.value
        self.enableReset(False)
        self._unsavedData = True
        self._dirty = False
        self.enableDownstream(True)
        
        # copy over seeds, and saved objects
        if self._prepData[0] is not None:
            mst.object_lut = self._prepData[0].object_lut
            mst.object_names = self._prepData[0].object_names
            mst.object_seeds_bg_voxels = self._prepData[0].object_seeds_bg_voxels
            mst.object_seeds_fg_voxels = self._prepData[0].object_seeds_fg_voxels
            mst.bg_priority = self._prepData[0].bg_priority
            mst.no_bias_below = self._prepData[0].no_bias_below
            
        result[0] = mst

        #Cache result
        self._prepData = result
        
        return result

    
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
        if slot == self.InputData:
            #complete restart
            #No values will be reused any more
            self.initialSigma = None
            self.initialFilter = None
            self._prepData = [None]
        
        ws_source_changed = False
        if slot == self.WatershedSource or \
          (slot == self.Filter and self.WatershedSource.value == 'filtered') or \
           slot == self.InvertWatershedSource:
            self._opWatershedProvider.Input.setDirty(slice(None))
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

    def isDirty(self):
        h5PreprocessingGrp = self._hdf5File.require_group('preprocessing')
        h5WatershedGrp = h5PreprocessingGrp.require_group('watershed_labels')

        return self.is_dirty(h5WatershedGrp)

    def is_dirty(self, watershedGrp):
        if self._dirty:
           return True

        watershedValid = len(watershedGrp.keys()) > 0 and \
                         'cache_valid' in watershedGrp.attrs.keys() and \
                         watershedGrp.attrs['cache_valid']
        return not watershedValid


