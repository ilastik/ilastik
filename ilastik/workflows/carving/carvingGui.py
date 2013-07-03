#Python
import os
from functools import partial
import numpy
import random

#PyQt
from PyQt4.QtGui import QShortcut, QKeySequence
from PyQt4.QtGui import QColor, QMenu
from PyQt4.QtGui import QInputDialog, QMessageBox
from PyQt4 import uic

#volumina
from volumina.pixelpipeline.datasources import LazyflowSource, ArraySource
from volumina.layer import ColortableLayer, GrayscaleLayer
from volumina.utility import ShortcutManager
from volumina import colortables
from ilastik.widgets.labelListModel import LabelListModel
try:
    from volumina.view3d.volumeRendering import RenderingManager
except:
    pass

#ilastik
from ilastik.utility import bind
from ilastik.applets.labeling.labelingGui import LabelingGui

#===----------------------------------------------------------------------------------------------------------------===

class CarvingGui(LabelingGui):
    def __init__(self, topLevelOperatorView, drawerUiPath=None ):
        self.topLevelOperatorView = topLevelOperatorView

        labelingSlots = LabelingGui.LabelingSlots()
        labelingSlots.labelInput = topLevelOperatorView.WriteSeeds
        labelingSlots.labelOutput = topLevelOperatorView.opLabelArray.Output
        labelingSlots.labelEraserValue = topLevelOperatorView.opLabelArray.EraserLabelValue
        labelingSlots.labelDelete = topLevelOperatorView.opLabelArray.DeleteLabel
        labelingSlots.maxLabelValue = topLevelOperatorView.opLabelArray.MaxLabelValue
        labelingSlots.labelsAllowed = topLevelOperatorView.LabelsAllowed

        # We provide our own UI file (which adds an extra control for interactive mode)
        directory = os.path.split(__file__)[0]
        if drawerUiPath is None:
            drawerUiPath = os.path.join(directory, 'carvingDrawer.ui')
        self.dialogdirCOM = os.path.join(directory, 'carvingObjectManagement.ui')
        self.dialogdirSAD = os.path.join(directory, 'saveAsDialog.ui')

        rawInputSlot = topLevelOperatorView.RawData        
        super(CarvingGui, self).__init__(labelingSlots, topLevelOperatorView, drawerUiPath, rawInputSlot)

        # Init special base class members
        self.minLabelNumber = 2
        self.maxLabelNumber = 2
        
        mgr = ShortcutManager()
        
        #set up keyboard shortcuts
        segmentShortcut = QShortcut(QKeySequence("3"), self, member=self.labelingDrawerUi.segment.click,
                                    ambiguousMember=self.labelingDrawerUi.segment.click)
        mgr.register("Carving", "Run interactive segmentation", segmentShortcut, self.labelingDrawerUi.segment)
        

        self._doneSegmentationLayer = None
        self._showSegmentationIn3D = False
        
        #volume rendering
        try:
            self.render = True
            self._shownObjects3D = {}
            self._renderMgr = RenderingManager(
                renderer=self.editor.view3d.qvtk.renderer,
                qvtk=self.editor.view3d.qvtk)
        except:
            self.render = False

        
        self.labelingDrawerUi.segment.clicked.connect(self.onSegmentButton)
        self.labelingDrawerUi.segment.setEnabled(True)

        self.topLevelOperatorView.Segmentation.notifyDirty( bind( self._update_rendering ) )

        def onUncertaintyFGButton():
            print "uncertFG button clicked"
            pos = self.topLevelOperatorView.getMaxUncertaintyPos(label=2)
            self.editor.posModel.slicingPos = (pos[0], pos[1], pos[2])
        self.labelingDrawerUi.pushButtonUncertaintyFG.clicked.connect(onUncertaintyFGButton)
        self.labelingDrawerUi.pushButtonUncertaintyFG.setEnabled(True)

        def onUncertaintyBGButton():
            print "uncertBG button clicked"
            pos = self.topLevelOperatorView.getMaxUncertaintyPos(label=1)
            self.editor.posModel.slicingPos = (pos[0], pos[1], pos[2])
        self.labelingDrawerUi.pushButtonUncertaintyBG.clicked.connect(onUncertaintyBGButton)
        self.labelingDrawerUi.pushButtonUncertaintyBG.setEnabled(True)


        def onBackgroundPrioritySpin(value):
            print "background priority changed to %f" % value
            self.topLevelOperatorView.BackgroundPriority.setValue(value)
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
            self.topLevelOperatorView.UncertaintyType.setValue(value)
        self.labelingDrawerUi.uncertaintyCombo.currentIndexChanged.connect(onuncertaintyCombo)

        def onBackgroundPriorityDirty(slot, roi):
            oldValue = self.labelingDrawerUi.backgroundPrioritySpin.value()
            newValue = self.topLevelOperatorView.BackgroundPriority.value
            if  newValue != oldValue:
                self.labelingDrawerUi.backgroundPrioritySpin.setValue(newValue)
        self.topLevelOperatorView.BackgroundPriority.notifyDirty(onBackgroundPriorityDirty)
        
        def onNoBiasBelowDirty(slot, roi):
            oldValue = self.labelingDrawerUi.noBiasBelowSpin.value()
            newValue = self.topLevelOperatorView.NoBiasBelow.value
            if  newValue != oldValue:
                self.labelingDrawerUi.noBiasBelowSpin.setValue(newValue)
        self.topLevelOperatorView.NoBiasBelow.notifyDirty(onNoBiasBelowDirty)
        
        def onNoBiasBelowSpin(value):
            print "background priority changed to %f" % value
            self.topLevelOperatorView.NoBiasBelow.setValue(value)
        self.labelingDrawerUi.noBiasBelowSpin.valueChanged.connect(onNoBiasBelowSpin)

        self.labelingDrawerUi.saveAs.clicked.connect(self.onSaveAsButton)
        self.labelingDrawerUi.save.clicked.connect(self.onSaveButton)
        self.labelingDrawerUi.save.setEnabled(False) #initially, the user need to use "Save As"

        self.labelingDrawerUi.clear.clicked.connect(self.topLevelOperatorView.clearCurrentLabeling)
        self.labelingDrawerUi.clear.setEnabled(True)
        
        self.labelingDrawerUi.namesButton.clicked.connect(self.onShowObjectNames)
        
        def labelBackground():
            self.selectLabel(0)
        def labelObject():
            self.selectLabel(1)

        self._labelControlUi.labelListModel.allowRemove(False)

        bg = QShortcut(QKeySequence("1"), self, member=labelBackground, ambiguousMember=labelBackground)
        bgToolTipObject = LabelListModel.EntryToolTipAdapter(self._labelControlUi.labelListModel, 0)
        mgr.register("Carving", "Select background label", bg, bgToolTipObject)
        fg = QShortcut(QKeySequence("2"), self, member=labelObject, ambiguousMember=labelObject)
        fgToolTipObject = LabelListModel.EntryToolTipAdapter(self._labelControlUi.labelListModel, 1)
        mgr.register("Carving", "Select object label", fg, fgToolTipObject)

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
        addLayerToggleShortcut("hints","t")

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
            self._doneSegmentationColortable.append(QColor(0,255,0).rgba())
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
        
    def onSegmentButton(self):
        print "segment button clicked"
        self.topLevelOperatorView.Trigger.setDirty(slice(None))
    
    def saveAsDialog(self):
        '''special functionality: reject names given to other objects'''
        dialog = uic.loadUi(self.dialogdirSAD)
        dialog.warning.setVisible(False)
        dialog.Ok.clicked.connect(dialog.accept)
        dialog.Cancel.clicked.connect(dialog.reject)
        listOfItems = self.topLevelOperatorView.AllObjectNames[:].wait()
        dialog.isDisabled = False
        def validate():
            name = dialog.lineEdit.text()
            if name in listOfItems:
                dialog.Ok.setEnabled(False)
                dialog.warning.setVisible(True)
                dialog.isDisabled = True
            elif dialog.isDisabled:
                dialog.Ok.setEnabled(True)
                dialog.warning.setVisible(False)
                dialog.isDisabled = False
        dialog.lineEdit.textChanged.connect(validate)
        result = dialog.exec_()
        if result:
            return str(dialog.lineEdit.text())
    
    def onSaveAsButton(self):
        print "save object as?"
        if self.topLevelOperatorView.dataIsStorable():
            name = self.saveAsDialog()
            if name is None:
                return
            objects = self.topLevelOperatorView.AllObjectNames[:].wait()
            if name in objects:
                QMessageBox.critical(self, "Save Object As", "An object with name '%s' already exists.\nPlease choose a different name." % name)
                return
            self.topLevelOperatorView.saveObjectAs(name)
            print "save object as %s" % name
        else:
            msgBox = QMessageBox(self)
            msgBox.setText("The data does not seem fit to be stored.")
            msgBox.setWindowTitle("Problem with Data")
            msgBox.setIcon(2)
            msgBox.exec_()
            print "object not saved due to faulty data."
    
    def onSaveButton(self):
        if self.topLevelOperatorView.dataIsStorable():
            if self.topLevelOperatorView.hasCurrentObject():
                name = self.topLevelOperatorView.currentObjectName()
                self.topLevelOperatorView.saveObjectAs( name )
            else:
                self.onSaveAsButton()
        else:
            msgBox = QMessageBox(self)
            msgBox.setText("The data does no seem fit to be stored.")
            msgBox.setWindowTitle("Lousy Data")
            msgBox.setIcon(2)
            msgBox.exec_()
            print "object not saved due to faulty data."
    
    def onShowObjectNames(self):
        '''show object names and allow user to load/delete them'''
        dialog = uic.loadUi(self.dialogdirCOM)
        listOfItems = self.topLevelOperatorView.AllObjectNames[:].wait()
        dialog.objectNames.addItems(sorted(listOfItems))
        
        def loadSelection():
            for name in dialog.objectNames.selectedItems():
                objectname = str(name.text())
                self.topLevelOperatorView.loadObject(objectname)
        
        def deleteSelection():
            items = dialog.objectNames.selectedItems()
            if self.confirmAndDelete([str(name.text()) for name in items]):
                for name in items:
                    name.setHidden(True)
        
        dialog.loadButton.clicked.connect(loadSelection)
        dialog.deleteButton.clicked.connect(deleteSelection)
        dialog.cancelButton.clicked.connect(dialog.close)
        dialog.exec_()
    
    def confirmAndDelete(self,namelist):
        print namelist
        objectlist = "".join("\n  "+str(i) for i in namelist)
        confirmed = QMessageBox.question(self, "Delete Object", \
                    "Do you want to delete these objects?"+objectlist, \
                    QMessageBox.Yes | QMessageBox.Cancel, \
                    defaultButton=QMessageBox.Yes)
            
        if confirmed == QMessageBox.Yes:
            for name in namelist:
                self.topLevelOperatorView.deleteObject(name)
            return True
        return False
    
    def labelingContextMenu(self,names,op,position5d):
        menu = QMenu(self)
        menu.setObjectName("carving_context_menu")
        posItem = menu.addAction("position %d %d %d" % (position5d[1], position5d[2], position5d[3]))
        posItem.setEnabled(False)
        menu.addSeparator()
        for name in names:
            submenu = QMenu(name,menu)
            
            # Load
            loadAction = submenu.addAction("Load %s" % name)
            loadAction.triggered.connect( partial(op.loadObject, name) )
            
            # Delete
            def onDelAction(_name):
                self.confirmAndDelete([_name])
                if self.render and self._renderMgr.ready:
                    self._update_rendering()
            delAction = submenu.addAction("Delete %s" % name)
            delAction.triggered.connect( partial(onDelAction, name) )

            if self.render:
                if name in self._shownObjects3D:
                    # Remove
                    def onRemove3D(_name):
                        label = self._shownObjects3D.pop(_name)
                        self._renderMgr.removeObject(label)
                        self._update_rendering()
                    removeAction = submenu.addAction("Remove %s from 3D view" % name)
                    removeAction.triggered.connect( partial(onRemove3D, name) )
                else:
                    # Show
                    def onShow3D(_name):
                        label = self._renderMgr.addObject()
                        self._shownObjects3D[_name] = label
                        self._update_rendering()
                    showAction = submenu.addAction("Show 3D %s" % name)
                    showAction.triggered.connect( partial(onShow3D, name ) )
                        
            menu.addMenu(submenu)

        if names:
            menu.addSeparator()

        menu.addSeparator()
        showSeg3DAction = menu.addAction( "Show Editing Segmentation in 3D" )
        showSeg3DAction.setCheckable(True)
        showSeg3DAction.setChecked( self._showSegmentationIn3D )
        showSeg3DAction.triggered.connect( self._toggleSegmentation3D )
        
        if op.dataIsStorable():
            menu.addAction("Save objects").triggered.connect( self.onSegmentButton )
        menu.addAction("Browse objects").triggered.connect( self.topLevelOperatorView.clearCurrentLabeling )
        menu.addAction("Segment").triggered.connect( self.onShowObjectNames )
        menu.addAction("Clear").triggered.connect( self.onSaveAsButton )
        return menu
    
    def handleEditorRightClick(self, position5d, globalWindowCoordinate):
        names = self.topLevelOperatorView.doneObjectNamesForPosition(position5d[1:4])
        op = self.topLevelOperatorView

        # (Subclasses may override menu)
        menu = self.labelingContextMenu(names,op,position5d)
        if menu is not None:
            menu.exec_(globalWindowCoordinate)

    def _toggleSegmentation3D(self):
        self._showSegmentationIn3D = not self._showSegmentationIn3D
        if self._showSegmentationIn3D:
            self._segmentation_3d_label = self._renderMgr.addObject()
        else:
            self._renderMgr.removeObject(self._segmentation_3d_label)
        self._update_rendering()
    
    def _update_rendering(self):
        if not self.render:
            return

        op = self.topLevelOperatorView
        if not self._renderMgr.ready:
            self._renderMgr.setup(op.InputData.meta.shape[1:4])

        # remove nonexistent objects
        self._shownObjects3D = dict((k, v) for k, v in self._shownObjects3D.iteritems()
                                    if k in op.MST.value.object_lut.keys())

        lut = numpy.zeros(len(op.MST.value.objects.lut), dtype=numpy.int32)
        for name, label in self._shownObjects3D.iteritems():
            objectSupervoxels = op.MST.value.object_lut[name]
            lut[objectSupervoxels] = label

        if self._showSegmentationIn3D:
            # Add segmentation as label, which is green
            lut[:] = numpy.where( op.MST.value.segmentation.lut == 2, self._segmentation_3d_label, lut )
                    
        self._renderMgr.volume = lut[op.MST.value.regionVol] # (Advanced indexing)
        self._update_colors()
        self._renderMgr.update()

    def _update_colors(self):
        op = self.topLevelOperatorView
        ctable = self._doneSegmentationLayer.colorTable

        for name, label in self._shownObjects3D.iteritems():
            color = QColor(ctable[op.MST.value.object_names[name]])
            color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            self._renderMgr.setColor(label, color)

        if self._showSegmentationIn3D:
            self._renderMgr.setColor(self._segmentation_3d_label, (0.0, 1.0, 0.0)) # Green


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
            currObj = self.topLevelOperatorView.CurrentObjectName.value
            hasSeg  = self.topLevelOperatorView.HasSegmentation.value
            #nzLB    = self.topLevelOperatorView.opLabeling.NonzeroLabelBlocks[:].wait()[0]
            
            self.labelingDrawerUi.currentObjectLabel.setText("current object: %s" % currObj)
            self.labelingDrawerUi.save.setEnabled(currObj != "" and hasSeg)
            self.labelingDrawerUi.saveAs.setEnabled(currObj == "" and hasSeg)
            #rethink this
            #self.labelingDrawerUi.segment.setEnabled(len(nzLB) > 0)
            #self.labelingDrawerUi.clear.setEnabled(len(nzLB) > 0)
        self.topLevelOperatorView.CurrentObjectName.notifyDirty(onButtonsEnabled)
        self.topLevelOperatorView.HasSegmentation.notifyDirty(onButtonsEnabled)
        self.topLevelOperatorView.opLabelArray.NonzeroBlocks.notifyDirty(onButtonsEnabled)
        
        # Labels
        labellayer, labelsrc = self.createLabelLayer(direct=True)
        if labellayer is not None:
            layers.append(labellayer)
            # Tell the editor where to draw label data
            self.editor.setLabelSink(labelsrc)

        #uncertainty
        uncert = self.topLevelOperatorView.Uncertainty
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
        seg = self.topLevelOperatorView.Segmentation
        
        #seg = self.topLevelOperatorView.MST.value.segmentation
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
        done = self.topLevelOperatorView.DoneObjects
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
            hints = self.topLevelOperatorView.HintOverlay
            layer = ColortableLayer(LazyflowSource(hints), ctable, direct=True)
        else:
            hints = self.topLevelOperatorView._hints
            layer = ColortableLayer(ArraySource(hints), ctable, direct=True)
        if not useLazyflow or hints.ready():
            layer.name = "hints"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)
            
        #pmaps
        useLazyflow = True
        pmaps = self.topLevelOperatorView._pmap
        if pmaps is not None:
            layer = GrayscaleLayer(ArraySource(pmaps), direct=True)
            layer.name = "pmap"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)

        #done seg
        doneSeg = self.topLevelOperatorView.DoneSegmentation
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
        sv = self.topLevelOperatorView.Supervoxels
        if sv.ready():
            for i in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            layer = ColortableLayer(LazyflowSource(sv), colortable, direct=True)
            layer.name = "supervoxels"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)

        #raw data
        rawSlot = self.topLevelOperatorView.RawData
        if rawSlot.ready():
            raw5D = self.topLevelOperatorView.RawData.value
            layer = GrayscaleLayer(ArraySource(raw5D), direct=True)
            #layer = GrayscaleLayer( LazyflowSource(rawSlot) )
            layer.name = "raw"
            layer.visible = True
            layer.opacity = 1.0
            layers.append(layer)

        inputSlot = self.topLevelOperatorView.InputData
        if inputSlot.ready():
            layer = GrayscaleLayer( LazyflowSource(inputSlot), direct=True )
            layer.name = "input"
            layer.visible = not rawSlot.ready()
            layer.opacity = 1.0
            layers.append(layer)

        filteredSlot = self.topLevelOperatorView.FilteredInputData
        if filteredSlot.ready():
            layer = GrayscaleLayer( LazyflowSource(filteredSlot) )
            layer.name = "filtered input"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)

        return layers
