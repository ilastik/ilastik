import os
import numpy

from PyQt4 import uic
from PyQt4.QtGui import QColor, QFileDialog

from volumina.pixelpipeline.datasources import LazyflowSource, ArraySource
from volumina.layer import ColortableLayer, GrayscaleLayer

from ilastik.utility import bind
from ilastik.applets.layerViewer import LayerViewerGui

class SplitBodySupervoxelExportGui(LayerViewerGui):

    def __init__(self, topLevelOperatorView):
        super( SplitBodySupervoxelExportGui, self ).__init__( topLevelOperatorView )

    def initAppletDrawerUi(self):
        """
        Overridden from LayerViewerGui
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        self._drawer.exportButton.clicked.connect( self.exportRelabeling )

    def exportRelabeling(self):
        # Ask for the export path
        exportPath = QFileDialog.getSaveFileName( self,
                                                  "Save supervoxel relabeling",
                                                  "",
                                                  "Hdf5 Files (*.h5 *.hdf5)",
                                                  options=QFileDialog.Options(QFileDialog.DontUseNativeDialog) )
        if exportPath.isNull():
            return

        def handleProgress(progress):
            # TODO: Hook this up to the progress bar
            print "Export progress: {}%".format( progress )

        op = self.topLevelOperatorView
        req = op.exportFinalSupervoxels( str(exportPath), 
                                          "zyx",
                                          handleProgress )
        self._drawer.exportButton.setEnabled(False)
        def handleFinish(*args):
            self._drawer.exportButton.setEnabled(True)
        req.notify_finished( handleFinish )
        req.notify_failed( handleFinish )
        
        
    
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

        supervoxelsSlot = op.Supervoxels
        if supervoxelsSlot.ready():
            colortable = []
            for i in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            supervoxelsLayer = ColortableLayer(LazyflowSource(supervoxelsSlot), colortable)
            supervoxelsLayer.name = "Input Supervoxels"
            supervoxelsLayer.visible = False
            supervoxelsLayer.opacity = 1.0
            layers.append(supervoxelsLayer)

        def addFragmentSegmentationLayers(mslot, name):
            if mslot.ready():
                for index, slot in enumerate(mslot):
                    if slot.ready():
                        raveler_label = slot.meta.selected_label
                        colortable = []
                        for i in range(256):
                            r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                            colortable.append(QColor(r,g,b).rgba())
                        colortable[0] = QColor(0,0,0,0).rgba()
                        fragSegLayer = ColortableLayer(LazyflowSource(slot), colortable, direct=True)
                        fragSegLayer.name = "{} #{} ({})".format( name, index, raveler_label )
                        fragSegLayer.visible = False
                        fragSegLayer.opacity = 1.0
                        layers.append(fragSegLayer)

        addFragmentSegmentationLayers( op.MaskedSupervoxels, "Masked Supervoxels" )
        addFragmentSegmentationLayers( op.FilteredMaskedSupervoxels, "Filtered Masked Supervoxels" )
        addFragmentSegmentationLayers( op.HoleFilledSupervoxels, "Hole Filled Supervoxels" )
        addFragmentSegmentationLayers( op.RelabeledSupervoxels, "Relabeled Supervoxels" )

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

        finalSegSlot = op.FinalSupervoxels
        if finalSegSlot.ready():
            colortable = []
            for _ in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            finalLayer = ColortableLayer(LazyflowSource(finalSegSlot), colortable)
            finalLayer.name = "Final Supervoxels"
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
        if rawSlot.ready():
            raw5D = self.topLevelOperatorView.RawData.value
            layer = GrayscaleLayer(ArraySource(raw5D), direct=True)
            #layer = GrayscaleLayer( LazyflowSource(rawSlot) )
            layer.name = "raw"
            layer.visible = True
            layer.opacity = 1.0
            layers.append(layer)

        return layers



