from PyQt4.QtGui import QColor, QFileDialog

from volumina.api import LazyflowSource, ColortableLayer
import volumina.colortables as colortables

from lazyflow.operators.generic import axisTagsToString
from lazyflow.rtype import SubRegion
from lazyflow.utility import Tracer

import logging
import os
import numpy as np
import vigra
from ilastik.applets.tracking.base.trackingUtilities import relabel,write_events
from volumina.layer import GrayscaleLayer
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

from ilastik.config import cfg as ilastik_config

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

class TrackingBaseGui( LayerViewerGui ):
    """
    """
    
    withMergers=False
    
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################        

    def appletDrawer( self ):
        return self._drawer

    def reset( self ):
        print "TrackinGui.reset(): not implemented"

    
    ###########################################
    ###########################################
    
    def __init__(self, topLevelOperatorView):
        """
        """
        self.topLevelOperatorView = topLevelOperatorView
        super(TrackingBaseGui, self).__init__(topLevelOperatorView)
        self.mainOperator = topLevelOperatorView

        self._initColors()
        
        if self.mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = self.mainOperator.LabelImage.meta.shape
        self.mainOperator.LabelImage.notifyMetaChanged( self._onMetaChanged)


    def _onMetaChanged( self, slot ):
        if slot is self.mainOperator.LabelImage:
            if slot.meta.shape:                
                self.editor.dataShape = slot.meta.shape

                maxt = slot.meta.shape[0] - 1
                self._setRanges()
                self._drawer.from_time.setValue(0)                
                self._drawer.to_time.setValue(maxt)
            
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

    
    def setupLayers( self ):        
        layers = []
        
        if "MergerOutput" in self.topLevelOperatorView.outputs:
            ct = colortables.create_default_8bit()
            for i in range(7):
                ct[i] = self.mergerColors[i].rgba()
            self.mergersrc = LazyflowSource( self.topLevelOperatorView.MergerOutput )
            mergerLayer = ColortableLayer( self.mergersrc, ct )
            mergerLayer.name = "Merger"
            mergerLayer.visible = True
            layers.append(mergerLayer)     
            
            
        ct = colortables.create_random_16bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        ct[1] = QColor(128,128,128,255).rgba() # misdetections have id 1 and will be indicated by grey
        self.trackingsrc = LazyflowSource( self.topLevelOperatorView.Output )
        trackingLayer = ColortableLayer( self.trackingsrc, ct )
        trackingLayer.name = "Tracking"
        trackingLayer.visible = True
        trackingLayer.opacity = 0.8
        layers.append(trackingLayer)
        
        
        self.objectssrc = LazyflowSource( self.topLevelOperatorView.LabelImage )
#        ct = colortables.create_default_8bit()
        ct = colortables.create_random_16bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        objLayer = ColortableLayer( self.objectssrc, ct )
        objLayer.name = "Objects"
        objLayer.opacity = 0.8
        objLayer.visible = True
        layers.append(objLayer)


        ## raw data layer
        self.rawsrc = None
        self.rawsrc = LazyflowSource( self.mainOperator.RawImage )
        rawLayer = GrayscaleLayer( self.rawsrc )
        rawLayer.name = "Raw"        
        layers.insert( len(layers), rawLayer )   
        
        
        if self.topLevelOperatorView.LabelImage.meta.shape:
            self.editor.dataShape = self.topLevelOperatorView.LabelImage.meta.shape

            maxt = self.topLevelOperatorView.LabelImage.meta.shape[0] - 1
            maxx = self.topLevelOperatorView.LabelImage.meta.shape[1] - 1            
            maxy = self.topLevelOperatorView.LabelImage.meta.shape[2] - 1
            maxz = self.topLevelOperatorView.LabelImage.meta.shape[3] - 1
                    
            if not self.mainOperator.Parameters.ready():
                raise Exception("Parameter slot is not ready")
            
            parameters = self.mainOperator.Parameters.value
            self._setRanges() 
            if 'size_range' in parameters:                
                self._drawer.to_size.setValue(parameters['size_range'][1])
                self._drawer.from_size.setValue(parameters['size_range'][0])
            else:
                self._drawer.from_size.setValue(0)
                self._drawer.to_size.setValue(10000)
                
            if 'x_range' in parameters:                
                self._drawer.to_x.setValue(parameters['x_range'][1]-1)
                self._drawer.from_x.setValue(parameters['x_range'][0])
            else:
                self._drawer.from_x.setValue(0)
                self._drawer.to_x.setValue(maxx)
                
            if 'y_range' in parameters:
                self._drawer.to_y.setValue(parameters['y_range'][1]-1)
                self._drawer.from_y.setValue(parameters['y_range'][0])                
            else:
                self._drawer.from_y.setValue(0)
                self._drawer.to_y.setValue(maxy)
                
            if 'z_range' in parameters:
                self._drawer.to_z.setValue(parameters['z_range'][1]-1)
                self._drawer.from_z.setValue(parameters['z_range'][0])                
            else:
                self._drawer.from_z.setValue(0)
                self._drawer.to_z.setValue(maxz)
            
            if 'time_range' in parameters:
                self._drawer.to_time.setValue(parameters['time_range'][1])
                self._drawer.from_time.setValue(parameters['time_range'][0])                
            else:
                self._drawer.from_time.setValue(0)
                self._drawer.to_time.setValue(maxt)
            
            if 'scales' in parameters:
                self._drawer.x_scale.setValue(parameters['scales'][0])
                self._drawer.y_scale.setValue(parameters['scales'][1])
                self._drawer.z_scale.setValue(parameters['scales'][2])
            else:
                self._drawer.x_scale.setValue(1)
                self._drawer.y_scale.setValue(1)
                self._drawer.z_scale.setValue(1)
               
        
        self.topLevelOperatorView.RawImage.notifyReady( self._onReady )
        self.topLevelOperatorView.RawImage.notifyMetaChanged( self._onMetaChanged )
        
        return layers


    def _setRanges(self):
        maxt = self.topLevelOperatorView.LabelImage.meta.shape[0] - 1
        maxx = self.topLevelOperatorView.LabelImage.meta.shape[1] - 1
        maxy = self.topLevelOperatorView.LabelImage.meta.shape[2] - 1
        maxz = self.topLevelOperatorView.LabelImage.meta.shape[3] - 1
        
        from_time = self._drawer.from_time
        to_time = self._drawer.to_time
        from_x = self._drawer.from_x
        to_x = self._drawer.to_x
        from_y = self._drawer.from_y
        to_y = self._drawer.to_y
        from_z = self._drawer.from_z
        to_z = self._drawer.to_z
                
        from_time.setRange(0, to_time.value()-1)        
        to_time.setRange(from_time.value()+1,maxt)      
        
        from_x.setRange(0,to_x.value())
        to_x.setRange(from_x.value(),maxx)
        
        from_y.setRange(0,to_y.value())
        to_y.setRange(from_y.value(),maxy)
        
        from_z.setRange(0,to_z.value())
        to_z.setRange(from_z.value(),maxz)
        

    def _initColors(self):
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
    
    def initAppletDrawerUi(self):        
        self._drawer = self._loadUiFile()
        
        self._drawer.TrackButton.pressed.connect(self._onTrackButtonPressed)
        self._drawer.exportButton.pressed.connect(self._onExportButtonPressed)
        self._drawer.exportTifButton.pressed.connect(self._onExportTifButtonPressed)
#        self._drawer.lineageTreeButton.pressed.connect(self._onLineageTreeButtonPressed)
#        self._drawer.lineageFileNameButton.pressed.connect(self._onLineageFileNameButton)
#        self._drawer.lineageFileNameEdit.setText(os.getenv('HOME') + '/lineage.png')

        self._drawer.from_time.valueChanged.connect(self._setRanges)
        self._drawer.from_x.valueChanged.connect(self._setRanges)
        self._drawer.from_y.valueChanged.connect(self._setRanges)
        self._drawer.from_z.valueChanged.connect(self._setRanges)
        self._drawer.to_time.valueChanged.connect(self._setRanges)
        self._drawer.to_x.valueChanged.connect(self._setRanges)
        self._drawer.to_y.valueChanged.connect(self._setRanges)
        self._drawer.to_z.valueChanged.connect(self._setRanges)
        


    def _onExportButtonPressed(self):
        options = QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog

        directory = QFileDialog.getExistingDirectory(self, 'Select Directory',os.getenv('HOME'), options=options)      
        
        if directory is None:
            print "cancelled."
            return
        
        # determine from_time (it could has been changed in the GUI meanwhile)
        for t_from, label2color_at in enumerate(self.mainOperator.label2color):
            if len(label2color_at) == 0:                
                continue
            else:
                break
            
        print "Saving first label image..."
        key = []
        for idx, flag in enumerate(axisTagsToString(self.mainOperator.LabelImage.meta.axistags)):
            if flag is 't':
                key.append(slice(t_from,t_from+1))
            elif flag is 'c':
                key.append(slice(0,1))                
            else:
                key.append(slice(0,self.mainOperator.LabelImage.meta.shape[idx]))                        
        
        roi = SubRegion(self.mainOperator.LabelImage, key)
        labelImage = self.mainOperator.LabelImage.get(roi).wait()
        labelImage = labelImage[0,...,0]
        
        write_events([], str(directory), t_from, labelImage)
        
        events = self.mainOperator.events
        print "Saving events..."
        print "Length of events " + str(len(events))
        
        for i, events_at in enumerate(events):
            t = t_from + i            
            key[0] = slice(t+1,t+2)
            roi = SubRegion(self.mainOperator.LabelImage, key)
            labelImage = self.mainOperator.LabelImage.get(roi).wait()
            labelImage = labelImage[0,...,0]
            if self.withMergers:                
                write_events(events_at, str(directory), t+1, labelImage, self.mainOperator.mergers)
            else:
                write_events(events_at, str(directory), t+1, labelImage)
            
            
    def _onExportTifButtonPressed(self):
        options = QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog

        directory = QFileDialog.getExistingDirectory(self, 'Select Directory',os.getenv('HOME'), options=options)      
        
        if directory is None:
            print "cancelled."
            return
        
        print 'Saving results as tiffs...'
        
        label2color = self.mainOperator.label2color
        lshape = list(self.mainOperator.LabelImage.meta.shape)
    
        for t, label2color_at in enumerate(label2color):
            if len(label2color_at) == 0:                
                continue
            print 'exporting tiffs for t = ' + str(t)            
            
            roi = SubRegion(self.mainOperator.LabelImage, start=[t,] + 4*[0,], stop=[t+1,] + list(lshape[1:]))
            labelImage = self.mainOperator.LabelImage.get(roi).wait()
            relabeled = relabel(labelImage[0,...,0],label2color_at)
            for i in range(relabeled.shape[2]):
                out_im = relabeled[:,:,i]
                out_fn = str(directory) + '/vis_t' + str(t).zfill(4) + '_z' + str(i).zfill(4) + '.tif'
                vigra.impex.writeImage(np.asarray(out_im,dtype=np.uint32), out_fn)
        
        print 'Tiffs exported.'
                    
                    
    def _onLineageFileNameButton(self):
        options = QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog
        fn = QFileDialog.getSaveFileName(self, 'Save Lineage Trees', os.getenv('HOME'), options=options)
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
    
    
    def _setLayerVisible(self, name, visible):
        for layer in self.layerstack:
            if layer.name is name:
                layer.visible = visible
    
