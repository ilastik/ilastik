from collections import defaultdict
import numpy

from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper

from volumina.adaptors import Op5ifyer

from opCarving import OpCarving

from ilastik.utility import OperatorSubView, OpAutoMultiLane

class OpCarvingTopLevel(Operator):
    name = "OpCarvingTopLevel"
    
    RawData = InputSlot(level=1)
    
    Segmentation = OutputSlot(level=1)
    DoneObjects = OutputSlot(level=1)
    HintOverlay = OutputSlot(level=1)
    DoneSegmentation = OutputSlot(level=1)
    Supervoxels = OutputSlot(level=1)

    ###
    # Multi-lane Operator
    ###
    
    def addLane(self, laneIndex):
        # Just add to our input slot, which will propagate to the rest of the internal connections
        assert len(self.RawData) == laneIndex
        self.RawData.resize(laneIndex+1)

    def removeLane(self, index, final_length):
        # Just remove from our input slot, which will propagate to the rest of the internal connections
        assert len(self.RawData) == final_length + 1
        self.RawData.removeSlot( index, final_length )

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)

    def __init__(self, parent=None, labelingOperator=None, carvingGraphFile=None, hintOverlayFile=None):
        super(OpCarvingTopLevel, self).__init__(parent=parent)

        # Convert data to 5d before giving it to the real operators
        op5 = OpAutoMultiLane( Op5ifyer, parent=self, graph=self.graph )
        op5.input.connect( self.RawData )
        
        a = operator_kwargs={'carvingGraphFilename': carvingGraphFile, 'hintOverlayFile': hintOverlayFile}
        self.opCarving = OpAutoMultiLane( OpCarving, operator_kwargs=a, parent=self )
        
        self.opLabeling = labelingOperator
        self.opLabeling.InputImages.connect( op5.output )
        
        self.opCarving.RawData.connect( op5.output )
        
        self.opCarving.WriteSeeds.connect(self.opLabeling.LabelInputs)

        # The GUI monitors all top-level slots to decide when to refresh.
        # Hook up these top-level slots so the GUI can find them.
        self.Segmentation.connect( self.opCarving.Segmentation )
        self.DoneObjects.connect( self.opCarving.DoneObjects )
        self.HintOverlay.connect( self.opCarving.HintOverlay )
        self.DoneSegmentation.connect( self.opCarving.DoneSegmentation )
        self.Supervoxels.connect( self.opCarving.Supervoxels )
        
        #for each imageindex, keep track of a set of object names that have changed since
        #the last serialization of this object to disk
        self._dirtyObjects = defaultdict(set)
    
    def _clear(self):
        #clear the labels 
        self.opLabeling.LabelDelete.setValue(2)
        self.opLabeling.LabelDelete.setValue(1)
        self.opLabeling.LabelDelete.setValue(-1)
        
    def saveObjectAs(self, name, opSubView):
        """
        TODO: This function should ideally be part of the single-image operator (opCarving),
        not this top-level operator.  For now, we have to pass in a sub-view that we can 
        use to determine which image index the GUI is using.
        """
        # Determine the image index we're dealing with.
        imageIndex = self.RawData.index( opSubView.RawData )
        
        # first, save the object under "name"
        self.opCarving.innerOperators[imageIndex].saveCurrentObjectAs(name)
        # Sparse label array automatically shifts label values down 1
        
        nonzeroSlicings = self.opLabeling.NonzeroLabelBlocks[imageIndex][:].wait()[0]
        
        #the voxel coordinates of fg and bg labels
        def coordinateList(): 
            coors1 = [[], [], []]
            coors2 = [[], [], []]
            for sl in nonzeroSlicings:
                a = self.opLabeling.LabelImages[imageIndex][sl].wait()
                w1 = numpy.where(a == 1)
                w2 = numpy.where(a == 2)
                w1 = [w1[i] + sl[i].start for i in range(1,4)]
                w2 = [w2[i] + sl[i].start for i in range(1,4)]
                for i in range(3):
                    coors1[i].append( w1[i] )
                    coors2[i].append( w2[i] )
            
            for i in range(3):
                coors1[i] = numpy.concatenate(coors1[i])
                coors2[i] = numpy.concatenate(coors2[i])
            return (coors2, coors1)
        fgVoxels, bgVoxels = coordinateList()
        
        self.opCarving.innerOperators[imageIndex].attachVoxelLabelsToObject(name, fgVoxels=fgVoxels, bgVoxels=bgVoxels)
       
        self._clear()
         
        # trigger a re-computation
        self.opCarving.innerOperators[imageIndex].Trigger.setDirty(slice(None))
        
        self._dirtyObjects[imageIndex].add(name)
        
    def loadObject(self, name, opSubView):
        """
        TODO: This function should ideally be part of the single-image operator (opCarving),
        not this top-level operator.  For now, we have to pass in a sub-view that we can 
        use to determine which image index the GUI is using.
        """
        # Determine the image index we're dealing with.
        imageIndex = self.RawData.index( opSubView.RawData )

        print "want to load object with name = %s" % name
        if not self.opCarving.innerOperators[imageIndex].hasObjectWithName(name):
            print "  --> no such object '%s'" % name 
            return False
        
        if opSubView.opCarving.hasCurrentObject():
            opSubView.opCarving.saveCurrentObject()
        self._clear()
        
        fgVoxels, bgVoxels = self.opCarving.innerOperators[imageIndex].loadObject(name)
        
        #if we want to supervoxelize the seeds, do this:
        #self.opLabeling.LabelInputs[imageIndex][:] = self.opCarving.innerOperators[imageIndex]._mst.seeds[:]
        
        #else:
        shape = self.opLabeling.LabelImages[imageIndex].meta.shape
        dtype = self.opLabeling.LabelImages[imageIndex].meta.dtype
        z = numpy.zeros(shape, dtype=dtype)
        z[0][fgVoxels] = 2
        z[0][bgVoxels] = 1
        self.opLabeling.LabelInputs[imageIndex][0:1, :shape[1],:shape[2],:shape[3]] = z[:,:,:]
        
        #restore the correct parameter values 
        o=self.opCarving
        mst = self.opCarving.innerOperators[imageIndex]._mst
        
        assert name in mst.object_lut
        assert name in mst.object_seeds_fg_voxels
        assert name in mst.object_seeds_bg_voxels
        assert name in mst.bg_priority
        assert name in mst.no_bias_below

        assert name in mst.bg_priority 
        assert name in mst.no_bias_below 
        
        o.BackgroundPriority.setValue( mst.bg_priority[name] )
        o.NoBiasBelow.setValue( mst.no_bias_below[name] )
        
        return True
        
    def deleteObject(self, name, opSubView):
        """
        TODO: This function should ideally be part of the single-image operator (opCarving),
        not this top-level operator.  For now, we have to pass in a sub-view that we can 
        use to determine which image index the GUI is using.
        """
        # Determine the image index we're dealing with.
        imageIndex = self.RawData.index( opSubView.RawData )

        print "want to delete object with name = %s" % name
        if not self.opCarving.innerOperators[imageIndex].hasObjectWithName(name):
            print "  --> no such object '%s'" % name 
            return False
        
        self.opCarving.innerOperators[imageIndex].deleteObject(name)
        #clear the user labels 
        self._clear()
        # trigger a re-computation
        self.opCarving.innerOperators[imageIndex].Trigger.setDirty(slice(None))
        self._dirtyObjects[imageIndex].add(name)
        
        return True
