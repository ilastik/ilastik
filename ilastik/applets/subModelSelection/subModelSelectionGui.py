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
#		   http://ilastik.org/license.html
###############################################################################
import os

from PyQt4 import uic
from PyQt4.QtGui import QVBoxLayout, QSpacerItem, QSizePolicy

from volumina.widgets.subModelSelectionWidget import SubModelSelectionWidget
#from volumina.imageView2D import ImageView2D
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.widgets.cropListView import CropListView
from ilastik.applets.cropping.croppingGui import CroppingGui

class SubModelSelectionGui(LayerViewerGui):
#class SubModelSelectionGui(CroppingGui):
    """
    Sub model selection applet
    """
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def appletDrawer(self):
        return self._drawer

    def __init__(self, parentApplet, topLevelOperatorView):
        """
        """
        self.topLevelOperatorView = topLevelOperatorView






        # Tell our base class which slots to monitor
        #cropSlots = CroppingGui.CroppingSlots()
        #cropSlots.cropInput = topLevelOperatorView.CropInputs
        #cropSlots.cropOutput = topLevelOperatorView.CropImages
        #cropSlots.cropEraserValue = None#topLevelOperatorView.opCropPipeline.opCropArray.eraser
        #cropSlots.cropDelete = None#topLevelOperatorView.opCropPipeline.DeleteCrop
        #cropSlots.cropNames = topLevelOperatorView.CropNames
        #cropSlots.cropsAllowed = topLevelOperatorView.CropsAllowedFlags

        # We provide our own UI file (which adds an extra control for interactive mode)
        #croppingDrawerUiPath = os.path.split(__file__)[0] + '/croppingDrawer.ui'

        #super(SubModelSelectionGui, self).__init__(parentApplet, cropSlots, self.topLevelOperatorView, croppingDrawerUiPath)




        super(SubModelSelectionGui, self).__init__(parentApplet, self.topLevelOperatorView)
        self.subModels = []

    def initAppletDrawerUi(self):
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        self.subModelSelectionWidget = SubModelSelectionWidget(self)
        data_has_z_axis = True
        if self.topLevelOperatorView.InputImage.ready():
            tShape = self.topLevelOperatorView.InputImage.meta.getTaggedShape()
            if not 'z' in tShape or tShape['z']==1:
                data_has_z_axis = False

        self.subModelSelectionWidget._minSliderZ.setVisible(data_has_z_axis)
        self.subModelSelectionWidget._maxSliderZ.setVisible(data_has_z_axis)
        self.subModelSelectionWidget._minSpinZ.setVisible(data_has_z_axis)
        self.subModelSelectionWidget._maxSpinZ.setVisible(data_has_z_axis)
        self.subModelSelectionWidget.labelMinZ.setVisible(data_has_z_axis)
        self.subModelSelectionWidget.labelMaxZ.setVisible(data_has_z_axis)

        self.subModelSelectionWidget.NewCropButton.clicked.connect( self.apply_gui_settings_to_operator )
        self.subModelSelectionWidget.NewCropButton.clicked.connect( self.apply_gui_settings_to_operator )

        self.topLevelOperatorView.MinValueT.notifyDirty(self.apply_operator_settings_to_gui)
        self.topLevelOperatorView.MaxValueT.notifyDirty(self.apply_operator_settings_to_gui)
        self.topLevelOperatorView.MinValueX.notifyDirty(self.apply_operator_settings_to_gui)
        self.topLevelOperatorView.MaxValueX.notifyDirty(self.apply_operator_settings_to_gui)
        self.topLevelOperatorView.MinValueY.notifyDirty(self.apply_operator_settings_to_gui)
        self.topLevelOperatorView.MaxValueY.notifyDirty(self.apply_operator_settings_to_gui)
        self.topLevelOperatorView.MinValueZ.notifyDirty(self.apply_operator_settings_to_gui)
        self.topLevelOperatorView.MaxValueZ.notifyDirty(self.apply_operator_settings_to_gui)

        self.topLevelOperatorView.InputImage.notifyDirty(self.setDefaultValues)
        self.topLevelOperatorView.PredictionImage.notifyDirty(self.setDefaultValues)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget( self.subModelSelectionWidget )
        layout.addSpacerItem( QSpacerItem(0,0,vPolicy=QSizePolicy.Expanding) )

        self._drawer.setLayout( layout )
        print "==================================>",self.subModelSelectionWidget._cropListView

        self.setDefaultValues()
        self.apply_operator_settings_to_gui()

        self.editor.showCropLines(True)
        self.editor.cropModel.changed.connect(self.onCropModelChanged)
        self.editor.posModel.timeChanged.connect(self.updateTime)
        self.subModelSelectionWidget._minSliderT.valueChanged.connect(self._onMinSliderTMoved)
        self.subModelSelectionWidget._maxSliderT.valueChanged.connect(self._onMaxSliderTMoved)
        self.subModelSelectionWidget._minSliderX.valueChanged.connect(self._onMinSliderXMoved)
        self.subModelSelectionWidget._maxSliderX.valueChanged.connect(self._onMaxSliderXMoved)
        self.subModelSelectionWidget._minSliderY.valueChanged.connect(self._onMinSliderYMoved)
        self.subModelSelectionWidget._maxSliderY.valueChanged.connect(self._onMaxSliderYMoved)
        self.subModelSelectionWidget._minSliderZ.valueChanged.connect(self._onMinSliderZMoved)
        self.subModelSelectionWidget._maxSliderZ.valueChanged.connect(self._onMaxSliderZMoved)

    def createSubModel(self):
        try:
            print "=====>", self.get_roi_4d(), self.numSubModels(), self.subModels
            newSubModel = ["Sub Model "+str(self.numSubModels() + 1),self.get_roi_4d()]
            self.subModels += [newSubModel]
            print "----->", self.get_roi_4d(), self.numSubModels(), self.subModels

            self.subModelSelectionWidget._cropListView
        except:
            print " ERROR: Structured Learning: Failed to create sub model!"

    def numSubModels(self):
        return len(self.subModels)

    def get_roi_4d(self):
        return [(self.topLevelOperatorView.MinValueT.value,self.topLevelOperatorView.MinValueX.value,self.topLevelOperatorView.MinValueY.value,self.topLevelOperatorView.MinValueZ.value),
                (self.topLevelOperatorView.MaxValueT.value,self.topLevelOperatorView.MaxValueX.value,self.topLevelOperatorView.MaxValueY.value,self.topLevelOperatorView.MaxValueZ.value)]

    def updateTime(self):
        delta = self.subModelSelectionWidget._minSliderT.value() - self.editor.posModel.time
        if delta > 0:
            self.editor.navCtrl.changeTimeRelative(delta)
        else:
            delta = self.subModelSelectionWidget._maxSliderT.value() - self.editor.posModel.time
            if delta < 0:
                self.editor.navCtrl.changeTimeRelative(delta)

    def _onMinSliderTMoved(self):
        delta = self.subModelSelectionWidget._minSliderT.value() - self.editor.posModel.time
        if delta > 0:
            self.editor.navCtrl.changeTimeRelative(delta)
        self.topLevelOperatorView.MinValueT.setValue(self.subModelSelectionWidget._minSliderT.value())

    def _onMaxSliderTMoved(self):
        delta = self.subModelSelectionWidget._maxSliderT.value() - self.editor.posModel.time
        if delta < 0:
            self.editor.navCtrl.changeTimeRelative(delta)
        self.topLevelOperatorView.MaxValueT.setValue(self.subModelSelectionWidget._maxSliderT.value())

    def _onMinSliderXMoved(self):
        [(minValueX,minValueY,minValueZ),(maxValueX,maxValueY,maxValueZ)] = self.editor.cropModel.get_roi_3d()
        self.editor.cropModel.set_roi_3d([(self.subModelSelectionWidget._minSliderX.value(),minValueY,minValueZ),(maxValueX,maxValueY,maxValueZ)])

    def _onMaxSliderXMoved(self):
        [(minValueX,minValueY,minValueZ),(maxValueX,maxValueY,maxValueZ)] = self.editor.cropModel.get_roi_3d()
        self.editor.cropModel.set_roi_3d([(minValueX,minValueY,minValueZ),(self.subModelSelectionWidget._maxSliderX.value()+1,maxValueY,maxValueZ)])

    def _onMinSliderYMoved(self):
        [(minValueX,minValueY,minValueZ),(maxValueX,maxValueY,maxValueZ)] = self.editor.cropModel.get_roi_3d()
        self.editor.cropModel.set_roi_3d([(minValueX,self.subModelSelectionWidget._minSliderY.value(),minValueZ),(maxValueX,maxValueY,maxValueZ)])

    def _onMaxSliderYMoved(self):
        [(minValueX,minValueY,minValueZ),(maxValueX,maxValueY,maxValueZ)] = self.editor.cropModel.get_roi_3d()
        self.editor.cropModel.set_roi_3d([(minValueX,minValueY,minValueZ),(maxValueX,self.subModelSelectionWidget._maxSliderY.value()+1,maxValueZ)])

    def _onMinSliderZMoved(self):
        [(minValueX,minValueY,minValueZ),(maxValueX,maxValueY,maxValueZ)] = self.editor.cropModel.get_roi_3d()
        self.editor.cropModel.set_roi_3d([(minValueX,minValueY,self.subModelSelectionWidget._minSliderZ.value()),(maxValueX,maxValueY,maxValueZ)])

    def _onMaxSliderZMoved(self):
        [(minValueX,minValueY,minValueZ),(maxValueX,maxValueY,maxValueZ)] = self.editor.cropModel.get_roi_3d()
        self.editor.cropModel.set_roi_3d([(minValueX,minValueY,minValueZ),(maxValueX,maxValueY,self.subModelSelectionWidget._maxSliderZ.value()+1)])

    def onCropModelChanged(self):
        starts, stops = self.editor.cropModel.get_roi_3d()
        for dim, start, stop in zip("xyz", starts, stops):
            if dim=='x':
                self.topLevelOperatorView.MinValueX.setValue(start)
                self.topLevelOperatorView.MaxValueX.setValue(stop)
            elif dim=='y':
                self.topLevelOperatorView.MinValueY.setValue(start)
                self.topLevelOperatorView.MaxValueY.setValue(stop)
            elif dim=='z':
                self.topLevelOperatorView.MinValueZ.setValue(start)
                self.topLevelOperatorView.MaxValueZ.setValue(stop)
            else:
                print "MY ERROR: Setting up an axis that does NOT exist!"

        return [[start, stop] for dim, start, stop in zip("xyz", starts, stops)]

    def apply_operator_settings_to_gui(self,*args):
        minValueT, maxValueT, minValueX, maxValueX, minValueY, maxValueY, minValueZ, maxValueZ = [0]*8

        inputImageSlot = self.topLevelOperatorView.InputImage
        tagged_shape = inputImageSlot.meta.getTaggedShape()

        self.editor.posModel.shape5D = [tagged_shape['t'],tagged_shape['x'],tagged_shape['y'],tagged_shape['z'],tagged_shape['c']]

        # t
        if self.topLevelOperatorView.MinValueT.ready():
            minValueT = self.topLevelOperatorView.MinValueT.value
        if self.topLevelOperatorView.MaxValueT.ready():
            maxValueT = self.topLevelOperatorView.MaxValueT.value
        if maxValueT == 0:
            maxValueT =  tagged_shape['t']-1

        # x
        if self.topLevelOperatorView.MinValueX.ready():
            minValueX = self.topLevelOperatorView.MinValueX.value
        if self.topLevelOperatorView.MaxValueX.ready():
            maxValueX = self.topLevelOperatorView.MaxValueX.value

        # y
        if self.topLevelOperatorView.MinValueY.ready():
            minValueY = self.topLevelOperatorView.MinValueY.value
        if self.topLevelOperatorView.MaxValueY.ready():
            maxValueY = self.topLevelOperatorView.MaxValueY.value

        # z
        if self.topLevelOperatorView.MinValueZ.ready():
            minValueZ = self.topLevelOperatorView.MinValueZ.value
        if self.topLevelOperatorView.MaxValueZ.ready():
            maxValueZ = self.topLevelOperatorView.MaxValueZ.value

        self.editor.cropModel.set_roi_3d([(minValueX,minValueY,minValueZ),(maxValueX,maxValueY,maxValueZ)])
        self.subModelSelectionWidget.setValue(minValueT, maxValueT, minValueX, maxValueX-1, minValueY, maxValueY-1, minValueZ, maxValueZ-1)
        self.updateTime()

    def setTimeValues(self, minValueT, maxValueT):
        self.topLevelOperatorView.MinValueT.setValue(minValueT)
        self.topLevelOperatorView.MaxValueT.setValue(maxValueT)

    def setValues(self, minValueT, maxValueT, minValueX, maxValueX, minValueY, maxValueY, minValueZ, maxValueZ):
        self.topLevelOperatorView.MinValueT.setValue(minValueT)
        self.topLevelOperatorView.MaxValueT.setValue(maxValueT)
        self.topLevelOperatorView.MinValueX.setValue(minValueX)
        self.topLevelOperatorView.MaxValueX.setValue(maxValueX)
        self.topLevelOperatorView.MinValueY.setValue(minValueY)
        self.topLevelOperatorView.MaxValueY.setValue(maxValueY)
        self.topLevelOperatorView.MinValueZ.setValue(minValueZ)
        self.topLevelOperatorView.MaxValueZ.setValue(maxValueZ)

    def apply_gui_settings_to_operator(self, ):
        minValueT, maxValueT, minValueX, maxValueX, minValueY, maxValueY, minValueZ, maxValueZ = self.subModelSelectionWidget.getValues()
        self.topLevelOperatorView.MinValueT.setValue(minValueT)
        self.topLevelOperatorView.MaxValueT.setValue(maxValueT)

        self.topLevelOperatorView.MinValueX.setValue(minValueX)
        self.topLevelOperatorView.MaxValueX.setValue(maxValueX+1)

        self.topLevelOperatorView.MinValueY.setValue(minValueY)
        self.topLevelOperatorView.MaxValueY.setValue(maxValueY+1)

        self.topLevelOperatorView.MinValueZ.setValue(minValueZ)
        self.topLevelOperatorView.MaxValueZ.setValue(maxValueZ+1)

        self.createSubModel()

    def setupLayers(self):
        """
        Overridden from LayerViewerGui.
        Create a list of all layer objects that should be displayed.
        """
        layers = []

        cropImageSlot = self.topLevelOperatorView.CropImage
        if cropImageSlot.ready():
            cropImageLayer = self.createStandardLayerFromSlot( cropImageSlot )
            cropImageLayer.name = "Sub-Model"
            cropImageLayer.visible = False #True
            cropImageLayer.opacity = 0.25
            layers.append(cropImageLayer)

        # Show the prediction data
        predictionImageSlot = self.topLevelOperatorView.PredictionImage
        if predictionImageSlot.ready():
            inputPredictionLayer = self.createStandardLayerFromSlot( predictionImageSlot )
            inputPredictionLayer.name = "Prediction Input"
            inputPredictionLayer.visible = False
            inputPredictionLayer.opacity = 0.75
            layers.append(inputPredictionLayer)

        # Show the raw input data
        inputImageSlot = self.topLevelOperatorView.InputImage
        if inputImageSlot.ready():
            #print " ..... SLT .....> in if inputImageSlot.ready()"
            inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
            inputLayer.name = "Raw Input"
            inputLayer.visible = True
            inputLayer.opacity = 0.75
            layers.append(inputLayer)

        return layers

    def defaultRangeValues(self):
        inputImageSlot = self.topLevelOperatorView.InputImage

        if not inputImageSlot.ready():
            return [0]*8

        tagged_shape = inputImageSlot.meta.getTaggedShape()
        minValueT = 0
        maxValueT = tagged_shape['t']

        # x
        minValueX = 0
        maxValueX = tagged_shape['x']

        # y
        minValueY = 0
        maxValueY = tagged_shape['y']

        # z
        minValueZ = 0
        maxValueZ = tagged_shape['z']

        return minValueT,maxValueT-1,minValueX,maxValueX-1,minValueY,maxValueY-1,minValueZ,maxValueZ-1

    def defaultValues(self):
        inputImageSlot = self.topLevelOperatorView.InputImage
        if not inputImageSlot.ready():
            return [0]*8

        tagged_shape = inputImageSlot.meta.getTaggedShape()
        minValueT = 0
        maxValueT = tagged_shape['t'] - 1

        if self.topLevelOperatorView.MinValueT.ready():
            minValueTnew = self.topLevelOperatorView.MinValueT.value
        else:
            minValueTnew = 0

        if self.topLevelOperatorView.MaxValueT.ready():
            maxValueTnew = self.topLevelOperatorView.MaxValueT.value
        else:
            maxValueTnew = tagged_shape['t'] - 1

        minValueT = max(minValueT,minValueTnew)
        maxValueT = min(maxValueT,maxValueTnew)

        # x
        if self.topLevelOperatorView.MinValueX.ready():
            minValueX = self.topLevelOperatorView.MinValueX.value
        else:
            minValueX = 0
        if self.topLevelOperatorView.MaxValueX.ready():
            maxValueX = self.topLevelOperatorView.MaxValueX.value
        else:
            maxValueX = tagged_shape['x'] - 1

        # y
        if self.topLevelOperatorView.MinValueY.ready():
            minValueY = self.topLevelOperatorView.MinValueY.value
        else:
            minValueY = 0
        if self.topLevelOperatorView.MaxValueY.ready():
            maxValueY = self.topLevelOperatorView.MaxValueY.value
        else:
            maxValueY = tagged_shape['y'] - 1

  # z
        if self.topLevelOperatorView.MinValueZ.ready():
            minValueZ = self.topLevelOperatorView.MinValueZ.value
        else:
            minValueZ = 0
        if self.topLevelOperatorView.MaxValueZ.ready():
            maxValueZ = self.topLevelOperatorView.MaxValueZ.value
        else:
            maxValueZ = tagged_shape['z'] - 1
        self.setValues(minValueT,maxValueT,minValueX,maxValueX,minValueY,maxValueY,minValueZ,maxValueZ)
        return minValueT,maxValueT,minValueX,maxValueX,minValueY,maxValueY,minValueZ,maxValueZ

    def setDefaultValues(self,*args):
        minValueT,maxValueT,minValueX,maxValueX,minValueY,maxValueY,minValueZ,maxValueZ = self.defaultRangeValues()
        self.subModelSelectionWidget.setRange(minValueT, maxValueT, minValueX, maxValueX, minValueY, maxValueY, minValueZ, maxValueZ)

        minValueT,maxValueT,minValueX,maxValueX,minValueY,maxValueY,minValueZ,maxValueZ = self.defaultValues()
        self.subModelSelectionWidget.setValue(minValueT, maxValueT, minValueX, maxValueX-1, minValueY, maxValueY-1, minValueZ, maxValueZ-1)
