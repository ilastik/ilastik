from functools import partial
import logging
import os

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QIcon

from ilastik.applets.labeling.labelingGui import LabelingGui
from ilastik.applets.pixelClassification import pixelClassificationGui
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.utility import bind

try:
    from volumina.view3d.volumeRendering import RenderingManager
except ImportError:
    logger.debug("Can't import volumina.view3d.volumeRendering.RenderingManager")


# Loggers
logger = logging.getLogger(__name__)

class VoxelSegmentationGui(pixelClassificationGui.PixelClassificationGui):
    def __init__(self, parentApplet, topLevelOperatorView, labelingDrawerUiPath=None):
        self.parentApplet = parentApplet
        # Tell our base class which slots to monitor
        labelSlots = LabelingGui.LabelingSlots()
        labelSlots.labelInput = topLevelOperatorView.LabelInputs
        labelSlots.labelOutput = topLevelOperatorView.LabelImages
        labelSlots.labelEraserValue = topLevelOperatorView.opLabelPipeline.opLabelArray.eraser
        labelSlots.labelDelete = topLevelOperatorView.opLabelPipeline.DeleteLabel
        labelSlots.labelNames = topLevelOperatorView.LabelNames

        self.__cleanup_fns = []

        # We provide our own UI file (which adds an extra control for interactive mode)
        if labelingDrawerUiPath is None:
            labelingDrawerUiPath = os.path.split(pixelClassificationGui.__file__)[0] + '/labelingDrawer.ui'

        # Base class init
        super(pixelClassificationGui.PixelClassificationGui, self).__init__( parentApplet, labelSlots, topLevelOperatorView, labelingDrawerUiPath)

        self.topLevelOperatorView = topLevelOperatorView

        self.interactiveModeActive = False
        # Immediately update our interactive state
        self.toggleInteractive( not self.topLevelOperatorView.FreezePredictions.value )

        self._currentlySavingPredictions = False

        self._showSegmentationIn3D = False

        self.labelingDrawerUi.labelListView.support_merges = True

        self.labelingDrawerUi.liveUpdateButton.setEnabled(False)
        self.labelingDrawerUi.liveUpdateButton.setIcon(QIcon(ilastikIcons.Play))
        self.labelingDrawerUi.liveUpdateButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.labelingDrawerUi.liveUpdateButton.toggled.connect(self.toggleInteractive)

        self.initFeatSelDlg()
        self.labelingDrawerUi.suggestFeaturesButton.clicked.connect(self.show_feature_selection_dialog)
        self.featSelDlg.accepted.connect(self.update_features_from_dialog)
        self.labelingDrawerUi.suggestFeaturesButton.setEnabled(False)

        self.topLevelOperatorView.LabelNames.notifyDirty( bind(self.handleLabelSelectionChange) )
        self.__cleanup_fns.append(partial(self.topLevelOperatorView.LabelNames.unregisterDirty, bind(self.handleLabelSelectionChange)))

        self._initShortcuts()

        self._bookmarks_window = pixelClassificationGui.BookmarksWindow(self, self.topLevelOperatorView)


        # FIXME: We MUST NOT enable the render manager by default,
        #        since it will drastically slow down the app for large volumes.
        #        For now, we leave it off by default.
        #        To re-enable rendering, we need to allow the user to render a segmentation
        #        and then initialize the render manager on-the-fly.
        #        (We might want to warn the user if her volume is not small.)
        self.render = True
        self._renderMgr = None
        self._renderedLayers = {} # (layer name, label number)

        # Always off for now (see note above)
        if self.render:
            # try:
            self._renderMgr = RenderingManager(self.editor.view3d)
            # except:
                # self.render = False

        # toggle interactive mode according to freezePredictions.value
        self.toggleInteractive(not self.topLevelOperatorView.FreezePredictions.value)
        def FreezePredDirty():
            self.toggleInteractive(not self.topLevelOperatorView.FreezePredictions.value)
        # listen to freezePrediction changes
        self.topLevelOperatorView.FreezePredictions.notifyDirty(bind(FreezePredDirty))
        self.__cleanup_fns.append(partial(self.topLevelOperatorView.FreezePredictions.unregisterDirty, bind(FreezePredDirty) ) )

    def menus(self):
        menus = super(VoxelSegmentationGui, self).menus()
        for menu in menus:
            if menu.title == "Advanced":
                if self.render:
                    showSeg3DAction = menu.addAction( "Show Supervoxel Segmentation in 3D" )
                    showSeg3DAction.setCheckable(True)
                    showSeg3DAction.setChecked( self._showSegmentationIn3D )
                    showSeg3DAction.triggered.connect( self._toggleSegmentation3D )
        
        return menus


    def _toggleSegmentation3D(self):
        self._showSegmentationIn3D = not self._showSegmentationIn3D
        if self._showSegmentationIn3D:
            self._segmentation_3d_label = self._renderMgr.addObject()
        else:
            self._renderMgr.removeObject(self._segmentation_3d_label)
            self._segmentation_3d_label = None
        self._update_rendering()


    def stopAndCleanUp(self):
        for fn in self.__cleanup_fns:
            fn()

        # Base class
        super(pixelClassificationGui.PixelClassificationGui, self).stopAndCleanUp()

