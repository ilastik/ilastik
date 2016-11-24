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
#from functools import partial
#from contextlib import contextmanager
#import threading

import numpy as np

from pixelValueDisplaying import PixelValueDisplaying 
from importAndResetLabels import ImportAndResetLabels 
import volumina.colortables as colortables
from ilastik.applets.watershedLabeling.watershedLabelingGui import WatershedLabelingGui

import logging
logger = logging.getLogger(__name__)



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



#LayerViewerGui->LabelingGui->WatershedSegmentationGui
class WatershedSegmentationGui(WatershedLabelingGui):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget( self ):
        return self
    
    '''
    def appletDrawer(self):
        return self._drawer
    '''

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


        #self.__cleanup_fns = []
        #self._currently_updating = False

        #init the _existingSeedsSlot variable as True. Only reset it, if there is no seed input given
        self._existingSeedsSlot = True

        #init the 256 color table with first color as invisible
        self._colortable = colortables.create_random_8bit_zero_transparent()

        ############################################################
        # BEGIN TODO
        ############################################################
        """
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



        self._LabelPipeline = op.opWSLP.opLabelPipeline

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


        # Any time watershed is re-computed, re-update the layer set, 
        # in case the set of debug layers has changed.
        '''
        self.topLevelOperatorView.watershed_completed.subscribe( self.updateAllLayers )
        '''

    
        # init the class to import and reset Labels
        self.importAndResetLabels = ImportAndResetLabels (
                op.CorrectedSeedsIn,
                self._existingSeedsSlot,
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
        # BEGIN TODO
        ############################################################



        ############################################################
        # END TODO
        ############################################################

    '''

    def initAppletDrawerUi(self):
        """
        Overridden from base class (LayerViewerGui)
        """
        op = self.topLevelOperatorView
        
        #handler which takes the qt_signal and the slot that fits to this signal and connects them
        # clean-up and dirty-Notification will be done here too
        def configure_update_handlers( qt_signal, op_slot ):
            qt_signal.connect( self.configure_operator_from_gui )
            op_slot.notifyDirty( self.configure_gui_from_operator )
            self.__cleanup_fns.append( partial( op_slot.unregisterDirty, self.configure_gui_from_operator ) )

        def control_layout_wlw( widget1, label_text, widget2 ):
            """
            Define the way, how the labels for input widgets are shown in the gui
            They are added to a horizontal BoxLayout and afterwards 
            this layout is added to a vertivalLayoutBox
            """
            row_layout = QHBoxLayout()
            row_layout.addWidget(widget1)
            row_layout.addWidget( QLabel(label_text) )
            row_layout.addSpacerItem( QSpacerItem(10, 0, QSizePolicy.Expanding) )
            row_layout.addWidget(widget2)
            return row_layout

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



        ############################################################
        #Configure the Gui
        ############################################################
        drawer_layout = QVBoxLayout()

            ############################################################
            # additional seeds
            ############################################################
        drawer_layout.addLayout( control_layout("Set additional seeds:") )
        drawer_layout.addLayout( control_layout("Caution: no effect in Batch Processing") )
        drawer_layout.addLayout( control_layout("") )

        """
        #channel Selection
        channel_box = QSpinBox()
        def set_channel_box_range(*args):
            if sip.isdeleted(channel_box):
                return
            channel_box.setMinimum(0)
            #throws an exception, if probabilities in input data aren't there, 
            #Fixed with op.Input.ready()
            if op.RawData.ready():
                channel_box.setMaximum( op.RawData.meta.getTaggedShape()['c']-1 )
            else:
                #only showed in debug mode
                #TODO not good, because emitted everytime when Input Data is changed
                logging.warning( "RawData not ready (maybe not existing)" )

        set_channel_box_range()
        op.RawData.notifyMetaChanged( set_channel_box_range )
        configure_update_handlers( channel_box.valueChanged, op.ChannelSelection )
        drawer_layout.addLayout( control_layout( self.RawDataName + " Channel", channel_box ) )
        self.channel_box = channel_box
        #connect the channel spinbox with the layer channel box
        self.channel_box.valueChanged.connect(self.on_RawData_channelChanged)
        """


        #show pixel value
        pixelValue = QLabel('unused')
        showPixelValue = QCheckBox()
        #configure_update_handlers not necessary here, 
        #because no information is passed on for calculations
        drawer_layout.addLayout( control_layout_wlw(showPixelValue, "Show Pixel-Value for Seeds:", pixelValue) )
        self.pixelValue = pixelValue
        self.showPixelValue = showPixelValue
        self.showPixelValue.stateChanged.connect(self.toggleConnectionPixelValue)
        
        

        #brush value dropdown or similar
        brush_value_box = QSpinBox()
        
        def set_brush_value_box_range(*args):
            if sip.isdeleted(brush_value_box):
                return
            brush_value_box.setMinimum(0)
            #throws an exception, if probabilities in input data aren't there, 
            #Fixed with op.Input.ready()
            if op.RawData.ready():
                if op.RawData.meta.drange:
                    #set min and max to the value range of the image
                    brush_value_box.setMinimum( op.RawData.meta.drange[0] )
                    brush_value_box.setMaximum( op.RawData.meta.drange[1] )
            else:
                #only showed in debug mode
                #TODO not good, because emitted everytime when Input Data is changed
                logging.warning( "RawData not ready (maybe not existing)" )
        set_brush_value_box_range()
        op.RawData.notifyMetaChanged( set_brush_value_box_range )
        configure_update_handlers( brush_value_box.valueChanged, op.BrushValue )
        drawer_layout.addLayout( control_layout("Brush value:", brush_value_box) )
        self.brush_value_box = brush_value_box
        #self.showPixelValue.stateChanged.connect(self.toggleConnectionPixelValue)

        ############################################################
        # BEGIN TODO
        ############################################################

        #pixel classification training applets
        # We provide our own UI file (which adds an extra control for interactive mode)
        #watershedLabelingDrawerUiPath = os.path.split(__file__)[0] + '/watershedLabelingDrawer.ui'

        #SIEHE TODO LISTE AUF BLOCK

        #toolBar = QToolBar()
        #first =  QToolButton()
        #arrowToolButton
        #paintToolButton
        #eraserToolButton
        #thresToolButton
        #brushSizeCaption
        #brushSizeComboBox
        
        #c++
        #button->setIcon(QIcon("<imagePath>"));
        #button->setIconSize(QSize(65,65));


        ############################################################
        # END TODO
        ############################################################

            ############################################################
            # seeded watershed
            ############################################################
        drawer_layout.addLayout( control_layout("") )
        drawer_layout.addLayout( control_layout("Seeded watershed:") )


        """
        seed_method_combo = QComboBox()
        seed_method_combo.addItem("Connected")
        seed_method_combo.addItem("Clustered")
        configure_update_handlers( seed_method_combo.currentIndexChanged, op.GroupSeeds )
        drawer_layout.addLayout( control_layout( "Seed WatershedLabeling", seed_method_combo ) )
        self.seed_method_combo = seed_method_combo
        
        enable_debug_box = QCheckBox()
        configure_update_handlers( enable_debug_box.toggled, op.EnableDebugOutputs )
        drawer_layout.addLayout( control_layout( "Show Debug Layers", enable_debug_box ) )
        self.enable_debug_box = enable_debug_box

        compute_button = QPushButton("Update Watershed", clicked=self.onUpdateWatershedsButton)
        drawer_layout.addWidget( compute_button )
        """

        
        ############################################################
        #Init the drawer for the Applet
        ############################################################
        # Finally, the whole drawer widget
        # which means all widgets created before are initilized to one widget, 
        # that is saved as a class member
        drawer = QWidget(parent=self)
        drawer.setLayout(drawer_layout)

        # Save these members for later use
        self._drawer = drawer

        # Initialize everything with the operator's initial values
        self.configure_gui_from_operator()

        # Delete space, so that the Layout lies on top of the page and not on bottom
        drawer_layout.setSpacing(0)
        drawer_layout.addSpacerItem( QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding) )

    '''

    def initLayer(self, slot, name, layerList, visible=True, opacity=1.0, layerFunction=None):
        """
        :param slot: InputSlot or OutputSlot for which a layer will be created
        :param name: str is the name of the layer, that will be displayed in the gui
        :param visible: bool whether the layer is visible or not (at the initialization)
        :param opacity: float from 0.0 to 1.0; describes how much you can see through this layer 
        :param layerFunction: if layerFunction is None, then use the default: 
            self._create_8bit_ordered_random_colortable_zero_transparent_layer_from_slot
        """
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
        Responsable for the elements in the 'Viewer Controls'
        These are the views (e.g. opacity of Raw Data)
        that can be adjusted in the left corner of the program
        And for the Elements, that can be seen in the 'Central Widget', 
        these are excactly the one, that are shown in the Viewer Controls

        """

        # Base class provides the label layer.
        #needed to add here. otherwise the reset button doesn't work well
        layers = super(WatershedSegmentationGui, self).setupLayers()
        #layers[0].visible = False
        #remove the Label-Layer, because it is not needed here
        layers = []

        op = self.topLevelOperatorView

        #Raw Data
        self.initLayer(op.RawData, "Raw Data", layers, visible=False, 
                layerFunction=self.createStandardLayerFromSlot ) 

        #Boundaries
        self.initLayer(op.Boundaries, "Boundaries", layers, opacity=0.1, 
                layerFunction=self.createGrayscaleLayer) 

        #Seeds
        self.initLayer(op.Seeds, "Seeds", layers, visible=False)

        #CorrectedSeedsOut
        self.initLayer(op.CorrectedSeedsOut, "Corrected Seeds", layers)



        #if you have a channel-box in the gui, that shall be synchronized with the layer channel
        #layer.channelChanged.connect(self.channel_box.setValue)
        #setValue() will emit valueChanged() if the new value is different from the old one.
        #not necessary: self.channel_box.valueChanged.emit(i)

        return layers


