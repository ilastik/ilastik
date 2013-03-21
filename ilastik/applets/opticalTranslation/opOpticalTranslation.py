import vigra
import pgmlink
import numpy
from lazyflow.graph import Operator, InputSlot, OutputSlot
import h5py
from lazyflow.request.request import RequestLock
from lazyflow.rtype import SubRegion

class OpOpticalTranslation(Operator):
    name = "Optical Translation"
    BinaryImage = InputSlot()
    RawImage = InputSlot()
    Parameters = InputSlot( value={'templateSize':100, 'maxTranslation':20, 'overlap':50, 'method':'xor',
                                   'maxDiffVals':10} )
    
    TranslationVectors = OutputSlot()
    TranslationVectorsComputation = OutputSlot(stype="float")
    TranslationVectorsDisplay = OutputSlot()
    

    def __init__(self, parent=None, graph=None):
        super(OpOpticalTranslation, self).__init__(parent=parent,graph=graph)
        
        self._mem_h5 = h5py.File(str(id(self)), driver='core', backing_store=False)
        self._processedTimeSteps = set()
#        self._lock = RequestLock()
        
    def setupOutputs(self):
        assert(self.BinaryImage.meta.shape[-1] == 1, "this operator does only work with binary labels yet")
        
        self.TranslationVectors.meta.assignFrom(self.BinaryImage.meta)
        self.TranslationVectors.meta.dtype = numpy.float
        shape = list(self.TranslationVectors.meta.shape)
        shape[-1] = 3                
        self.TranslationVectors.meta.shape = shape
        
        self.TranslationVectorsComputation.meta.dtype = numpy.float
        self.TranslationVectorsComputation.meta.shape = [0]
        
        
        self._mem_h5.create_dataset('TranslationVectors', shape=shape, dtype=self.TranslationVectors.meta.dtype, 
                                    compression=1,chunks=True) 
    
    
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
            
            if t == 0:
                dest[t,...][:] = [0]
                self._processedTimeSteps.add(t)
                self.TranslationVectors._sig_value_changed()
                continue
            
            # assumes t,x,y,z,c
            sroi_cur = SubRegion(self.BinaryImage,
                             start=[t,0,0,0,0],
                             stop=[t+1,] + list(shape[1:]))
            sroi_prev = SubRegion(self.BinaryImage,
                             start=[t-1,0,0,0,0],
                             stop=[t,] + list(shape[1:]))
            img_cur = self.BinaryImage.get(sroi_cur).wait()
            img_cur = numpy.array(img_cur[0,...,0], dtype=numpy.float)                    
            img_prev = self.BinaryImage.get(sroi_prev).wait()
            img_prev = numpy.array(img_prev[0,...,0], dtype=numpy.float)
            
            if not self.Parameters.ready():
                raise Exception("Parameter slot is not ready")
            
            paras = self.Parameters.value
            templateSize = paras['templateSize']
            maxTranslation = paras['maxTranslation']
            overlap = paras['overlap']
            method = paras['method']   
            maxDiffVals = paras['maxDiffVals']                                 
                                                                                                            
            dest[t,...] = pgmlink.patchedOpticalTranslation(img_prev,
                                                            img_cur,
                                                            int(templateSize),
                                                            int(maxTranslation),
                                                            int(overlap),
                                                            method,
                                                            int(maxDiffVals))                                            
            self._processedTimeSteps.add(t)
            self.TranslationVectors._sig_value_changed()
    
    
    def execute(self, slot, subindex, roi, result):
#        with self._lock:
            if slot is self.TranslationVectorsComputation:
                self._computeTranslationVectors(roi, result)
            elif slot is self.TranslationVectors:
                start, stop = roi.start[0], roi.stop[0]
                for t in range(start, stop):
                    slc = (slice(t, t + 1),) + roi.toSlice()[1:]
                    dslc = slice(t - start, t - start + 1)
                    if t not in self._processedTimeSteps:
                        self._computeTranslationVectors(roi, result)                    
                    src = self._mem_h5['TranslationVectors']                    
                    result[dslc] = src[slc]
                return result
        
        
        
    def propagateDirty(self, slot, subindex, roi):
        if slot is self.BinaryImage or slot is self.Parameters:
            start, stop = roi.start[0], roi.stop[0]
            self.TranslationVectors.setDirty(slice(start,stop))
            for t in range(start, stop):
                try:
                    self._processedTimeSteps.remove(t)
                except KeyError:
                    continue
        else:
            print "Unknown dirty input slot: " + str(slot.name)    
