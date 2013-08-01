import vigra
import pgmlink
import numpy
from lazyflow.graph import Operator, InputSlot, OutputSlot
import h5py
import lazyflow.request
from lazyflow.rtype import SubRegion
import math
from lazyflow.operators.generic import axisTagsToString
from lazyflow.roi import roiToSlice, sliceToRoi

class OpOpticalTranslation(Operator):
    name = "Optical Translation"
    BinaryImage = InputSlot()
    RawImage = InputSlot()
    Parameters = InputSlot( value={'templateSize':40, 'maxTranslation':10, 'overlap':0, 'method':'xcorr',
                                   'maxDiffVals':10} )
    
    TranslationVectors = OutputSlot()
    TranslationVectorsComputation = OutputSlot(stype="float")
    TranslationVectorsDisplay = OutputSlot()
    WarpedImage = OutputSlot()
    

    def __init__(self, parent=None, graph=None):
        super(OpOpticalTranslation, self).__init__(parent=parent,graph=graph)
        
        self._mem_h5 = h5py.File(str(id(self)), driver='core', backing_store=False)
        self._processedTimeSteps = set()
        self._processedTimeStepsWarped = set()
        self._lock = lazyflow.request.RequestLock()
        self._lock_warped = lazyflow.request.RequestLock()
        
    def setupOutputs(self):
        # FIXME: assumes c to be last index
        assert self.BinaryImage.meta.shape[-1] == 1, "this operator does only work with binary labels yet"
        
        self.TranslationVectors.meta.assignFrom(self.BinaryImage.meta)
        self.TranslationVectors.meta.dtype = numpy.int8
        shape = list(self.TranslationVectors.meta.shape)
        ndim = 3
        # assumes t, x, y, z, c
        if shape[3] == 1:
            ndim = 2            
        shape[-1] = ndim                
        self.TranslationVectors.meta.shape = shape
        
        self.TranslationVectorsComputation.meta.dtype = numpy.float
        self.TranslationVectorsComputation.meta.shape = [0]
    
        self.TranslationVectorsDisplay.meta.assignFrom(self.TranslationVectors.meta)
        self.TranslationVectorsDisplay.meta.dtype = numpy.uint8        
        self.WarpedImage.meta.assignFrom(self.BinaryImage.meta)
        self.WarpedImage.meta.dtype = numpy.uint8
        
        
        if 'TranslationVectors' not in self._mem_h5.keys():
            chunks = (1,min(64,shape[1]),min(64,shape[2]),min(64,shape[3]),ndim)
            self._mem_h5.create_dataset('TranslationVectors', shape=shape, dtype=self.TranslationVectors.meta.dtype, 
                                        compression=1,chunks=chunks) 
        if 'WarpedImage' not in self._mem_h5.keys():
            chunks = (1,min(64,shape[1]),min(64,shape[2]),min(64,shape[3]),1)        
            self._mem_h5.create_dataset('WarpedImage', shape=self.WarpedImage.meta.shape, dtype=self.WarpedImage.meta.dtype, 
                                    compression=1,chunks=chunks)
        
        self.twospacedim = False
        if axisTagsToString(self.BinaryImage.meta.axistags)[3] != 'c' and self.BinaryImage.meta.shape[3] == 1:
            self.twospacedim = True
    
    
    def cleanUp(self):
        self._mem_h5.close()
        super( OpOpticalTranslation, self ).cleanUp()
    
    
    def _computeTranslationVectors(self, roi, result):
        shape = self.BinaryImage.meta.shape        
        for t in range(roi.start[0], roi.stop[0]):
            if t in self._processedTimeSteps:                
                continue                
            
            print ("Calculating TranslationVectors at t={}".format(t))
            dest = self._mem_h5['TranslationVectors']
            
            if t == shape[0]-1:
                dest[t,...][:] = 0
                self._processedTimeSteps.add(t)
                self.TranslationVectors._sig_value_changed()
                continue
            
            # assumes t,x,y,z,c
            sroi_cur = SubRegion(self.BinaryImage,
                             start=[t,0,0,0,0],
                             stop=[t+1,] + list(shape[1:]))
            sroi_next = SubRegion(self.BinaryImage,
                             start=[t+1,0,0,0,0],
                             stop=[t+2,] + list(shape[1:]))
            img_cur = self.BinaryImage.get(sroi_cur).wait()
            img_next = self.BinaryImage.get(sroi_next).wait()
            
            # since txyc images are pumped up to txyzc, we have to handle that case            
            if self.twospacedim:                
                img_cur = numpy.array(img_cur[0,...,0,0], dtype=numpy.float)            
                img_next = numpy.array(img_next[0,...,0,0], dtype=numpy.float)
            else:
                img_cur = numpy.array(img_cur[0,...,0], dtype=numpy.float)                                
                img_next = numpy.array(img_next[0,...,0], dtype=numpy.float)
            
            if not self.Parameters.ready():
                raise Exception("Parameter slot is not ready")
            
            paras = self.Parameters.value
            templateSize = paras['templateSize']
            maxTranslation = paras['maxTranslation']
            overlap = paras['overlap']
            method = paras['method']   
            maxDiffVals = paras['maxDiffVals']                                 
            
            print 'img_next.shape, img_cur.shape, templateSize, maxTranslation, overlap, method, maxDiffVals = ',img_next.shape, img_cur.shape, templateSize, maxTranslation, overlap, method, maxDiffVals
            res = pgmlink.patchedOpticalTranslation(img_cur,
                                                    img_next,
                                                    int(templateSize),
                                                    int(maxTranslation),
                                                    int(overlap),
                                                    method,
                                                    int(maxDiffVals))
            
        
            if self.twospacedim:
                dest[t,...,0,:] = res.astype(numpy.int8).squeeze()[...,0:2]
            else:
                dest[t,...] = res.astype(numpy.int8)
                                                        
            self._processedTimeSteps.add(t)
            self.TranslationVectors._sig_value_changed()
    
    
    def execute(self, slot, subindex, roi, result):
            if slot is self.TranslationVectorsComputation:
                with self._lock:
                    self._computeTranslationVectors(roi, result)
            elif slot is self.TranslationVectors:
                with self._lock:
                    start, stop = roi.start[0], roi.stop[0]
                    for t in range(start, stop):
                        slc = (slice(t, t + 1),) + roi.toSlice()[1:]
                        dslc = slice(t - start, t - start + 1)
                        if t not in self._processedTimeSteps:                            
                            self._computeTranslationVectors(roi, result)                    
                        src = self._mem_h5['TranslationVectors']                    
                        result[dslc] = src[slc]
                    return result
            elif slot is self.TranslationVectorsDisplay:     
                tstart, tstop = roi.start[0], roi.stop[0]                
                maxTranslation = self.Parameters.value['maxTranslation'] 
                scale = math.floor(255/(2*maxTranslation))           
                # FIXME: assumes t,x,y,z,c
                # the entire image for the roi time slices
                troi = SubRegion(self.TranslationVectors, start = [tstart,] + 4*[0,], stop = [tstop,] + self.TranslationVectors.meta.shape[1:])
                # the corresponding sub-image
                translVectors = (self.TranslationVectors.get(troi).wait()).astype(numpy.int16)[[slice(0,tstop-tstart),] + list(roiToSlice(roi.start, roi.stop))[1:]]
                translVectors *= scale
                translVectors += 128                
                result = translVectors.astype(numpy.uint8)                    
                return result
            elif slot is self.WarpedImage:
                start, stop = roi.start[0], roi.stop[0]
                assert stop-start == 1, "only implemented for single timesteps yet"
                if start == self.WarpedImage.meta.shape[0]-1:
                    result[:] = 0
                    return result 
            
                with self._lock_warped:                                        
                    if start not in self._processedTimeStepsWarped:
                        croi = SubRegion(self.TranslationVectors,
                                         start = [roi.start[0],] + [0,0,0,0,],
                                         stop = [roi.stop[0],] + list(self.TranslationVectors.meta.shape[1:]))                
                        translVectors = (self.TranslationVectors.get(croi).wait()).astype(numpy.float)
                        
                        
                        sroi = SubRegion(self.BinaryImage,
                                         start = [roi.start[0],] + [0,0,0,0,],
                                         stop = [roi.stop[0],] + list(self.BinaryImage.meta.shape[1:]))
                        img_cur = (self.BinaryImage.get(sroi).wait()).astype(numpy.float)
                        
                        if self.twospacedim:                            
                            self._mem_h5['WarpedImage'][start,...,0,0] = pgmlink.translateImage(img_cur.squeeze(),translVectors.squeeze())
                        else:
                            self._mem_h5['WarpedImage'][start,...,0] = pgmlink.translateImage(img_cur.squeeze(),translVectors.squeeze())
                        self._processedTimeStepsWarped.add(start)                
                        
                    result = self._mem_h5['WarpedImage'][roiToSlice(roi.start,roi.stop)]
                    return result
                    
        
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.BinaryImage or slot == self.Parameters:            
            self.TranslationVectors.setDirty(slice(None))
            self.TranslationVectorsDisplay.setDirty(slice(None))
            self.WarpedImage.setDirty(slice(None))
            self._processedTimeSteps = set()
            self._processedTimeStepsWarped = set()
                        
        else:
            print "Unknown dirty input slot: " + str(slot.name)    
