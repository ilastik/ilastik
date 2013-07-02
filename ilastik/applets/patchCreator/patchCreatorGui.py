from PyQt4.QtGui import QWidget, QVBoxLayout, QColor
from PyQt4 import uic
from volumina.api import ColortableLayer
from volumina.pixelpipeline.datasources import LazyflowSource

import os
import opGridCreator

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

from ilastik.utility import bind

class PatchCreatorGui(LayerViewerGui):

    # FIXME: put these in the operator, so skipping this gui does not
    # prevent downstream slots from becoming ready.
    default_patchWidth = 16
    default_patchHeight = 16
    default_patchOverlapVertical = 8
    default_patchOverlapHorizontal= 8
    default_gridStartVertical = 0
    default_gridStartHorizontal = 0
    default_gridWidth = 32
    default_gridHeight = 32

    def __init__(self, topLevelOperatorView):
        self.topLevelOperatorView = topLevelOperatorView
        super(PatchCreatorGui, self).__init__(topLevelOperatorView)

    def check_and_update(self):
        patchWidth = self._drawer.patchWidthSpinBox.value()
        patchHeight = self._drawer.patchHeightSpinBox.value()
        patchOverlapVertical = self._drawer.patchOverlapVerticalSpinBox.value()
        patchOverlapHorizontal = self._drawer.patchOverlapHorizontalSpinBox.value()
        gridStartVertical = self._drawer.gridStartVerticalSpinBox.value()
        gridStartHorizontal = self._drawer.gridStartHorizontalSpinBox.value()
        gridWidth = self._drawer.gridWidthSpinBox.value()
        gridHeight = self._drawer.gridHeightSpinBox.value()

        op = self.topLevelOperatorView
        shape_y, shape_x = op.RawInput.meta.shape[:2]

        valid = True

        # FIXME: do not override entire style sheet
        def check_value(widget, isValid):
            if isValid:
                widget.setStyleSheet("background-color: rgba(0, 0, 0, 0)")
            else:
                widget.setStyleSheet("background-color: rgba(255, 0, 0, 255)")
            return isValid

        valid &= check_value(self._drawer.gridStartVerticalSpinBox,
                             (0 <= gridStartVertical < shape_x and
                              gridStartVertical + gridHeight <= shape_x))

        valid &= check_value(self._drawer.gridStartHorizontalSpinBox,
                             (0 <= gridStartHorizontal < shape_y and
                              gridStartHorizontal + gridWidth <= shape_y))

        valid &= check_value(self._drawer.gridHeightSpinBox,
                             (0 < gridHeight <= shape_x and
                              gridStartVertical + gridHeight <= shape_x and
                              gridHeight >= patchHeight))

        valid &= check_value(self._drawer.gridWidthSpinBox,
                             (0 < gridWidth <= shape_y and
                              gridStartHorizontal + gridWidth <= shape_y and
                              gridWidth >= patchWidth))

        valid &= check_value(self._drawer.patchHeightSpinBox,
                             (patchHeight > 0 and
                              patchHeight <= min(gridHeight, shape_x - gridStartVertical)))

        valid &= check_value(self._drawer.patchWidthSpinBox,
                             (patchWidth > 0 and
                              patchWidth <= min(gridWidth, shape_y - gridStartHorizontal)))

        valid &= check_value(self._drawer.patchOverlapVerticalSpinBox,
                             0 <= patchOverlapVertical < patchHeight)

        valid &= check_value(self._drawer.patchOverlapHorizontalSpinBox,
                             0 <= patchOverlapHorizontal < patchWidth)

        if valid:
            # FIXME: prevent operator from executing or dirty signals
            # from propagating until all values have been set.
            # opDepatchImage is requesting NumPatches, which is
            # causing execution prematurely with bad values.
            op.PatchWidth.setValue(patchWidth)
            op.PatchHeight.setValue(patchHeight)
            op.PatchOverlapVertical.setValue(patchOverlapVertical)
            op.PatchOverlapHorizontal.setValue(patchOverlapHorizontal)
            op.GridStartVertical.setValue(gridStartVertical)
            op.GridStartHorizontal.setValue(gridStartHorizontal)
            op.GridWidth.setValue(gridWidth)
            op.GridHeight.setValue(gridHeight)


    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        op = self.topLevelOperatorView

        # If the user changes a setting the GUI, update the appropriate operator slot.
        self._drawer.patchWidthSpinBox.valueChanged.connect(self.check_and_update)
        self._drawer.patchHeightSpinBox.valueChanged.connect(self.check_and_update)
        self._drawer.patchOverlapVerticalSpinBox.valueChanged.connect(self.check_and_update)
        self._drawer.patchOverlapHorizontalSpinBox.valueChanged.connect(self.check_and_update)
        self._drawer.gridStartVerticalSpinBox.valueChanged.connect(self.check_and_update)
        self._drawer.gridStartHorizontalSpinBox.valueChanged.connect(self.check_and_update)
        self._drawer.gridWidthSpinBox.valueChanged.connect(self.check_and_update)
        self._drawer.gridHeightSpinBox.valueChanged.connect(self.check_and_update)

        def updateDrawerFromOperator():
            patchWidth = self.default_patchWidth
            patchHeight = self.default_patchHeight
            patchOverlapVertical = self.default_patchOverlapVertical
            patchOverlapHorizontal = self.default_patchOverlapHorizontal
            gridStartVertical = self.default_gridStartVertical
            gridStartHorizontal = self.default_gridStartHorizontal
            gridWidth = self.default_gridWidth
            gridHeight = self.default_gridHeight

            if op.PatchWidth.ready():
                patchWidth = op.PatchWidth.value

            if op.PatchHeight.ready():
                patchHeight = op.PatchHeight.value

            if op.PatchOverlapVertical.ready():
                patchOverlapVertical = op.PatchOverlapVertical.value

            if op.PatchOverlapHorizontal.ready():
                patchOverlapHorizontal = op.PatchOverlapHorizontal.value

            if op.GridStartVertical.ready():
                gridStartVertical = op.GridStartVertical.value

            if op.GridStartHorizontal.ready():
                gridStartHorizontal = op.GridStartHorizontal.value

            if op.GridWidth.ready():
                gridWidth = op.GridWidth.value
            else:
                if op.RawInput.ready():
                    gridWidth = op.RawInput.meta.shape[0] - gridStartHorizontal

            if op.GridHeight.ready():
                gridHeight = op.GridHeight.value
            else:
                if op.RawInput.ready():
                    gridHeight = op.RawInput.meta.shape[1] - gridStartVertical

            # set values in spinboxes
            self._drawer.patchWidthSpinBox.setValue(patchWidth)
            self._drawer.patchHeightSpinBox.setValue(patchHeight)
            self._drawer.patchOverlapVerticalSpinBox.setValue(patchOverlapVertical)
            self._drawer.patchOverlapHorizontalSpinBox.setValue(patchOverlapHorizontal)
            self._drawer.gridStartVerticalSpinBox.setValue(gridStartVertical)
            self._drawer.gridStartHorizontalSpinBox.setValue(gridStartHorizontal)
            self._drawer.gridWidthSpinBox.setValue(gridWidth)
            self._drawer.gridHeightSpinBox.setValue(gridHeight)


        # If the operator is changed, update the GUI to match the new
        # operator slot values.
        for slot in op.inputSlots:
            slot.notifyDirty(bind(updateDrawerFromOperator))

        # Initialize the GUI with the operator's initial state.
        updateDrawerFromOperator()

    def getAppletDrawerUi(self):
        return self._drawer

    def setupLayers(self):
        """The LayerViewer base class calls this function to obtain
        the list of layers that should be displaye in the central
        viewer.

        """
        layers = []

        inputGrid = LazyflowSource(self.topLevelOperatorView.GridOutput)
        colortable = [QColor(0, 0, 0, 0).rgba(), QColor(255, 0, 0).rgba(),]
        gridlayer = ColortableLayer(inputGrid, colortable)
        gridlayer.name = "Grid"
        gridlayer.zeroIsTransparent = True
        layers.insert(0, gridlayer)

        # Show the raw input data as a convenience for the user
        inputImageSlot = self.topLevelOperatorView.RawInput
        if inputImageSlot.ready():
            inputLayer = self.createStandardLayerFromSlot(inputImageSlot)
            inputLayer.name = "Raw Input"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

        return layers