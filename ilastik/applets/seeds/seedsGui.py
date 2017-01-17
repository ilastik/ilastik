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

from ilastik.utility.VigraIlastikConversionFunctions import removeChannelAxis, addChannelAxis, getArray, evaluateSlicing

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

        # init the Comboboxes with values
        self.initComboBoxes()


        # copy Seeds to generated Seeds if Seeds is ready and GeneratedSeeds is None
        #TODO just for debugging and testing
        if op.Seeds.ready():
            print "seeds supplied"
        else: 
            print "no seeds supplied"

        if op.GeneratedSeeds.ready():
            print "ready"
            if op.GeneratedSeeds.value == None:
                print "tst"
        else:
            print "not ready"

    def onGenerateButtonClicked(self):
        #TODO
        # for testing, commented
        '''
        op = self.topLevelOperatorView 
        if op.Seeds.ready(): 
            print "ready"
            msgBox = QMessageBox()
            msgBox.setText('Do you really want to override the given seeds?')
            msgBox.addButton(QMessageBox.Yes)
            msgBox.addButton(QMessageBox.No)
            ret = msgBox.exec_()

            if (ret == QMessageBox.No):
                return
        else:
            print "not ready"
        '''

        self.configure_operator_from_gui()
        for layer in self.layerstack:
            if "Test" in layer.name:
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
            
            #op.WSMethodIn.setValue("UnionFind") 
        else:
            self.setEnabledEverthingButUnseeded(True)
            #self.setWatershedMethodToTurboOrRegionGrowing()

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

    def setWatershedMethodToTurboOrRegionGrowing_depricated(self):
        """
        Set the correct watershed method
        boundaries-input uint8: Turbo
        boundaries-input not uint8: RegionGrowing
        """
        '''
        op = self.topLevelOperatorView 
        # if boundaries has type uint8, then use Turbo, otherwise RegionGrowing
        if (op.Boundaries.meta.dtype == numpy.uint8):
            op.WSMethodIn.setValue("Turbo") 
        else:
            op.WSMethodIn.setValue("RegionGrowing") 
        '''
        pass

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
    # depricated
    ############################################################

    def assignSlotToLayer_depricated(self, toSlot, fromSlotMeta, array): 
        #TODO conversion to uint8 is ok?
        # conversion
        array           = array.astype(numpy.uint8)
        array           = addChannelAxis(array)
        # output sets
        toSlot.meta.assignFrom(fromSlotMeta.meta)
        #only one channel as output
        toSlot.meta.shape = fromSlotMeta.meta.shape[:-1] + (1,)
        toSlot.meta.drange = (0,255)
        toSlot.setValue(array)




    def generateSeeds_depricated(self):
        print "generate Seeds start"
        op = self.topLevelOperatorView 

        # get boundaries
        boundaries      = getArray(op.Boundaries)
        #boundaries     = boundaries.astype(np.float32)
        #sigma           = op.SmoothingSigma.value

        #cut off the channel dimension
        boundaries      = removeChannelAxis(boundaries)


        # Smoothing
        smoothedBoundaries  = self.getAndUseSmoothingMethod(boundaries)

        # for distance transform: seeds.dtype === uint32 or float? but not uint8
        smoothedBoundaries  = smoothedBoundaries.astype(numpy.float32)


        # Compute here: distance transform
        #seeds           = vigra.filters.distanceTransform(seeds)
        seeds               = self.getAndUseComputeMethod(smoothedBoundaries)

        # label the seeds 
        # TODO TODO TODO label array depending on slicing or not Depends on Execute, etc, so don't do it here
        seeds  = seeds.astype(numpy.uint8)
        labeled_seeds = vigra.analysis.labelMultiArrayWithBackground(seeds)


        #self.assignSlotToLayer(op.GeneratedSeeds, op.Boundaries, labeled_seeds)
        #self.assignSlotToLayer(op.GeneratedSeeds, op.Boundaries, seeds)

        # refresh the layers
        #self.updateAllLayers()


        print "generate Seeds end"

    def slicedMinOrMax(self, boundaries, tAxis, function, marker=1):
        # not used anymore, because only one t or all, with execute
        #TODO docu
        """
        uses Maxima for the main algorithm execution
        but slices the data for it, so that that algorithm can be used easily

        :param boundaries: the array, that contains the boundaries data
        :param seeds: the array, that contains the seeds data
        :param tAxis: the dimension number of the time axis
        :return: labelImageArray: the concatenated watershed result of all slices 
        """

            
        labelImageArray = np.ndarray(shape=boundaries.shape, dtype=boundaries.dtype)
        for i in range(boundaries.shape[tAxis]):
            # iterate over the axis of the time
            boundariesSlice  = boundaries.take( i, axis=tAxis)

            labelImage           = function(boundariesSlice, marker=marker)

            # write in the correct column of the output array, 
            # because the dimensions must fit
            if (tAxis == 0):
                labelImageArray[i] = labelImage
            elif (tAxis == 1):
                labelImageArray[:,i] = labelImage
            elif (tAxis == 2):
                labelImageArray[:,:,i] = labelImage
            elif (tAxis == 3):
                labelImageArray[:,:,:,i] = labelImage
        return labelImageArray

    def MinOrMax_depricated(self, boundaries, functionName="Minimum", tUsed=False, tAxis=0):
        #TODO docu
        diff = 0
        if tUsed:
            diff = 1
        if functionName == "Minimum":
            if (boundaries.ndim - diff == 2):
                function = vigra.analysis.extendedLocalMinima
            else:
                function = vigra.analysis.extendedLocalMinima3D
        else:
            if (boundaries.ndim - diff == 2):
                function = vigra.analysis.extendedLocalMaxima
            else:
                function = vigra.analysis.extendedLocalMaxima3D

        marker = 1
        if tUsed:
            return self.slicedMinOrMax(boundaries, tAxis, function=function, marker=marker)
        else:
            return function(boundaries, marker=marker)




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


        # TestMe
        self._initLayer(op.TestMe,          "TestMe",     layers, visible=False,
                layerFunction=self.createGrayscaleLayer) 

        '''
        # only display Seeds if no Generated Seeds are supplied
        if not op.GeneratedSeeds.ready():
            self._initLayer(op.Seeds,                "Seeds",        layers, opacity=0.5)

        self._initLayer(op.GeneratedSeeds,       "Generated Seeds",        layers,  opacity=0.5)
        '''
        self._initLayer(op.SeedsOut,            "Seeds",        layers,  opacity=0.5)

        self._initLayer(op.Smoothing,            "Smoothing",        layers, opacity=0.5,
                layerFunction=self.createGrayscaleLayer) 
        self._initLayer(op.Compute,            "Compute",        layers,
                layerFunction=self.createGrayscaleLayer) 
        
        # Boundaries
        self._initLayer(op.Boundaries,       "Boundaries",   layers, opacity=0.5, 
                layerFunction=self.createGrayscaleLayer) 


        # Raw Data
        self._initLayer(op.RawData,          "Raw Data",     layers, 
                layerFunction=self.createStandardLayerFromSlot ) 



        return layers
