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
from volumina.imageView2D import ImageView2D
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.widgets.subModelListView import SubModelListView

class SubModelSelectionGui(LayerViewerGui):
    """
    Sub model selection applet
    """
    #print " ..... SLT .....> in SubModelSelectionGui"

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def appletDrawer(self):
        return self._drawer

    # (Other methods already provided by our base class)

    ###########################################
    ###########################################

    def __init__(self, parentApplet, topLevelOperatorView):
        """
        """
        #print " ..... SLT .....> in __init__ SubModelSelectionGui"
        self.topLevelOperatorView = topLevelOperatorView
        super(SubModelSelectionGui, self).__init__(parentApplet, self.topLevelOperatorView)
        self.subModels = []

    def initAppletDrawerUi(self):
        #print " ..... SLT .....> in initAppletDrawerUi SubModelSelectionGui"
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        # Init sub-model selection widget
        #print "/////////////////////////////// >",
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

        #self.subModelSelectionWidget.valueChanged.connect( self.apply_gui_settings_to_operator )

        self.subModelSelectionWidget.ApplyButton.clicked.connect( self.apply_gui_settings_to_operator )
        self.subModelSelectionWidget.ApplyButton.clicked.connect( self.apply_gui_settings_to_operator )

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

        # Add widget to a layout
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget( self.subModelSelectionWidget )
        layout.addSpacerItem( QSpacerItem(0,0,vPolicy=QSizePolicy.Expanding) )

        # Apply layout to the drawer
        self._drawer.setLayout( layout )

        # Initialize the gui with the operator's current values
        self.setDefaultValues()
        print "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<, apply_operator_settings_to_gui"
        self.apply_operator_settings_to_gui()

        #self.editor.newImageView2DFocus.connect(self.onCropShapeChanged)

        self.editor.showCropLines(True)
        self.editor.cropModel.changed.connect(self.onCropModelChanged)
        self.editor.posModel.timeChanged.connect(self.changeTime)

        #self.imageView2D = ImageView2D() #parent, cropModel, imagescene2d
        #viewportRect()
        #for view in self.editor.imageViews:
            #view.shapeChanged.connect(self.onCropShapeChanged)
            #print "my rectangles view.viewportRect()",view.viewportRect()

        #self.topLevelOperatorView.MinValueX.valueChanged.connect(self.onMinXChanged)

        self.subModelSelectionWidget._minSliderT.valueChanged.connect(self._onMinSliderTMoved)
        self.subModelSelectionWidget._maxSliderT.valueChanged.connect(self._onMaxSliderTMoved)
        self.subModelSelectionWidget._minSliderX.valueChanged.connect(self._onMinSliderXMoved)
        self.subModelSelectionWidget._maxSliderX.valueChanged.connect(self._onMaxSliderXMoved)
        self.subModelSelectionWidget._minSliderY.valueChanged.connect(self._onMinSliderYMoved)
        self.subModelSelectionWidget._maxSliderY.valueChanged.connect(self._onMaxSliderYMoved)
        self.subModelSelectionWidget._minSliderZ.valueChanged.connect(self._onMinSliderZMoved)
        self.subModelSelectionWidget._maxSliderZ.valueChanged.connect(self._onMaxSliderZMoved)

        #self.subModelSelectionWidget._subModelListView = SubModelListView(self)

    def createSubModel(self):
        print "              in createSubModel"
        try:
            # add a model
            print "0"
            newSubModel = ["Sub Model "+str(self.numSubModels() + 1),self.get_roi_4d()]
            print "1"
            self.subModels += newSubModel
            print ">>>> Sub Model Created", newSubModel

        except:
            print " ERROR: Structured Learning: Failed to create sub model!"

    def numSubModels(self):
        return len(self.subModels)

    def get_roi_4d(self):
        return [(self.topLevelOperatorView.MinValueT.value,self.topLevelOperatorView.MinValueX.value,self.topLevelOperatorView.MinValueY.value,self.topLevelOperatorView.MinValueZ.value),
                (self.topLevelOperatorView.MaxValueT.value,self.topLevelOperatorView.MaxValueX.value,self.topLevelOperatorView.MaxValueY.value,self.topLevelOperatorView.MaxValueZ.value)]

    def changeTime(self):
        print "---------------------------->change TIME"
        delta = self.subModelSelectionWidget._minSliderT.value() - self.editor.posModel.time
        print "delta", delta
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
        print("===== On crop model  CHANGED   -----   CURRENT CROP MODEL =====")
        for dim, start, stop in zip("xyz", starts, stops):
            #print(dim + ": {} to {}".format(start, stop))
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

        print "---->",[[start, stop] for dim, start, stop in zip("xyz", starts, stops)]
        return [[start, stop] for dim, start, stop in zip("xyz", starts, stops)]

#    def onMinXChanged(self):
#        self.editor.cropModel.set_roi_3d([(minValueX,minValueY,minValueZ),(maxValueX,maxValueY,maxValueZ)])
#        self.editor.cropModel.set_roi_3d([(minValueX,0,0),(99,99,99)])

#    def apply_model_settings_to_operator(self,*args):
#        self.topLevelOperatorView.MinValueT.setValue(self.editor.posModel.time)
#        self.topLevelOperatorView.MaxValueT.setValue(self.editor.posModel.time)
#
#        self.topLevelOperatorView.MinValueX.setValue()
#        self.topLevelOperatorView.MaxValueX.setValue()
#
#        self.topLevelOperatorView.MinValueY.setValue()
#        self.topLevelOperatorView.MaxValueY.setValue()
#
#        self.topLevelOperatorView.MinValueZ.setValue()
#        self.topLevelOperatorView.MaxValueZ.setValue()

    def apply_operator_settings_to_gui(self,*args):
        print ""
        print ""
        print ""
        print " ..... SLT .....> in apply_operator_settings_to_gui SubModelSelectionGui"
        minValueT, maxValueT, minValueX, maxValueX, minValueY, maxValueY, minValueZ, maxValueZ = [-1]*8

        # t
        print "is TIME min READY",self.topLevelOperatorView.MinValueT.ready()
        if self.topLevelOperatorView.MinValueT.ready():
            minValueT = self.topLevelOperatorView.MinValueT.value
        print "is TIME max READY",self.topLevelOperatorView.MaxValueT.ready()
        if self.topLevelOperatorView.MaxValueT.ready():
            maxValueT = self.topLevelOperatorView.MaxValueT.value
        self.setTimeValues(minValueT,maxValueT)

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

        print " TIME=",minValueT, maxValueT, minValueX, maxValueX, minValueY, maxValueY, minValueZ, maxValueZ
        self.editor.cropModel.set_roi_3d([(minValueX,minValueY,minValueZ),(maxValueX,maxValueY,maxValueZ)])
        self.subModelSelectionWidget.setValue(minValueT, maxValueT, minValueX, maxValueX-1, minValueY, maxValueY-1, minValueZ, maxValueZ-1)
        #print "............> roi   =",self.editor.cropModel.get_roi_3d()#[[minValueX,minValueY,minValueZ],[maxValueX,maxValueY,maxValueZ]])
        #print "............> values=",[[minValueX,minValueY,minValueZ],[maxValueX,maxValueY,maxValueZ]]
        #self.topLevelOperatorView.MinValueT.setValue(minValueT)
        #self.topLevelOperatorView.MaxValueT.setValue(maxValueT)

    def setTimeValues(self, minValueT, maxValueT):
        print " ..... SLT .....> in setTimeValues",minValueT, maxValueTgit

        self.topLevelOperatorView.MinValueT.setValue(minValueT)
        self.topLevelOperatorView.MaxValueT.setValue(maxValueT)

    def setValues(self, minValueT, maxValueT, minValueX, maxValueX, minValueY, maxValueY, minValueZ, maxValueZ):
        print " ..... SLT .....> in setValues"

        self.topLevelOperatorView.MinValueT.setValue(minValueT)
        self.topLevelOperatorView.MaxValueT.setValue(maxValueT)
        self.topLevelOperatorView.MinValueX.setValue(minValueX)
        self.topLevelOperatorView.MaxValueX.setValue(maxValueX)
        self.topLevelOperatorView.MinValueY.setValue(minValueY)
        self.topLevelOperatorView.MaxValueY.setValue(maxValueY)
        self.topLevelOperatorView.MinValueZ.setValue(minValueZ)
        self.topLevelOperatorView.MaxValueZ.setValue(maxValueZ)

    def apply_gui_settings_to_operator(self, ):
        print " ..... SLT .....> in apply_gui_settings_to_operator SubModelSelectionGui"

        minValueT, maxValueT, minValueX, maxValueX, minValueY, maxValueY, minValueZ, maxValueZ = self.subModelSelectionWidget.getValues()
        self.topLevelOperatorView.MinValueT.setValue(minValueT)
        self.topLevelOperatorView.MaxValueT.setValue(maxValueT)

        self.topLevelOperatorView.MinValueX.setValue(minValueX)
        self.topLevelOperatorView.MaxValueX.setValue(maxValueX+1)

        self.topLevelOperatorView.MinValueY.setValue(minValueY)
        self.topLevelOperatorView.MaxValueY.setValue(maxValueY+1)

        self.topLevelOperatorView.MinValueZ.setValue(minValueZ)
        self.topLevelOperatorView.MaxValueZ.setValue(maxValueZ+1)

        print "before createSubModel"
        self.createSubModel()
        print "after createSubModel"

        #self.updateAllLayers()

    def setupLayers(self):
        """
        Overridden from LayerViewerGui.
        Create a list of all layer objects that should be displayed.
        """
        layers = []

        #print " ..... SLT .....> in setupLayers SubModelSelectionGui"

        # Show the cropped data
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
            inputPredictionLayer = self.createStandardLayerFromSlot( predictionImageSlot ) ###xxx there are also other methods:greyScaleLayer or colorTableLayer... in Volumina
            #from volumina.layer import ColortableLayer, GrayscaleLayer, RGBALayer, ClickableColortableLayer
            inputPredictionLayer.name = "Prediction Input"
            inputPredictionLayer.visible = False
            inputPredictionLayer.opacity = 0.75
            layers.append(inputPredictionLayer)

        # Show the raw input data
        inputImageSlot = self.topLevelOperatorView.InputImage
        #print " ..... SLT .....> inputImageSlot.ready()=", inputImageSlot.ready()
        if inputImageSlot.ready():
            #print " ..... SLT .....> in if inputImageSlot.ready()"
            inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
            inputLayer.name = "Raw Input"
            inputLayer.visible = True
            inputLayer.opacity = 0.75
            layers.append(inputLayer)

        # Show the cropped prediction
        #cropPredictionSlot = self.topLevelOperatorView.CropPrediction
        #if cropPredictionSlot.ready():
        #    cropPredictionLayer = self.createStandardLayerFromSlot( cropPredictionSlot )
        #    cropPredictionLayer.name = "Cropped Prediction Input"
        #    cropPredictionLayer.visible = False #True
        #    cropPredictionLayer.opacity = 0.25
        #    layers.append(cropPredictionLayer)



        #print " ..... SLT .....> layers=", layers
        #print " ..... SLT .....> end setupLayers SubModelSelectionGui"

        return layers

    def defaultRangeValues(self):
        print "defaultRangeValues"
        inputImageSlot = self.topLevelOperatorView.InputImage

        if not inputImageSlot.ready():
            print "defaultRangeValues ---> ZEROS"
            return [0]*8

        tagged_shape = inputImageSlot.meta.getTaggedShape()
        #if self.topLevelOperatorView.MinValueT.ready():
        #    minValueT = self.topLevelOperatorView.MinValueT.value
        #else:
        minValueT = 0

        #if self.topLevelOperatorView.MaxValueT.ready():
        #    maxValueT = self.topLevelOperatorView.MaxValueT.value
        #else:
        maxValueT = tagged_shape['t'] - 1

        # x
        #if self.topLevelOperatorView.MinValueX.ready():
        #    minValueX = self.topLevelOperatorView.MinValueX.value
        #else:
        minValueX = 0

        #if self.topLevelOperatorView.MaxValueX.ready():
        #    maxValueX = self.topLevelOperatorView.MaxValueX.value
        #else:
        maxValueX = tagged_shape['x'] - 1

        # y
        #if self.topLevelOperatorView.MinValueY.ready():
        #    minValueY = self.topLevelOperatorView.MinValueY.value
        #else:
        minValueY = 0

        #if self.topLevelOperatorView.MaxValueY.ready():
        #    maxValueY = self.topLevelOperatorView.MaxValueY.value
        #else:
        maxValueY = tagged_shape['y'] - 1

  # z
        #if self.topLevelOperatorView.MinValueZ.ready():
        #    minValueZ = self.topLevelOperatorView.MinValueZ.value
        #else:
        minValueZ = 0

        #if self.topLevelOperatorView.MaxValueZ.ready():
        #    maxValueZ = self.topLevelOperatorView.MaxValueZ.value
        #else:
        maxValueZ = tagged_shape['z'] - 1

        print "defaultRangeValues ---> Image SHAPE",minValueT,maxValueT,minValueX,maxValueX,minValueY,maxValueY,minValueZ,maxValueZ

        return minValueT,maxValueT,minValueX,maxValueX,minValueY,maxValueY,minValueZ,maxValueZ

    def defaultValues(self):
        print "==========================defaultValues========================="
        #inputImageSlot = self.topLevelOperatorView.InputImage
        #cropImageSlot = self.editor.cropModel

        inputImageSlot = self.topLevelOperatorView.InputImage
        if not inputImageSlot.ready():
            print "defaultValues zeros"
            return [0]*8

        #print "cropImageSlot",cropImageSlot
        #if cropImageSlot==None:
        #    print "defaultValues ----> MAX RANGES"
        #    return self.defaultRangeValues()

        print "defaultValues ----> OPERATOR model"
        #[(minValueX,minValueY,minValueZ),(maxValueX,maxValueY,maxValueZ)] = self.editor.cropModel.get_roi_3d()

        #editor.quadview.statusBar.timeSpinBox.



        tagged_shape = inputImageSlot.meta.getTaggedShape()
        minValueT = 0#max(0,self.topLevelOperatorView.MinValueT.value)
        maxValueT = tagged_shape['t'] - 1
        self.setTimeValues(minValueT,maxValueT)

        if self.topLevelOperatorView.MinValueT.ready():
            minValueT = self.topLevelOperatorView.MinValueT.value
        else:
            minValueT = 0

        if self.topLevelOperatorView.MaxValueT.ready():
            maxValueT = self.topLevelOperatorView.MaxValueT.value
        else:
            maxValueT = tagged_shape['t'] - 1

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
                #minValueT = 0#max(0,self.topLevelOperatorView.MinValueT.value)
        #maxValueT = tagged_shape['t'] - 1

        #if inputImageSlot.ready():
        #    tagged_shape = inputImageSlot.meta.getTaggedShape()
        #    maxValueT = min(self.topLevelOperatorView.MaxValueT.value,tagged_shape['t'] - 1)
        #else:
        #    maxValueT = self.topLevelOperatorView.MaxValueT.value

#        minValueX = max(0,self.topLevelOperatorView.MinValueX.value)
#        if inputImageSlot.ready():
#            tagged_shape = inputImageSlot.meta.getTaggedShape()
#            maxValueX = min(self.topLevelOperatorView.MaxValueX.value,tagged_shape['t'] - 1)
#        else:
#            maxValueX = self.topLevelOperatorView.MaxValueX.value#
#
#
#
#        minValueY = self.topLevelOperatorView.MinValueY.value
#        maxValueY = self.topLevelOperatorView.MaxValueY.value
#        minValueZ = self.topLevelOperatorView.MinValueZ.value
#        maxValueZ = self.topLevelOperatorView.MaxValueZ.value
        print "?????????????????>",minValueT,maxValueT,minValueX,maxValueX,minValueY,maxValueY,minValueZ,maxValueZ
        return minValueT,maxValueT,minValueX,maxValueX,minValueY,maxValueY,minValueZ,maxValueZ

    def setDefaultValues(self,*args):
        print "setDefault RANGE Values"
        minValueT,maxValueT,minValueX,maxValueX,minValueY,maxValueY,minValueZ,maxValueZ = self.defaultRangeValues()
        self.subModelSelectionWidget.setRange(minValueT, maxValueT, minValueX, maxValueX, minValueY, maxValueY, minValueZ, maxValueZ)

        print "setDefault VALUES"
        minValueT,maxValueT,minValueX,maxValueX,minValueY,maxValueY,minValueZ,maxValueZ = self.defaultValues()
        #self.setValues(minValueT,maxValueT,minValueX,maxValueX,minValueY,maxValueY,minValueZ,maxValueZ)
        self.subModelSelectionWidget.setValue(minValueT, maxValueT, minValueX, maxValueX-1, minValueY, maxValueY-1, minValueZ, maxValueZ-1)

        print "TIME-----------------------",self.editor.posModel.time
        self.changeTime()
        print "TIME-----------------------",self.editor.posModel.time
        #self.apply_gui_settings_to_operator()

#    def onCropShapeChanged(self):
#        print " in onCropShapeChanged"
#        for view in self.editor.imageViews:
#            print "my rectangles view.viewportRect()",view.viewportRect()




