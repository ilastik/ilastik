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
from PyQt4.Qt import pyqtSlot

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

        # TODO make serialized slot out of it or better: 
        # TODO make something totally diffrent from that, and talk to anna about this 
        # init the _existingSeedsSlot variable as True. Only reset it, if there is no seed input given
        self._existingSeedsSlot = True


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


        lst_seeds = [ op.Seeds , op.CorrectedSeedsIn ]
        #lst_seeds = [ op.Seeds , op.CorrectedSeedsIn, op.opLabelPipeline.LabelInput]
        for operator in lst_seeds:
            if not operator.ready():
                self._existingSeedsSlot = False
                '''
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
                '''

        '''
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


    
        # init the class to import and reset Labels
        self.importAndResetLabels = ImportAndResetLabels (
                op.CorrectedSeedsIn,
                self._existingSeedsSlot,
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

            


        ############################################################
        # BEGIN TODO
        ############################################################


        # Neighbors
        # add the options for the neighbors and set the default value
        defaultIndex = 0
        self._labelControlUi.neighborsComboBox.addItems(["direct","indirect"])
        self._labelControlUi.neighborsComboBox.setCurrentIndex(defaultIndex)
        
        # TODO emit signal instead, so that the default index is the value of the WSNeighbors
        op.WSNeighbors.setValue( self._labelControlUi.neighborsComboBox.itemText(defaultIndex) )
        # connect the change Event
        self._labelControlUi.neighborsComboBox.currentIndexChanged.connect(self.onNeighborsComboBoxCurrentIndexChanged)



        ############################################################
        # END TODO
        ############################################################



    '''
    def initAppletDrawerUi(self):
        """
        Overridden from base class (LayerViewerGui)
        """
        def control_layout(*args):
            """
            Define the way, how the input widgets are shown in the gui
            They are added to a horizontal BoxLayout and afterwards 
            this layout is added to a vertivalLayoutBox
            """
            space=10
            row_layout = QHBoxLayout()
            begin = True
            # Add all arguments passed on
            for widget in args:
                #convert strings to QLabel
                #for python3.x add:
                #basestring = str
                if isinstance(widget, basestring):
                    widget = QLabel(widget)
                #only add space after first widget
                if not begin:
                    row_layout.addSpacerItem( QSpacerItem(space, 0, QSizePolicy.Expanding) )
                row_layout.addWidget(widget)
                begin = False
            return row_layout
    '''

    @pyqtSlot(int)
    def onNeighborsComboBoxCurrentIndexChanged(self, index):
        op = self.topLevelOperatorView 
        op.WSNeighbors.setValue( self._labelControlUi.neighborsComboBox.itemText(index) )
        #TODO
        print op.WSNeighbors.value

    @pyqtSlot()
    def onRunWatershedPushButtonClicked(self):
        """
        Responsable to set the ShowWatershedLayer slot to True,
        so that a new Layer for the watershed results can be added.
        Executes the watershed algorithm

        """
        op = self.topLevelOperatorView
        if not op.ShowWatershedLayer.value: 
            op.ShowWatershedLayer.setValue(True)
            self.updateAllLayers()

        # execute the watershed algorithm
        self.topLevelOperatorView.opWSC.execWatershedAlgorithm()







    def _initLayer(self, slot, name, layerList, visible=True, opacity=1.0, layerFunction=None):
        """
        :param slot: for which a layer will be created
        :type slot: InputSlot or OutputSlot 
        :param name:  is the name of the layer, that will be displayed in the gui
        :type name: str
        :param visible: whether the layer is visible or not (at the initialization)
        :type visible: bool
        :param opacity: describes how much you can see through this layer 
        :type opacity: float from 0.0 to 1.0 
        :param layerFunction: if layerFunction is None, then use the default: 
            self._create_8bit_ordered_random_colortable_zero_transparent_layer_from_slot
        """
        #if you have a channel-box in the gui, that shall be synchronized with the layer channel
        #layer.channelChanged.connect(self.channel_box.setValue)
        #setValue() will emit valueChanged() if the new value is different from the old one.
        #not necessary: self.channel_box.valueChanged.emit(i)

        if layerFunction is None:
            layerFunction = self.create_8bit_ordered_random_colortable_zero_transparent_layer_from_slot

        if slot.ready():
            layer           = layerFunction(slot)
            layer.name      = name
            layer.visible   = visible
            layer.opacity   = opacity
            layerList.append(layer)
            del layer
        else:
            logger.info("slot not ready; didn't add a layer with name: " + name)




    def setupLayers(self):
        """
        For illustration of what a layer is, see: http://ilastik.org/documentation/basics/layers

        Responsable for the elements in the 'Viewer Controls'.

        These are the views (e.g. opacity of Raw Data)
        that can be adjusted in the left corner of the program
        and for the Elements, that can be seen in the 'Central Widget'. 
        These are excactly the ones, that are shown in the Viewer Controls.

        Uses :py:meth:`_initLayer` to create a single layer

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

