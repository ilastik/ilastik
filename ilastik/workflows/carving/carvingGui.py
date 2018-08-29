from __future__ import division
###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
#Python
import os
from functools import partial
from collections import defaultdict
import numpy

#PyQt
from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMenu, QMessageBox, QFileDialog

#volumina
from volumina.pixelpipeline.datasources import LazyflowSource, ArraySource
from volumina.layer import ColortableLayer, GrayscaleLayer
from volumina.utility import ShortcutManager, PreferencesManager

from ilastik.widgets.labelListModel import LabelListModel
#try:
#    from volumina.view3d.volumeRendering import RenderingManager
#    from volumina.view3d.view3d import convertVTPtoOBJ
#    from volumina.view3d.GenerateModelsFromLabels_thread import MeshExtractorDialog
#    from vtk import vtkXMLPolyDataWriter, vtkPolyDataWriter
#    _have_vtk = True
#except ImportError:
_have_vtk = False

from volumina.view3d.meshgenerator import MeshGeneratorDialog, mesh_to_obj
from volumina.view3d.volumeRendering import RenderingManager

#ilastik
from ilastik.utility import bind
from ilastik.applets.labeling.labelingGui import LabelingGui


import logging
logger = logging.getLogger(__name__)

CURRENT_SEGMENTATION_NAME = "__current_segmentation__"
#===----------------------------------------------------------------------------------------------------------------===

class CarvingGui(LabelingGui):
    def __init__(self, parentApplet, topLevelOperatorView, drawerUiPath=None ):
        self.topLevelOperatorView = topLevelOperatorView

        #members
        self._doneSegmentationLayer = None
        self._showSegmentationIn3D = False
        #self._showUncertaintyLayer = False
        #end: members

        labelingSlots = LabelingGui.LabelingSlots()
        labelingSlots.labelInput       = topLevelOperatorView.WriteSeeds
        labelingSlots.labelOutput      = topLevelOperatorView.opLabelArray.Output
        labelingSlots.labelEraserValue = topLevelOperatorView.opLabelArray.EraserLabelValue
        labelingSlots.labelNames       = topLevelOperatorView.LabelNames
        labelingSlots.labelDelete      = topLevelOperatorView.opLabelArray.DeleteLabel
        labelingSlots.maxLabelValue    = topLevelOperatorView.opLabelArray.MaxLabelValue
        
        # We provide our own UI file (which adds an extra control for interactive mode)
        directory = os.path.split(__file__)[0]
        if drawerUiPath is None:
            drawerUiPath = os.path.join(directory, 'carvingDrawer.ui')
        self.dialogdirCOM = os.path.join(directory, 'carvingObjectManagement.ui')
        self.dialogdirSAD = os.path.join(directory, 'saveAsDialog.ui')

        # Add 3DWidget only if the data is 3D
        is_3d = self._is_3d()

        super(CarvingGui, self).__init__(parentApplet, labelingSlots, topLevelOperatorView, drawerUiPath,
                                         is_3d_widget_visible=is_3d)

        self.labelingDrawerUi.currentObjectLabel.setText("<not saved yet>")

        # Init special base class members
        self.minLabelNumber = 2
        self.maxLabelNumber = 2

        mgr = ShortcutManager()
        ActionInfo = ShortcutManager.ActionInfo

        #set up keyboard shortcuts
        mgr.register( "3", ActionInfo( "Carving",
                                       "Run interactive segmentation",
                                       "Run interactive segmentation",
                                       self.labelingDrawerUi.segment.click,
                                       self.labelingDrawerUi.segment,
                                       self.labelingDrawerUi.segment  ) )


        # Disable 3D view by default
        self.render = False
        if is_3d:
            try:
                self._renderMgr = RenderingManager( self.editor.view3d )
                self._shownObjects3D = {}
                self.render = True
            except:
                self.render = False

        # Segmentation is toggled on by default in _after_init, below.
        # (We can't enable it until the layers are all present.)
        self._showSegmentationIn3D = False
        self._segmentation_3d_label = None
                
        self.labelingDrawerUi.segment.clicked.connect(self.onSegmentButton)
        self.labelingDrawerUi.segment.setEnabled(True)

        self.topLevelOperatorView.Segmentation.notifyDirty( bind( self._segmentation_dirty ) )
        self.topLevelOperatorView.HasSegmentation.notifyValueChanged( bind( self._updateGui ) )

        ## uncertainty

        #self.labelingDrawerUi.pushButtonUncertaintyFG.setEnabled(False)
        #self.labelingDrawerUi.pushButtonUncertaintyBG.setEnabled(False)

        #def onUncertaintyFGButton():
        #    logger.debug( "uncertFG button clicked" )
        #    pos = self.topLevelOperatorView.getMaxUncertaintyPos(label=2)
        #    self.editor.posModel.slicingPos = (pos[0], pos[1], pos[2])
        #self.labelingDrawerUi.pushButtonUncertaintyFG.clicked.connect(onUncertaintyFGButton)

        #def onUncertaintyBGButton():
        #    logger.debug( "uncertBG button clicked" )
        #    pos = self.topLevelOperatorView.getMaxUncertaintyPos(label=1)
        #    self.editor.posModel.slicingPos = (pos[0], pos[1], pos[2])
        #self.labelingDrawerUi.pushButtonUncertaintyBG.clicked.connect(onUncertaintyBGButton)

        #def onUncertaintyCombo(value):
        #    if value == 0:
        #        value = "none"
        #        self.labelingDrawerUi.pushButtonUncertaintyFG.setEnabled(False)
        #        self.labelingDrawerUi.pushButtonUncertaintyBG.setEnabled(False)
        #        self._showUncertaintyLayer = False
        #    else:
        #        if value == 1:
        #            value = "localMargin"
        #        elif value == 2:
        #            value = "exchangeCount"
        #        elif value == 3:
        #            value = "gabow"
        #        else:
        #            raise RuntimeError("unhandled case '%r'" % value)
        #        self.labelingDrawerUi.pushButtonUncertaintyFG.setEnabled(True)
        #        self.labelingDrawerUi.pushButtonUncertaintyBG.setEnabled(True)
        #        self._showUncertaintyLayer = True
        #        logger.debug( "uncertainty changed to %r" % value )
        #    self.topLevelOperatorView.UncertaintyType.setValue(value)
        #    self.updateAllLayers() #make sure that an added/deleted uncertainty layer is recognized
        #self.labelingDrawerUi.uncertaintyCombo.currentIndexChanged.connect(onUncertaintyCombo)


        ## save

        self.labelingDrawerUi.save.clicked.connect(self.onSaveButton)

        ## clear

        self.labelingDrawerUi.clear.clicked.connect(self._onClearAction)
        
        ## object names
        
        self.labelingDrawerUi.namesButton.clicked.connect(self.onShowObjectNames)
        if hasattr( self.labelingDrawerUi, 'exportAllMeshesButton' ):
            self.labelingDrawerUi.exportAllMeshesButton.clicked.connect(self._exportAllObjectMeshes)

        self.labelingDrawerUi.labelListView.allowDelete = False
        self._labelControlUi.labelListModel.allowRemove(False)

        def layerIndexForName(name):
            return self.layerstack.findMatchingIndex(lambda x: x.name == name)
        
        def addLayerToggleShortcut(layername, shortcut):
            def toggle():
                row = layerIndexForName(layername)
                self.layerstack.selectRow(row)
                layer = self.layerstack[row]
                layer.visible = not layer.visible
                self.viewerControlWidget().layerWidget.setFocus()

            mgr.register(shortcut, ActionInfo( "Carving", 
                                               "Toggle layer %s" % layername, 
                                               "Toggle layer %s" % layername, 
                                               toggle,
                                               self.viewerControlWidget(),
                                               None ) )

        #TODO
        addLayerToggleShortcut("Completed segments (unicolor)", "d")
        addLayerToggleShortcut("Segmentation", "s")
        addLayerToggleShortcut("Input Data", "r")

        def makeColortable():
            self._doneSegmentationColortable = [QColor(0,0,0,0).rgba()]
            for i in range(254):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                # ensure colors have sufficient distance to pure red and pure green
                while (255 - r)+g+b<128 or r+(255-g)+b<128:
                    r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                self._doneSegmentationColortable.append(QColor(r,g,b).rgba())
            self._doneSegmentationColortable.append(QColor(0,255,0).rgba())
        makeColortable()
        self._updateGui()

    def _is_3d(self):
        tagged_shape = defaultdict(lambda: 1)
        tagged_shape.update(self.topLevelOperatorView.InputData.meta.getTaggedShape())
        is_3d = tagged_shape['x'] > 1 and tagged_shape['y'] > 1 and tagged_shape['z'] > 1
        return is_3d

    def _after_init(self):
        super(CarvingGui, self)._after_init()
        if self.render:
            self._toggleSegmentation3D()
        
    def _updateGui(self):
        self.labelingDrawerUi.save.setEnabled( self.topLevelOperatorView.dataIsStorable() )
        
    def onSegmentButton(self):
        logger.debug( "segment button clicked" )
        bkPriorityValue = self.labelingDrawerUi.backgroundPrioritySpin.value()
        self.topLevelOperatorView.BackgroundPriority.setValue(bkPriorityValue)
        biasValue = self.labelingDrawerUi.noBiasBelowSpin.value()
        self.topLevelOperatorView.NoBiasBelow.setValue(biasValue)
        self.topLevelOperatorView.Trigger.setDirty(slice(None))
    
    def saveAsDialog(self, name=""):
        '''special functionality: reject names given to other objects'''
        dialog = uic.loadUi(self.dialogdirSAD)
        dialog.lineEdit.setText(name)
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
    
    def onSaveButton(self):
        logger.info( "save object as?" )
        if self.topLevelOperatorView.dataIsStorable():
            prevName = ""
            if self.topLevelOperatorView.hasCurrentObject():
                prevName = self.topLevelOperatorView.currentObjectName()
            if prevName == "<not saved yet>":
                prevName = ""
            name = self.saveAsDialog(name=prevName)
            if name is None:
                return
            objects = self.topLevelOperatorView.AllObjectNames[:].wait()
            if name in objects and name != prevName:
                QMessageBox.critical(self, "Save Object As", "An object with name '%s' already exists.\nPlease choose a different name." % name)
                return
            self.topLevelOperatorView.saveObjectAs(name)
            logger.info( "save object as %s" % name )
            if prevName != name and prevName != "":
                self.topLevelOperatorView.deleteObject(prevName)
            elif prevName == name:
                self._renderMgr.removeObject(prevName)
                self._renderMgr.invalidateObject(prevName)
                self._shownObjects3D.pop(prevName, None)
        else:
            msgBox = QMessageBox(self)
            msgBox.setText("The data does not seem fit to be stored.")
            msgBox.setWindowTitle("Problem with Data")
            msgBox.setIcon(2)
            msgBox.exec_()
            logger.error( "object not saved due to faulty data." )
    
    def onShowObjectNames(self):
        '''show object names and allow user to load/delete them'''
        dialog = uic.loadUi(self.dialogdirCOM)
        listOfItems = self.topLevelOperatorView.AllObjectNames[:].wait()
        dialog.objectNames.addItems(sorted(listOfItems))
        
        def loadSelection():
            selected = [str(name.text()) for name in dialog.objectNames.selectedItems()]
            dialog.close()
            for objectname in selected: 
                self.topLevelOperatorView.loadObject(objectname)
        
        def deleteSelection():
            items = dialog.objectNames.selectedItems()
            if self.confirmAndDelete([str(name.text()) for name in items]):
                for name in items:
                    name.setHidden(True)
            dialog.close()
        
        dialog.loadButton.clicked.connect(loadSelection)
        dialog.deleteButton.clicked.connect(deleteSelection)
        dialog.cancelButton.clicked.connect(dialog.close)
        dialog.exec_()
    
    def confirmAndDelete(self,namelist):
        logger.info( "confirmAndDelete: {}".format( namelist ) )
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
            
            # Export mesh

            exportAction = submenu.addAction("Export mesh for %s" % name)
            exportAction.triggered.connect( partial(self._onContextMenuExportMesh, name) )
                        
            menu.addMenu(submenu)

        if names:
            menu.addSeparator()

        menu.addSeparator()
        if self.render:
            showSeg3DAction = menu.addAction( "Show Editing Segmentation in 3D" )
            showSeg3DAction.setCheckable(True)
            showSeg3DAction.setChecked( self._showSegmentationIn3D )
            showSeg3DAction.triggered.connect( self._toggleSegmentation3D )
        
        if op.dataIsStorable():
            menu.addAction("Save object").triggered.connect( self.onSaveButton )
        menu.addAction("Browse objects").triggered.connect( self.onShowObjectNames )
        menu.addAction("Segment").triggered.connect( self.onSegmentButton )
        menu.addAction("Clear").triggered.connect( self._onClearAction )
        return menu

    def _onClearAction(self):
        confirm = QMessageBox.warning(self, "Really Clear?", "Clear all brushtrokes?", QMessageBox.Ok | QMessageBox.Cancel)
        if confirm == QMessageBox.Ok:
            self.topLevelOperatorView.clearCurrentLabeling()

    def _onContextMenuExportMesh(self, _name):
        """
        Export a single object mesh to a user-specified filename.
        """
        recent_dir = PreferencesManager().get( 'carving', 'recent export mesh directory' )
        if recent_dir is None:
            defaultPath = os.path.join( os.path.expanduser('~'), '{}obj'.format(_name) )
        else:
            defaultPath = os.path.join( recent_dir, '{}.obj'.format(_name) )
        filepath, _filter = QFileDialog.getSaveFileName(self, 
                                               "Save meshes for object '{}'".format(_name),
                                               defaultPath,
                                               "OBJ Files (*.obj)")
        if not filepath:
            return
        obj_filepath = str(filepath)
        PreferencesManager().set( 'carving', 'recent export mesh directory', os.path.split(obj_filepath)[0] )
        
        self._exportMeshes([_name], [obj_filepath])

    def _exportAllObjectMeshes(self):
        """
        Export all objects in the project as separate .obj files, stored to a user-specified directory.
        """
        mst = self.topLevelOperatorView.MST.value
        if not list(mst.object_lut.keys()):
            QMessageBox.critical(self, "Can't Export", "You have no saved objets, so there are no meshes to export.")
            return
        
        recent_dir = PreferencesManager().get( 'carving', 'recent export mesh directory' )
        if recent_dir is None:
            defaultPath = os.path.join( os.path.expanduser('~') )
        else:
            defaultPath = os.path.join( recent_dir )
        export_dir = QFileDialog.getExistingDirectory( self, 
                                                       "Select export directory for mesh files",
                                                       defaultPath)
        if not export_dir:
            return
        export_dir = str(export_dir)
        PreferencesManager().set( 'carving', 'recent export mesh directory', export_dir )

        # Get the list of all object names
        object_names = []
        obj_filepaths = []
        for object_name in list(mst.object_lut.keys()):
            object_names.append( object_name )
            obj_filepaths.append( os.path.join( export_dir, "{}.obj".format( object_name ) ) )
        
        if object_names:
            self._exportMeshes( object_names, obj_filepaths )

    def _exportMeshes(self, object_names, obj_filepaths):
        """
        Export a mesh .obj file for each object in the object_names list to the corresponding file name from the obj_filepaths list.
        This function is pseudo-recursive. It works like this:
        1) Pop the first name/file from the args
        2) Kick off the export by launching the export mesh dlg
        3) return from this function to allow the eventloop to resume while the export is running
        4) When the export dlg is finished, create the mesh file
        5) If there are still more items in the object_names list to process, repeat this function.
        """
        # Pop the first object off the list
        object_name = object_names.pop(0)
        obj_filepath = obj_filepaths.pop(0)
        
        # Construct a volume with only this object.
        # We might be tempted to get the object directly from opCarving.DoneObjects, 
        #  but that won't be correct for overlapping objects.
        mst = self.topLevelOperatorView.MST.value
        object_supervoxels = mst.object_lut[object_name]
        object_lut = numpy.zeros(mst.nodeNum+1, dtype=numpy.int32)
        object_lut[object_supervoxels] = 1
        supervoxel_volume = mst.supervoxelUint32
        object_volume = object_lut[supervoxel_volume]

        if len(numpy.unique(object_volume)) <= 1:
            if object_names:
                self._exportMeshes(object_names, obj_filepaths)
            return

        # Run the mesh extractor
        window = MeshGeneratorDialog(self)
        
        def onMeshesComplete(mesh):
            """
            Called when mesh extraction is complete.
            Writes the extracted mesh to an .obj file
            """
            logger.info( "Mesh generation complete." )

            # FIXME: the old comment: Mesh count can sometimes be 0 for the '<not saved yet>' object...
            # FIXME: is this still relevant???
            '''
            mesh_count = len( window.extractor.meshes )
            if mesh_count > 0:
                assert mesh_count == 1, \
                    "Found {} meshes processing object '{}',"\
                    "(only expected 1)".format( mesh_count, object_name )
                mesh = list(window.extractor.meshes.values())[0]
                logger.info( "Saving meshes to {}".format( obj_filepath ) )
    
                # Use VTK to write to a temporary .vtk file
                tmpdir = tempfile.mkdtemp()
                vtkpoly_path = os.path.join(tmpdir, 'meshes.vtk')
                w = vtkPolyDataWriter()
                w.SetFileTypeToASCII()
                w.SetInput(mesh)
                w.SetFileName(vtkpoly_path)
                w.Write()
                
                # Now convert the file to .obj format.
                convertVTPtoOBJ(vtkpoly_path, obj_filepath)
            '''
            logger.info("Saving meshes to {}".format(obj_filepath))
            mesh_to_obj(mesh, obj_filepath, object_name)
            # Cleanup: We don't need the window anymore.
            window.setParent(None)

            # If there are still objects left to process,
            #   start again with the remainder of the list.
            if object_names:
                self._exportMeshes(object_names, obj_filepaths)
            
        window.finished.connect( onMeshesComplete )

        # Kick off the save process and exit to the event loop
        window.show()
        QTimer.singleShot(0, partial(window.run, object_volume))


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
            self._segmentation_3d_label = None
        self._update_rendering()

    def _segmentation_dirty(self):
        if self.render:
            self._renderMgr.invalidateObject(CURRENT_SEGMENTATION_NAME)
            self._renderMgr.removeObject(CURRENT_SEGMENTATION_NAME)

        self._update_rendering()

    def _update_rendering(self):
        if not self.render:
            return

        op = self.topLevelOperatorView
        if not self._renderMgr.ready:
            shape = op.InputData.meta.shape[1:4]
            self._renderMgr.setup(op.InputData.meta.shape[1:4])

        # remove nonexistent objects
        self._shownObjects3D = dict((k, v) for k, v in self._shownObjects3D.items()
                                    if k in list(op.MST.value.object_lut.keys()))

        lut = numpy.zeros(op.MST.value.nodeNum+1, dtype=numpy.int32)
        label_name_map = {}
        for name, label in self._shownObjects3D.items():
            objectSupervoxels = op.MST.value.object_lut[name]
            lut[objectSupervoxels] = label
            label_name_map[label] = name
            label_name_map[name] = label

        if self._showSegmentationIn3D:
            # Add segmentation as label, which is green
            label_name_map[self._segmentation_3d_label] = CURRENT_SEGMENTATION_NAME
            label_name_map[CURRENT_SEGMENTATION_NAME] = self._segmentation_3d_label
            lut[:] = numpy.where( op.MST.value.getSuperVoxelSeg() == 2, self._segmentation_3d_label, lut )

        self._renderMgr.volume = lut[op.MST.value.supervoxelUint32], label_name_map  # (Advanced indexing)
        self._update_colors()
        self._renderMgr.update()

    def _update_colors(self):
        op = self.topLevelOperatorView
        ctable = self._doneSegmentationLayer.colorTable

        for name, label in self._shownObjects3D.items():
            color = QColor(ctable[op.MST.value.object_names[name]])
            color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            self._renderMgr.setColor(label, color)

        if self._showSegmentationIn3D and self._segmentation_3d_label is not None:
            self._renderMgr.setColor(self._segmentation_3d_label, (0.0, 1.0, 0.0)) # Green

    def _getNext(self, slot, parentFun, transform=None):
        numLabels = self.labelListData.rowCount()
        value = slot.value
        if numLabels < len(value):
            result = value[numLabels]
            if transform is not None:
                result = transform(result)
            return result
        else:
            return parentFun()

    def getNextLabelName(self):
        return self._getNext(self.topLevelOperatorView.LabelNames,
                             super(CarvingGui, self).getNextLabelName)

    def appletDrawers(self):
        return [ ("Carving", self._labelControlUi) ]

    def setupLayers( self ):
        logger.debug( "setupLayers" )
        
        layers = []

        def onButtonsEnabled(slot, roi):
            currObj = self.topLevelOperatorView.CurrentObjectName.value
            hasSeg  = self.topLevelOperatorView.HasSegmentation.value
            
            self.labelingDrawerUi.currentObjectLabel.setText(currObj)
            self.labelingDrawerUi.save.setEnabled(hasSeg)

        self.topLevelOperatorView.CurrentObjectName.notifyDirty(onButtonsEnabled)
        self.topLevelOperatorView.HasSegmentation.notifyDirty(onButtonsEnabled)
        self.topLevelOperatorView.opLabelArray.NonzeroBlocks.notifyDirty(onButtonsEnabled)
        
        # Labels
        labellayer, labelsrc = self.createLabelLayer(direct=True)
        if labellayer is not None:
            labellayer._allowToggleVisible = False
            layers.append(labellayer)
            # Tell the editor where to draw label data
            self.editor.setLabelSink(labelsrc)

        #uncertainty
        #if self._showUncertaintyLayer:
        #    uncert = self.topLevelOperatorView.Uncertainty
        #    if uncert.ready():
        #        colortable = []
        #        for i in range(256-len(colortable)):
        #            r,g,b,a = i,0,0,i
        #            colortable.append(QColor(r,g,b,a).rgba())
        #        layer = ColortableLayer(LazyflowSource(uncert), colortable, direct=True)
        #        layer.name = "Uncertainty"
        #        layer.visible = True
        #        layer.opacity = 0.3
        #        layers.append(layer)
       
        #segmentation 
        seg = self.topLevelOperatorView.Segmentation
        
        #seg = self.topLevelOperatorView.MST.value.segmentation
        #temp = self._done_lut[self.MST.value.supervoxelUint32[sl[1:4]]]
        if seg.ready():
            #source = RelabelingArraySource(seg)
            #source.setRelabeling(numpy.arange(256, dtype=numpy.uint8))

            # assign to the object label color, 0 is transparent, 1 is background
            colortable = [QColor(0,0,0,0).rgba(), QColor(0,0,0,0).rgba(), labellayer._colorTable[2]]
            for i in range(256-len(colortable)):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())

            layer = ColortableLayer(LazyflowSource(seg), colortable, direct=True)
            layer.name = "Segmentation"
            layer.setToolTip("This layer displays the <i>current</i> segmentation. Simply add foreground and background " \
                             "labels, then press <i>Segment</i>.")
            layer.visible = True
            layer.opacity = 0.3
            layers.append(layer)
        
        #done 
        doneSeg = self.topLevelOperatorView.DoneSegmentation
        if doneSeg.ready():
            #FIXME: if the user segments more than 255 objects, those with indices that divide by 255 will be shown as transparent
            #both here and in the _doneSegmentationColortable
            colortable = 254*[QColor(230, 25, 75).rgba()]
            colortable.insert(0, QColor(0, 0, 0, 0).rgba())

            #have to use lazyflow because it provides dirty signals
            layer = ColortableLayer(LazyflowSource(doneSeg), colortable, direct=True)
            layer.name = "Completed segments (unicolor)"
            layer.setToolTip("In order to keep track of which objects you have already completed, this layer " \
                             "shows <b>all completed object</b> in one color (<b>blue</b>). " \
                             "The reason for only one color is that for finding out which " \
                              "objects to label next, the identity of already completed objects is unimportant " \
                              "and destracting.")
            layer.visible = False
            layer.opacity = 0.5
            layers.append(layer)

            layer = ColortableLayer(LazyflowSource(doneSeg), self._doneSegmentationColortable, direct=True)
            layer.name = "Completed segments (one color per object)"
            layer.setToolTip("<html>In order to keep track of which objects you have already completed, this layer " \
                             "shows <b>all completed object</b>, each with a random color.</html>")
            layer.visible = False
            layer.opacity = 0.5
            layer.colortableIsRandom = True
            self._doneSegmentationLayer = layer
            layers.append(layer)

        #supervoxel
        sv = self.topLevelOperatorView.Supervoxels
        if sv.ready():
            colortable = []
            for i in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            layer = ColortableLayer(LazyflowSource(sv), colortable, direct=True)
            layer.name = "Supervoxels"
            layer.setToolTip("<html>This layer shows the partitioning of the input image into <b>supervoxels</b>. The carving " \
                             "algorithm uses these tiny puzzle-piceces to piece together the segmentation of an " \
                             "object. Sometimes, supervoxels are too large and straddle two distinct objects " \
                             "(undersegmentation). In this case, it will be impossible to achieve the desired " \
                             "segmentation. This layer helps you to understand these cases.</html>")
            layer.visible = False
            layer.colortableIsRandom = True
            layer.opacity = 0.5
            layers.append(layer)

        # Visual overlay (just for easier labeling)
        overlaySlot = self.topLevelOperatorView.OverlayData
        if overlaySlot.ready():
            overlay5D = self.topLevelOperatorView.OverlayData.value
            layer = GrayscaleLayer(ArraySource(overlay5D), direct=True)
            layer.visible = True
            layer.name = 'Overlay'
            layer.opacity = 1.0
            # if the flag window_leveling is set the contrast 
            # of the layer is adjustable
            layer.window_leveling = True
            self.labelingDrawerUi.thresToolButton.show()
            layers.append(layer)
            del layer

        inputSlot = self.topLevelOperatorView.InputData
        if inputSlot.ready():
            layer = GrayscaleLayer( LazyflowSource(inputSlot), direct=True )
            layer.name = "Input Data"
            layer.setToolTip("<html>The data originally loaded into ilastik (unprocessed).</html>")
            #layer.visible = not rawSlot.ready()
            layer.visible = True
            layer.opacity = 1.0

            # Window leveling is already active on the Overlay,
            # but if no overlay was provided, then activate window_leveling on the raw data instead.
            if not overlaySlot.ready():
                # if the flag window_leveling is set the contrast 
                # of the layer is adjustable
                layer.window_leveling = True
                self.labelingDrawerUi.thresToolButton.show()

            layers.append(layer)
            del layer

        filteredSlot = self.topLevelOperatorView.FilteredInputData
        if filteredSlot.ready():
            layer = GrayscaleLayer( LazyflowSource(filteredSlot) )
            layer.name = "Filtered Input"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)

        return layers
