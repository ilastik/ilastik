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
from PyQt4.Qt import pyqtSlot
from PyQt4 import uic
import os
from functools import partial
from contextlib import contextmanager

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

    def __init__(self, parentApplet, topLevelOperatorView, DrawerUiPath=None ):
        self.topLevelOperatorView = topLevelOperatorView
        op = self.topLevelOperatorView 
        self.__cleanup_fns = []
        self._currently_updating = False
        super( SeedsGui, self ).__init__(parentApplet, topLevelOperatorView)

        # init the Comboboxes with values
        self.initComboBoxes()


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
        self.onUnseededCheckBoxStateChanged()


    ############################################################
    # synchronisation of gui elements and operators
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
            '''
            self.channel_box.setValue( op.ChannelSelection.value )
            input_layer = self.getLayerByName("Input")
            if input_layer:
                input_layer.channel = op.ChannelSelection.value
            
            self.threshold_box.setValue( op.Pmin.value )
            self.membrane_size_box.setValue( op.MinMembraneSize.value )
            self.superpixel_size_box.setValue( op.MinSegmentSize.value )
            self.seed_presmoothing_box.setValue( op.SigmaMinima.value )
            self.watershed_presmoothing_box.setValue( op.SigmaWeights.value )
            self.seed_method_combo.setCurrentIndex( int(op.GroupSeeds.value) )
            self.preserve_pmaps_box.setChecked( op.PreserveMembranePmaps.value )
            '''
            self._drawer.unseededCheckBox.setChecked( op.Unseeded.value )
            self._drawer.smoothingComboBox.setCurrentIndex( int(op.SmoothingMethod.value) )
            self._drawer.smoothingDoubleSpinBox.setValue( op.SmoothingSigma.value )
            self._drawer.computeComboBox.setCurrentIndex( int(op.ComputeMethod.value) )
            

    def configure_operator_from_gui(self):
        if self._currently_updating:
            return False
        with self.set_updating():
            op = self.topLevelOperatorView
            '''
            op.ChannelSelection.setValue( self.channel_box.value() )
            op.Pmin.setValue( self.threshold_box.value() )
            op.MinMembraneSize.setValue( self.membrane_size_box.value() )
            op.MinSegmentSize.setValue( self.superpixel_size_box.value() )
            op.SigmaMinima.setValue( self.seed_presmoothing_box.value() )
            op.SigmaWeights.setValue( self.watershed_presmoothing_box.value() )
            op.GroupSeeds.setValue( bool(self.seed_method_combo.currentIndex()) )
            op.PreserveMembranePmaps.setValue( self.preserve_pmaps_box.isChecked() )
            '''
            op.Unseeded.setValue( self._drawer.unseededCheckBox.isChecked() )
            op.SmoothingMethod.setValue( self._drawer.smoothingComboBox.currentIndex() )
            op.SmoothingSigma.setValue( self._drawer.smoothingDoubleSpinBox.value() )
            op.ComputeMethod.setValue( self._drawer.computeComboBox.currentIndex() )

    



    ############################################################
    # synchronisation of gui elements and operators
    ############################################################

    def setEnabledEverthingButUnseeded(self, enable):
        """
        Enables or disables all gui elements except the unseeded checkbox. 
        Gui-Elements must be added manually.

        :param enable: if True, enable all gui elements, else: disable
        :type enable: bool
        """
        gui = self._drawer
        guiElements = [
            gui.smoothingComboBox,
            gui.smoothingDoubleSpinBox,
            gui.computeComboBox,
            gui.generateButton
        ]

        for widget in guiElements:
            widget.setEnabled(enable) 


    @pyqtSlot()
    def onUnseededCheckBoxStateChanged(self):
        """
        See if the Unseeded-CheckBox is checked or not.

        Checked: Use UnionFind as watershed method
            and disable all gui-elements except this checkbox

        Unchecked: use setWatershedMethodToTurboOrRegionGrowing to decide whether Turbo or RegionGrowing
            and enable all gui-elements 
        """

        op = self.topLevelOperatorView 
        # change the enable state of the gui elements
        #if (state == QtCore.Qt.Checked):
        if self._drawer.unseededCheckBox.isChecked():
            self.setEnabledEverthingButUnseeded(False)
            
            op.WSMethodIn.setValue("UnionFind") 
        else:
            self.setEnabledEverthingButUnseeded(True)
            self.setWatershedMethodToTurboOrRegionGrowing()


    def setWatershedMethodToTurboOrRegionGrowing(self):
        """
        Set the correct watershed method
        boundaries-input uint8: Turbo
        boundaries-input not uint8: RegionGrowing
        """
        op = self.topLevelOperatorView 
        # if boundaries has type uint8, then use Turbo, otherwise RegionGrowing
        if (op.Boundaries.meta.dtype == numpy.uint8):
            op.WSMethodIn.setValue("Turbo") 
        else:
            op.WSMethodIn.setValue("RegionGrowing") 



    ############################################################
    # initialization of the Comboboxes with values
    ############################################################
    def initComboBoxes(self):
        op = self.topLevelOperatorView 
        # this value needs to be preserved, because adding some new elements 
        # changes the op.SmoothingMethod.value
        temp1 = op.SmoothingMethod.value
        temp2 = op.ComputeMethod.value

        self.initSmoothingComboBox()
        self.initComputeComboBox()

        op.SmoothingMethod.setValue(temp1)
        op.ComputeMethod.setValue(temp2)

    def initSmoothingComboBox(self):
        itemList = ["Gaussian", "MedianFilter"]
        self._drawer.smoothingComboBox.addItems(itemList)

    def initComputeComboBox(self):
        itemList = ["HeightMap", "DistanceTransform"]
        self._drawer.computeComboBox.addItems(itemList)




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

