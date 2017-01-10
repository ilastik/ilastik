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

#import numpy as Qtnp
from PyQt4.Qt import pyqtSlot
from PyQt4 import uic, QtCore
import os

#from ilastik.applets.watershedLabeling.watershedLabelingGui import WatershedLabelingGui
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

import logging
logger = logging.getLogger(__name__)




#LayerViewerGui->LabelingGui->WatershedLabelingGui
class SeedsGui(LayerViewerGui):
#class SeedsGui(WatershedLabelingGui):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget( self ):
        return self
    

    def appletDrawer(self):
        return self._drawer
    ###########################################
    ###########################################


    def initAppletDrawerUi(self):
        """
        Reimplemented from LayerViewerGui base class.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/seeds.ui")
    
    def __init__(self, parentApplet, topLevelOperatorView, DrawerUiPath=None ):

        self.topLevelOperatorView = topLevelOperatorView
        op = self.topLevelOperatorView 

        self.__cleanup_fns = []
        super( SeedsGui, self ).__init__(parentApplet, topLevelOperatorView)

        self._drawer.unseededCheckBox.stateChanged.connect(self.onUnseededCheckBoxStateChanged)


    def setEnabledEverthingButUnseeded(self, enable):
        gui = self._drawer
        guiElements = [
            gui.smoothingComboBox,
            gui.smoothingDoubleSpinBox,
            gui.computeComboBox,
            gui.generateButton
        ]

        for widget in guiElements:
            widget.setEnabled(enable) 

    def onUnseededCheckBoxStateChanged(self,state):
        if (state == QtCore.Qt.Checked):
            self.setEnabledEverthingButUnseeded(False)
        else:
            self.setEnabledEverthingButUnseeded(True)





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
        layers = super(SeedsGui, self).setupLayers()
        #layers[0].visible = False
        # remove the Label-Layer, because it is not needed here
        layers = []

        op = self.topLevelOperatorView

        #TODO if Seeds are supplied already
        # Seeds
        #self._initLayer(op.Seeds,            "Seeds",        layers, visible=False)

        
        # Boundaries
        self._initLayer(op.Boundaries,       "Boundaries",   layers, opacity=0.5, 
                layerFunction=self.createGrayscaleLayer) 


        # Raw Data
        self._initLayer(op.RawData,          "Raw Data",     layers, 
                layerFunction=self.createStandardLayerFromSlot ) 



        return layers

