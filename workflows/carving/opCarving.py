import numpy
import time

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque

from cylemon.segmentation import MSTSegmentor

class OpCarving(Operator):
    name = "Carving"
    category = "interactive segmentation"
    
    # I n p u t s #
    
    #filename of the pre-processed carving graph file 
    CarvingGraphFile = InputSlot()
            
    #raw data on which carving works
    RawData      = InputSlot() 
    
    #write the seeds that the users draw into this slot 
    WriteSeeds   = InputSlot() 
    
    #trigger an update by writing into this slot
    Trigger      = InputSlot(value = numpy.zeros((1,), dtype=numpy.uint8))
   
    #number between 0.0 and 1.0 
    #bias of the background
    #FIXME: correct name?
    BackgroundPriority = InputSlot()
    
    #a number between 0 and 256
    #below the number, no background bias will be applied to the edge weights
    NoBiasBelow        = InputSlot()
    
    # O u t p u t s #
    
    #current object + background
    Segmentation = OutputSlot()
    
    Supervoxels  = OutputSlot()
    
    #contains an array with the object labels done so far, one label for each 
    #object
    DoneObjects  = OutputSlot()
    
    #contains an array with where all objects done so far are labeled the same
    DoneSegmentation = OutputSlot()
    
    CurrentObjectName = OutputSlot(stype=Opaque)
    
    #current object has an actual segmentation
    HasSegmentation   = OutputSlot(stype=Opaque)
    
    #Hint Overlay
    HintOverlay = OutputSlot()
    
    def __init__(self, graph=None, carvingGraphFilename=None, hintOverlayFile=None, parent=None):
        super(OpCarving, self).__init__(graph=graph, parent=parent)
        print "[Carving id=%d] CONSTRUCTOR" % id(self) 
        self._mst = MSTSegmentor.loadH5(carvingGraphFilename,  "graph")
        self._hintOverlayFile = hintOverlayFile
        
        #supervoxels of finished and saved objects 
        self._done_lut = None
        self._done_seg_lut = None
        self._hints = None
        if hintOverlayFile is not None:
            try:
                f = h5py.File(hintOverlayFile,"r")
            except:
                raise RuntimeError("Could not open hint overlay '%s'" % hintOverlayFile)
            self._hints  = f["/hints"].value[numpy.newaxis, :,:,:, numpy.newaxis]
       
        self._setCurrObjectName("")
        self.HasSegmentation.setValue(False)
    
    
    def _setCurrObjectName(self, n):
        """
        Sets the current object name to n.
        """
        self._currObjectName = n
        self.CurrentObjectName.setValue(n)
   
    def _buildDone(self):
        """
        Builds the done segmentation anew, for example after saving an object or
        deleting an object.
        """
        self._done_lut = numpy.zeros(len(self._mst.objects.lut), dtype=numpy.int32) 
        self._done_seg_lut = numpy.zeros(len(self._mst.objects.lut), dtype=numpy.int32)
        print "building done"
        for i, (name, objectSupervoxels) in enumerate(self._mst.object_lut.iteritems()): 
            if name == self._currObjectName:
                continue
            print name,
            self._done_lut[objectSupervoxels] += 1
            self._done_seg_lut[objectSupervoxels] = i+1
        print ""
   
    def dataIsStorable(self):
        seed = 2
        lut_seeds = self._mst.seeds.lut[:]
        fg_seedNum = len(numpy.where(lut_seeds == 2)[0])
        bg_seedNum = len(numpy.where(lut_seeds == 1)[0])
        if not (fg_seedNum > 0 and bg_seedNum > 0):
            return False
        else:
            return True
   
    def setupOutputs(self):
        self.Segmentation.meta.assignFrom(self.RawData.meta)
        self.Supervoxels.meta.assignFrom(self.RawData.meta)
        self.DoneObjects.meta.assignFrom(self.RawData.meta)
        self.DoneSegmentation.meta.assignFrom(self.RawData.meta)
        self.HintOverlay.meta.assignFrom(self.RawData.meta)
        
        self.Trigger.meta.shape = (1,)
        self.Trigger.meta.dtype = numpy.uint8
        
    def hasCurrentObject(self):
        """
        Returns current object name. None if it is not set.
        """
        #FIXME: This is misleading. Having a current object and that object having
        #a name is not the same thing.
        return self._currObjectName
    
    def currentObjectName(self):
        """
        Returns current object name. None if it is not set.
        """
        return self._currObjectName
    
    def hasObjectWithName(self, name):
        """
        Returns True if object with name is existent. False otherwise.
        """ 
        return name in self._mst.object_lut
    
    def doneObjectNamesForPosition(self, position3d):
        """
        Returns a list of names of objects which occupy a specific 3D position.
        List is empty if there are no objects present.
        """
        assert len(position3d) == 3
          
        #find the supervoxel that was clicked 
        sv = self._mst.regionVol[position3d]
        names = []
        for name, objectSupervoxels in self._mst.object_lut.iteritems(): 
            if numpy.sum(sv == objectSupervoxels) > 0: 
                names.append(name)
        print "click on %r, supervoxel=%d: %r" % (position3d, sv, names)
        return names
    
    @Operator.forbidParallelExecute
    def attachVoxelLabelsToObject(self, name, fgVoxels, bgVoxels):
        """
        Attaches Voxellabes to an object called name.
        """
        self._mst.object_seeds_fg_voxels[name] = fgVoxels
        self._mst.object_seeds_bg_voxels[name] = bgVoxels
  
    @Operator.forbidParallelExecute
    def clearCurrentLabeling(self):
        """
        Clears the current labeling.
        """
        self._mst.seeds[:] = 0
        lut_segmentation = self._mst.segmentation.lut[:]
        lut_segmentation[:] = 0
        lut_seeds = self._mst.seeds.lut[:]
        lut_seeds[:] = 0
        self.HasSegmentation.setValue(False)
                
    def loadObject(self, name):
        """
        Loads a single object called name to be the currently edited object. Its
        not part of the done segmentation anymore. 
        """
        assert self._mst is not None
        print "[OpCarving] load object %s (opCarving=%d, mst=%d)" % (name, id(self), id(self._mst)) 
        
        assert name in self._mst.object_lut
        assert name in self._mst.object_seeds_fg_voxels
        assert name in self._mst.object_seeds_bg_voxels
        assert name in self._mst.bg_priority
        assert name in self._mst.no_bias_below
            
        lut_segmentation = self._mst.segmentation.lut[:]
        lut_objects = self._mst.objects.lut[:]
        lut_seeds = self._mst.seeds.lut[:]
        # clean seeds
        lut_seeds[:] = 0

        # set foreground and background seeds
        fgVoxels = self._mst.object_seeds_fg_voxels[name]
        bgVoxels = self._mst.object_seeds_bg_voxels[name]
       
        #user-drawn seeds:
        self._mst.seeds[:] = 0
        self._mst.seeds[fgVoxels] = 2
        self._mst.seeds[bgVoxels] = 1

        newSegmentation = numpy.ones(len(lut_objects), dtype=numpy.int32) 
        newSegmentation[ self._mst.object_lut[name] ] = 2
        lut_segmentation[:] = newSegmentation
        
        self._setCurrObjectName(name)
        self.HasSegmentation.setValue(False)
       
        #now that 'name' is no longer part of the set of finished objects, rebuild the done overlay 
        self._buildDone()
        return (fgVoxels, bgVoxels)
    
    @Operator.forbidParallelExecute
    def deleteObject(self, name):
        """
        Deletes an object called name.
        """
        lut_seeds = self._mst.seeds.lut[:]
        # clean seeds
        lut_seeds[:] = 0
        self._mst.seeds[:] = 0
        
        del self._mst.object_lut[name]
        del self._mst.object_seeds_fg_voxels[name]
        del self._mst.object_seeds_bg_voxels[name]
        del self._mst.bg_priority[name]
        del self._mst.no_bias_below[name]
        
        self._setCurrObjectName("")
        
        #now that 'name' has been deleted, rebuild the done overlay 
        self._buildDone()
    
    @Operator.forbidParallelExecute
    def saveCurrentObject(self):
        """
        Saves the objects which is currently edited.
        """
        if self._currObjectName:
            name = copy.copy(self._currObjectName)
            print "saving object %s" % self._currObjectName
            self.saveCurrentObjectAs(self._currObjectName)
            return name
        return ""
    
    @Operator.forbidParallelExecute
    def saveCurrentObjectAs(self, name):
        """
        Saves current object as name.
        """
        seed = 2
        print "   --> Saving object %r from seed %r" % (name, seed)
        if self._mst.object_names.has_key(name):
            objNr = self._mst.object_names[name]
        else:
            # find free objNr
            if len(self._mst.object_names.values())> 0:
                objNr = numpy.max(numpy.array(self._mst.object_names.values())) + 1
            else:
                objNr = 1

        #delete old object, if it exists
        lut_objects = self._mst.objects.lut[:]
        lut_objects[:] = numpy.where(lut_objects == objNr, 0, lut_objects)

        #save new object 
        lut_segmentation = self._mst.segmentation.lut[:]
        lut_objects[:] = numpy.where(lut_segmentation == seed, objNr, lut_objects)
        
        objectSupervoxels = numpy.where(lut_segmentation == seed)
        self._mst.object_lut[name] = objectSupervoxels

        #save object name with objNr
        self._mst.object_names[name] = objNr

        lut_seeds = self._mst.seeds.lut[:]
  
        # save object seeds
        self._mst.object_seeds_fg[name] = numpy.where(lut_seeds == seed)[0]
        self._mst.object_seeds_bg[name] = numpy.where(lut_seeds == 1)[0] #one is background=
       
        # reset seeds 
        self._mst.seeds[:] = numpy.int32(-1) #see segmentation.pyx: -1 means write zeros
       
        #numpy.asarray([BackgroundPriority.value()], dtype=numpy.float32)
        #numpy.asarray([NoBiasBelow.value()], dtype=numpy.int32)
        self._mst.bg_priority[name] = self.BackgroundPriority.value
        self._mst.no_bias_below[name] = self.NoBiasBelow.value
        
        self._setCurrObjectName("")
        self.HasSegmentation.setValue(False)
        
        #now that 'name' is no longer part of the set of finished objects, rebuild the done overlay 
        self._buildDone()
    
    def execute(self, slot, subindex, roi, result):
        start = time.time()
        
        if self._mst is None:
            return
        sl = roi.toSlice()
        if slot == self.Segmentation:
            #avoid data being copied
            temp = self._mst.segmentation[sl[1:4]]
            temp.shape = (1,) + temp.shape + (1,)
        elif slot == self.Supervoxels:
            #avoid data being copied
            temp = self._mst.regionVol[sl[1:4]]
            temp.shape = (1,) + temp.shape + (1,)
        elif slot  == self.DoneObjects:
            #avoid data being copied
            if self._done_lut is None:
                result[0,:,:,:,0] = 0
                return result
            else:
                temp = self._done_lut[self._mst.regionVol[sl[1:4]]]
                temp.shape = (1,) + temp.shape + (1,)
        elif slot  == self.DoneSegmentation:
            #avoid data being copied
            if self._done_seg_lut is None:
                result[0,:,:,:,0] = 0
                return result
            else:
                temp = self._done_seg_lut[self._mst.regionVol[sl[1:4]]]
                temp.shape = (1,) + temp.shape + (1,)
        elif slot == self.HintOverlay:
            if self._hints is None:
                result[:] = 0
                return result
            else: 
                result[:] = self._hints[roi.toSlice()]
                return result
        else:
            raise RuntimeError("unknown slot")
        
        return temp #avoid copying data
    
    def setInSlot(self, slot, subindex, roi, value):
        key = roi.toSlice()
        if slot == self.WriteSeeds: 
            assert self._mst is not None
        
            value = numpy.where(value == 100, 255, value[:])
            
            if hasattr(key, '__len__'):
                self._mst.seeds[key[1:4]] = value
            else:
                self._mst.seeds[key] = value
                
        else:
            raise RuntimeError("unknown slots")
        
    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        if slot == self.Trigger or slot == self.BackgroundPriority or slot == self.NoBiasBelow: 
            if self._mst is None:
                return 
            if not self.BackgroundPriority.ready():
                return
            if not self.NoBiasBelow.ready():
                return
            
            bgPrio = self.BackgroundPriority.value
            noBiasBelow = self.NoBiasBelow.value
            print "compute new carving results with bg priority = %f, no bias below %d" % (bgPrio, noBiasBelow)
           
            labelCount = 2
            
            params = dict()
            params["prios"] = [1.0, bgPrio, 1.0] 
            params["uncertainty"] = "none" 
            params["noBiasBelow"] = noBiasBelow 
            
            unaries =  numpy.zeros((self._mst.numNodes,labelCount+1)).astype(numpy.float32)
            #assert numpy.sum(self._mst.seeds > 2) == 0, "seeds > 2 at %r" % numpy.where(self._mst.seeds > 2)
            self._mst.run(unaries, **params)
            
            self.Segmentation.setDirty(slice(None))
            self.HasSegmentation.setValue(True)
            
        elif slot == self.CarvingGraphFile:
            if self._mst is not None:
                #if the carving graph file is not valid, all outputs must be invalid
                for output in self.outputs.values():
                    output.setDirty(slice(0,None))
           
            #FIXME: currently, the carving graph file is loaded in the constructor
            #       refactor such that it is only loaded here
            ''' 
            fname = self.CarvingGraphFile.value
            
            self._mst = MSTSegmentor.loadH5(fname,  "graph")
            print "[Carving id=%d] loading graph file %s (mst=%d)" % (id(self), fname, id(self._mst)) 
            '''
            
            self.Segmentation.setDirty(slice(None))
            
        else:
            super(OpCarving, self).notifyDirty(slot, key) 
    