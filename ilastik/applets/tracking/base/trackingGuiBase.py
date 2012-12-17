from PyQt4.QtGui import QWidget, QColor, QFileDialog
from PyQt4 import uic

from volumina.api import LazyflowSource, LayerStackModel, VolumeEditor, VolumeEditorWidget, ColortableLayer
import volumina.colortables as colortables

from lazyflow.operators.obsolete.generic import axisTagsToString
from lazyflow.rtype import SubRegion
from lazyflow.tracer import Tracer

import logging
import os
import numpy as np
import vigra
from ilastik.applets.tracking.base.trackingUtilities import relabel,write_events
from volumina.layer import GrayscaleLayer

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

class TrackingGuiBase( QWidget ):
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
        print "TrackinGui.reset(): not implemented"

    
    ###########################################
    ###########################################
    
    def __init__(self, mainOperator):
        """
        """
        super(TrackingGuiBase, self).__init__()
        self.mainOperator = mainOperator
        self.layerstack = LayerStackModel()

        self._viewerControlWidget = None
        self._initViewerControlUi()
        
        self.initColors()
        
        self.editor = None
        self._initEditor()

        self._initAppletDrawerUi()
        
        if self.mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = self.mainOperator.LabelImage.meta.shape
        self.mainOperator.LabelImage.notifyMetaChanged( self._onMetaChanged)
        self._initViewer()


    def _onMetaChanged( self, slot ):
        if slot is self.mainOperator.LabelImage:
            if slot.meta.shape:
                print slot.meta.shape
                self.editor.dataShape = slot.meta.shape

                maxt = slot.meta.shape[0]
                self._drawer.from_time.setRange(0,maxt-1)
                self._drawer.from_time.setValue(0)
                self._drawer.to_time.setRange(0,maxt-2)
                self._drawer.to_time.setValue(maxt-2)
                self._drawer.lineageFromBox.setRange(0,maxt-1)
                self._drawer.lineageToBox.setRange(0,maxt-2)
                self._drawer.lineageFromBox.setValue(0)
                self._drawer.lineageToBox.setValue(maxt-2)
        


    def _initViewer( self ):
        mainOperator = self.mainOperator

        self.objectssrc = LazyflowSource( mainOperator.LabelImage )
#        ct = colortables.create_default_8bit()
        ct = colortables.create_random_8bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        layer = ColortableLayer( self.objectssrc, ct )
        layer.name = "Objects"
        self.layerstack.append(layer)

        ct[255] = QColor(255,255,255,230).rgba() # misdetections
        self.trackingsrc = LazyflowSource( mainOperator.Output )
        layer = ColortableLayer( self.trackingsrc, ct )
        layer.name = "Tracking"
        self.layerstack.append(layer)
        
        if "MergerOutput" in mainOperator.outputs:
            ct = colortables.create_default_8bit()
            for i in range(7):
                ct[i] = self.mergerColors[i].rgba()
            self.mergersrc = LazyflowSource( mainOperator.MergerOutput )
            layer = ColortableLayer( self.mergersrc, ct )
            layer.name = "Merger"
            layer.visible = True
            self.layerstack.append(layer)        

        if mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = mainOperator.LabelImage.meta.shape

            maxt = mainOperator.LabelImage.meta.shape[0]
            maxx = mainOperator.LabelImage.meta.shape[1]
            maxy = mainOperator.LabelImage.meta.shape[2]
            maxz = mainOperator.LabelImage.meta.shape[3]            
            self._drawer.from_time.setRange(0,maxt-1)
            self._drawer.from_time.setValue(0)
            self._drawer.to_time.setRange(0,maxt-2)
            self._drawer.to_time.setValue(maxt-2)   

            self._drawer.from_x.setRange(0,maxx-1)
            self._drawer.from_x.setValue(0)
            self._drawer.to_x.setRange(0,maxx-1)
            self._drawer.to_x.setValue(maxx-1)       
        
            self._drawer.from_y.setRange(0,maxy-1)
            self._drawer.from_y.setValue(0)
            self._drawer.to_y.setRange(0,maxy-1)
            self._drawer.to_y.setValue(maxy-1)       

            self._drawer.from_z.setRange(0,maxz-1)
            self._drawer.from_z.setValue(0)
            self._drawer.to_z.setRange(0,maxz-1)
            self._drawer.to_z.setValue(maxz-1)
            
            self._drawer.lineageFromBox.setRange(0,maxt-1)
            self._drawer.lineageFromBox.setValue(0)
            self._drawer.lineageToBox.setRange(0,maxt-2)
            self._drawer.lineageToBox.setValue(maxt-2)    
        
        ## raw data layer
        self.rawsrc = None
        self.rawsrc = LazyflowSource( self.mainOperator.RawImage )
        layerraw = GrayscaleLayer( self.rawsrc )
        layerraw.name = "Raw"
        self.layerstack.insert( len(self.layerstack), layerraw )   
    

    def initColors(self):
        self.mergerColors = [
                             QColor(0,0,0,0),
                             QColor(1,1,1,0),
                             QColor(255,0,0,255),
                             QColor(0,255,0,255),
                             QColor(0,0,255,255),
                             QColor(255,128,128,255),
                             QColor(128,255,128,255),
                             QColor(128,128,255,255)
                             ]
        


    def _initEditor(self):
        """
        Initialize the Volume Editor GUI.
        """

        self.editor = VolumeEditor(self.layerstack)

        #self.editor.newImageView2DFocus.connect(self.setIconToViewMenu)
        #self.editor.setInteractionMode( 'navigation' )
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

    def _labelSetStyleSheet(self, qlabel, qcolor):        
        qlabel.setAutoFillBackground(True)                 
        values = "{r}, {g}, {b}, {a}".format(r = qcolor.red(),
                                     g = qcolor.green(),
                                     b = qcolor.blue(),
                                     a = qcolor.alpha()
                                     )
        qlabel.setStyleSheet("QLabel { color: rgba(0,0,0,255); background-color: rgba("+values+"); }")
            
    def _loadUiFile(self):
        raise NotImplementedError
    
    def _initAppletDrawerUi(self):        
        self._drawer = self._loadUiFile()
        
        self._drawer.TrackButton.pressed.connect(self._onTrackButtonPressed)
        self._drawer.exportButton.pressed.connect(self._onExportButtonPressed)
        self._drawer.exportTifButton.pressed.connect(self._onExportTifButtonPressed)
        self._drawer.lineageTreeButton.pressed.connect(self._onLineageTreeButtonPressed)
        self._drawer.lineageFileNameButton.pressed.connect(self._onLineageFileNameButton)
        self._drawer.lineageFileNameEdit.setText(os.getenv('HOME') + '/lineage.png')


    def _initViewerControlUi( self ):
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self._viewerControlWidget = uic.loadUi(p+"viewerControls.ui")

    def _onExportButtonPressed(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory',os.getenv('HOME'))      
        
        if directory is None:
            print "cancelled."
            return
        
        print "Saving first label image..."
        key = []
        for idx, flag in enumerate(axisTagsToString(self.mainOperator.LabelImage.meta.axistags)):
            if flag is 't':
                key.append(slice(0,1))
            elif flag is 'c':
                key.append(slice(0,1))                
            else:
                key.append(slice(0,self.mainOperator.LabelImage.meta.shape[idx]))                        
        
        roi = SubRegion(self.mainOperator.LabelImage, key)
        labelImage = self.mainOperator.LabelImage.get(roi).wait()
        
        write_events([], str(directory), 0, labelImage)
        
        events = self.mainOperator.events
        print "Saving events..."
        print "Length of events " + str(len(events))
        
        for i, events_at in enumerate(events):
            self._write_events(events_at, str(directory), i+1)
            
            
    def _onExportTifButtonPressed(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory',os.getenv('HOME'))      
        
        if directory is None:
            print "cancelled."
            return
        
        print 'Saving results as tiffs...'
        
        label2color = self.mainOperator.label2color
        lshape = list(self.mainOperator.LabelImage.meta.shape)
    
        for t, label2color_at in enumerate(label2color):
            print 'exporting tiffs for t = ' + str(t)            
            
            roi = SubRegion(self.mainOperator.LabelImage, start=[t,] + 4*[0,], stop=[t+1,] + list(lshape[1:]))
            labelImage = self.mainOperator.LabelImage.get(roi).wait()
            relabeled = relabel(labelImage[0,...,0],label2color_at)
            for i in range(relabeled.shape[2]):
                out_im = relabeled[:,:,i]
                out_fn = str(directory) + '/vis_' + str(t).zfill(4) + '_' + str(i).zfill(4) + '.tif'
                vigra.impex.writeImage(np.asarray(out_im,dtype=np.uint8), out_fn)
        
        print 'Tiffs exported.'
                    
                    
    def _onLineageFileNameButton(self):
        fn = QFileDialog.getSaveFileName(self, 'Save Lineage Trees', os.getenv('HOME'))
        if fn is None:
            print "cancelled."
            return        
        self._drawer.lineageFileNameEdit.setText(str(fn))
        
        
    def _onLineageTreeButtonPressed(self):
        fn = self._drawer.lineageFileNameEdit.text()
        
        width = self._drawer.widthBox.value()
        height = self._drawer.heightBox.value()
        if width == 0:
            width = None
        if height == 0:
            height = None
        circular = self._drawer.circularBox.isChecked()
        withAppearing = self._drawer.withAppearingBox.isChecked()
        
        from_t = self._drawer.lineageFromBox.value()
        to_t = self._drawer.lineageToBox.value()
        
        print "Computing Lineage Trees..."
        self._createLineageTrees(str(fn), width=width, height=height, circular=circular, withAppearing=withAppearing, from_t=from_t, to_t=to_t)
        print 'Lineage Trees saved.'
        
    def _onTrackButtonPressed( self ):
        raise NotImplementedError        
                
    def handleThresholdGuiValuesChanged(self, minVal, maxVal):
        with Tracer(traceLogger):
            self.mainOperator.MinValue.setValue(minVal)
            self.mainOperator.MaxValue.setValue(maxVal)
    
    
    
