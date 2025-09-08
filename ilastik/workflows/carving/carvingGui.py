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
# 		   http://ilastik.org/license.html
###############################################################################
# Python
import os
import re
import string
from functools import partial
from collections import defaultdict
from typing import List
import numpy

# PyQt
from qtpy import uic
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QMenu, QMessageBox, QFileDialog

# lazyflow
from lazyflow.request import Request

# volumina
from volumina.api import createDataSource, ArraySource
from volumina.layer import ColortableLayer, GrayscaleLayer
from volumina.utility import ShortcutManager, preferences

from volumina.view3d.meshgenerator import mesh_to_obj, labeling_to_mesh
from volumina.view3d.volumeRendering import RenderingManager

# ilastik
from ilastik.utility import bind
from ilastik.applets.labeling.labelingGui import LabelingGui, LabelingSlots


import logging

logger = logging.getLogger(__name__)

CURRENT_SEGMENTATION_NAME = "__current_segmentation__"
DEFAULT_OBJECT_NAME = "<not saved yet>"
# ===----------------------------------------------------------------------------------------------------------------===


class CarvingGui(LabelingGui):
    def __init__(self, parentApplet, topLevelOperatorView, drawerUiPath=None):
        self.topLevelOperatorView = topLevelOperatorView
        self.isInitialized = (
            False  # Need this flag in carvingApplet where initialization is terminated with label selection
        )

        # members
        self._doneSegmentationLayer = None
        self._showSegmentationIn3D = False
        # end: members

        labelingSlots = LabelingSlots(
            labelInput=topLevelOperatorView.WriteSeeds,
            labelOutput=topLevelOperatorView.opLabelArray.Output,
            labelEraserValue=topLevelOperatorView.opLabelArray.EraserLabelValue,
            labelNames=topLevelOperatorView.LabelNames,
            labelDelete=topLevelOperatorView.opLabelArray.DeleteLabel,
            nonzeroLabelBlocks=topLevelOperatorView.opLabelArray.NonzeroBlocks,
        )

        # We provide our own UI file (which adds an extra control for interactive mode)
        directory = os.path.split(__file__)[0]
        if drawerUiPath is None:
            drawerUiPath = os.path.join(directory, "carvingDrawer.ui")
        self.dialogdirCOM = os.path.join(directory, "carvingObjectManagement.ui")
        self.dialogdirSAD = os.path.join(directory, "saveAsDialog.ui")

        # Add 3DWidget only if the data is 3D
        is_3d = self._is_3d()

        super(CarvingGui, self).__init__(
            parentApplet, labelingSlots, topLevelOperatorView, drawerUiPath, is_3d_widget_visible=is_3d
        )

        self.parentApplet = parentApplet
        self.labelingDrawerUi.currentObjectLabel.setText(DEFAULT_OBJECT_NAME)

        # Init special base class members
        self.minLabelNumber = 2
        self.maxLabelNumber = 2

        mgr = ShortcutManager()
        ActionInfo = ShortcutManager.ActionInfo

        # set up keyboard shortcuts
        mgr.register(
            "3",
            ActionInfo(
                "Carving",
                "Run interactive segmentation",
                "Run interactive segmentation",
                self.labelingDrawerUi.segment.click,
                self.labelingDrawerUi.segment,
                self.labelingDrawerUi.segment,
            ),
        )

        # Disable 3D view by default
        self.render = False
        if is_3d:
            try:
                self._renderMgr = RenderingManager(self.editor.view3d)
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

        self.topLevelOperatorView.Segmentation.notifyDirty(bind(self._segmentation_dirty))
        self.topLevelOperatorView.CanObjectBeSaved.notifyValueChanged(bind(self._updateGui))

        self.labelingDrawerUi.objPrefix.setText(self.objectPrefix)
        self.labelingDrawerUi.objPrefix.textChanged.connect(self.setObjectPrefix)

        ## save

        self.labelingDrawerUi.save.clicked.connect(self.onSaveButton)

        ## clear

        self.labelingDrawerUi.clear.clicked.connect(self._onClearAction)

        ## object names

        self.labelingDrawerUi.namesButton.clicked.connect(self.onShowObjectNames)
        if hasattr(self.labelingDrawerUi, "exportAllMeshesButton"):
            # Mesh export only works for 3D. Disable for now until we implement a 2D workaround.
            input_data_shape = self.topLevelOperatorView.InputData.meta.getTaggedShape()
            if "z" in input_data_shape and input_data_shape["z"] > 1:
                self.labelingDrawerUi.exportAllMeshesButton.clicked.connect(self._exportAllObjectMeshes)
            else:
                self.labelingDrawerUi.exportAllMeshesButton.setEnabled(False)
                self.labelingDrawerUi.exportAllMeshesButton.setToolTip("Not available for 2D images")

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

            mgr.register(
                shortcut,
                ActionInfo(
                    "Carving",
                    "Toggle layer %s" % layername,
                    "Toggle layer %s" % layername,
                    toggle,
                    self.viewerControlWidget(),
                    None,
                ),
            )

        # TODO
        addLayerToggleShortcut("Completed segments (unicolor)", "d")
        addLayerToggleShortcut("Segmentation", "s")
        addLayerToggleShortcut("Input Data", "r")

        def makeColortable():
            self._doneSegmentationColortable = [QColor(0, 0, 0, 0).rgba()]
            for i in range(254):
                r, g, b = numpy.random.randint(0, 255), numpy.random.randint(0, 255), numpy.random.randint(0, 255)
                # ensure colors have sufficient distance to pure red and pure green
                while (255 - r) + g + b < 128 or r + (255 - g) + b < 128:
                    r, g, b = numpy.random.randint(0, 255), numpy.random.randint(0, 255), numpy.random.randint(0, 255)
                self._doneSegmentationColortable.append(QColor(r, g, b).rgba())
            self._doneSegmentationColortable.append(QColor(0, 255, 0).rgba())

        makeColortable()
        self._updateGui()

    @property
    def objectPrefix(self):
        return self.topLevelOperatorView.ObjectPrefix.value

    def setObjectPrefix(self, value):
        self.topLevelOperatorView.ObjectPrefix.setValue(value)

    def _is_3d(self):
        tagged_shape = defaultdict(lambda: 1)
        tagged_shape.update(self.topLevelOperatorView.InputData.meta.getTaggedShape())
        is_3d = tagged_shape["x"] > 1 and tagged_shape["y"] > 1 and tagged_shape["z"] > 1
        return is_3d

    def _after_init(self):
        super(CarvingGui, self)._after_init()
        if self.render:
            self._toggleSegmentation3D()

    def _updateGui(self):
        self.labelingDrawerUi.save.setEnabled(self.topLevelOperatorView.CanObjectBeSaved.value)

    def onSegmentButton(self):
        logger.debug("segment button clicked")
        if not self.topLevelOperatorView.CanRunSegmentation.value:
            QMessageBox.critical(
                self,
                "Unable to Run Segmentation",
                "Both foreground and background labels are required to run segmentation.",
            )
            return
        bkPriorityValue = self.labelingDrawerUi.backgroundPrioritySpin.value()
        self.topLevelOperatorView.BackgroundPriority.setValue(bkPriorityValue)
        biasValue = self.labelingDrawerUi.noBiasBelowSpin.value()
        self.topLevelOperatorView.NoBiasBelow.setValue(biasValue)
        self.topLevelOperatorView.Trigger.setDirty(slice(None))

    def getObjectNames(self):
        return self.topLevelOperatorView.AllObjectNames[:].wait()

    def generateObjectName(self):
        names = self.getObjectNames()
        highest_existing_suffix = 0

        for n in names:
            match = re.match(rf"^{self.objectPrefix}(?P<suffix>\d+)", n)
            if match:
                val = int(match.group("suffix"))
                if val > highest_existing_suffix:
                    highest_existing_suffix = val

        return f"{self.objectPrefix}{highest_existing_suffix + 1}"

    def saveAsDialog(self, name_input_default: str, existing_names: List[str]):
        dialog = uic.loadUi(self.dialogdirSAD)
        dialog.lineEdit.setText(name_input_default)
        dialog.lineEdit.selectAll()
        dialog.warning.setVisible(False)
        dialog.Ok.clicked.connect(dialog.accept)
        dialog.Cancel.clicked.connect(dialog.reject)

        def validate():
            name = dialog.lineEdit.text().strip()
            if name in existing_names and name != name_input_default:
                dialog.Ok.setEnabled(False)
                dialog.warning.setVisible(True)
            elif name:
                dialog.Ok.setEnabled(True)
                dialog.warning.setVisible(False)
            else:
                dialog.Ok.setEnabled(False)

        validate()
        dialog.lineEdit.textChanged.connect(validate)
        result = dialog.exec_()
        if result:
            return str(dialog.lineEdit.text().strip())

    def onSaveButton(self):
        logger.info("save object as?")
        if not self.topLevelOperatorView.CanObjectBeSaved.value:
            QMessageBox.warning(self, "Problem with Data", "The data does not seem fit to be stored.")
            logger.error("object not saved due to faulty data.")
            return

        old_name = self.topLevelOperatorView.CurrentObjectName.value
        saved_object_names = self.getObjectNames()
        was_object_previously_saved = old_name in saved_object_names

        new_name = self.saveAsDialog(old_name or self.generateObjectName(), saved_object_names)
        if new_name is None:
            return

        is_name_changed = new_name != old_name
        if is_name_changed and new_name in saved_object_names:
            QMessageBox.critical(
                self,
                "Unable to Save Object",
                f"<p>An object with name {new_name!r} already exists.</p><p>Please choose a different name.</p>",
            )
            return

        self.topLevelOperatorView.saveObjectAs(new_name)

        if was_object_previously_saved:
            if is_name_changed:
                self.topLevelOperatorView.deleteObject(old_name)
            else:
                self._renderMgr.removeObject(old_name)
                self._renderMgr.invalidateObject(old_name)
                self._shownObjects3D.pop(old_name, None)

    def onShowObjectNames(self):
        """show object names and allow user to load/delete them"""
        dialog = uic.loadUi(self.dialogdirCOM)
        names = self.getObjectNames()
        dialog.objectNames.addItems(human_sorted(names))

        def loadSelection():
            selected = dialog.objectNames.selectedItems()
            if len(selected) != 1:
                return
            name = selected[0].text()
            dialog.close()
            if self.confirmLoadObject():
                self.topLevelOperatorView.loadObject(name)

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

    def confirmLoadObject(self) -> bool:
        if self.topLevelOperatorView.has_seeds:
            response = QMessageBox.warning(
                self,
                "Discard Unsaved Data?",
                "Loading an object will discard unsaved work. Proceed?",
                buttons=QMessageBox.Yes | QMessageBox.Cancel,
                defaultButton=QMessageBox.Yes,
            )
            if response == QMessageBox.Cancel:
                return False

        return True

    def confirmAndDelete(self, namelist):
        logger.info("confirmAndDelete: {}".format(namelist))
        objectlist = "".join("\n  " + str(i) for i in namelist)
        confirmed = QMessageBox.question(
            self,
            "Delete Object",
            "Do you want to delete these objects?" + objectlist,
            QMessageBox.Yes | QMessageBox.Cancel,
            defaultButton=QMessageBox.Yes,
        )

        if confirmed == QMessageBox.Yes:
            for name in namelist:
                self.topLevelOperatorView.deleteObject(name)
            return True
        return False

    def labelingContextMenu(self, names, op, position5d):
        menu = QMenu(self)
        menu.setObjectName("carving_context_menu")
        posItem = menu.addAction("position %d %d %d" % (position5d[1], position5d[2], position5d[3]))
        posItem.setEnabled(False)
        menu.addSeparator()
        for name in names:
            submenu = QMenu(name, menu)

            # Load
            def onLoadAction(_name):
                if self.confirmLoadObject():
                    op.loadObject(_name)

            loadAction = submenu.addAction(f"Load {name}")
            loadAction.triggered.connect(partial(onLoadAction, name))

            # Delete
            def onDelAction(_name):
                self.confirmAndDelete([_name])
                if self.render and self._renderMgr.ready:
                    self._update_rendering()

            delAction = submenu.addAction(f"Delete {name}")
            delAction.triggered.connect(partial(onDelAction, name))

            if self.render:
                if name in self._shownObjects3D:
                    # Remove
                    def onRemove3D(_name):
                        label = self._shownObjects3D.pop(_name)
                        self._renderMgr.removeObject(label)
                        self._update_rendering()

                    removeAction = submenu.addAction("Remove %s from 3D view" % name)
                    removeAction.triggered.connect(partial(onRemove3D, name))
                else:
                    # Show
                    def onShow3D(_name):
                        label = self._renderMgr.addObject()
                        self._shownObjects3D[_name] = label
                        self._update_rendering()

                    showAction = submenu.addAction("Show 3D %s" % name)
                    showAction.triggered.connect(partial(onShow3D, name))

            # Export mesh (only works for 3D. Do not offer for 2D until we have a workaround)
            input_data_shape = op.InputData.meta.getTaggedShape()
            if "z" in input_data_shape and input_data_shape["z"] > 1:
                exportAction = submenu.addAction(f"Export mesh for {name}")
                exportAction.triggered.connect(partial(self._onContextMenuExportMesh, name))
            else:
                exportAction = submenu.addAction("(Mesh export not available for 2D)")
                exportAction.setEnabled(False)

            menu.addMenu(submenu)

        if names:
            menu.addSeparator()

        menu.addSeparator()
        if self.render:
            showSeg3DAction = menu.addAction("Show Editing Segmentation in 3D")
            showSeg3DAction.setCheckable(True)
            showSeg3DAction.setChecked(self._showSegmentationIn3D)
            showSeg3DAction.triggered.connect(self._toggleSegmentation3D)

        if op.CanObjectBeSaved.value:
            menu.addAction("Save object").triggered.connect(self.onSaveButton)
        menu.addAction("Browse objects").triggered.connect(self.onShowObjectNames)
        menu.addAction("Segment").triggered.connect(self.onSegmentButton)
        menu.addAction("Clear").triggered.connect(self._onClearAction)
        return menu

    def _onClearAction(self):
        confirm = QMessageBox.warning(
            self, "Really Clear?", "Clear all brushtrokes and start new object?", QMessageBox.Ok | QMessageBox.Cancel
        )
        if confirm == QMessageBox.Ok:
            self.topLevelOperatorView.clearCurrentLabelsAndObject()

    def _clearLabelListGui(self):
        # Remove rows until we have the right number
        while self._labelControlUi.labelListModel.rowCount() > 2:
            self._removeLastLabel()

    def _onContextMenuExportMesh(self, _name):
        """
        Export a single object mesh to a user-specified filename.
        """
        recent_dir = preferences.get("carving", "recent export mesh directory")
        if recent_dir is None:
            defaultPath = os.path.join(os.path.expanduser("~"), "{}obj".format(_name))
        else:
            defaultPath = os.path.join(recent_dir, "{}.obj".format(_name))
        filepath, _filter = QFileDialog.getSaveFileName(
            self, "Save meshes for object '{}'".format(_name), defaultPath, "OBJ Files (*.obj)"
        )
        if not filepath:
            return
        obj_filepath = str(filepath)
        preferences.set("carving", "recent export mesh directory", os.path.split(obj_filepath)[0])

        self._exportMeshes([_name], [obj_filepath])

    def _exportAllObjectMeshes(self):
        """
        Export all objects in the project as separate .obj files, stored to a user-specified directory.
        """
        mst = self.topLevelOperatorView.MST.value
        if not list(mst.object_lut.keys()):
            QMessageBox.critical(self, "Can't Export", "You have no saved objects, so there are no meshes to export.")
            return

        recent_dir = preferences.get("carving", "recent export mesh directory")
        if recent_dir is None:
            defaultPath = os.path.join(os.path.expanduser("~"))
        else:
            defaultPath = os.path.join(recent_dir)
        export_dir = QFileDialog.getExistingDirectory(self, "Select export directory for mesh files", defaultPath)
        if not export_dir:
            return
        export_dir = str(export_dir)
        preferences.set("carving", "recent export mesh directory", export_dir)

        # Get the list of all object names
        object_names = []
        obj_filepaths = []
        for object_name in list(mst.object_lut.keys()):
            object_names.append(object_name)
            obj_filepaths.append(os.path.join(export_dir, "{}.obj".format(object_name)))

        if object_names:
            self._exportMeshes(object_names, obj_filepaths)

    def _exportMeshes(self, object_names: List[str], obj_filepaths: List[str]) -> Request:
        """Save objects in the mst to .obj files

        Args:
            object_names: Names of the objects in the mst
            obj_filepaths: One path for each object in object_names

        Returns:
            Returns the request object, used in testing
        """

        def get_label_volume_from_mst(mst, object_name):
            object_supervoxels = mst.object_lut[object_name]
            object_lut = numpy.zeros(mst.nodeNum + 1, dtype=numpy.int32)
            object_lut[object_supervoxels] = 1
            supervoxel_volume = mst.supervoxelUint32
            object_volume = object_lut[supervoxel_volume]
            return object_volume

        mst = self.topLevelOperatorView.MST.value

        def exportMeshes(object_names, obj_filepaths):
            n_objects = len(object_names)
            progress_update = 100 / n_objects
            try:
                for obj, obj_path, obj_n in zip(object_names, obj_filepaths, range(n_objects)):
                    object_volume = get_label_volume_from_mst(mst, obj)
                    unique_ids = len(numpy.unique(object_volume))

                    if unique_ids <= 1:
                        logger.info(f"No voxels found for {obj}, skipping")
                        continue
                    elif unique_ids > 2:
                        logger.info(f"Supervoxel segmentation not unique for {obj}, skipping, got {unique_ids}")
                        continue

                    logger.info(f"Generating mesh for {obj}")
                    _, mesh_data = list(labeling_to_mesh(object_volume, [1]))[0]
                    self.parentApplet.progressSignal(int((obj_n + 0.5) * progress_update))
                    logger.info(f"Mesh generation for {obj} complete.")

                    logger.info(f"Saving mesh for {obj} to {obj_path}")
                    mesh_to_obj(mesh_data, obj_path, obj)
                    self.parentApplet.progressSignal(int((obj_n + 1) * progress_update))
            finally:
                self.parentApplet.busy = False
                self.parentApplet.progressSignal(100)
                self.parentApplet.appletStateUpdateRequested()

        self.parentApplet.busy = True
        self.parentApplet.progressSignal(-1)
        self.parentApplet.appletStateUpdateRequested()

        req = Request(partial(exportMeshes, object_names, obj_filepaths))
        req.submit()
        return req

    def handleEditorRightClick(self, position5d, globalWindowCoordinate):
        names = self.topLevelOperatorView.doneObjectNamesForPosition(position5d[1:4])
        op = self.topLevelOperatorView

        # (Subclasses may override menu)
        menu = self.labelingContextMenu(names, op, position5d)
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
        self._shownObjects3D = dict(
            (k, v) for k, v in self._shownObjects3D.items() if k in list(op.MST.value.object_lut.keys())
        )

        lut = numpy.zeros(op.MST.value.nodeNum + 1, dtype=numpy.int32)
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
            lut[:] = numpy.where(op.MST.value.getSuperVoxelSeg() == 2, self._segmentation_3d_label, lut)

        self._renderMgr.volume = lut[op.MST.value.supervoxelUint32], label_name_map  # (Advanced indexing)
        self._update_colors()
        self._renderMgr.update()

    def _update_colors(self):
        """Update colors of objects in 3D viewport"""
        op = self.topLevelOperatorView
        if not self._shownObjects3D.items():
            return
        ctable = self._doneSegmentationLayer.colorTable

        for name, label in self._shownObjects3D.items():
            color = QColor(ctable[op.MST.value.object_names[name]])
            color = (color.red() / 255, color.green() / 255, color.blue() / 255)
            self._renderMgr.setColor(label, color)

        if self._showSegmentationIn3D and self._segmentation_3d_label is not None:
            # color of the foreground label from label list data
            labels = self.labelListData
            assert len(labels) == 2
            fg_label = labels[1]
            color = fg_label.pmapColor()  # 2 is the foreground index
            self._renderMgr.setColor(
                self._segmentation_3d_label, (color.red() / 255, color.green() / 255, color.blue() / 255)
            )

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
        return self._getNext(self.topLevelOperatorView.LabelNames, super(CarvingGui, self).getNextLabelName)

    def appletDrawers(self):
        return [("Carving", self._labelControlUi)]

    def setupLayers(self):
        logger.debug("setupLayers")

        layers = []

        def onButtonsEnabled(slot, roi):
            currObj = self.topLevelOperatorView.CurrentObjectName.value
            canSave = bool(self.topLevelOperatorView.CanObjectBeSaved.value)
            label = currObj if currObj else DEFAULT_OBJECT_NAME

            self.labelingDrawerUi.currentObjectLabel.setText(label)
            self.labelingDrawerUi.save.setEnabled(canSave)

        self.topLevelOperatorView.CurrentObjectName.notifyDirty(onButtonsEnabled)
        self.topLevelOperatorView.CanObjectBeSaved.notifyDirty(onButtonsEnabled)
        self.topLevelOperatorView.opLabelArray.NonzeroBlocks.notifyDirty(onButtonsEnabled)

        # Labels
        labellayer, labelsrc = self.createLabelLayer(direct=True)
        if labellayer is not None:
            labellayer._allowToggleVisible = False
            layers.append(labellayer)
            # Tell the editor where to draw label data
            self.editor.setLabelSink(labelsrc)

        # uncertainty
        # if self._showUncertaintyLayer:
        #    uncert = self.topLevelOperatorView.Uncertainty
        #    if uncert.ready():
        #        colortable = []
        #        for i in range(256-len(colortable)):
        #            r,g,b,a = i,0,0,i
        #            colortable.append(QColor(r,g,b,a).rgba())
        #        layer = ColortableLayer(createDataSource(uncert), colortable, direct=True)
        #        layer.name = "Uncertainty"
        #        layer.visible = True
        #        layer.opacity = 0.3
        #        layers.append(layer)

        # segmentation
        seg = self.topLevelOperatorView.Segmentation

        # seg = self.topLevelOperatorView.MST.value.segmentation
        # temp = self._done_lut[self.MST.value.supervoxelUint32[sl[1:4]]]
        if seg.ready():
            # source = RelabelingArraySource(seg)
            # source.setRelabeling(numpy.arange(256, dtype=numpy.uint8))

            # assign to the object label color, 0 is transparent, 1 is background
            colortable = [QColor(0, 0, 0, 0).rgba(), QColor(0, 0, 0, 0).rgba(), labellayer._colorTable[2]]
            for i in range(256 - len(colortable)):
                r, g, b = numpy.random.randint(0, 255), numpy.random.randint(0, 255), numpy.random.randint(0, 255)
                colortable.append(QColor(r, g, b).rgba())

            layer = ColortableLayer(createDataSource(seg), colortable, direct=True)
            layer.name = "Segmentation"
            layer.setToolTip(
                "This layer displays the <i>current</i> segmentation. Simply add foreground and background "
                "labels, then press <i>Segment</i>."
            )
            layer.visible = True
            layer.opacity = 0.3
            layers.append(layer)

        # done
        doneSeg = self.topLevelOperatorView.DoneSegmentation
        if doneSeg.ready():
            # FIXME: if the user segments more than 255 objects, those with indices that divide by 255 will be shown as transparent
            # both here and in the _doneSegmentationColortable
            colortable = 254 * [QColor(230, 25, 75).rgba()]
            colortable.insert(0, QColor(0, 0, 0, 0).rgba())

            # have to use lazyflow because it provides dirty signals
            layer = ColortableLayer(createDataSource(doneSeg), colortable, direct=True)
            layer.name = "Completed segments (unicolor)"
            layer.setToolTip(
                "In order to keep track of which objects you have already completed, this layer "
                "shows <b>all completed object</b> in one color (<b>blue</b>). "
                "The reason for only one color is that for finding out which "
                "objects to label next, the identity of already completed objects is unimportant "
                "and destracting."
            )
            layer.visible = False
            layer.opacity = 0.5
            layers.append(layer)

            layer = ColortableLayer(createDataSource(doneSeg), self._doneSegmentationColortable, direct=True)
            layer.name = "Completed segments (one color per object)"
            layer.setToolTip(
                "<html>In order to keep track of which objects you have already completed, this layer "
                "shows <b>all completed object</b>, each with a random color.</html>"
            )
            layer.visible = False
            layer.opacity = 0.5
            layer.colortableIsRandom = True
            self._doneSegmentationLayer = layer
            layers.append(layer)

        # supervoxel
        sv = self.topLevelOperatorView.Supervoxels
        if sv.ready():
            colortable = []
            for i in range(256):
                r, g, b = numpy.random.randint(0, 255), numpy.random.randint(0, 255), numpy.random.randint(0, 255)
                colortable.append(QColor(r, g, b).rgba())
            layer = ColortableLayer(createDataSource(sv), colortable, direct=True)
            layer.name = "Supervoxels"
            layer.setToolTip(
                "<html>This layer shows the partitioning of the input image into <b>supervoxels</b>. The carving "
                "algorithm uses these tiny puzzle-piceces to piece together the segmentation of an "
                "object. Sometimes, supervoxels are too large and straddle two distinct objects "
                "(undersegmentation). In this case, it will be impossible to achieve the desired "
                "segmentation. This layer helps you to understand these cases.</html>"
            )
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
            layer.name = "Overlay"
            layer.opacity = 1.0
            # if the flag window_leveling is set the contrast
            # of the layer is adjustable
            layer.window_leveling = True
            self.labelingDrawerUi.thresToolButton.show()
            layers.append(layer)
            del layer

        inputSlot = self.topLevelOperatorView.InputData
        if inputSlot.ready():
            layer = GrayscaleLayer(createDataSource(inputSlot), direct=True)
            layer.name = "Input Data"
            layer.setToolTip("<html>The data originally loaded into ilastik (unprocessed).</html>")
            # layer.visible = not rawSlot.ready()
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
            layer = GrayscaleLayer(createDataSource(filteredSlot))
            layer.name = "Filtered Input"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)

        return layers


def human_sorted(items):
    """
    If there is a trailing number, sort it numerically and not alphabetically.
    Sort those without trailing number ("c") before those with ("c0").
    >>> lst = ['3', 'c0', 'c', 'a 1', 'b 2', 'a 10', 'a 9']
    >>> sorted(lst)
    ['3', 'a 1', 'a 10', 'a 9', 'b 2', 'c', 'c0']
    >>> human_sorted(lst)
    ['3', 'a 1', 'a 9', 'a 10', 'b 2', 'c', 'c0']
    """
    keys = {}
    for item in items:
        prefix = item.rstrip(string.digits)
        trailing_digits = item[len(prefix) :]
        keys[item] = prefix, len(trailing_digits), trailing_digits
    return sorted(items, key=keys.__getitem__)
