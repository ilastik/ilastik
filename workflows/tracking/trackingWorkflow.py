from lazyflow.graph import Graph, Operator, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector

from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.objectExtraction import ObjectExtractionApplet
from ilastik.applets.tracking import TrackingApplet


from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader
from ilastik.applets.tracking.opTracking import *
import ctracking
class OpTrackingDataProvider( Operator ):
    Raw = OutputSlot()
    LabelImage = OutputSlot()
    Traxels = OutputSlot( stype=Opaque )

    def __init__( self, parent = None, graph = None, register = True ):
        super(OpTrackingDataProvider, self).__init__(parent=parent, graph=graph,register=register)
        self._traxel_cache = None

        self._rawReader = OpInputDataReader( graph )
        self._rawReader.FilePath.setValue('/home/bkausler/src/ilastik/tracking/relabeled-stack/objects.h5/raw')
        self.Raw.connect( self._rawReader.Output )

        self._labelImageReader = OpInputDataReader( graph )
        self._labelImageReader.FilePath.setValue('/home/bkausler/src/ilastik/tracking/relabeled-stack/objects.h5/objects')
        self.LabelImage.connect( self._labelImageReader.Output )

    def setupOutputs( self ):
        self.Traxels.meta.shape = self.Raw.meta.shape
        self.Traxels.meta.dtype = self.Raw.meta.dtype

    def execute( self, slot, roi, result ):
        if slot is self.Traxels:
            if self._traxel_cache:
                return self._traxel_cache
            else:
                print "extract traxels"
                self._traxel_cache = ctracking.TraxelStore()
                f = h5py.File("/home/bkausler/src/ilastik/tracking/relabeled-stack/regioncenter.h5", 'r')
                for t in range(15):
                    og = f['samples/'+str(t)+'/objects']
                    traxels = cTraxels_from_objects_group( og, t)
                    self._traxel_cache.add_from_Traxels(traxels)
                    print "-- extracted %d traxels at t %d" % (len(traxels), t)
                f.close()
                return self._traxel_cache



class TrackingWorkflow( Workflow ):
    def __init__( self ):
        super(TrackingWorkflow, self).__init__()
        self._applets = []
        self._imageNameListSlot = None
        self._graph = None

        # Create a graph to be shared by all operators
        graph = Graph()
    
        ######################
        # Interactive workflow
        ######################
        
        ## Create applets 
        self.dataSelectionApplet = DataSelectionApplet(graph, "Input Segmentation", "Input Segmentation", batchDataGui=False)

        self.objectExtractionApplet = ObjectExtractionApplet( graph )
        #self.trackingApplet = TrackingApplet( graph )

        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator
        opObjExtraction = self.objectExtractionApplet.topLevelOperator
        #opTracking = self.trackingApplet.topLevelOperator
        
        ## Connect operators ##
        dataProv = OpTrackingDataProvider( graph=graph )
        opObjExtraction.BinaryImage.connect( opData.Image )

        #opTracking.LabelImage.connect( opObjExtraction.LabelImage )
        #opTracking.LabelImage.connect( dataProv.LabelImage )        

        #opTracking.RawData.connect( dataProv.Raw )
        #opTracking.Traxels.connect( dataProv.Traxels )
        #opTracking.ObjectCenters.connect( opObjExtraction.RegionCenters )

        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.objectExtractionApplet)
        #self._applets.append(self.trackingApplet)

        # The shell needs a slot from which he can read the list of image names to switch between.
        # Use an OpAttributeSelector to create a slot containing just the filename from the OpDataSelection's DatasetInfo slot.
        opSelectFilename = OperatorWrapper( OpAttributeSelector(graph=graph) )
        opSelectFilename.InputObject.connect( opData.Dataset )
        opSelectFilename.AttributeName.setValue( 'filePath' )

        self._imageNameListSlot = opSelectFilename.Result

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self._imageNameListSlot
    
