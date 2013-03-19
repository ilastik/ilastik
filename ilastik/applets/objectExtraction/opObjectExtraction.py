import copy
import collections

import numpy
import vigra.analysis

from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.stype import Opaque
from lazyflow.rtype import SubRegion, List
from lazyflow.operators import OpCachedLabelImage, OpMultiArraySlicer2, OpMultiArrayStacker, OpArrayCache, OpCompressedCache

from lazyflow.request import Request, Pool

from ilastik.applets.objectExtraction import config

import time
from functools import partial

class OpRegionFeatures3d(Operator):
    """
    Produces region features (i.e. a vigra.analysis.RegionFeatureAccumulator) for a 3d image.
    The image MUST have xyz axes, and is permitted to have t and c axes of dim 1.
    """
    RawVolume = InputSlot()
    LabelVolume = InputSlot()
    
    Output = OutputSlot()
    
    def __init__(self, featureNames, *args, **kwargs):
        super( OpRegionFeatures3d, self ).__init__(*args, **kwargs)
        self._vigraFeatureNames = featureNames[0]
        self._otherFeatureNames = featureNames[1]
        self.margin = 30
        
    def setupOutputs(self):
        assert self.LabelVolume.meta.shape == self.RawVolume.meta.shape, "different shapes for label volume {} and raw data {}".format(self.LabelVolume.meta.shape, self.RawVolume.meta.shape)
        assert self.LabelVolume.meta.axistags == self.RawVolume.meta.axistags

        taggedOutputShape = self.LabelVolume.meta.getTaggedShape()
        if 't' in taggedOutputShape.keys():
            assert taggedOutputShape['t'] == 1
        if 'c' in taggedOutputShape.keys():
            assert taggedOutputShape['c'] == 1
        assert set(taggedOutputShape.keys()) - set('tc') == set('xyz'), "Input volumes must have xyz axes."

        # Remove the spatial dims (keep t and c, if present)
        del taggedOutputShape['x']
        del taggedOutputShape['y']
        del taggedOutputShape['z']

        self.Output.meta.shape = tuple( taggedOutputShape.values() )
        self.Output.meta.axistags = vigra.defaultAxistags( "".join( taggedOutputShape.keys() ) )
        # The features for the entire block (in xyz) are provided for the requested tc coordinates.
        self.Output.meta.dtype = object

    def execute(self, slot, subindex, roi, result):
        assert len(roi.start) == len(roi.stop) == len(self.Output.meta.shape)
        assert slot == self.Output
        
        # Process ENTIRE volume
        rawVolume = self.RawVolume[:].wait()
        labelVolume = self.LabelVolume[:].wait()

        # Convert to 3D (preserve axis order)
        spatialAxes = self.RawVolume.meta.getTaggedShape().keys()
        spatialAxes = filter( lambda k: k in 'xyz', spatialAxes )

        rawVolume = rawVolume.view(vigra.VigraArray)
        rawVolume.axistags = self.RawVolume.meta.axistags
        rawVolume3d = rawVolume.withAxes(*spatialAxes)

        labelVolume = labelVolume.view(vigra.VigraArray)
        labelVolume.axistags = self.LabelVolume.meta.axistags
        labelVolume3d = labelVolume.withAxes(*spatialAxes)

        assert numpy.prod(roi.stop - roi.start) == 1        
        acc = self._extract(rawVolume3d, labelVolume3d)
        result[tuple(roi.start)] = acc
        return result

    def _extract(self, image, labels):
        assert len(image.shape) == len(labels.shape) == 3, "Images must be 3D.  Shapes were: {} and {}".format( image.shape, labels.shape )
        print "starting feature extraction..." 
        xAxis = image.axistags.index('x')
        yAxis = image.axistags.index('y')
        zAxis = image.axistags.index('z')
        image = numpy.asarray(image, dtype=numpy.float32)
        labels = numpy.asarray(labels, dtype=numpy.uint32)
        
        
        minmax = vigra.analysis.extractRegionFeatures(image, labels, ["Coord<Minimum>", "Coord<Maximum>", "Count"], ignoreLabel=0)
    
        mins = minmax["Coord<Minimum>"]
        maxs = minmax["Coord<Maximum>"]
        counts = minmax["Count"]
        
        nobj = mins.shape[0]
        features_obj = [None] #don't compute for the 0-th object (the background)
        features_incl = [None]
        features_excl = [None]
        first_good = 1
        pool = Pool()
        otherFeatures_dict = {}
        if len(self._otherFeatureNames)>0:
            #there are non-vigra features. let's make room for them
            #we can't do that for vigra features, because vigra computes more than 
            #we specify in featureNames and we want to keep that
            otherFeatures_dict = {}
            for key in self._otherFeatureNames:
                otherFeatures_dict[key]=[None]
            
        for i in range(1,nobj):
            print "processing object ", i
            if counts[i]>1000000:
                #avoid computing features for over-large objects which are clearly not synapses
                #this can happen despite the size filtering in two-level thresholding, as one giant object
                #can break into many smaller pieces at higher threshold and then get merged again at lower
                features_incl.append(None)
                features_excl.append(None)
                features_obj.append(None)
                for key in otherFeatures_dict.keys():
                    otherFeatures_dict[key].append(None)
                
                if first_good<=i:
                    first_good=i+1
                continue
            minx = max(mins[i][xAxis]-self.margin, 0)
            miny = max(mins[i][yAxis]-self.margin, 0)
            minz = max(mins[i][zAxis], 0)
            # Coord<Minimum> and Coord<Maximum> give us the [min,max] 
            # coords of the object, but we want the bounding box: [min,max), so add 1
            maxx = min(maxs[i][xAxis]+1+self.margin, image.shape[xAxis])
            maxy = min(maxs[i][yAxis]+1+self.margin, image.shape[yAxis])
            maxz = min(maxs[i][zAxis]+1, image.shape[zAxis])
            
            #FIXME: there must be a better way
            key = 3*[None]
            key[xAxis] = slice(minx, maxx, None)
            key[yAxis] = slice(miny, maxy, None)
            key[zAxis] = slice(minz, maxz, None)
            key = tuple(key)
            
            ccbbox = labels[key]
            rawbbox = image[key]
            ccbboxobject = numpy.where(ccbbox==i, 1, 0)
            
            #ccbbox = labels[minx:maxx, miny:maxy, minz:maxz]
            #rawbbox = image[minx:maxx, miny:maxy, minz:maxz]
            #ccbboxobject = numpy.where(ccbbox==i, 1, 0)
            
            bboxshape = 3*[None]
            bboxshape[xAxis] = maxx-minx
            bboxshape[yAxis] = maxy-miny
            bboxshape[zAxis] = maxz-minz
            bboxshape = tuple(bboxshape)
            passed = numpy.zeros(bboxshape, dtype=bool)
            #passed = numpy.zeros((maxx-minx, maxy-miny, maxz-minz), dtype=bool)
            
            for iz in range(maxz-minz):
                #FIXME: shoot me, axistags
                bboxkey = 3*[None]
                bboxkey[xAxis] = slice(None, None, None)
                bboxkey[yAxis] = slice(None, None, None)
                bboxkey[zAxis] = iz
                bboxkey = tuple(bboxkey)
                #TODO: Ulli once mentioned that distance transform can be made anisotropic in 3D
                dt = vigra.filters.distanceTransform2D(ccbbox[bboxkey].astype(numpy.float32))
                passed[bboxkey] = dt<self.margin
                #dt = vigra.filters.distanceTransform2D(ccbbox[:, :, iz].astype(numpy.float32))
                #passed[:, :, iz] = dt<self.margin
                
            ccbboxexcl = passed-ccbboxobject
            if "bad_slices" in self._otherFeatureNames:
                #compute the quality score of an object. lower is better
                nbadslices = 0
                badslices = []
                area = rawbbox.shape[xAxis]*rawbbox.shape[yAxis]
                bboxkey = 3*[None]
                bboxkey[xAxis] = slice(None, None, None)
                bboxkey[yAxis] = slice(None, None, None)
                for iz in range(maxz-minz):
                    bboxkey[zAxis] = iz
                    nblack = numpy.sum(rawbbox[tuple(bboxkey)]==0)
                    if nblack>0.5*area:
                        nbadslices = nbadslices+1
                        badslices.append(iz)
                otherFeatures_dict["bad_slices"].append(numpy.array([nbadslices]))
                #interpolate the raw data
                imagekey = 3*[None]
                imagekey[xAxis] = slice(minx, maxx, None)
                imagekey[yAxis] = slice(miny, maxy, None)
                try:
                    for sl in badslices:
                        if sl==0:
                            if minz==0:
                                continue
                            slprev=minz
                            slprevsum = area
                            while slprevsum>0.5*area and slprev>0:
                                slprev = slprev-1
                                imagekey[zAxis]=slprev
                                slprevsum = numpy.sum(image[tuple(imagekey)])
                        else:
                            slprev = sl+minz
                            while slprev-minz in badslices and slprev>=0:
                                slprev = slprev-1
                                
                        if sl==maxz-1:
                            if sl==image.shape[zAxis]-1:
                                continue
                            slnext = maxz-1
                            slnextsum = area
                            while slnextsum>0.5*area and slnext<image.shape[zAxis]-1:
                                slnext = slnext+1
                                imagekey[zAxis] = slnext
                                slnextsum = numpy.sum(image[tuple(imagekey)])
                        else:
                            slnext = sl+minz
                            while slnext-minz in badslices and slnext<maxz:
                                slnext = slnext+1
                            
                            
                        interval = slnext-slprev
                        weightnext = float(slnext-sl)/interval
                        weightprev = float(sl-slprev)/interval
                        bboxkey[zAxis] = sl
                        keycurrent = tuple(bboxkey)
                        imagekey[zAxis] = slprev
                        keyprev = tuple(imagekey)
                        imagekey[zAxis] = slnext
                        keynext = tuple(imagekey)
                        rawbbox[keycurrent] = weightnext*image[keynext] + weightprev*image[keyprev]
                except:
                    #interpolation didn't work. just go on.
                    print "interpolation failed"
                    
                    
                
                
            labeled_bboxes = [passed, ccbboxexcl, ccbboxobject]
            feats = [None, None, None]
            for ibox, bbox in enumerate(labeled_bboxes):
                def extractObjectFeatures(ibox):
                    feats[ibox] = vigra.analysis.extractRegionFeatures(rawbbox.astype(numpy.float32), \
                                                                    labeled_bboxes[ibox].astype(numpy.uint32), \
                                                                    self._vigraFeatureNames, \
                                                                    histogramRange=[0, 255], \
                                                                    binCount = 10,\
                                                                    ignoreLabel=0)
                req = pool.request(partial(extractObjectFeatures, ibox))
            pool.wait()

            features_incl.append(feats[0])
            features_excl.append(feats[1])
            features_obj.append(feats[2])
            #f_incl = vigra.analysis.extractRegionFeatures(rawbbox.astype(numpy.float32), passed.astype(numpy.uint32),\
            #                                              self._vigraFeatureNames, histogramRange=[0, 255], binCount=10,\
            #                                              ignoreLabel=0)

            #f_excl = vigra.analysis.extractRegionFeatures(rawbbox.astype(numpy.float32), ccbboxexcl.astype(numpy.uint32),\
            #                                              self._vigraFeatureNames, histogramRange=[0, 255], binCount=10,\
            #                                              ignoreLabel=0)

            #f_obj = vigra.analysis.extractRegionFeatures(rawbbox.astype(numpy.float32), ccbboxobject.astype(numpy.uint32),\
            #                                              self._vigraFeatureNames, histogramRange=[0, 255], binCount=10,\
            #                                              ignoreLabel=0)
            #features_incl.append(f_incl)
            #features_excl.append(f_excl)
            #features_obj.append(f_obj)


            if "lbp_obj" in self._otherFeatureNames:
                #FIXME: there is a mess about which of the lbp features are computed
                
                #print "computing lbp features"
                #compute lbp features
                import skimage.feature as ft
                P=8
                R=1
                lbp_total = numpy.zeros(passed.shape)
                for iz in range(maxz-minz): 
                    #an lbp image
                    bboxkey = 3*[None]
                    bboxkey[xAxis] = slice(None, None, None)
                    bboxkey[yAxis] = slice(None, None, None)
                    bboxkey[zAxis] = iz
                    bboxkey = tuple(bboxkey)
                    lbp_total[bboxkey] = ft.local_binary_pattern(rawbbox[bboxkey], P, R, "uniform")
                #extract relevant parts
                #print "computed lbp for volume:", lbp_total.shape,
                #print "extracting pieces:", passed.shape, ccbboxexcl.shape, ccbboxobject.shape
                lbp_incl = lbp_total[passed]
                lbp_excl = lbp_total[ccbboxexcl.astype(bool)]
                lbp_obj = lbp_total[ccbboxobject.astype(bool)]
                #print "extracted pieces", lbp_incl.shape, lbp_excl.shape, lbp_obj.shape
                lbp_hist_incl, _ = numpy.histogram(lbp_incl, normed=True, bins=P+2, range=(0, P+2))
                lbp_hist_excl, _ = numpy.histogram(lbp_excl, normed=True, bins=P+2, range=(0, P+2))
                lbp_hist_obj, _ = numpy.histogram(lbp_obj, normed=True, bins=P+2, range=(0, P+2))
                #print "computed histogram"
                otherFeatures_dict["lbp_incl"].append(lbp_hist_incl)
                otherFeatures_dict["lbp_excl"].append(lbp_hist_excl)
                otherFeatures_dict["lbp_obj"].append(lbp_hist_obj)

           

            if "lapl_obj" in self._otherFeatureNames:
                #compute mean and variance of laplacian in the object and its neighborhood
                lapl = None
                try:
                    lapl = vigra.filters.laplacianOfGaussian(rawbbox)
                except RuntimeError:
                    #kernel longer than line. who cares?
                    otherFeatures_dict["lapl_incl"].append(None)
                    otherFeatures_dict["lapl_excl"].append(None)
                    otherFeatures_dict["lapl_obj"].append(None)
                else:
                    lapl_incl = lapl[passed]
                    lapl_excl = lapl[ccbboxexcl.astype(bool)]
                    lapl_obj = lapl[ccbboxobject.astype(bool)]
                    lapl_mean_incl = numpy.mean(lapl_incl)
                    lapl_var_incl = numpy.var(lapl_incl)
                    lapl_mean_excl = numpy.mean(lapl_excl)
                    lapl_var_excl = numpy.var(lapl_excl)
                    lapl_mean_obj = numpy.mean(lapl_obj)
                    lapl_var_obj = numpy.var(lapl_obj)
                    otherFeatures_dict["lapl_incl"].append(numpy.array([lapl_mean_incl, lapl_var_incl]))
                    otherFeatures_dict["lapl_excl"].append(numpy.array([lapl_mean_excl, lapl_var_excl]))
                    otherFeatures_dict["lapl_obj"].append(numpy.array([lapl_mean_obj, lapl_var_obj]))
                
           
                    
                    
                
            
        feature_keys = features_incl[first_good].keys()
        feature_dict = {}
        feature_dict["Coord<Minimum>"]=mins
        feature_dict["Coord<Maximum>"]=maxs
        feature_dict["Count"]=counts
        #copy over non-vigra features and turn them into numpy arrays
        for key in otherFeatures_dict.keys():
            #print otherFeatures_dict[key]
            #find the number of channels
            feature = otherFeatures_dict[key]
            nchannels = feature[first_good].shape[0]
            for irow, row in enumerate(feature):
                if row is None:
                    #print "NaNs in row", irow
                    feature[irow]=numpy.zeros((nchannels,))
            
            feature_dict[key]=numpy.vstack(otherFeatures_dict[key])
            assert feature_dict[key].shape[0]==nobj, "didn't compute features for all objects {}".format(key)
            #print key, feature_dict[key].shape
            
        for key in feature_keys:
            
            nchannels = 0
            #we always have two objects, background is first
            #unless, of course, it's a global measurement, and then it's just one element, grrrh
            
            #sometimes, vigra returns one-dimensional features as (nobj, 1) and sometimes as (nobj,)
            #the following try-except is for this case
            
            try:
                nchannels = len(features_incl[first_good][key][0])
            except TypeError:
                nchannels = 1
            #print "assembling key:", key, "nchannels:", nchannels
            #print "feature arrays:", len(features_incl), len(features_excl), len(features_obj)
            #FIXME: find the maximum number of channels and pre-allocate
            feature_obj = numpy.zeros((nobj, nchannels))
            feature_incl = numpy.zeros((nobj, nchannels))
            feature_excl = numpy.zeros((nobj, nchannels))
            
            for i in range(nobj):
                if features_obj[i] is not None:
                    try:
                        feature_obj[i] = features_obj[i][key][1]
                        feature_incl[i] = features_incl[i][key][1]
                        feature_excl[i] = features_excl[i][key][1]
                    except:
                        #global number, not a list, haha
                        feature_obj[i] = features_obj[i][key]
                        feature_incl[i] = features_incl[i][key]
                        feature_excl[i] = features_excl[i][key]
            
            feature_dict[key+"_obj"]=feature_obj
            feature_dict[key+"_incl"]=feature_incl
            feature_dict[key+"_excl"]=feature_excl
            #print key, feature_obj.shape, feature_incl.shape, feature_excl.shape
        end1 = time.clock()
        #print "computed the following features:", feature_dict.keys()
        return feature_dict

    def propagateDirty(self, slot, subindex, roi):
        axes = self.RawVolume.meta.getTaggedShape().keys()
        dirtyStart = collections.OrderedDict( zip( axes, roi.start ) )
        dirtyStop = collections.OrderedDict( zip( axes, roi.stop ) )
        
        # Remove the spatial dims (keep t and c, if present)
        del dirtyStart['x']
        del dirtyStart['y']
        del dirtyStart['z']
            
        del dirtyStop['x']
        del dirtyStop['y']
        del dirtyStop['z']
            
        self.Output.setDirty( dirtyStart.values(), dirtyStop.values() )

class OpRegionFeatures(Operator):
    RawImage = InputSlot()
    LabelImage = InputSlot()
    Output = OutputSlot()

    # Schematic:
    # 
    # RawImage ----> opRawTimeSlicer ----> opRawChannelSlicer -----
    #                                                              \
    # LabelImage --> opLabelTimeSlicer --> opLabelChannelSlicer --> opRegionFeatures3dBlocks --> opChannelStacker --> opTimeStacker -> Output

    def __init__(self, featureNames, *args, **kwargs):
        super( OpRegionFeatures, self ).__init__( *args, **kwargs )

        # Distribute the raw data
        self.opRawTimeSlicer = OpMultiArraySlicer2( parent=self )
        self.opRawTimeSlicer.AxisFlag.setValue('t')
        self.opRawTimeSlicer.Input.connect( self.RawImage )
        assert self.opRawTimeSlicer.Slices.level == 1

        self.opRawChannelSlicer = OperatorWrapper( OpMultiArraySlicer2, parent=self )
        self.opRawChannelSlicer.AxisFlag.setValue( 'c' )
        self.opRawChannelSlicer.Input.connect( self.opRawTimeSlicer.Slices )
        assert self.opRawChannelSlicer.Slices.level == 2

        # Distribute the labels
        self.opLabelTimeSlicer = OpMultiArraySlicer2( parent=self )
        self.opLabelTimeSlicer.AxisFlag.setValue('t')
        self.opLabelTimeSlicer.Input.connect( self.LabelImage )
        assert self.opLabelTimeSlicer.Slices.level == 1

        self.opLabelChannelSlicer = OperatorWrapper( OpMultiArraySlicer2, parent=self )
        self.opLabelChannelSlicer.AxisFlag.setValue( 'c' )
        self.opLabelChannelSlicer.Input.connect( self.opLabelTimeSlicer.Slices )
        assert self.opLabelChannelSlicer.Slices.level == 2
        
        class OpWrappedRegionFeatures3d(Operator):
            """
            This quick hack is necessary because there's not currently a way to wrap an OperatorWrapper.
            We need to double-wrap OpRegionFeatures3d, so we need this operator to provide the first level of wrapping.
            """
            RawVolume = InputSlot(level=1)
            LabelVolume = InputSlot(level=1)
            Output = OutputSlot(level=1)

            def __init__(self, featureNames, *args, **kwargs):
                super( OpWrappedRegionFeatures3d, self ).__init__( *args, **kwargs )
                self._innerOperator = OperatorWrapper( OpRegionFeatures3d, operator_args=[featureNames], parent=self )
                self._innerOperator.RawVolume.connect( self.RawVolume )
                self._innerOperator.LabelVolume.connect( self.LabelVolume )
                self.Output.connect( self._innerOperator.Output )
            
            def setupOutputs(self):
                pass
        
            def execute(self, slot, subindex, roi, destination):
                assert False, "Shouldn't get here."
    
            def propagateDirty(self, slot, subindex, roi):
                pass # Nothing to do...

        # Wrap OpRegionFeatures3d TWICE.
        self.opRegionFeatures3dBlocks = OperatorWrapper( OpWrappedRegionFeatures3d, operator_args=[featureNames], parent=self )
        assert self.opRegionFeatures3dBlocks.RawVolume.level == 2
        assert self.opRegionFeatures3dBlocks.LabelVolume.level == 2
        self.opRegionFeatures3dBlocks.RawVolume.connect( self.opRawChannelSlicer.Slices )
        self.opRegionFeatures3dBlocks.LabelVolume.connect( self.opLabelChannelSlicer.Slices )

        assert self.opRegionFeatures3dBlocks.Output.level == 2
        self.opChannelStacker = OperatorWrapper( OpMultiArrayStacker, parent=self )
        self.opChannelStacker.AxisFlag.setValue('c')

        assert self.opChannelStacker.Images.level == 2
        self.opChannelStacker.Images.connect( self.opRegionFeatures3dBlocks.Output )

        self.opTimeStacker = OpMultiArrayStacker( parent=self )
        self.opTimeStacker.AxisFlag.setValue('t')

        assert self.opChannelStacker.Output.level == 1
        assert self.opTimeStacker.Images.level == 1
        self.opTimeStacker.Images.connect( self.opChannelStacker.Output )

        # Connect our outputs
        self.Output.connect( self.opTimeStacker.Output )
    
    def setupOutputs(self):
        pass
        
    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."
    
    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do...

class OpCachedRegionFeatures(Operator):
    RawImage = InputSlot()
    LabelImage = InputSlot()
    CacheInput = InputSlot(optional=True)
    
    Output = OutputSlot()
    CleanBlocks = OutputSlot()

    # Schematic:
    #
    # RawImage -----   blockshape=(t,c)=(1,1)
    #               \                        \
    # LabelImage ----> OpRegionFeatures ----> OpArrayCache --> Output
    #                                                     \
    #                                                      --> CleanBlocks

    def __init__(self, featureNames, *args, **kwargs):
        super(OpCachedRegionFeatures, self).__init__(*args, **kwargs)
        
        # Hook up the labeler
        self._opRegionFeatures = OpRegionFeatures(featureNames, parent=self )
        self._opRegionFeatures.RawImage.connect( self.RawImage )
        self._opRegionFeatures.LabelImage.connect( self.LabelImage )

        # Hook up the cache.
        self._opCache = OpArrayCache( parent=self )
        self._opCache.Input.connect( self._opRegionFeatures.Output )
        
        # Hook up our output slots
        self.Output.connect( self._opCache.Output )
        self.CleanBlocks.connect( self._opCache.CleanBlocks )
    
    def setupOutputs(self):
        assert self.LabelImage.meta.shape == self.RawImage.meta.shape
        assert self.LabelImage.meta.axistags == self.RawImage.meta.axistags

        # Every value in the regionfeatures output is cached seperately as it's own "block"
        blockshape = (1,) * len( self._opRegionFeatures.Output.meta.shape )
        self._opCache.blockShape.setValue( blockshape )

    def setInSlot(self, slot, subindex, roi, value):
        assert slot == self.CacheInput
        # Forward to our cache to force label values in from an external source.
        self._opCache.setInSlot(self._opCache.Input, subindex, roi, value)

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."
    
    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do...

class OpAdaptTimeListRoi(Operator):
    """
    Adapts the tc array output from OpRegionFeatures to an Output slot that is called with a 
    'List' rtype, where the roi is a list of time slices, and the output is a 
    dict-of-lists (dict by time, list by channels).
    """
    Input = InputSlot()
    Output = OutputSlot(stype=Opaque, rtype=List)
    
    def setupOutputs(self):
        # Number of time steps
        self.Output.meta.shape = self.Input.meta.getTaggedShape()['t']
        self.Output.meta.dtype = object
    
    def execute(self, slot, subindex, roi, destination):
        assert slot == self.Output, "Unknown output slot"
        taggedShape = self.Input.meta.getTaggedShape()
        numChannels = taggedShape['c']
        channelIndex = taggedShape.keys().index('c')

        # Special case: An empty roi list means "request everything"
        if len(roi) == 0:
            roi = range( taggedShape['t'] )

        taggedShape['t'] = 1
        timeIndex = taggedShape.keys().index('t')
        
        result = {}
        for t in roi:
            result[t] = []
            start = [0] * len(taggedShape)
            stop = taggedShape.values()
            start[timeIndex] = t
            stop[timeIndex] = 1
            a = self.Input(start, stop).wait()
            # Result is provided as a list of arrays by channel
            channelResults = numpy.split(a, numChannels, channelIndex)
            for channelResult in channelResults:
                # Extract from 1x1 ndarray
                result[t].append( channelResult.flat[0] )
        return result

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.Input
        timeIndex = self.Input.meta.axistags.index('t')
        self.Output.setDirty( List(self.Output, range(roi.start[timeIndex], roi.stop[timeIndex])) )

class OpObjectCenterImage(Operator):
    """A cross in the center of each connected component."""
    BinaryImage = InputSlot()
    RegionCenters = InputSlot(rtype=List)
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.BinaryImage.meta)

    @staticmethod
    def __contained_in_subregion(roi, coords):
        b = True
        for i in range(len(coords)):
            b = b and (roi.start[i] <= coords[i] and coords[i] < roi.stop[i])
        return b

    @staticmethod
    def __make_key(roi, coords):
        key = [coords[i] - roi.start[i] for i in range(len(roi.start))]
        return tuple(key)

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot"
        result[:] = 0
        for t in range(roi.start[0], roi.stop[0]):
            centers = self.RegionCenters([t]).wait()
            for ch in range(roi.start[-1], roi.stop[-1]):
                centers = centers[t][ch]['RegionCenter']
                centers = numpy.asarray(centers, dtype=numpy.uint32)
                if centers.size:
                    centers = centers[1:,:]
                for center in centers:
                    x, y, z = center[0:3]
                    for dim in (1, 2, 3):
                        for offset in (-1, 0, 1):
                            c = [t, x, y, z, ch]
                            c[dim] += offset
                            c = tuple(c)
                            if self.__contained_in_subregion(roi, c):
                                result[self.__make_key(roi, c)] = 255
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.RegionCenters:
            self.Output.setDirty(slice(None))


class OpObjectExtraction(Operator):
    name = "Object Extraction"

    RawImage = InputSlot()
    BinaryImage = InputSlot()
    BackgroundLabels = InputSlot()

    LabelImage = OutputSlot()
    ObjectCenterImage = OutputSlot()
    RegionFeatures = OutputSlot(stype=Opaque, rtype=List)

    BlockwiseRegionFeatures = OutputSlot() # For compatibility with tracking workflow, the RegionFeatures output
                                           # has rtype=List, indexed by t.
                                           # For other workflows, output has rtype=ArrayLike, indexed by (t,c)

    # these features are needed by classification applet.
    default_features = [
        'RegionCenter',
        'Coord<Minimum>',
        'Coord<Maximum>',
    ]

    # Schematic:
    #
    # BackgroundLabels              LabelImage
    #                 \            /
    # BinaryImage ---> opLabelImage ---> opRegFeats ---> opRegFeatsAdaptOutput ---> RegionFeatures
    #                                   /                                     \
    # RawImage--------------------------                      BinaryImage ---> opObjectCenterImage --> opCenterCache --> ObjectCenterImage

    def __init__(self, *args, **kwargs):

        super(OpObjectExtraction, self).__init__(*args, **kwargs)

        features = list(set(config.vigra_features).union(set(self.default_features)))
        features = [features, config.other_features]

        print "features:", features
        # internal operators
        self._opLabelImage = OpCachedLabelImage(parent=self)
        self._opRegFeats = OpCachedRegionFeatures(features, parent=self)
        self._opRegFeatsAdaptOutput = OpAdaptTimeListRoi(parent=self)
        self._opObjectCenterImage = OpObjectCenterImage(parent=self)

        # connect internal operators
        self._opLabelImage.Input.connect(self.BinaryImage)
        self._opLabelImage.BackgroundLabels.connect(self.BackgroundLabels)

        self._opRegFeats.RawImage.connect(self.RawImage)
        self._opRegFeats.LabelImage.connect(self._opLabelImage.Output)

        self._opRegFeatsAdaptOutput.Input.connect(self._opRegFeats.Output)
        
        self._opObjectCenterImage.BinaryImage.connect(self.BinaryImage)
        self._opObjectCenterImage.RegionCenters.connect(self._opRegFeatsAdaptOutput.Output)

        self._opCenterCache = OpCompressedCache(parent=self)
        self._opCenterCache.Input.connect( self._opObjectCenterImage.Output )

        # connect outputs
        self.LabelImage.connect(self._opLabelImage.Output)
        self.ObjectCenterImage.connect(self._opCenterCache.Output)
        self.RegionFeatures.connect(self._opRegFeatsAdaptOutput.Output)
        self.BlockwiseRegionFeatures.connect(self._opRegFeats.Output)

    def setupOutputs(self):
        taggedShape = self.Input.meta.getTaggedShape()
        for k in taggedShape.keys():
            if k == 't' or k == 'c':
                taggedShape[k] = 1
            else:
                taggedShape[k] = 256
        self._opCenterCache.BlockShape.setValue( tuple( taggedShape.values() ) )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here."

    def propagateDirty(self, inputSlot, subindex, roi):
        pass
