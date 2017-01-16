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
from importAndResetLabels import ImportAndResetLabels 
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



        ############################################################
        # BEGIN TODO
        ############################################################
        """
        THIS IS ONLY NECESSARY IF THE SEEDS INPUT FROM DATA SELECTION IS EMPTY

        #here try to propagate the dirty things:
        so that other slots see, that I changed the the correctedSeedsIn and the labelcache works fine

        Use some things of a workflow: multicut where you can decide whether to have an input or not
        """


        '''
        #only for debugging
        op = self.topLevelOperatorView 
        # Check if all necessary InputSlots are available and ready
        # and set CorrectedSeedsIn if not supplied
        lst = [ op.RawData , op.Boundaries , op.Seeds , op.CorrectedSeedsIn ]
        #show a debug information, so that the user knows that not all data is supplied, that is needed
        for operator in lst:
            if not operator.ready():
                logger.info( "InputData: " + operator.name + " not ready")
        '''


        '''
        lst_seeds = [ op.Seeds , op.CorrectedSeedsIn ]
        #lst_seeds = [ op.Seeds , op.CorrectedSeedsIn, op.opLabelPipeline.LabelInput]
        for operator in lst_seeds:
            if not operator.ready():
                self._existingSeedsSlot = False
                #TODO setting the CorrectedSeedsIn here
                #if (not op.CorrectedSeedsIn.ready() and op.CorrectedSeedsIn.meta.shape == None ):
                if op.Boundaries.ready():
                    # copy the meta-data from boandaries
                    #default_seeds_volume = op.Boundaries[:].wait()
                    operator.meta = op.Boundaries.meta
                    operator._value =  np.zeros(op.Boundaries.meta.shape)
                    #print op.operator._value
                else:
                    logger.info( "Boundaries are not ready," +
                        "can't init seeds and CorrectedSeedsIn with default zeros" )

        #for debug
        for operator in lst:
            if operator.ready():
                logger.info( "InputData: " + operator.name + " is ready now")
        '''

        #TODO
        #op.opLabelPipeline.LabelInput.notifyDirty(op.CorrectedSeedsIn)
        #op.CorrectedSeedsIn.setDirty()

        ############################################################
        # END TODO
        ############################################################

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


        #if not (op.WSMethod.value == "UnionFind"):
        #print "\nMethod: '" + op.WSMethod.value + "'\n\n"
    
        # init the class to import and reset Labels
        self.importAndResetLabels = ImportAndResetLabels (
                op.CorrectedSeedsIn,
                op.SeedsExist.value,
                op.UseCachedLabels.value,
                self._labelControlUi.labelListModel, 
                self._LabelPipeline.opLabelArray,
                op.LabelNames, 
                op.LabelColors, 
                op.PmapColors
                )
        # 1. First import seeds, and connect slot
        # 2. then look at their pixelValues (including looking at their channels) 
        #   in pixelValueDisplaying
        # import the Labels from CorrectedSeedsIn, if possible
        self.importAndResetLabels.importLabelsFromSlot()

        # use the Cache of the CorrectedSeedsOut for the next Time, the watershed applet will be reloaded
        op.UseCachedLabels.setValue(True)

        # resetSeedsPushButton functionality added by connecting signal with slot
        self._labelControlUi.resetSeedsPushButton.clicked.connect(self.importAndResetLabels.resetLabelsToSlot)

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

            


        # handle the init values and the sync with the operator
        self._initNeighborsComboBox()


    @pyqtSlot()
    def onRunWatershedPushButtonClicked(self):
        """
        Responsable to set the ShowWatershedLayer slot to True,
        so that a new Layer for the watershed results can be added.
        Executes the watershed algorithm

        """
        op = self.topLevelOperatorView

        # if no seeds but not UnionFind => not possible => ErrorMessage
        if not (op.WSMethod == "UnionFind") and not op.SeedsExist.value:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("No Seeds supplied and watershed not unseeded")
            #msg.setInformativeText("This is additional information")
            msg.setWindowTitle("Action invalid")
            msg.setStandardButtons(QMessageBox.Ok)
            #msg.buttonClicked.connect(msgbtn)
	
            retval = msg.exec_()

        else:
            if not op.ShowWatershedLayer.value: 
                op.ShowWatershedLayer.setValue(True)
                self.updateAllLayers()

            # execute the watershed algorithm
            self.topLevelOperatorView.opWSC.execWatershedAlgorithm()




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

