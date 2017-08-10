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
from functools import partial
from contextlib import contextmanager
import threading

import numpy as np

import sip
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QWidget, QLabel, QSpinBox, QDoubleSpinBox, QVBoxLayout, \
                        QHBoxLayout, QSpacerItem, QSizePolicy, QColor, QPen, QComboBox, QPushButton

from ilastik.utility.gui import threadRouted
from volumina.pixelpipeline.datasources import LazyflowSource, ArraySource
from volumina.layer import GrayscaleLayer, ColortableLayer, generateRandomColors
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

from lazyflow.request import Request
from lazyflow.utility import TransposedView

import logging
from PyQt4.Qt import QCheckBox, QLineEdit, QButtonGroup, QRadioButton
logger = logging.getLogger(__name__)

class ChannelSelectionGui(LayerViewerGui):


    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def appletDrawer(self):
        return self._drawer

    #take all the unregisteredDirty Slots and clean them, so something like this
    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        # Base class
        # including: Remove all layers
        super( ChannelSelectionGui, self ).stopAndCleanUp()
    
    ###########################################
    ###########################################
    
    def __init__(self, parentApplet, topLevelOperatorView):
        self.__cleanup_fns = []
        self._currently_updating = False
        self.topLevelOperatorView = topLevelOperatorView
        super(ChannelSelectionGui, self).__init__( parentApplet, topLevelOperatorView )
        '''
        self._sp_colortable = generateRandomColors(256, clamp={'v': 1.0, 's' : 0.5}, zeroIsTransparent=True)
        self._threshold_colortable = [ QColor(0, 0, 0, 0).rgba(),      # transparent
                                       QColor(0, 255, 0, 255).rgba() ] # green

        # Any time watershed is re-computed, re-update the layer set, in case the set of debug layers has changed.
        self.topLevelOperatorView.watershed_completed.subscribe( self.updateAllLayers )
        '''

    def initAppletDrawerUi(self):
        """
        Overridden from base class (LayerViewerGui)
        executed in __init__ of base class
        """
        op = self.topLevelOperatorView
        
        
        #handler which takes the qt_signal and the slot that fits to this signal and connects them
        # clean-up and dirty-Notification will be done here too
        def configure_update_handlers( qt_signal, op_slot ):
            qt_signal.connect( self.configure_operator_from_gui )
            op_slot.notifyDirty( self.configure_gui_from_operator )
            self.__cleanup_fns.append( partial( op_slot.unregisterDirty, self.configure_gui_from_operator ) )
            


        def control_layout_labels( label1, label2, label3, label4, label5): #, label6):
            """
            Define the way, how the labels for input widgets are shown in the gui
            The spaces are adjusted to the widgets width
            They are added to a horizontal BoxLayout and afterwards 
            this layout is added to a vertivalLayoutBox
            """

            def addSpace(_row_layout, space):
                _row_layout.addSpacerItem( QSpacerItem(space, 0))#, QSizePolicy.MinimumExpanding) )

            row_layout = QHBoxLayout()
            row_layout.addWidget( QLabel(label1) )
            addSpace(row_layout, 5)
            row_layout.addWidget( QLabel(label2) )
            addSpace(row_layout, 60)
            row_layout.addWidget( QLabel(label3) )
            addSpace(row_layout, 3)
            row_layout.addWidget( QLabel(label4) )
            addSpace(row_layout, 3)
            row_layout.addWidget( QLabel(label5) )
            #addSpace(row_layout, 10)
            return row_layout


        def control_layout(label_text, *args):
            """
            Define the way, how the input widgets are shown in the gui
            They are added to a horizontal BoxLayout and afterwards 
            this layout is added to a vertivalLayoutBox
            """
            space=10
            row_layout = QHBoxLayout()
            row_layout.addWidget( QLabel(label_text) )
            # Add all other arguments passed on
            for widget in args:
                row_layout.addSpacerItem( QSpacerItem(space, 0, QSizePolicy.Expanding) )
                row_layout.addWidget(widget)
            return row_layout




        ############################################################
        #Configure the Gui
        ############################################################
        drawer_layout = QVBoxLayout()
        op = self.topLevelOperatorView

        drawer_layout.addLayout( control_layout_labels( "#" , "Label", "Seed", "View", "Use" ) )
        #lists for the boxes (gui elements)
        visibility_box  = []
        utilize_box     = []
        text_box        = []
        radio_box       = []
        radio_group     = QButtonGroup()

        # take the number of channels from the Probability input
        self.numChannels = op.Probability.meta.getTaggedShape()['c']
        for i in range(self.numChannels):
            #print "Number of channels: ", self.numChannels


            #labels
            text = QLineEdit()
            text.setText("Label " + str(i))
            text_box.append(text)
            del text
            configure_update_handlers( text_box[i].textChanged, op.Label )

            #RadioButton for seeds
            radio = QRadioButton()
            radio_group.addButton(radio)
            radio_box.append(radio)
            if i == 0:
                radio.setChecked(True)
            del radio
            configure_update_handlers( radio_box[i].clicked, op.Seed )


            #visibility
            checkbox = QCheckBox()
            visibility_box.append(checkbox)
            del checkbox
            configure_update_handlers( visibility_box[i].stateChanged, op.Visibility )
            
            #utilization
            checkbox = QCheckBox()
            utilize_box.append(checkbox)
            del checkbox
            configure_update_handlers( utilize_box[i].stateChanged, op.Utilize )

            # Add all elements of one channel to the layout
            drawer_layout.addLayout( control_layout( str(i), \
                    text_box[i], radio_box[i],  visibility_box[i], utilize_box[i] ) )


        # set the boxes to class values
        self.visibility_box = visibility_box
        self.utilize_box    = utilize_box
        self.text_box       = text_box
        self.radio_box      = radio_box
        self.radio_group    = radio_group
        
        ############################################################
        #Init the drawer for the Applet
        ############################################################

        # Finally, the whole drawer widget, 
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


        #Change the visibility of the Channels when clicked on the checkbox
        for i in range(self.numChannels):
            self.visibility_box[i].stateChanged.connect(self._onCheckboxClicked)

        


    def _onLayerVisibleClicked(self):
        """
        used when the layer-icon: eye is clicked and used to update the visibility box therefore
        """
        for i in range(self.numChannels):
            if ( self.getLayerByName( "Channel " + str(i) ).visible == True):
                self.visibility_box[i].setChecked(True)
            else:
                self.visibility_box[i].setChecked(False)

    def _onCheckboxClicked(self):
        """
        used when the visibility checkbox is clicked
        """
        for i in range(self.numChannels):
            if (self.visibility_box[i].isChecked()):
                #print "checked"
                self.getLayerByName("Channel " + str(i)).visible = True

            else:
                #print "not checked"
                self.getLayerByName("Channel " + str(i)).visible = False


    @contextmanager
    def set_updating(self):
        assert not self._currently_updating
        self._currently_updating = True
        yield
        self._currently_updating = False

    def configure_gui_from_operator(self, *args):
        """
        see configure_update_handlers
        """

        if self._currently_updating:
            return False
        with self.set_updating():
            op = self.topLevelOperatorView
            '''
            self.channel_box.setValue( op.ChannelSelection.value )
            input_layer = self.getLayerByName("Input")
            if input_layer:
                input_layer.channel = op.ChannelSelection.value
            '''
            #worked
            #self.visibility_box.setChecked( op.Visibility.value )
            
            for i in range(self.numChannels):
                self.visibility_box[i].setChecked( op.Visibility.value )
                self.utilize_box[i].setChecked( op.Utilize.value )
                self.radio_box[i].setChecked( op.Seed.value )
            '''
            self.membrane_size_box.setValue( op.MinMembraneSize.value )
            self.seed_method_combo.setCurrentIndex( int(op.GroupSeeds.value) )
            '''

    def configure_operator_from_gui(self):
        """
        see configure_update_handlers
        """

        if self._currently_updating:
            return False
        with self.set_updating():
            op = self.topLevelOperatorView
            #worked
            #op.Visibility.setValue( self.visibility_box.isChecked() )

            for i in range(self.numChannels):
                op.Visibility.setValue( self.visibility_box[i].isChecked() )
                op.Utilize.setValue( self.utilize_box[i].isChecked() )
                op.Seed.setValue( self.radio_box[i].isChecked() )

            '''
            op.MinMembraneSize.setValue( self.membrane_size_box.value() )
            op.GroupSeeds.setValue( bool(self.seed_method_combo.currentIndex()) )
            '''

    def setupLayers(self):
        """
        Responsable for the elements in the 'Viewer Controls'
        These are the views (e.g. opacitiy of Raw Data)
        that can be adjusted in the left corner of the program
        And for the Elements, that can be seen in the 'Central Widget', 
        these are excactly the one, that are shown in the Viewer Controls

        """
        layers = []
        op = self.topLevelOperatorView
        '''
        # Debug layers
        if op.debug_results:
            for name, compressed_array in op.debug_results.items():
                axiskeys = op.Superpixels.meta.getAxisKeys()[:-1] # debug images don't have a channel axis
                permutation = map(lambda key: axiskeys.index(key) if key in axiskeys else None, 'txyzc')
                arraysource = ArraySource( TransposedView(compressed_array, permutation) )
                if compressed_array.dtype == np.uint32:
                    layer = ColortableLayer(arraysource, self._sp_colortable)
                else:
                    layer = GrayscaleLayer(arraysource)
                    # TODO: Normalize? Maybe the drange should be included with the debug image.
                layer.name = name
                layer.visible = False
                layer.opacity = 1.0
                layers.append(layer)
                del layer
        '''

        # Probabilities
        if op.Probability.ready():
            #For each channel, add one View
            for i in range(self.numChannels):
                layer = self._create_single_color_layer_from_slot( op.Probability, i )
                layer.name = "Channel " + str(i)
                layer.visible = True
                layer.opacity = 1.0
                #change the visibility of the Applet Checkbox when clicked of the Layer-Visibility Box
                layer.visibleChanged.connect(self._onLayerVisibleClicked)
                layers.append(layer)
                del layer

        # Raw Data 
        if op.RawData.ready():
            layer = self.createStandardLayerFromSlot( op.RawData )
            #layer = self._create_grayscale_layer_from_slot( op.Input, op.Input.meta.getTaggedShape()['c'] )
            layer.name = "RawData"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)
            del layer

        return layers



            


    """
    TODO
    Check: 1. Visibility wenn man unten klickt auch oben veraendern

    2. Applet fuer 3. auf Blatt machen, also auswahl zwischen Threshold oder Maxima
    2.1 Dazu muss man  den Output von ChannelSelection mit Seed steuern
    2.2 Output von Channelselection ohne Seed nach watershed 
        + Output von Threshold/Maxima Applet nach watershed

        Output: If seed clicked, then it is utilized
    """
