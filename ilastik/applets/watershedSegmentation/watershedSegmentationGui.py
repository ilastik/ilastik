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
#           http://ilastik.org/license.html
##############################################################################

#import numpy as np
from PyQt4.Qt import pyqtSlot, QMessageBox

from pixelValueDisplaying import PixelValueDisplaying 
#from importAndResetLabels import ImportAndResetLabels 
from ilastik.applets.watershedLabeling.watershedLabelingGui import WatershedLabelingGui

import logging
logger = logging.getLogger(__name__)



#from functools import partial
#from contextlib import contextmanager
#import threading
#import volumina.colortables as colortables
#import sip
#from ilastik.utility.gui import threadRouted
#from volumina.pixelpipeline.datasources import LazyflowSource, ArraySource
#from volumina.layer import GrayscaleLayer, ColortableLayer, generateRandomColors
#from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
#from lazyflow.request import Request
#from lazyflow.utility import TransposedView
#from lazyflow.operators import OpValueCache, OpTrainClassifierBlocked, OpClassifierPredict,\
                               #OpSlicedBlockedArrayCache, OpMultiArraySlicer2, \
                               #OpPixelOperator, OpMaxChannelIndicatorOperator, OpCompressedUserLabelArray, OpFeatureMatrixCache

#for the LabelPipeline
#from lazyflow.operators import OpCompressedUserLabelArray
#from PyQt4.QtCore import Qt
#from PyQt4.QtGui import QWidget, QLabel, QSpinBox, QDoubleSpinBox, QVBoxLayout, \
                        #QHBoxLayout, QSpacerItem, QSizePolicy, QColor, QPen, QComboBox, QPushButton, \
                        #QMessageBox
#from PyQt4.Qt import QCheckBox, QLineEdit, QButtonGroup, QRadioButton, pyqtSlot



#LayerViewerGui->LabelingGui->WatershedLabelingGui
class WatershedSegmentationGui(WatershedLabelingGui):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget( self ):
        return self
    

    '''
    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        # Base class
        super( WatershedSegmentationGui, self ).stopAndCleanUp()
    '''
    
    ###########################################
    ###########################################
    
    def __init__(self, parentApplet, topLevelOperatorView, watershedLabelingDrawerUiPath=None ):

        self.topLevelOperatorView = topLevelOperatorView
        op = self.topLevelOperatorView 

        #operator._value =  np.zeros(op.Boundaries.meta.shape)

        ############################################################
        # BEGIN TODO
        ############################################################
        ############################################################
        # END TODO
        ############################################################




        ############################################################
        # for the Labels
        ############################################################
        self._LabelPipeline         = op.opWSLP.opLabelPipeline

        #init the slots
        labelSlots                  = WatershedLabelingGui.LabelingSlots()
        labelSlots.labelInput       = op.CorrectedSeedsIn
        labelSlots.labelOutput      = op.CorrectedSeedsOut
        labelSlots.labelEraserValue = self._LabelPipeline.opLabelArray.eraser
        labelSlots.labelDelete      = self._LabelPipeline.DeleteLabel
        labelSlots.labelNames       = op.LabelNames


        '''
        import os
        # We provide our own UI file (which adds an extra control for interactive mode)
        if watershedLabelingDrawerUiPath is None:
            watershedLabelingDrawerUiPath = os.path.split(__file__)[0] + '/watershedLabelingDrawer.ui'
        '''

        super(WatershedSegmentationGui, self).__init__( parentApplet, \
                labelSlots, topLevelOperatorView, watershedLabelingDrawerUiPath )



        # resetSeedsPushButton functionality added by connecting signal with slot
        self._labelControlUi.resetSeedsPushButton.clicked.connect(self.onResetSeedsPushButton)


        # set the functionality of the pixelValue in the gui
        self.pixelValueDisplaying = PixelValueDisplaying (
                op.CorrectedSeedsOut,  
                self._labelControlUi.pixelValue,
                self._labelControlUi.pixelValueCheckBox,
                self.volumeEditorWidget.quadViewStatusBar,
                channel=0
                )
        self.pixelValueDisplaying.Label = "Show Corrected Seeds pixel value:"

        

        ############################################################
        # for the Watershed Algorithm
        ############################################################

        # responsable for the watershed algorithm
        self._labelControlUi.runWatershedPushButton.clicked.connect(self.onRunWatershedPushButtonClicked)

        # set the number of maximum labels
        self.setMaximumLabelNumber()

        # handle the init values and the sync with the operator
        self._initNeighborsComboBox()



        # notify any change to change settings in the gui
        op.SeedsExist   .notifyMetaChanged(self.onSeedsExistOrWSMethodChanged)
        op.WSMethod     .notifyMetaChanged(self.onSeedsExistOrWSMethodChanged)


        # TODO
        # value changed seems to be for cached stuff? 
        # well, it works on notifyMetaChanged. 
        #op.SeedsExist   .notifyValueChanged(self.onSeedsExistOrWSMethodChanged)
        #op.WSMethod     .notifyValueChanged(self.onSeedsExistOrWSMethodChanged)

        # TODO as workaround: on startup here
        print "init watershedSegmentationGui"
        op.resetLabelsToSlot()


    @pyqtSlot()
    def onResetSeedsPushButton(self):
        """
        import Labels from Slot which overrides the cache
        """
        from PyQt4.QtGui import QMessageBox
        #decision box with yes or no
        msgBox = QMessageBox()
        msgBox.setText('Are you sure to delete all progress in Corrected Seeds' 
                + ' and reset to Seeds?')
        msgBox.addButton(QMessageBox.Yes)
        msgBox.addButton(QMessageBox.No)
        #msgBox.addButton(QPushButton('Yes'), QMessageBox.YesRole)
        #msgBox.addButton(QPushButton('No'), QMessageBox.NoRole)
        #msgBox.addButton(QPushButton('Cancel'), QMessageBox.RejectRole)
        ret = msgBox.exec_()

        if (ret == QMessageBox.Yes):
            op = self.topLevelOperatorView
            op.resetLabelsToSlot()



    @pyqtSlot()
    def onRunWatershedPushButtonClicked(self):
        """
        Responsable to set the ShowWatershedLayer slot to True,
        so that a new Layer for the watershed results can be added.
        Executes the watershed algorithm

        """
        op = self.topLevelOperatorView

        # if no seeds but not UnionFind => not possible => ErrorMessage and return
        if not (op.WSMethod.value == "UnionFind") and not op.SeedsExist.value:
            self.show_error_message()
            return


        # show the watershedLayer after the first time and update the layers afterwards
        # updating concludes to calculation
        if not op.ShowWatershedLayer.value: 
            op.ShowWatershedLayer.setValue(True)

        #
        for layer in self.layerstack:
            if "Watershed" in layer.name:
                layer.visible = True

        self.updateAllLayers()
        # execute the watershed algorithm
        #self.topLevelOperatorView.opWSC.execWatershedAlgorithm()



    def show_error_message(self):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("No Seeds supplied and watershed not unseeded")
            #msg.setInformativeText("This is additional information")
            msg.setWindowTitle("Action invalid")
            msg.setStandardButtons(QMessageBox.Ok)
            #msg.buttonClicked.connect(msgbtn)
	
            retval = msg.exec_()





    ############################################################
    # Neighbors
    ############################################################

    def _initNeighborsComboBox(self):
        """
        Handle the init values and the sync with the operator.

        See opWatershedSegmentation for default value of WSNeighbors.
        """

        op = self.topLevelOperatorView 
        # add the options for the neighbors and set the default value
        self._labelControlUi.neighborsComboBox.addItems(["direct","indirect"])
        defaultIndex = self._labelControlUi.neighborsComboBox.findText(op.WSNeighbors.value)
        self._labelControlUi.neighborsComboBox.setCurrentIndex(defaultIndex)
        
        # connect the change event
        self._labelControlUi.neighborsComboBox.currentIndexChanged.connect(self.onNeighborsComboBoxCurrentIndexChanged)


    @pyqtSlot(int)
    def onNeighborsComboBoxCurrentIndexChanged(self, index):
        """
        Change the value of the operator WSNeighbor 
        when the user has changed the element of the combobox.

        :param index: index of the text selected in the combobox
        :type index: int
        """
        op = self.topLevelOperatorView 
        op.WSNeighbors.setValue( str(self._labelControlUi.neighborsComboBox.itemText(index)) )






    ############################################################
    # grayout gui or not (if seeds for watershed should be used or not)
    ############################################################

    def onSeedsExistOrWSMethodChanged(self, x):
        """
        use setGuiEnabledExceptWatershedButton to disable all elements not necessary for 
        following working steps
        """

        op = self.topLevelOperatorView

        # if no seeds or unionfind, then only "run watershed" button shall be accessable
        if (not op.SeedsExist.value) or (op.WSMethod.value == "UnionFind"):
            self.setGuiEnabledExceptWatershedButton(False)
        else:
            self.setGuiEnabledExceptWatershedButton(True)


    def setGuiEnabledExceptWatershedButton(self, enable):
        """
        enables or disables the watershed Gui 
        :param enable: True: enable; False: disable
        :type enable: bool
        """

        # disable all brush and erase elements except the navigation tool 
        for tool, button in self.toolButtons.items():
            toolId=0 #navigation
            if tool != toolId:
                button.setChecked(False)
                button.setEnabled(enable)
            else: 
                button.setChecked(True)

        #self._labelControlUi.runWatershedPushButton.setEnabled(enable)
        self._labelControlUi.brushSizeComboBox.setEnabled(enable)
        #self._labelControlUi.neighborsComboBox.setEnabled(enable)
        self._labelControlUi.resetSeedsPushButton.setEnabled(enable)
        self._labelControlUi.pixelValueCheckBox.setEnabled(enable)

        # if the maximum number of labels is reached, then you can't add a new label and 
        # the AddLabelButton is disabled in the updateLabelList and in changeInterActionMode in LabelingGui
        # if the number of max labels is 0, then you can't add any new labels and the button is disabled
        if enable:
            self.setMaximumLabelNumber()
        else:
            self.maxLabelNumber = 0



    #def initAppletDrawerUi(self):
        #super(WatershedSegmentationGui, self).initAppletDrawerUi()

    def setMaximumLabelNumber(self):
        """
        set the value of the eraser to 255 and afterwards set the 
        maximum number of labels to 254 (not with the setter, this gives an error, see code)
        """
        # set the eraser value to 255
        self.editor.brushingModel.erasingNumber = 255
        self._labelingSlots.labelEraserValue.setValue(self.editor.brushingModel.erasingNumber)

        # set the number of maximum labels to 254, one below the eraser value
        # caution: don't use the setter: self.maxLabelNumber, this leads to an error, where it wants to 
        # use the removeRow of the labelListModel with position -1, and that isn't possible
        self._maxLabelNumber         = 254


    ############################################################
    # setupLayers
    ############################################################

    def setupLayers(self):
        """
        For illustration of what a layer is, see: http://ilastik.org/documentation/basics/layers

        Responsable for the elements in the 'Viewer Controls'.

        These are the views (e.g. opacity of Raw Data)
        that can be adjusted in the left corner of the program
        and for the Elements, that can be seen in the 'Central Widget'. 
        These are excactly the ones, that are shown in the Viewer Controls.

        Uses :py:meth:`_initLayer` to create a single layer (see base-class LayerViewerGui)

        :returns: the list with the layers that are created in this function
        :rtype: list of layers

        """

        # Base class provides the label layer.
        # needed to add here. otherwise the reset button doesn't work well
        layers = super(WatershedSegmentationGui, self).setupLayers()
        #layers[0].visible = False
        # remove the Label-Layer, because it is not needed here
        layers = []

        op = self.topLevelOperatorView

        # handle the watershed output, 
        # changes in slot ready/unready of all slots lead to the execution of setupLayers
        # therefore a slot is used to not lose this layer (after restart as well, therefore slot)
        # use the cached version here
        if op.ShowWatershedLayer.value: 
            # WatershedCalculations
            self._initLayer(op.WSCCOCachedOutput,"Watershed Calculations", layers)

        if op.SeedsExist.value:
            # CorrectedSeedsOut
            self._initLayer(op.CorrectedSeedsOut,"Corrected Seeds", layers)

            # Seeds
            self._initLayer(op.Seeds,            "Seeds",        layers, visible=False)

        
        # Boundaries
        self._initLayer(op.Boundaries,       "Boundaries",   layers, opacity=0.5, 
                layerFunction=self.createGrayscaleLayer) 


        # Raw Data
        self._initLayer(op.RawData,          "Raw Data",     layers, 
                layerFunction=self.createStandardLayerFromSlot ) 



        return layers

