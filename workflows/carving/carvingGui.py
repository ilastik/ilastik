import os
import numpy
import time

from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QShortcut, QKeySequence
from PyQt4.QtGui import QColor, QMenu
from PyQt4.QtGui import QInputDialog, QMessageBox

from volumina.pixelpipeline.datasources import LazyflowSource, ArraySource
from volumina.layer import ColortableLayer, GrayscaleLayer

from ilastik.applets.labeling.labelingGui import LabelingGui

class CarvingGui(LabelingGui):
    def __init__(self, labelingSlots, observedSlots, drawerUiPath=None, rawInputSlot=None,
                 carvingApplet=None):
        # We provide our own UI file (which adds an extra control for interactive mode)
        directory = os.path.split(__file__)[0]
        carvingDrawerUiPath = os.path.join(directory, 'carvingDrawer.ui')

        super(CarvingGui, self).__init__(labelingSlots, observedSlots, carvingDrawerUiPath, rawInputSlot)
        self._carvingApplet = carvingApplet
        
        #set up keyboard shortcuts
        c = QShortcut(QKeySequence("3"), self, member=self.labelingDrawerUi.segment.click, ambiguousMember=self.labelingDrawerUi.segment.click)
       
        #volume rendering 
        self._volumeRenderingInitialized = False
        self._volumeRendering = None
        self._dataImporter    = None
        self._colorFunc       = None
        self._doneSegmentationLayer = None

        def onSegmentButton():
            print "segment button clicked"
            self._carvingApplet.topLevelOperator.opCarving.Trigger[0].setDirty(slice(None))
        self.labelingDrawerUi.segment.clicked.connect(onSegmentButton)
        self.labelingDrawerUi.segment.setEnabled(True)
        
        def onBackgroundPrioritySpin(value):
            print "background priority changed to %f" % value
            self._carvingApplet.topLevelOperator.opCarving.BackgroundPriority.setValue(value)
        self.labelingDrawerUi.backgroundPrioritySpin.valueChanged.connect(onBackgroundPrioritySpin)
        
        def onBackgroundPriorityDirty(slot, roi):
            oldValue = self.labelingDrawerUi.backgroundPrioritySpin.value()
            newValue = self._carvingApplet.topLevelOperator.opCarving.BackgroundPriority.value
            if  newValue != oldValue:
                self.labelingDrawerUi.backgroundPrioritySpin.setValue(newValue)
        self._carvingApplet.topLevelOperator.opCarving.BackgroundPriority.notifyDirty(onBackgroundPriorityDirty)
        
        def onNoBiasBelowDirty(slot, roi):
            oldValue = self.labelingDrawerUi.noBiasBelowSpin.value()
            newValue = self._carvingApplet.topLevelOperator.opCarving.NoBiasBelow.value
            if  newValue != oldValue:
                self.labelingDrawerUi.noBiasBelowSpin.setValue(newValue)
        self._carvingApplet.topLevelOperator.opCarving.NoBiasBelow.notifyDirty(onNoBiasBelowDirty)
        
        def onNoBiasBelowSpin(value):
            print "background priority changed to %f" % value
            self._carvingApplet.topLevelOperator.opCarving.NoBiasBelow.setValue(value)
        self.labelingDrawerUi.noBiasBelowSpin.valueChanged.connect(onNoBiasBelowSpin)
        
        def onSaveAsButton():
            print "save object as?"
            if self._carvingApplet.topLevelOperator.opCarving[self.imageIndex].dataIsStorable():
                name, ok = QInputDialog.getText(self, 'Save Object As', 'object name') 
                name = str(name)
                if not ok:
                    return
                self._carvingApplet.topLevelOperator.saveObjectAs(name, self.imageIndex)
                print "save object as %s" % name
            else:
                msgBox = QMessageBox(self)
                msgBox.setText("The data does no seem fit to be stored.")
                msgBox.setWindowTitle("Lousy Data")
                msgBox.setIcon(2)
                msgBox.exec_()
                print "object not saved due to faulty data."

        self.labelingDrawerUi.saveAs.clicked.connect(onSaveAsButton)
            
        def onDeleteButton():
            print "delete which object?"
            name, ok = QInputDialog.getText(self, 'Delete Object', 'object name') 
            name = str(name)
            print "delete object %s" % name
            if not ok:
                return
            success = self._carvingApplet.topLevelOperator.deleteObject(name, self.imageIndex)
            if not success:
                QMessageBox.critical(self, "Delete Object", "Could not delete object named '%s'" % name)
        self.labelingDrawerUi.deleteObject.clicked.connect(onDeleteButton)
        
        def onSaveButton():
            if self._carvingApplet.topLevelOperator.opCarving[self.imageIndex].dataIsStorable():
                if self._carvingApplet.topLevelOperator.hasCurrentObject(self.imageIndex):
                    self._carvingApplet.topLevelOperator.saveCurrentObject(self.imageIndex)
                else:
                    onSaveAsButton()
            else:
                msgBox = QMessageBox(self)
                msgBox.setText("The data does no seem fit to be stored.")
                msgBox.setWindowTitle("Lousy Data")
                msgBox.setIcon(2)
                msgBox.exec_()
                print "object not saved due to faulty data."
        self.labelingDrawerUi.save.clicked.connect(onSaveButton)
        self.labelingDrawerUi.save.setEnabled(False) #initially, the user need to use "Save As"
        
        def onClearButton():
            self._carvingApplet.topLevelOperator.clearCurrentLabeling(self.imageIndex)
        self.labelingDrawerUi.clear.clicked.connect(onClearButton)
        self.labelingDrawerUi.clear.setEnabled(True)
        
        def onLoadObjectButton():
            print "load which object?"
            name, ok = QInputDialog.getText(self, 'Load Object', 'object name') 
            name = str(name)
            print "load object %s" % name
            if ok:
                success = self._carvingApplet.topLevelOperator.loadObject(name, self.imageIndex)
                if not success:
                    QMessageBox.critical(self, "Load Object", "Could not load object named '%s'" % name)
                
        self.labelingDrawerUi.load.clicked.connect(onLoadObjectButton)
        
        def labelBackground():
            self.selectLabel(0)
        def labelObject():
            self.selectLabel(1)
       
        self._labelControlUi.labelListModel.allowRemove(False) 
        
        QShortcut(QKeySequence("1"), self, member=labelBackground, ambiguousMember=labelBackground)
        QShortcut(QKeySequence("2"), self, member=labelObject, ambiguousMember=labelObject)
       
        def layerIndexForName(name): 
            return self.layerstack.findMatchingIndex(lambda x: x.name == name)
        
        def addLayerToggleShortcut(layername, shortcut): 
            def toggle():
                row = layerIndexForName(layername)
                self.layerstack.selectRow(row)
                layer = self.layerstack[row]
                layer.visible = not layer.visible
                self.viewerControlWidget().layerWidget.setFocus()
            QShortcut(QKeySequence(shortcut), self, member=toggle, ambiguousMember=toggle)
        
        addLayerToggleShortcut("done", "d")
        addLayerToggleShortcut("segmentation", "s")
        addLayerToggleShortcut("raw", "r")
        addLayerToggleShortcut("pmap", "v")
        addLayerToggleShortcut("done seg", "b")
        addLayerToggleShortcut("hints","h")
        
        def updateLayerTimings():
            s = "Layer timings:\n"
            for l in self.layerstack:
                s += "%s: %f sec.\n" % (l.name, l.averageTimePerTile)
            self.labelingDrawerUi.layerTimings.setText(s)
        t = QTimer(self)
        t.setInterval(1*1000) # 10 seconds
        t.start()
        t.timeout.connect(updateLayerTimings)
        
        def makeColortable():
            self._doneSegmentationColortable = [QColor(0,0,0,0).rgba()]
            for i in range(254):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                self._doneSegmentationColortable.append(QColor(r,g,b).rgba())
        makeColortable()
        self._doneSegmentationLayer = None
        def onRandomizeColors():
            if self._doneSegmentationLayer is not None:
                print "randomizing colors ..."
                makeColortable()
                self._doneSegmentationLayer.colorTable = self._doneSegmentationColortable
        self.labelingDrawerUi.randomizeColors.clicked.connect(onRandomizeColors)
      
    def _updateVolumeRendering(self):    
        op = self._carvingApplet.topLevelOperator.opCarving[0]
        if not self._volumeRenderingInitialized:
            a = time.time()
            from volumina.view3d.volumeRendering import makeVolumeRenderingPipeline
            dataImporter, colorFunc, volume = makeVolumeRenderingPipeline(op._volumeRenderingVolume) 
            b = time.time()
            print "creating volume rendering pipeline took %f sec." % (b-a)
            
            self.editor.view3d.qvtk.renderer.AddVolume(volume)
            self._volumeRendering = volume
            self._dataImporter    = dataImporter
            self._colorFunc       = colorFunc
            self._volumeRenderingInitialized = True
        self._dataImporter.Modified()
        self._volumeRendering.Update() 
        self.editor.view3d.qvtk.update()
        
    def handleEditorRightClick(self, currentImageIndex, position5d, globalWindowCoordinate):
        names = self._carvingApplet.topLevelOperator.doneObjectNamesForPosition(position5d[1:4], currentImageIndex)
       
        op = self._carvingApplet.topLevelOperator.opCarving[self.imageIndex]
        
        m = QMenu(self)
        m.addAction("position %d %d %d" % (position5d[1], position5d[2], position5d[3]))
        for n in names:
            m.addAction("edit %s" % n)
            m.addAction("delete %s" % n)
            if not n in op._shownObjects3D:
                m.addAction("show 3D %s" % n)
            else:
                m.addAction("remove %s from 3D view" % n)
            
        act = m.exec_(globalWindowCoordinate) 
        for n in names:
            if act is not None and act.text() == "edit %s" %n:
                self._carvingApplet.topLevelOperator.loadObject(n, self.imageIndex)
            elif act is not None and act.text() =="delete %s" % n:
                self._carvingApplet.topLevelOperator.deleteObject(n,self.imageIndex) 
            elif act is not None and act.text() == "show 3D %s" % n:
               
                self._updateVolumeRendering()
                
                label = op._getVolumeRenderingLabel()
                print "*** showing",n, "as", label
                op._shownObjects3D[n] = label 
               
                a = time.time() 
                ctable = self._doneSegmentationLayer.colorTable
                lut = numpy.zeros(len(op._mst.objects.lut), dtype=numpy.int32)
                for name, label in op._shownObjects3D.iteritems():
                    objectSupervoxels = op._mst.object_lut[name]
                    lut[objectSupervoxels] = label
                    import colorsys
                    rgb = colorsys.hsv_to_rgb(numpy.random.random(), 1.0, 1.0)
                    self._colorFunc.AddRGBPoint(label, *rgb)
                
                op._volumeRenderingVolume[:] = ( lut[op._mst.regionVol] )
                b = time.time()
                print "updating the volume rendering volume took %f sec." % (b-a)
                print "min/max: ",op._volumeRenderingVolume.min(), op._volumeRenderingVolume.max()
                self._updateVolumeRendering()
                
            elif act is not None and act.text() == "remove %s from 3D view" % n:
                a = time.time() 
                lut = numpy.zeros(len(op._mst.objects.lut), dtype=numpy.int32)
                for name, label in op._shownObjects3D.iteritems():
                    objectSupervoxels = op._mst.object_lut[name]
                    if name != n:
                        lut[objectSupervoxels] = label
                        
                    else:
                        lut[objectSupervoxels] = 0
                del op._shownObjects3D[n]
                
                op._volumeRenderingVolume[:] = ( lut[op._mst.regionVol] )
                b = time.time()
                print "[remove] updating the volume rendering volume took %f sec." % (b-a)
                self._updateVolumeRendering()
        
    def getNextLabelName(self):
        l = len(self._labelControlUi.labelListModel)
        if l == 0:
            return "Background"
        else:
            return "Object"
        
    def appletDrawers(self):
        return [ ("Carving", self._labelControlUi) ]

    def setupLayers( self, currentImageIndex ):
        layers = []
       
        def onButtonsEnabled(slot, roi):
            currObj = self._carvingApplet.topLevelOperator.opCarving[currentImageIndex].CurrentObjectName.value
            hasSeg  = self._carvingApplet.topLevelOperator.opCarving[currentImageIndex].HasSegmentation.value
            nzLB    = self._carvingApplet.topLevelOperator.opLabeling.NonzeroLabelBlocks[currentImageIndex][:].wait()[0]
            
            self.labelingDrawerUi.currentObjectLabel.setText("current object: %s" % currObj)
            self.labelingDrawerUi.save.setEnabled(currObj != "" and hasSeg)
            self.labelingDrawerUi.saveAs.setEnabled(currObj == "" and hasSeg)
            #rethink this
            #self.labelingDrawerUi.segment.setEnabled(len(nzLB) > 0)
            #self.labelingDrawerUi.clear.setEnabled(len(nzLB) > 0)
        self._carvingApplet.topLevelOperator.opCarving[currentImageIndex].CurrentObjectName.notifyDirty(onButtonsEnabled)
        self._carvingApplet.topLevelOperator.opCarving[currentImageIndex].HasSegmentation.notifyDirty(onButtonsEnabled)
        self._carvingApplet.topLevelOperator.opLabeling.NonzeroLabelBlocks[currentImageIndex].notifyDirty(onButtonsEnabled)
        
        # Labels
        labellayer, labelsrc = self.createLabelLayer(currentImageIndex, direct=True)
        if labellayer is not None:
            layers.append(labellayer)
            # Tell the editor where to draw label data
            self.editor.setLabelSink(labelsrc)
       
        #segmentation 
        seg = self._carvingApplet.topLevelOperator.opCarving.Segmentation[currentImageIndex]
        
        #seg = self._carvingApplet.topLevelOperator.opCarving[0]._mst.segmentation
        #temp = self._done_lut[self._mst.regionVol[sl[1:4]]]
        if seg.ready(): 
            #source = RelabelingArraySource(seg)
            #source.setRelabeling(numpy.arange(256, dtype=numpy.uint8))
            colortable = [QColor(0,0,0,0).rgba(), QColor(0,0,0,0).rgba(), QColor(0,255,0).rgba()]
            for i in range(256-len(colortable)):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
                
            layer = ColortableLayer(LazyflowSource(seg), colortable, direct=True)
            layer.name = "segmentation"
            layer.visible = True
            layer.opacity = 0.3
            layers.append(layer)
        
        #done 
        done = self._carvingApplet.topLevelOperator.opCarving.DoneObjects[currentImageIndex]
        if done.ready(): 
            colortable = [QColor(0,0,0,0).rgba(), QColor(0,0,255).rgba()]
            for i in range(254-len(colortable)):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            #have to use lazyflow because it provides dirty signals
            layer = ColortableLayer(LazyflowSource(done), colortable, direct=True)
            layer.name = "done"
            layer.visible = False
            layer.opacity = 0.5
            layers.append(layer)
            
        #hints
        useLazyflow = True
        ctable = [QColor(0,0,0,0).rgba(), QColor(255,0,0).rgba()]
        if useLazyflow:
            hints = self._carvingApplet.topLevelOperator.opCarving.HintOverlay[currentImageIndex]
            layer = ColortableLayer(LazyflowSource(hints), ctable, direct=True)
        else:
            hints = self._carvingApplet.topLevelOperator.opCarving[currentImageIndex]._hints
            layer = ColortableLayer(ArraySource(hints), ctable, direct=True)
        if not useLazyflow or hints.ready():
            layer.name = "hints"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)
        
        #done seg
        doneSeg = self._carvingApplet.topLevelOperator.opCarving.DoneSegmentation[currentImageIndex]
        if doneSeg.ready(): 
            layer = ColortableLayer(LazyflowSource(doneSeg), self._doneSegmentationColortable, direct=True)
            layer.name = "done seg"
            layer.visible = False
            layer.opacity = 0.5
            self._doneSegmentationLayer = layer
            layers.append(layer)
            
        #supervoxel
        sv = self._carvingApplet.topLevelOperator.opCarving.Supervoxels[currentImageIndex]
        if sv.ready():
            for i in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            layer = ColortableLayer(LazyflowSource(sv), colortable, direct=True)
            layer.name = "supervoxels"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)
        
        #
        # load additional layer: features / probability map
        #

#        import h5py
#        f = h5py.File("pmap.h5")
#        pmap = f["data"].value

        
        #
        # here we load the actual raw data from an ArraySource rather than from a LazyflowSource for speed reasons
        #
        raw = self._carvingApplet.topLevelOperator.opCarving[0]._mst.raw
        raw5D = numpy.zeros((1,)+raw.shape+(1,), dtype=raw.dtype)
        raw5D[0,:,:,:,0] = raw[:,:,:]
        layer = GrayscaleLayer(ArraySource(raw5D), direct=True)
        layer.name = "raw"
        layer.visible = True
        layer.opacity = 1.0
        layers.append(layer)
            
        return layers
