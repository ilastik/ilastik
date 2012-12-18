from PyQt4.QtGui import QWidget, QColor, QProgressDialog
from PyQt4 import uic
from PyQt4.QtCore import Qt, QString

from lazyflow.rtype import SubRegion
import os

from volumina.api import LazyflowSource, GrayscaleLayer, RGBALayer, ConstantSource, \
                         LayerStackModel, VolumeEditor, VolumeEditorWidget, ColortableLayer
import volumina.colortables as colortables


import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)


class ObjectExtractionMultiClassGui( QWidget ):
    """
    """
    
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget( self ):
        return self.volumeEditorWidget

    def appletDrawer( self ):
        return self._drawer

    def menus( self ):
        return []

    def viewerControlWidget( self ):
        return self._viewerControlWidget
            
    def stopAndCleanUp( self ):
        pass

    def reset( self ):
        print "reset(): not implemented"

    ###########################################
    ###########################################
    
    def __init__(self, topLevelOperatorView):
        """
        """
        super(ObjectExtractionMultiClassGui, self).__init__()
        self.mainOperator = topLevelOperatorView        
        self.layerstack = LayerStackModel()

        self._viewerControlWidget = None
        self._initViewerControlUi()

        self.editor = None
        self._initEditor()

        self._initAppletDrawerUi()
        assert(self.appletDrawer() is not None)
        self._initViewer()
        

    def _initViewer(self):       
        mainOperator = self.mainOperator        
        
        ct = colortables.create_default_8bit()
        self.binaryimages = LazyflowSource( mainOperator.BinaryImage )
#        layer = GrayscaleLayer( self.binaryimages, range=(0,1), normalize=(0,1) )
        ct[1] = QColor(0,0,0,0).rgba() # make 1 transparent      
#        ct[0] = QColor(0,0,0,255).rgba() # make 0 black  
        layer = ColortableLayer( self.binaryimages, ct )
        layer.name = "Input Image"
        layer.opacity = 0.5
        layer.visible = True        
        self.layerstack.append(layer)

        ct = colortables.create_default_16bit()
        self.objectssrc = LazyflowSource( mainOperator.LabelImage )
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent        
        layer = ColortableLayer( self.objectssrc, ct )
        layer.name = "Label Image"
        layer.opacity = 0.5
        layer.visible = True
        self.layerstack.append(layer)

        self.centerimagesrc = LazyflowSource( mainOperator.ObjectCenterImage )
        layer = RGBALayer( red=ConstantSource(255), alpha=self.centerimagesrc )
        layer.name = "Object Centers"
        layer.visible = False
        self.layerstack.append( layer )
                
#        self.distanceTransform = LazyflowSource( mainOperator.DistanceTransform )        
#        # FIXME range/normalize: magic numbers
#        layer = GrayscaleLayer( self.distanceTransform, range=(0,100), normalize=(0,5) )
#        layer.name = "Distance Transform Image"
#        layer.visible = False
#        self.layerstack.append(layer)
        
#        self.maxDistanceTransform = LazyflowSource( mainOperator.MaximumDistanceTransform )          
#        ct = colortables.create_default_8bit()
#        ct[1] = QColor(0,255,0,0).rgb() # make 1 green
#        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
#        ct[255] = QColor(255,255,255,0).rgba() # make 255 transparent
#        layer = ColortableLayer( self.maxDistanceTransform, ct )
#        layer.name = "Maximum Distance Image"
#        layer.visible = False
#        self.layerstack.append(layer)

        ## raw data layer
        self.rawsrc = None        
        self.rawsrc = LazyflowSource( self.mainOperator.RawImage )
        layerraw = GrayscaleLayer( self.rawsrc )
        layerraw.name = "Raw"
        layerraw.visible = True
        self.layerstack.insert( len(self.layerstack), layerraw )

        mainOperator.RawImage.notifyReady( self._onReady )
        mainOperator.RawImage.notifyMetaChanged( self._onMetaChanged )
    
        if mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = mainOperator.LabelImage.meta.shape
        mainOperator.Images.notifyMetaChanged( self._onMetaChanged )
        
        
    def _onMetaChanged( self, slot ):
        if slot is self.mainOperator.Images:
            if slot.meta.shape:
                self.editor.dataShape = slot.meta.shape
                
        if slot is self.mainOperator.RawImage:
            if slot.meta.shape and not self.rawsrc:
                self.rawsrc = LazyflowSource( self.mainOperator.RawImage )
                layerraw = GrayscaleLayer( self.rawsrc )
                layerraw.name = "Raw"
                self.layerstack.append( layerraw )
    
    def _onReady( self, slot ):
        if slot is self.mainOperator.RawImage:
            if slot.meta.shape and not self.rawsrc:
                self.rawsrc = LazyflowSource( self.mainOperator.RawImage )
                layerraw = GrayscaleLayer( self.rawsrc )
                layerraw.name = "Raw"
                self.layerstack.append( layerraw )
 
    def _initEditor(self):
        """
        Initialize the Volume Editor GUI.
        """

        self.editor = VolumeEditor(self.layerstack)

        self.volumeEditorWidget = VolumeEditorWidget()
        self.volumeEditorWidget.init(self.editor)

        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model = self.editor.layerStack
        model.canMoveSelectedUp.connect(self._viewerControlWidget.UpButton.setEnabled)
        model.canMoveSelectedDown.connect(self._viewerControlWidget.DownButton.setEnabled)
        model.canDeleteSelected.connect(self._viewerControlWidget.DeleteButton.setEnabled)     

        # Connect our layer movement buttons to the appropriate layerstack actions
        self._viewerControlWidget.layerWidget.init(model)
        self._viewerControlWidget.UpButton.clicked.connect(model.moveSelectedUp)
        self._viewerControlWidget.DownButton.clicked.connect(model.moveSelectedDown)
        self._viewerControlWidget.DeleteButton.clicked.connect(model.deleteSelected)

        self.editor._lastImageViewFocus = 0
        
            
    def _initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        self._drawer.labelImageButton.pressed.connect(self._onLabelImageButtonPressed)
        self._drawer.extractObjectsButton.pressed.connect(self._onExtractObjectsButtonPressed)
#        self._drawer.mergeSegmentationsButton.pressed.connect(self._onMergeSegmentationsButtonPressed)
#        self._drawer.distanceTransformButton.pressed.connect(self._onDistanceTransformButtonPressed)
#        self._drawer.maximumImageButton.pressed.connect(self._onMaximumImageButtonPressed)
        
#        self._drawer.doAllButton.pressed.connect(self._onDoAllButtonPressed)


    def _initViewerControlUi( self ):
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self._viewerControlWidget = uic.loadUi(p+"viewerControls.ui")

    def _onLabelImageButtonPressed( self ):
        m = self.mainOperator._opObjectExtraction.LabelImage.meta
        maxt = m.shape[0] - 1 # the last time frame will be dropped
        progress = QProgressDialog("Labeling Binary Images...", "Stop", 0, maxt)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButtonText(QString())
        progress.forceShow()

        reqs = []
        for t in range(maxt):            
            reqs.append(self.mainOperator._opObjectExtraction._opLabelImage.LabelImageComputation([t]))
            reqs[-1].submit()
                        
        for i, req in enumerate(reqs):
            progress.setValue(i)
            if progress.wasCanceled():
                req.cancel()
            else:
                req.wait()
                
        progress.setValue(maxt)        
        
        roi = SubRegion(self.mainOperator._opObjectExtraction.LabelImage, start=5*(0,), stop=m.shape)
        self.mainOperator._opObjectExtraction.LabelImage.setDirty(roi)
        
        print 'Label Segmentation: done.'


    def _onExtractObjectsButtonPressed( self ):
        maxt = self.mainOperator._opObjectExtraction.LabelImage.meta.shape[0] - 1 # the last time frame will be dropped
        progress = QProgressDialog("Extracting objects...", "Stop", 0, maxt)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButtonText(QString())

        reqs = []
        self.mainOperator._opObjectExtraction._opRegFeats.fixed = False
        for t in range(maxt):
            reqs.append(self.mainOperator._opObjectExtraction.RegionFeatures([t]))
            reqs[-1].submit()

        for i, req in enumerate(reqs):
            progress.setValue(i)
            if progress.wasCanceled():
                req.cancel()
            else:
                req.wait()
                
        self.mainOperator._opObjectExtraction._opRegFeats.fixed = True 
        progress.setValue(maxt)
                        
        print 'Object Extraction: done.'
        
        self._onMergeSegmentationsButtonPressed()


    def _onMergeSegmentationsButtonPressed(self):
        m = self.mainOperator._opObjectExtraction.LabelImage.meta
        maxt = m.shape[0] -1 # the last time frame will be dropped
        progress = QProgressDialog("Merging Background and Division Segmentations...", "Stop", 0, maxt)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButtonText(QString())
        progress.forceShow()

        reqs = []
        for t in range(maxt):
            reqs.append(self.mainOperator._opClassExtraction.ClassMapping([t]))
            reqs[-1].submit()
        for i, req in enumerate(reqs):
            progress.setValue(i)
            if progress.wasCanceled():
                req.cancel()
            else:
                req.wait()
        
        progress.setValue(maxt)
        
        roi = SubRegion(self.mainOperator.ClassMapping, start=5*(0,), stop=m.shape)
        self.mainOperator.ClassMapping.setDirty(roi)
        
        print 'Merge Segmentation: done.'
        
        
    def _onDistanceTransformButtonPressed(self):       
        m = self.mainOperator._opObjectExtraction.LabelImage.meta
        maxt = m.shape[0] -1 # the last time frame will be dropped
        progress = QProgressDialog("Computing the distance transform...", "Stop", 0, maxt)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButtonText(QString())
        progress.forceShow()        
                
        reqs = []        
        for t in range(maxt):
            reqs.append(self.mainOperator._opDistanceTransform.DistanceTransformComputation([t]))
            reqs[-1].submit()
        for i, req in enumerate(reqs):
            progress.setValue(i)
            if progress.wasCanceled():
                req.cancel()
            else:
                req.wait()
                
        progress.setValue(maxt)
        self.mainOperator._opDistanceTransform._fixed = False
        
        roi = SubRegion(self.mainOperator.DistanceTransform, start=5*(0,), stop=m.shape)
        self.mainOperator.DistanceTransform.setDirty(roi)
                
        print "Distance Transform: done."
    
    
    def _onMaximumImageButtonPressed(self):
        m = self.mainOperator._opObjectExtraction.LabelImage.meta
        maxt = m.shape[0] -1 # the last time frame will be dropped
        progress = QProgressDialog("Computing maximum distance transform...", "Stop", 0, 2*maxt)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButtonText(QString())
        progress.forceShow()        
        
        print "Computing Maximum Images"
        reqs = []        
        for t in range(maxt):
            reqs.append(self.mainOperator._opRegionalMaximum.MaximumImageComputation([t]))
            reqs[-1].submit()
            
        for i, req in enumerate(reqs):
            progress.setValue(i)
            if progress.wasCanceled():
                req.cancel()
            else:
                req.wait()
        self.mainOperator._opRegionalMaximum._fixed = False
        
        roi = SubRegion(self.mainOperator.MaximumDistanceTransform, start=5*(0,), stop=m.shape)
        self.mainOperator.MaximumDistanceTransform.setDirty(roi)
                         
        print "Computing Local Center Features"
        reqs = []
        for t in range(maxt):
            reqs.append(self.mainOperator._opRegionalMaximum.RegionLocalCenters([t]))
            reqs[-1].submit()
            
        for i, req in enumerate(reqs):
            progress.setValue(maxt+i)
            if progress.wasCanceled():
                req.cancel()
            else:
                req.wait()                                        
        progress.setValue(2*maxt)
                    
        print 'Maximum image: done'
        
        
#    def _onDoAllButtonPressed(self):    
#        self._onLabelImageButtonPressed()
#        self._onExtractObjectsButtonPressed()
#        self._onMergeSegmentationsButtonPressed()
