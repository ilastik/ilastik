#Python
import time
import numpy, h5py
import copy

#carving
from cylemon.segmentation import MSTSegmentor

#Lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import List

from cylemon.segmentation import MSTSegmentor

from lazyflow.operators.opDenseLabelArray import OpDenseLabelArray


class OpCarving(Operator):
    name = "Carving"
    category = "interactive segmentation"

    # I n p u t s #
    
    #MST of preprocessed Graph
    MST = InputSlot()

    # These three slots are for display only.
    # All computation is done with the MST.    
    RawData = InputSlot(optional=True) # Display-only: Available to the GUI in case the input data was preprocessed in some way but you still want to see the 'raw' data.
    InputData = InputSlot() # The data used by preprocessing (display only)
    FilteredInputData = InputSlot() # The output of the preprocessing filter
    
    #write the seeds that the users draw into this slot
    WriteSeeds   = InputSlot()

    #trigger an update by writing into this slot
    Trigger      = InputSlot(value = numpy.zeros((1,), dtype=numpy.uint8))

    #number between 0.0 and 1.0
    #bias of the background
    #FIXME: correct name?
    BackgroundPriority = InputSlot(value=0.95)

    #a number between 0 and 256
    #below the number, no background bias will be applied to the edge weights
    NoBiasBelow        = InputSlot(value=64)

    # uncertainty type
    UncertaintyType = InputSlot()

    LabelsAllowed = InputSlot(value=True)

    # O u t p u t s #

    #current object + background
    Segmentation = OutputSlot()

    Supervoxels  = OutputSlot()

    Uncertainty = OutputSlot()

    #contains an array with the object labels done so far, one label for each
    #object
    DoneObjects  = OutputSlot()

    #contains an array with where all objects done so far are labeled the same
    DoneSegmentation = OutputSlot()
    
    CurrentObjectName = OutputSlot(stype='string')
    
    AllObjectNames = OutputSlot(rtype=List, stype=Opaque)
    
    #current object has an actual segmentation
    HasSegmentation   = OutputSlot(stype='bool')
    
    #Hint Overlay
    HintOverlay = OutputSlot()
    
    #Pmap Overlay
    PmapOverlay = OutputSlot()

    def __init__(self, graph=None, hintOverlayFile=None, pmapOverlayFile=None, parent=None):
        super(OpCarving, self).__init__(graph=graph, parent=parent)
        self.opLabelArray = OpDenseLabelArray( parent=self )
        self.opLabelArray.EraserLabelValue.setValue( 100 )
        self.opLabelArray.MetaInput.connect( self.InputData )
        
        self._hintOverlayFile = hintOverlayFile
        self._mst = None

        #supervoxels of finished and saved objects
        self._done_lut = None
        self._done_seg_lut = None
        self._hints = None
        self._pmap = None
        if hintOverlayFile is not None:
            try:
                f = h5py.File(hintOverlayFile,"r")
            except Exception as e:
                print "Could not open hint overlay '%s'" % hintOverlayFile
                raise e
            self._hints  = f["/hints"].value[numpy.newaxis, :,:,:, numpy.newaxis]
        
        if pmapOverlayFile is not None:
            try:
                f = h5py.File(pmapOverlayFile,"r")
            except Exception as e:
                raise RuntimeError("Could not open pmap overlay '%s'" % pmapOverlayFile)
            self._pmap  = f["/data"].value[numpy.newaxis, :,:,:, numpy.newaxis]

        self._setCurrObjectName("")
        self.HasSegmentation.setValue(False)
        
        # keep track of a set of object names that have changed since
        # the last serialization of this object to disk
        self._dirtyObjects = set()
        
    def _clearLabels(self):
        #clear the labels 
        self.opLabelArray.DeleteLabel.setValue(2)
        self.opLabelArray.DeleteLabel.setValue(1)
        self.opLabelArray.DeleteLabel.setValue(-1)
        
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
        for name, objectSupervoxels in self._mst.object_lut.iteritems():
            if name == self._currObjectName:
                continue
            self._done_lut[objectSupervoxels] += 1
            assert name in self._mst.object_names, "%s not in self._mst.object_names, keys are %r" % (name, self._mst.object_names.keys())
            self._done_seg_lut[objectSupervoxels] = self._mst.object_names[name]
        print ""
    
    def dataIsStorable(self):
        lut_seeds = self._mst.seeds.lut[:]
        fg_seedNum = len(numpy.where(lut_seeds == 2)[0])
        bg_seedNum = len(numpy.where(lut_seeds == 1)[0])
        if not (fg_seedNum > 0 and bg_seedNum > 0):
            return False
        else:
            return True
        
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
        self._checkMeta(self.InputData)
        
        self.Segmentation.meta.assignFrom(self.InputData.meta)
        self.Segmentation.meta.dtype = numpy.int32
        
        self.Supervoxels.meta.assignFrom(self.Segmentation.meta)
        self.DoneObjects.meta.assignFrom(self.Segmentation.meta)
        self.DoneSegmentation.meta.assignFrom(self.Segmentation.meta)

        self.HintOverlay.meta.assignFrom(self.InputData.meta)
        self.PmapOverlay.meta.assignFrom(self.InputData.meta)

        self.Uncertainty.meta.assignFrom(self.InputData.meta)
        self.Uncertainty.meta.dtype = numpy.uint8

        self.Trigger.meta.shape = (1,)
        self.Trigger.meta.dtype = numpy.uint8

        if self._mst is not None:
            objects = self._mst.object_names.keys()
            self.AllObjectNames.meta.shape = len(objects)
        else: 
            self.AllObjectNames.meta.shape = 0
        
        self.AllObjectNames.meta.dtype = object

    def hasCurrentObject(self):
        """
        Returns current object name. None if it is not set.
        """
        #FIXME: This is misleading. Having a current object and that object having
        #a name is not the same thing.
        return self._currObjectName

    def currentObjectName(self):
        """
        Returns current object name. Return "" if no current object
        """
        assert self._currObjectName is not None, "FIXME: This function should either return '' or None.  Why does it sometimes return one and then the other?"
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
    def clearCurrentLabeling(self, trigger_recompute=True):
        """
        Clears the current labeling.
        """
        self._clearLabels()

        self._mst.seeds[:] = 0
        lut_segmentation = self._mst.segmentation.lut[:]
        lut_segmentation[:] = 0
        lut_seeds = self._mst.seeds.lut[:]
        lut_seeds[:] = 0
        self.HasSegmentation.setValue(False)

        self.Trigger.setDirty(slice(None))
                
    def loadObject_impl(self, name):
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
    
    def loadObject(self, name):
        print "want to load object with name = %s" % name
        if not self.hasObjectWithName(name):
            print "  --> no such object '%s'" % name 
            return False
        
        if self.hasCurrentObject():
            self.saveCurrentObject()
        self._clearLabels()
        
        fgVoxels, bgVoxels = self.loadObject_impl(name)
        
        shape = self.opLabelArray.Output.meta.shape
        dtype = self.opLabelArray.Output.meta.dtype

        z = numpy.zeros(shape, dtype=dtype)
        z[0][fgVoxels] = 2
        z[0][bgVoxels] = 1
        self.WriteSeeds[0:1, :shape[1],:shape[2],:shape[3]] = z[:,:,:]
        
        #restore the correct parameter values 
        mst = self._mst
        
        assert name in mst.object_lut
        assert name in mst.object_seeds_fg_voxels
        assert name in mst.object_seeds_bg_voxels
        assert name in mst.bg_priority
        assert name in mst.no_bias_below

        assert name in mst.bg_priority 
        assert name in mst.no_bias_below 
        
        self.BackgroundPriority.setValue( mst.bg_priority[name] )
        self.NoBiasBelow.setValue( mst.no_bias_below[name] )
        
        return True

    
    @Operator.forbidParallelExecute
    def deleteObject_impl(self, name):
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
        
        #delete it from object_names, as it indicates
        #whether the object exists
        del self._mst.object_names[name]

        self._setCurrObjectName("")

        #now that 'name' has been deleted, rebuild the done overlay
        self._buildDone()
    
    def deleteObject(self, name):
        print "want to delete object with name = %s" % name
        if not self.hasObjectWithName(name):
            print "  --> no such object '%s'" % name 
            return False
        
        self.deleteObject_impl(name)
        #clear the user labels 
        self._clearLabels()
        # trigger a re-computation
        self.Trigger.setDirty(slice(None))
        self._dirtyObjects.add(name)
        
        objects = self._mst.object_names.keys()
        print "save: len = ", len(objects)
        self.AllObjectNames.meta.shape = len(objects)
        
        return True
    
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

        objects = self._mst.object_names.keys()
        self.AllObjectNames.meta.shape = len(objects)

        #now that 'name' is no longer part of the set of finished objects, rebuild the done overlay
        self._buildDone()


    def get_label_voxels(self):
        nonzeroSlicings = self.opLabelArray.NonzeroBlocks[:].wait()[0]
        
        #the voxel coordinates of fg and bg labels
        coors1 = [[], [], []]
        coors2 = [[], [], []]
        for sl in nonzeroSlicings:
            a = self.opLabelArray.Output[sl].wait()
            w1 = numpy.where(a == 1)
            w2 = numpy.where(a == 2)
            w1 = [w1[i] + sl[i].start for i in range(1,4)]
            w2 = [w2[i] + sl[i].start for i in range(1,4)]
            for i in range(3):
                coors1[i].append( w1[i] )
                coors2[i].append( w2[i] )
        
        for i in range(3):
            if len(coors1[i]) > 0:
                coors1[i] = numpy.concatenate(coors1[i],0)
            else:
                coors1[i] = numpy.ndarray((0,), numpy.int32)
            if len(coors2[i]) > 0:
                coors2[i] = numpy.concatenate(coors2[i],0)
            else:
                coors2[i] = numpy.ndarray((0,), numpy.int32)
        return (coors2, coors1)

    
    def saveObjectAs(self, name):
        """
        TODO: This function should ideally be part of the single-image operator (opCarving),
        not this top-level operator.  For now, we have to pass in a sub-view that we can 
        use to determine which image index the GUI is using.
        """        
        # first, save the object under "name"
        self.saveCurrentObjectAs(name)
        # Sparse label array automatically shifts label values down 1
        
        fgVoxels, bgVoxels = self.get_label_voxels()
        
        self.attachVoxelLabelsToObject(name, fgVoxels=fgVoxels, bgVoxels=bgVoxels)
       
        self._clearLabels()
         
        # trigger a re-computation
        self.Trigger.setDirty(slice(None))
        
        self._dirtyObjects.add(name)


    def getMaxUncertaintyPos(self, label):
        # FIXME: currently working on
        uncertainties = self._mst.uncertainty.lut
        segmentation = self._mst.segmentation.lut
        uncertainty_fg = numpy.where(segmentation == label, uncertainties, 0)
        index_max_uncert = numpy.argmax(uncertainty_fg, axis = 0)
        pos = self._mst.regionCenter[index_max_uncert, :]

        return pos

    def execute(self, slot, subindex, roi, result):
        start = time.time()
        
        self._mst = self.MST.value
        
        if slot == self.AllObjectNames:
            ret = self._mst.object_names.keys()
            return ret
        
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
        elif slot == self.PmapOverlay:
            if self._pmap is None:
                result[:] = 0
                return result
            else:
                result[:] = self._pmap[roi.toSlice()]
                return result
        elif slot == self.Uncertainty:
            temp = self._mst.uncertainty[sl[1:4]]
            temp.shape = (1,) + temp.shape + (1,)
        else:
            raise RuntimeError("unknown slot")
        return temp #avoid copying data

    def setInSlot(self, slot, subindex, roi, value):
        key = roi.toSlice()
        if slot == self.WriteSeeds: 
            self.opLabelArray.LabelSinkInput[roi.toSlice()] = value
            
            assert self._mst is not None

            value = numpy.where(value == 100, 255, value[:])

            if hasattr(key, '__len__'):
                self._mst.seeds[key[1:4]] = value
            else:
                self._mst.seeds[key] = value

        else:
            raise RuntimeError("unknown slots")

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Trigger or slot == self.BackgroundPriority or slot == self.NoBiasBelow or slot == self.UncertaintyType:
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
            params["uncertainty"] = self.UncertaintyType.value
            params["noBiasBelow"] = noBiasBelow

            unaries =  numpy.zeros((self._mst.numNodes,labelCount+1), dtype=numpy.float32)
            #assert numpy.sum(self._mst.seeds > 2) == 0, "seeds > 2 at %r" % numpy.where(self._mst.seeds > 2)
            self._mst.run(unaries, **params)

            self.Segmentation.setDirty(slice(None))
            self.HasSegmentation.setValue(True)
        elif slot == self.MST:
            self._mst = self.MST.value
