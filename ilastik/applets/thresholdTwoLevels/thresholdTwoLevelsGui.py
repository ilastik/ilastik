import os
import logging
from functools import partial

from PyQt4 import uic
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QColor
from PyQt4.QtGui import QMessageBox

from volumina.api import LazyflowSource, AlphaModulatedLayer, ColortableLayer
from ilastik.applets.layerViewer import LayerViewerGui
from ilastik.utility import bind
from ilastik.utility.gui import threadRouted

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

class ThresholdTwoLevelsGui( LayerViewerGui ):
    
    def __init__(self, *args, **kwargs):
        super( self.__class__, self ).__init__(*args, **kwargs)
        self._channelColors = self._createDefault16ColorColorTable()
    
    def initAppletDrawerUi(self):
        """
        Reimplemented from LayerViewerGui base class.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        
        self._drawer.applyButton.clicked.connect( self._onApplyButtonClicked )
        self._drawer.tabWidget.currentChanged.connect( self._onTabCurrentChanged )

        self._sigmaSpinBoxes = { 'x' : self._drawer.sigmaSpinBox_X,
                                 'y' : self._drawer.sigmaSpinBox_Y,
                                 'z' : self._drawer.sigmaSpinBox_Z }

        self._allWatchedWidgets = self._sigmaSpinBoxes.values() + \
        [
            self._drawer.inputChannelSpinBox,
            self._drawer.lowThresholdSpinBox,
            self._drawer.highThresholdSpinBox,
            self._drawer.thresholdSpinBox,
            self._drawer.minSizeSpinBox,
            self._drawer.maxSizeSpinBox
        ]
        
        for widget in self._allWatchedWidgets:
            # If the user pressed enter inside a spinbox, auto-click "Apply"
            widget.installEventFilter( self )

        self._updateGuiFromOperator()
        self.topLevelOperatorView.InputImage.notifyReady( bind(self._updateGuiFromOperator) )
        self.topLevelOperatorView.InputImage.notifyMetaChanged( bind(self._updateGuiFromOperator) )
    
    @threadRouted
    def _updateGuiFromOperator(self):
        op = self.topLevelOperatorView

        numChannels = 0        
        if op.InputImage.ready():
            # Channel
            channelIndex = op.InputImage.meta.axistags.index('c')
            numChannels = op.InputImage.meta.shape[channelIndex]
        self._drawer.inputChannelSpinBox.setRange( 0, numChannels-1 )
        self._drawer.inputChannelSpinBox.setValue( op.Channel.value )

        # Sigmas
        sigmaDict = self.topLevelOperatorView.SmootherSigma.value
        for axiskey, spinBox in self._sigmaSpinBoxes.items():
            spinBox.setValue( sigmaDict[axiskey] )

        # Thresholds
        self._drawer.lowThresholdSpinBox.setValue( op.LowThreshold.value )
        self._drawer.highThresholdSpinBox.setValue( op.HighThreshold.value )
        self._drawer.thresholdSpinBox.setValue( op.SingleThreshold.value )

        # Size filters
        self._drawer.minSizeSpinBox.setValue( op.MinSize.value )
        self._drawer.maxSizeSpinBox.setValue( op.MaxSize.value )
        
        # Operator
        self._drawer.tabWidget.setCurrentIndex( op.CurOperator.value )
    
    def _updateOperatorFromGui(self):
        op = self.topLevelOperatorView

        # Read all gui settings before updating the operator
        # (The gui is still responding to operator changes, 
        #  and we don't want it to update until we've read all gui values.)
        
        # Read Channel
        channel = self._drawer.inputChannelSpinBox.value()
        
        # Read Sigmas
        sigmaSlot = self.topLevelOperatorView.SmootherSigma
        block_shape_dict = dict( sigmaSlot.value )
        block_shape_dict['x'] = self._sigmaSpinBoxes['x'].value()
        block_shape_dict['y'] = self._sigmaSpinBoxes['y'].value()
        block_shape_dict['z'] = self._sigmaSpinBoxes['z'].value()

        # Read Thresholds
        singleThreshold = self._drawer.thresholdSpinBox.value()
        lowThreshold = self._drawer.lowThresholdSpinBox.value()
        highThreshold = self._drawer.highThresholdSpinBox.value()
        
        if lowThreshold>highThreshold:
            mexBox=QMessageBox()
            mexBox.setText("Low threshold must be lower than high threshold ")
            mexBox.exec_()
            return
        
        # Read Size filters
        minSize = self._drawer.minSizeSpinBox.value()
        maxSize = self._drawer.maxSizeSpinBox.value()
        
        if minSize>=maxSize:
            mexBox=QMessageBox()
            mexBox.setText("Min size must be smaller than max size ")
            mexBox.exec_()
            return

        # Read the current thresholding method
        curIndex = self._drawer.tabWidget.currentIndex()
        #print "Setting operator to", curIndex+1, " thresholds"
        
        # Apply new settings to the operator
        op.CurOperator.setValue(curIndex)
        op.Channel.setValue( channel )
        sigmaSlot.setValue( block_shape_dict )
        op.SingleThreshold.setValue( singleThreshold )
        op.LowThreshold.setValue( lowThreshold )
        op.HighThreshold.setValue( highThreshold )
        op.MinSize.setValue( minSize )
        op.MaxSize.setValue( maxSize )
        

    def _onApplyButtonClicked(self):
        self._updateOperatorFromGui()
    
    def _onTabCurrentChanged(self, cur):
        self._updateOperatorFromGui()
        self.updateAllLayers()
        

    def eventFilter(self, watched, event):
        """
        If the user pressed 'enter' within a spinbox, auto-click the "apply" button.
        """
        if watched in self._allWatchedWidgets:
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Enter:
                self._drawer.applyButton.click()
                return True
        return False
    
    def setupLayers(self):
        layers = []        
        op = self.topLevelOperatorView
        binct = [QColor(Qt.black), QColor(Qt.white)]
        ct = self._createDefault16ColorColorTable()
        ct[0]=0
        # Show the cached output, since it goes through a blocked cache
        
        if op.CachedOutput.ready():
            outputSrc = LazyflowSource(op.CachedOutput)
            outputLayer = ColortableLayer(outputSrc, binct)
            outputLayer.name = "Output (Cached)"
            outputLayer.visible = False
            outputLayer.opacity = 1.0
            layers.append(outputLayer)

        #FIXME: We have to do that, because lazyflow doesn't have a way to make an operator partially ready
        curIndex = self._drawer.tabWidget.currentIndex()
        if curIndex==1:
            if op.BigRegions.ready():
                lowThresholdSrc = LazyflowSource(op.BigRegions)
                lowThresholdLayer = ColortableLayer(lowThresholdSrc, binct)
                lowThresholdLayer.name = "Big Regions"
                lowThresholdLayer.visible = False
                lowThresholdLayer.opacity = 1.0
                layers.append(lowThresholdLayer)
    
            if op.FilteredSmallLabels.ready():
                filteredSmallLabelsLayer = self.createStandardLayerFromSlot( op.FilteredSmallLabels )
                filteredSmallLabelsLayer.name = "Filtered Small Labels"
                filteredSmallLabelsLayer.visible = False
                filteredSmallLabelsLayer.opacity = 1.0
                layers.append(filteredSmallLabelsLayer)
    
            if op.SmallRegions.ready():
                highThresholdSrc = LazyflowSource(op.SmallRegions)
                highThresholdLayer = ColortableLayer(highThresholdSrc, binct)
                highThresholdLayer.name = "Small Regions"
                highThresholdLayer.visible = False
                highThresholdLayer.opacity = 1.0
                layers.append(highThresholdLayer)
        elif curIndex==0:
            if op.BeforeSizeFilter.ready():
                thSrc = LazyflowSource(op.BeforeSizeFilter)
                thLayer = ColortableLayer(thSrc, binct)
                thLayer.name = "Thresholded Labels"
                thLayer.visible = False
                thLayer.opacity = 1.0
                layers.append(thLayer)
        
        # Selected input channel, smoothed.
        if op.Smoothed.ready():
            smoothedLayer = self.createStandardLayerFromSlot( op.Smoothed )
            smoothedLayer.name = "Smoothed Input"
            smoothedLayer.visible = True
            smoothedLayer.opacity = 1.0
            layers.append(smoothedLayer)
        
        # Show the selected channel
        if op.InputChannel.ready():
            drange = op.InputChannel.meta.drange
            if drange is None:
                drange = (0.0, 1.0)
            channelSrc = LazyflowSource(op.InputChannel)
            channelLayer = AlphaModulatedLayer( channelSrc,
                                                tintColor=QColor(self._channelColors[op.Channel.value]),
                                                range=drange,
                                                normalize=drange )
            channelLayer.name = "Input Ch{}".format(op.Channel.value)
            channelLayer.opacity = 1.0
            #channelLayer.visible = channelIndex == op.Channel.value # By default, only the selected input channel is visible.    
            layers.append(channelLayer)
        
        # Show the raw input data
        rawSlot = self.topLevelOperatorView.RawInput
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append(rawLayer)

        return layers

    def _createDefault16ColorColorTable(self):
        colors = []

        # SKIP: Transparent for the zero label
        #colors.append(QColor(0,0,0,0))

        # ilastik v0.5 colors
        colors.append( QColor( Qt.red ) )
        colors.append( QColor( Qt.green ) )
        colors.append( QColor( Qt.yellow ) )
        colors.append( QColor( Qt.blue ) )
        colors.append( QColor( Qt.magenta ) )
        colors.append( QColor( Qt.darkYellow ) )
        colors.append( QColor( Qt.lightGray ) )

        # Additional colors
        colors.append( QColor(255, 105, 180) ) #hot pink
        colors.append( QColor(102, 205, 170) ) #dark aquamarine
        colors.append( QColor(165,  42,  42) ) #brown
        colors.append( QColor(0, 0, 128) )     #navy
        colors.append( QColor(255, 165, 0) )   #orange
        colors.append( QColor(173, 255,  47) ) #green-yellow
        colors.append( QColor(128,0, 128) )    #purple
        colors.append( QColor(240, 230, 140) ) #khaki

        colors.append( QColor(192, 192, 192) ) #silver

#        colors.append( QColor(69, 69, 69) )    # dark grey
#        colors.append( QColor( Qt.cyan ) )

        assert len(colors) == 16

        return [c.rgba() for c in colors]
