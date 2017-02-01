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

import numpy 
import numpy as np
import vigra
from PyQt4.Qt import pyqtSlot
from PyQt4.QtGui import QMessageBox
from PyQt4 import uic
import os
from functools import partial
from contextlib import contextmanager

#from ilastik.applets.watershedLabeling.watershedLabelingGui import WatershedLabelingGui
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui


import logging
logger = logging.getLogger(__name__)


class SmoothingMethods(object):
    """
    class that capsulates the methods and their index in the combobox
    """
    def __init__(self):
        self.methods = [ "Gaussian", "MedianFilter"]
        
class ComputeMethods(object):
    """
    class that capsulates the methods and their index in the combobox
    """
    def __init__(self):
        self.methods = [ "HeightMap Min", "HeightMap Max", "DistanceTransform"]


class SeedsGui(LayerViewerGui):

    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget( self ):
        return self
    

    def appletDrawer(self):
        return self._drawer
    ###########################################

    def __init__(self, parentApplet, topLevelOperatorView, DrawerUiPath=None ):
        self.topLevelOperatorView = topLevelOperatorView
        op = self.topLevelOperatorView 
        self.__cleanup_fns = []
        self._currently_updating = False
        super( SeedsGui, self ).__init__(parentApplet, topLevelOperatorView)




    ############################################################
    # generate button 
    ############################################################

    def onGenerateButtonClicked(self):
        op = self.topLevelOperatorView 
        # once overridden, don't ask again. 
        # only if op.Seeds has changed op.GenerateSeeds (see opSeeds.py)
        if op.Seeds.ready() and not op.GenerateSeeds.value: 
            msgBox = QMessageBox()
            msgBox.setText('Do you really want to override the given seeds?')
            msgBox.addButton(QMessageBox.Yes)
            msgBox.addButton(QMessageBox.No)
            ret = msgBox.exec_()

            if (ret == QMessageBox.No):
                return

        op.GenerateSeeds.setValue(True)

        self.configure_operator_from_gui()
        # make the wanted layer visible to ask for this roi
        for layer in self.layerstack:
            if "Seeds" in layer.name:
                layer.visible = True

        # refresh the layers
        self.updateAllLayers()




    ############################################################
    # initialization of the Comboboxes with values
    ############################################################
    def initComboBoxes(self):
        """
        Initializes the Smoothing and Compute ComboBox with selectables
        Therefore it is important, that the state of the SmoothingMethod and
        ComputeMethod is stored temporarily, because adding new elements 
        (probably emit signal for changing this Method index) changes each Method.
        """
        def initSmoothingComboBox():
            methodList = SmoothingMethods().methods
            for elem in methodList:
                self._drawer.smoothingComboBox.addItem(elem)


        def initComputeComboBox():
            methodList = ComputeMethods().methods
            for elem in methodList:
                self._drawer.computeComboBox.addItem(elem)

        op = self.topLevelOperatorView 
        # this value needs to be preserved, because adding some new elements 
        # changes the op.SmoothingMethod.value
        temp1 = op.SmoothingMethod.value
        temp2 = op.ComputeMethod.value

        initSmoothingComboBox()
        initComputeComboBox()

        # reset the methods
        op.SmoothingMethod.setValue(temp1)
        op.ComputeMethod.setValue(temp2)




    ############################################################
    # unseeded gui element functionality
    ############################################################

    @pyqtSlot()
    def onUnseededCheckBoxStateChanged(self):
        """
        See if the Unseeded-CheckBox is checked or not.

        Checked: disable all gui-elements except this checkbox.
        Unchecked: enable all gui-elements.

        Gui-Elements must be added manually.
        """
        gui = self._drawer

        # change the enable state of the gui elements
        if gui.unseededCheckBox.isChecked():
            enable = False
        else:
            enable = True

        # list of gui elements
        guiElements = [
            gui.smoothingComboBox,
            gui.smoothingDoubleSpinBox,
            gui.computeComboBox,
            gui.generateButton
        ]

        # enable/disable
        for widget in guiElements:
            widget.setEnabled(enable) 


    ############################################################
    # synchronisation of gui elements and operators and their functionality
    ############################################################

    def initAppletDrawerUi(self):
        """
        Reimplemented from LayerViewerGui base class.
        """
        op = self.topLevelOperatorView

        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/seeds.ui")

        # give function to the unseeded checkbox
        self._drawer.unseededCheckBox.stateChanged.connect(self.onUnseededCheckBoxStateChanged)
        self._drawer.generateButton.clicked.connect(self.onGenerateButtonClicked)

        # init the Comboboxes with values
        self.initComboBoxes()

        # to connect gui with operators
        def configure_update_handlers( qt_signal, op_slot ):
            qt_signal.connect( self.configure_operator_from_gui )
            op_slot.notifyDirty( self.configure_gui_from_operator )
            self.__cleanup_fns.append( partial( op_slot.unregisterDirty, self.configure_gui_from_operator ) )



        # handle the connection of gui elements and operators
        configure_update_handlers( self._drawer.unseededCheckBox.toggled, op.Unseeded )
        configure_update_handlers( self._drawer.smoothingComboBox.currentIndexChanged, op.SmoothingMethod )
        configure_update_handlers( self._drawer.smoothingDoubleSpinBox.valueChanged, op.SmoothingSigma )
        configure_update_handlers( self._drawer.computeComboBox.currentIndexChanged, op.ComputeMethod )



        # Initialize everything with the operator's initial values
        self.configure_gui_from_operator()


        # set the right watershed method given the current settings 
        # (of checkbox (now correct in gui) and boundaries dtype)
        #self.onUnseededCheckBoxStateChanged()

        '''
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




    ############################################################
    # helping functions: synchronisation of gui elements and operators
    ############################################################
    @contextmanager
    def set_updating(self):
        """
        used for the state while updating the gui from operators or vice versa
        """
        assert not self._currently_updating
        self._currently_updating = True
        yield
        self._currently_updating = False

    def configure_gui_from_operator(self, *args):
        """
        Used to set the Gui with the values of the operators
        """
        if self._currently_updating:
            return False
        with self.set_updating():
            op = self.topLevelOperatorView
            self._drawer.unseededCheckBox.setChecked( op.Unseeded.value )
            self._drawer.smoothingComboBox.setCurrentIndex( int(op.SmoothingMethod.value) )
            self._drawer.smoothingDoubleSpinBox.setValue( op.SmoothingSigma.value )
            self._drawer.computeComboBox.setCurrentIndex( int(op.ComputeMethod.value) )
            

    def configure_operator_from_gui(self):
        if self._currently_updating:
            return False
        with self.set_updating():
            op = self.topLevelOperatorView
            op.Unseeded.setValue( self._drawer.unseededCheckBox.isChecked() )
            op.SmoothingMethod.setValue( self._drawer.smoothingComboBox.currentIndex() )
            op.SmoothingSigma.setValue( self._drawer.smoothingDoubleSpinBox.value() )
            op.ComputeMethod.setValue( self._drawer.computeComboBox.currentIndex() )




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
        layers = super(SeedsGui, self).setupLayers()
        #layers[0].visible = False
        # remove the Label-Layer, because it is not needed here
        layers = []

        op = self.topLevelOperatorView


        '''
        # only display Seeds if no Generated Seeds are supplied
        if not op.GeneratedSeeds.ready():
            self._initLayer(op.Seeds,                "Seeds",        layers, opacity=0.5)

        self._initLayer(op.GeneratedSeeds,       "Generated Seeds",        layers,  opacity=0.5)
        '''

        # Seeds or generated Seeds
        if op.Seeds.ready() or op.GenerateSeeds.value:
            self._initLayer(op.SeedsOutCached,            "Seeds",        layers, opacity=0.5)

        #self._initLayer(op.Smoothing,            "Smoothing",        layers, opacity=0.5,
                #layerFunction=self.createGrayscaleLayer) 
        #self._initLayer(op.Compute,            "Compute",        layers,
                #layerFunction=self.createGrayscaleLayer) 
        
        # Boundaries
        self._initLayer(op.Boundaries,       "Boundaries",   layers, opacity=0.5, 
                layerFunction=self.createGrayscaleLayer) 


        # Raw Data
        self._initLayer(op.RawData,          "Raw Data",     layers, 
                layerFunction=self.createStandardLayerFromSlot ) 



        return layers
