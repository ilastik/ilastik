import os
import numpy
from functools import partial

from PyQt4 import uic
from PyQt4.QtGui import QColor, QFileDialog, QShortcut, QKeySequence

from volumina.pixelpipeline.datasources import LazyflowSource, ArraySource
from volumina.layer import ColortableLayer, GrayscaleLayer

from ilastik.utility import bind
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.applets.splitBodyCarving.bodySplitInfoWidget import BodySplitInfoWidget

class SplitBodyPostprocessingGui(LayerViewerGui):
    
    firstFragmentColors = [ QColor(0,0,0,0), # transparent (background)
                   QColor(0, 255, 255),   # cyan
                   QColor(255, 0, 255),   # magenta
                   QColor(0, 0, 128),     # navy
                   QColor(165,  42,  42), # brown        
                   QColor(255, 105, 180), # hot pink
                   QColor(255, 165, 0),   # orange
                   QColor(173, 255,  47), # green-yellow
                   QColor(102, 205, 170), # dark aquamarine
                   QColor(128,0, 128),    # purple
                   QColor(240, 230, 140), # khaki
                   QColor(192, 192, 192), # silver
                   QColor(69, 69, 69) ]   # dark grey

    _fragmentColors = []
    for i in range(254):
        r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
        _fragmentColors.append(QColor(r,g,b))
    _fragmentColors[0:len(firstFragmentColors)] = firstFragmentColors

    def __init__(self, topLevelOperatorView):
        super( SplitBodyPostprocessingGui, self ).__init__( topLevelOperatorView )
        
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        self._drawer.exportButton.clicked.connect( self.exportFinalSegmentation )

        # This comes from the upstream applet gui
        self.topLevelOperatorView.NavigationCoordinates.notifyDirty( bind(self._handleNavigationRequest) )
    
    def _handleNavigationRequest(self):
        coord3d = self.topLevelOperatorView.NavigationCoordinates.value
        self.editor.posModel.cursorPos = list(coord3d)
        self.editor.posModel.slicingPos = list(coord3d)
        self.editor.navCtrl.panSlicingViews( list(coord3d), [0,1,2] )
        
    def exportFinalSegmentation(self):
        # Ask for the export path
        exportPath = QFileDialog.getSaveFileName( self,
                                                  "Save final segmentation",
                                                  "",
                                                  "Hdf5 Files (*.h5 *.hdf5)",
                                                  options=QFileDialog.Options(QFileDialog.DontUseNativeDialog) )
        if exportPath.isNull():
            return

        def handleProgress(progress):
            # TODO: Hook this up to the progress bar
            print "Export progress: {}%".format( progress )

        op = self.topLevelOperatorView
        req = op.exportFinalSegmentation( str(exportPath), 
                                          "zyx",
                                          handleProgress )
        self._drawer.exportButton.setEnabled(False)
        def handleFinish(*args):
            self._drawer.exportButton.setEnabled(True)
        req.notify_finished( handleFinish )
        req.notify_failed( handleFinish )

        # TODO: Allow cancellation?
        # req.notify_cancelled( bind( self._drawer.exportButton.setEnabled, True ) )
        # self.cancelButton.clicked.connect( req.cancel )

    def setupLayers(self):
        layers = []
        
        op = self.topLevelOperatorView
        
        ravelerLabelsSlot = op.RavelerLabels
        if ravelerLabelsSlot.ready():
            colortable = []
            for _ in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            ravelerLabelLayer = ColortableLayer(LazyflowSource(ravelerLabelsSlot), colortable, direct=True)
            ravelerLabelLayer.name = "Raveler Labels"
            ravelerLabelLayer.visible = False
            ravelerLabelLayer.opacity = 0.4
            layers.append(ravelerLabelLayer)

        def addFragmentSegmentationLayers(mslot, name):
            if mslot.ready():
                for index, slot in enumerate(mslot):
                    if slot.ready():
                        raveler_label = slot.meta.selected_label
                        colortable = map(QColor.rgba, self._fragmentColors)
                        fragSegLayer = ColortableLayer(LazyflowSource(slot), colortable, direct=True)
                        fragSegLayer.name = "{} #{} ({})".format( name, index, raveler_label )
                        fragSegLayer.visible = False
                        fragSegLayer.opacity = 1.0
                        layers.append(fragSegLayer)

        addFragmentSegmentationLayers( op.FragmentedBodies, "Saved Fragments" )
        addFragmentSegmentationLayers( op.RelabeledFragments, "Relabeled Fragments" )
        addFragmentSegmentationLayers( op.FilteredFragmentedBodies, "CC-Filtered Fragments" )
        addFragmentSegmentationLayers( op.WatershedFilledBodies, "Watershed-filled Fragments" )

        mslot = op.EditedRavelerBodies
        for index, slot in enumerate(mslot):
            if slot.ready():
                raveler_label = slot.meta.selected_label
                # 0=Black, 1=Transparent
                colortable = [QColor(0, 0, 0).rgba(), QColor(0, 0, 0, 0).rgba()]
                bodyMaskLayer = ColortableLayer(LazyflowSource(slot), colortable, direct=True)
                bodyMaskLayer.name = "Raveler Body Mask #{} ({})".format( index, raveler_label )
                bodyMaskLayer.visible = False
                bodyMaskLayer.opacity = 1.0
                layers.append(bodyMaskLayer)

        finalSegSlot = op.FinalSegmentation
        if finalSegSlot.ready():
            colortable = []
            for _ in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            finalLayer = ColortableLayer(LazyflowSource(finalSegSlot), colortable, direct=True)
            finalLayer.name = "Final Segmentation"
            finalLayer.visible = False
            finalLayer.opacity = 0.4
            layers.append(finalLayer)

        inputSlot = op.InputData
        if inputSlot.ready():
            layer = GrayscaleLayer( LazyflowSource(inputSlot) )
            layer.name = "WS Input"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)

        #raw data
        rawSlot = self.topLevelOperatorView.RawData
        rawLayer = None
        if rawSlot.ready():
            raw5D = self.topLevelOperatorView.RawData.value
            rawLayer = GrayscaleLayer(ArraySource(raw5D), direct=True)
            #rawLayer = GrayscaleLayer( LazyflowSource(rawSlot) )
            rawLayer.name = "raw"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            rawLayer.shortcutRegistration = ( "Postprocessing",
                                              "Raw Data to Top",
                                              QShortcut( QKeySequence("g"),
                                                         self.viewerControlWidget(),
                                                         partial(self._toggleRawDataPosition, rawLayer) ),
                                             rawLayer )
            layers.append(rawLayer)

        return layers

    def _toggleRawDataPosition(self, rawLayer):
        index = self.layerstack.layerIndex(rawLayer)
        self.layerstack.selectRow( index )
        if index == 0:
            self.layerstack.moveSelectedToBottom()
        else:
            # Move it to the top
            self.layerstack.moveSelectedToRow(0)
            














