#Python
import os
import numpy
import random

#PyQt
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QShortcut, QKeySequence
from PyQt4.QtGui import QColor, QMenu
from PyQt4.QtGui import QInputDialog, QMessageBox
from PyQt4 import uic

#volumina
from volumina.pixelpipeline.datasources import LazyflowSource, ArraySource
from volumina.layer import ColortableLayer, GrayscaleLayer
from volumina.utility import ShortcutManager
from volumina import colortables
try:
    from volumina.view3d.volumeRendering import RenderingManager
except:
    pass

#ilastik
from ilastik.applets.labeling.labelingGui import LabelingGui

#===----------------------------------------------------------------------------------------------------------------===

class CarvingGui(LabelingGui):
    def __init__(self, labelingSlots, topLevelOperatorView, drawerUiPath=None, rawInputSlot=None ):
        self.topLevelOperatorView = topLevelOperatorView

        # We provide our own UI file (which adds an extra control for interactive mode)
        directory = os.path.split(__file__)[0]
        carvingDrawerUiPath = os.path.join(directory, 'carvingDrawer.ui')

        super(CarvingGui, self).__init__(labelingSlots, topLevelOperatorView, carvingDrawerUiPath, rawInputSlot)
        
        mgr = ShortcutManager()
        
        #set up keyboard shortcuts
        segmentShortcut = QShortcut(QKeySequence("3"), self, member=self.labelingDrawerUi.segment.click,
                                    ambiguousMember=self.labelingDrawerUi.segment.click)
        mgr.register("Carving", "Run interactive segmentation", segmentShortcut, self.labelingDrawerUi.segment)
        

        self._doneSegmentationLayer = None

        #volume rendering
        try:
            self.render = True
            self._shownObjects3D = {}
            self._renderMgr = RenderingManager(
                renderer=self.editor.view3d.qvtk.renderer,
                qvtk=self.editor.view3d.qvtk)
        except:
            self.render = False

        def onSegmentButton():
            print "segment button clicked"
            self.topLevelOperatorView.opCarving.Trigger.setDirty(slice(None))
        self.labelingDrawerUi.segment.clicked.connect(onSegmentButton)
        self.labelingDrawerUi.segment.setEnabled(True)

        def onBackgroundPrioritySpin(value):
            print "background priority changed to %f" % value
            self.topLevelOperatorView.opCarving.BackgroundPriority.setValue(value)
        self.labelingDrawerUi.backgroundPrioritySpin.valueChanged.connect(onBackgroundPrioritySpin)

        def onuncertaintyCombo(value):
            if value == 0:
                value = "none"
            if value == 1:
                value = "localMargin"
            if value == 2:
                value = "exchangeCount"
            if value == 3:
                value = "gabow"
            print "uncertainty changed to %r" % value
            self.topLevelOperatorView.opCarving.UncertaintyType.setValue(value)
        self.labelingDrawerUi.uncertaintyCombo.currentIndexChanged.connect(onuncertaintyCombo)

        def onBackgroundPriorityDirty(slot, roi):
            oldValue = self.labelingDrawerUi.backgroundPrioritySpin.value()
            newValue = self.topLevelOperatorView.opCarving.BackgroundPriority.value
            if  newValue != oldValue:
                self.labelingDrawerUi.backgroundPrioritySpin.setValue(newValue)
        self.topLevelOperatorView.opCarving.BackgroundPriority.notifyDirty(onBackgroundPriorityDirty)
        
        def onNoBiasBelowDirty(slot, roi):
            oldValue = self.labelingDrawerUi.noBiasBelowSpin.value()
            newValue = self.topLevelOperatorView.opCarving.NoBiasBelow.value
            if  newValue != oldValue:
                self.labelingDrawerUi.noBiasBelowSpin.setValue(newValue)
        self.topLevelOperatorView.opCarving.NoBiasBelow.notifyDirty(onNoBiasBelowDirty)
        
        def onNoBiasBelowSpin(value):
            print "background priority changed to %f" % value
            self.topLevelOperatorView.opCarving.NoBiasBelow.setValue(value)
        self.labelingDrawerUi.noBiasBelowSpin.valueChanged.connect(onNoBiasBelowSpin)

        def onSaveAsButton():
            print "save object as?"
            if self.topLevelOperatorView.opCarving.dataIsStorable():
                name, ok = QInputDialog.getText(self, 'Save Object As', 'object name') 
                name = str(name)
                if not ok:
                    return
                objects = self.topLevelOperatorView.opCarving.AllObjectNames[:].wait()
                if name in objects:
                    QMessageBox.critical(self, "Save Object As", "An object with name '%s' already exists.\nPlease choose a different name." % name)
                    return
                self.topLevelOperatorView.opCarving.saveObjectAs(name)
                print "save object as %s" % name
            else:
                msgBox = QMessageBox(self)
                msgBox.setText("The data does not seem fit to be stored.")
                msgBox.setWindowTitle("Problem with Data")
                msgBox.setIcon(2)
                msgBox.exec_()
                print "object not saved due to faulty data."

        self.labelingDrawerUi.saveAs.clicked.connect(onSaveAsButton)

        def onSaveButton():
            if self.topLevelOperatorView.opCarving.dataIsStorable():
                if self.topLevelOperatorView.opCarving.hasCurrentObject():
                    name = self.topLevelOperatorView.opCarving.currentObjectName()
                    self.topLevelOperatorView.opCarving.saveObjectAs( name )
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
            self.topLevelOperatorView.opCarving._clear()
            self.topLevelOperatorView.opCarving.clearCurrentLabeling()
            # trigger a re-computation
            self.topLevelOperatorView.opCarving.Trigger.setDirty(slice(None))
        self.labelingDrawerUi.clear.clicked.connect(onClearButton)
        self.labelingDrawerUi.clear.setEnabled(True)
        
        def onShowObjectNames():
            '''show object names and allow user to load/delete them'''
            dialog = uic.loadUi(os.path.join(directory, 'carvingObjectManagement.ui'))
            listOfItems = self.topLevelOperatorView.opCarving.AllObjectNames[:].wait()
            dialog.objectNames.addItems(sorted(listOfItems))
            
            def loadSelection():
                for name in dialog.objectNames.selectedItems():
                    objectname = str(name.text())
                    self.topLevelOperatorView.opCarving.loadObject(objectname)
            
            def deleteSelection():
                for name in dialog.objectNames.selectedItems():
                    objectname = str(name.text())
                    self.topLevelOperatorView.opCarving.deleteObject(objectname)
                    name.setHidden(True)
            
            dialog.loadButton.clicked.connect(loadSelection)
            dialog.deleteButton.clicked.connect(deleteSelection)
            dialog.cancelButton.clicked.connect(dialog.close)
            dialog.exec_()
        
        self.labelingDrawerUi.namesButton.clicked.connect(onShowObjectNames)
        
        def labelBackground():
            self.selectLabel(0)
        def labelObject():
            self.selectLabel(1)

        self._labelControlUi.labelListModel.allowRemove(False)

        bg = QShortcut(QKeySequence("1"), self, member=labelBackground, ambiguousMember=labelBackground)
        mgr.register("Carving", "Select background label", bg)
        fg = QShortcut(QKeySequence("2"), self, member=labelObject, ambiguousMember=labelObject)
        mgr.register("Carving", "Select object label", fg)

        def layerIndexForName(name):
            return self.layerstack.findMatchingIndex(lambda x: x.name == name)

        def addLayerToggleShortcut(layername, shortcut):
            def toggle():
                row = layerIndexForName(layername)
                self.layerstack.selectRow(row)
                layer = self.layerstack[row]
                layer.visible = not layer.visible
                self.viewerControlWidget().layerWidget.setFocus()
            shortcut = QShortcut(QKeySequence(shortcut), self, member=toggle, ambiguousMember=toggle)
            mgr.register("Carving", "Toggle layer %s" % layername, shortcut)

        addLayerToggleShortcut("done", "d")
        addLayerToggleShortcut("segmentation", "s")
        addLayerToggleShortcut("raw", "r")
        addLayerToggleShortcut("pmap", "v")
        addLayerToggleShortcut("hints","h")

        '''
        def updateLayerTimings():
            s = "Layer timings:\n"
            for l in self.layerstack:
                s += "%s: %f sec.\n" % (l.name, l.averageTimePerTile)
            self.labelingDrawerUi.layerTimings.setText(s)
        t = QTimer(self)
        t.setInterval(1*1000) # 10 seconds
        t.start()
        t.timeout.connect(updateLayerTimings)
        '''

        def makeColortable():
            self._doneSegmentationColortable = [QColor(0,0,0,0).rgba()]
            for i in range(254):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                self._doneSegmentationColortable.append(QColor(r,g,b).rgba())
            self._doneSegmentationColortable[1:17] = colortables.default16
        makeColortable()
        self._doneSegmentationLayer = None
        def onRandomizeColors():
            if self._doneSegmentationLayer is not None:
                print "randomizing colors ..."
                makeColortable()
                self._doneSegmentationLayer.colorTable = self._doneSegmentationColortable
                if self.render and self._renderMgr.ready:
                    self._update_rendering()
        #self.labelingDrawerUi.randomizeColors.clicked.connect(onRandomizeColors)
        
    def handleEditorRightClick(self, position5d, globalWindowCoordinate):
        names = self.topLevelOperatorView.opCarving.doneObjectNamesForPosition(position5d[1:4])
       
        op = self.topLevelOperatorView.opCarving
        
        menu = QMenu(self)
        menu.addAction("position %d %d %d" % (position5d[1], position5d[2], position5d[3]))
        for name in names:
            menu.addAction("edit %s" % name)
            menu.addAction("delete %s" % name)
            if self.render:
                if name in self._shownObjects3D:
                    menu.addAction("remove %s from 3D view" % name)
                else:
                    menu.addAction("show 3D %s" % name)

        act = menu.exec_(globalWindowCoordinate)
        for name in names:
            if act is not None and act.text() == "edit %s" %name:
                op.loadObject(name)
            elif act is not None and act.text() =="delete %s" % name:
                op.deleteObject(name)
                if self.render and self._renderMgr.ready:
                    self._update_rendering()
            elif act is not None and act.text() == "show 3D %s" % name:
                label = self._renderMgr.addObject()
                self._shownObjects3D[name] = label
                self._update_rendering()
            elif act is not None and act.text() == "remove %s from 3D view" % name:
                label = self._shownObjects3D.pop(name)
                self._renderMgr.removeObject(label)
                self._update_rendering()

    def _update_rendering(self):
        if not self.render:
            return

        op = self.topLevelOperatorView.opCarving
        if not self._renderMgr.ready:
            self._renderMgr.setup(op.MST.value.raw.shape)

        # remove nonexistent objects
        self._shownObjects3D = dict((k, v) for k, v in self._shownObjects3D.iteritems()
                                    if k in op.MST.value.object_lut.keys())

        lut = numpy.zeros(len(op.MST.value.objects.lut), dtype=numpy.int32)
        for name, label in self._shownObjects3D.iteritems():
            objectSupervoxels = op.MST.value.object_lut[name]
            lut[objectSupervoxels] = label

        self._renderMgr.volume = lut[op.MST.value.regionVol]
        self._update_colors()
        self._renderMgr.update()

    def _update_colors(self):
        op = self.topLevelOperatorView.opCarving
        ctable = self._doneSegmentationLayer.colorTable

        for name, label in self._shownObjects3D.iteritems():
            color = QColor(ctable[op.MST.value.object_names[name]])
            color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            self._renderMgr.setColor(label, color)


    def getNextLabelName(self):
        l = len(self._labelControlUi.labelListModel)
        if l == 0:
            return "Background"
        else:
            return "Object"

    def appletDrawers(self):
        return [ ("Carving", self._labelControlUi) ]

    def setupLayers( self ):
        layers = []

        def onButtonsEnabled(slot, roi):
            currObj = self.topLevelOperatorView.opCarving.CurrentObjectName.value
            hasSeg  = self.topLevelOperatorView.opCarving.HasSegmentation.value
            nzLB    = self.topLevelOperatorView.opCarving.opLabeling.NonzeroLabelBlocks[:].wait()[0]
            
            self.labelingDrawerUi.currentObjectLabel.setText("current object: %s" % currObj)
            self.labelingDrawerUi.save.setEnabled(currObj != "" and hasSeg)
            self.labelingDrawerUi.saveAs.setEnabled(currObj == "" and hasSeg)
            #rethink this
            #self.labelingDrawerUi.segment.setEnabled(len(nzLB) > 0)
            #self.labelingDrawerUi.clear.setEnabled(len(nzLB) > 0)
        self.topLevelOperatorView.opCarving.CurrentObjectName.notifyDirty(onButtonsEnabled)
        self.topLevelOperatorView.opCarving.HasSegmentation.notifyDirty(onButtonsEnabled)
        self.topLevelOperatorView.opCarving.opLabeling.NonzeroLabelBlocks.notifyDirty(onButtonsEnabled)
        
        # Labels
        labellayer, labelsrc = self.createLabelLayer(direct=True)
        if labellayer is not None:
            layers.append(labellayer)
            # Tell the editor where to draw label data
            self.editor.setLabelSink(labelsrc)

        #uncertainty
        uncert = self.topLevelOperatorView.opCarving.Uncertainty
        if uncert.ready():
            colortable = []
            for i in range(256-len(colortable)):
                r,g,b,a = i,0,0,i
                colortable.append(QColor(r,g,b,a).rgba())

            layer = ColortableLayer(LazyflowSource(uncert), colortable, direct=True)
            layer.name = "uncertainty"
            layer.visible = True
            layer.opacity = 0.3
            layers.append(layer)

       
        #segmentation 
        seg = self.topLevelOperatorView.opCarving.Segmentation
        
        #seg = self.topLevelOperatorView.opCarving.MST.value.segmentation
        #temp = self._done_lut[self.MST.value.regionVol[sl[1:4]]]
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
        done = self.topLevelOperatorView.opCarving.DoneObjects
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
        ctable.extend( [QColor(255*random.random(), 255*random.random(), 255*random.random()) for x in range(254)] )
        if useLazyflow:
            hints = self.topLevelOperatorView.opCarving.HintOverlay
            layer = ColortableLayer(LazyflowSource(hints), ctable, direct=True)
        else:
            hints = self.topLevelOperatorView.opCarving._hints
            layer = ColortableLayer(ArraySource(hints), ctable, direct=True)
        if not useLazyflow or hints.ready():
            layer.name = "hints"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)
            
        #pmaps
        useLazyflow = True
        pmaps = self.topLevelOperatorView.opCarving._pmap
        if pmaps is not None:
            layer = GrayscaleLayer(ArraySource(pmaps), direct=True)
            layer.name = "pmap"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)

        #done seg
        doneSeg = self.topLevelOperatorView.opCarving.DoneSegmentation
        if doneSeg.ready():
            if self._doneSegmentationLayer is None:
                layer = ColortableLayer(LazyflowSource(doneSeg), self._doneSegmentationColortable, direct=True)
                layer.name = "done seg"
                layer.visible = False
                layer.opacity = 0.5
                self._doneSegmentationLayer = layer
                layers.append(layer)
            else:
                layers.append(self._doneSegmentationLayer)

        #supervoxel
        sv = self.topLevelOperatorView.opCarving.Supervoxels
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
        # here we load the actual raw data from an ArraySource rather than from a LazyflowSource for speed reasons
        #
        
        #
        raw = numpy.add.reduce(self.topLevelOperatorView.RawData.value,3)
        raw5D = numpy.zeros((1,)+raw.shape+(1,), dtype=raw.dtype)
        raw5D[0,:,:,:,0] = raw[:,:,:]
        layer = GrayscaleLayer(ArraySource(raw5D), direct=True)
        layer.name = "raw"
        layer.visible = True
        layer.opacity = 1.0
        layers.append(layer)

        return layers
