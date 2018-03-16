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
from builtins import range
from functools import partial
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QMenu, QWidgetAction, QLabel
from PyQt5.QtGui import QColor, QIcon


from volumina.api import LazyflowSource, ColortableLayer
import volumina.colortables as colortables

from lazyflow.operators.generic import axisTagsToString
from lazyflow.rtype import SubRegion

import logging
import os
import numpy as np
import vigra
import h5py
from ilastik.applets.labeling.labelingGui import LabelingGui
from ilastik.applets.tracking.base.trackingUtilities import relabel,write_events
from volumina.layer import GrayscaleLayer
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

from ilastik.config import cfg as ilastik_config
from lazyflow.request.request import Request
from ilastik.utility.gui.threadRouter import threadRouted
from ilastik.utility.gui.titledMenu import TitledMenu
from ilastik.utility import log_exception
from ilastik.shell.gui.ipcManager import IPCFacade, Protocol


logger = logging.getLogger(__name__)

class TrackingBaseGui( LayerViewerGui ):
    """
    """

    withMergers=False

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################            

    def appletDrawer( self ):
        return self._drawer

    def stopAndCleanUp( self ):
        super( TrackingBaseGui, self ).stopAndCleanUp()


    ###########################################
    ###########################################

    def __init__(self, parentApplet, topLevelOperatorView):
        """
        """
        self._initColors()

        self.topLevelOperatorView = topLevelOperatorView
        super(TrackingBaseGui, self).__init__(parentApplet, topLevelOperatorView)
        self.mainOperator = topLevelOperatorView

        # get the applet reference from the workflow (needed for the progressSignal)
        self.applet = self.mainOperator.parent.parent.trackingApplet


    def setupLayers( self ):
        layers = []

        # use same colortable for the following two generated layers: the merger
        # and the tracking layer
        self.tracking_colortable = colortables.create_random_16bit()
        self.tracking_colortable[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        self.tracking_colortable[1] = QColor(128,128,128,255).rgba() # misdetections have id 1 and will be indicated by grey

        self.merger_colortable = colortables.create_default_16bit()
        for i in range(7):
            self.merger_colortable[i] = self.mergerColors[i].rgba()

        if "MergerOutput" in self.topLevelOperatorView.outputs:
            parameters = self.mainOperator.Parameters.value

            if 'withMergerResolution' in list(parameters.keys()) and not parameters['withMergerResolution']:
                merger_ct = self.merger_colortable
            else:
                merger_ct = self.tracking_colortable
                
            # Using same color table for tracking with and without mergers (Is there any reason for using different color tables?)
            merger_ct = self.tracking_colortable

            if self.topLevelOperatorView.MergerCachedOutput.ready():
                self.mergersrc = LazyflowSource( self.topLevelOperatorView.MergerCachedOutput )
            else:
                self.mergersrc = LazyflowSource( self.topLevelOperatorView.zeroProvider.Output )

            mergerLayer = ColortableLayer( self.mergersrc, merger_ct )
            mergerLayer.name = "Merger"

            if 'withMergerResolution' in list(parameters.keys()) and not parameters['withMergerResolution']:
                mergerLayer.visible = True
            else:
                mergerLayer.visible = False

            layers.append(mergerLayer)

        if self.topLevelOperatorView.CachedOutput.ready():
            self.trackingsrc = LazyflowSource( self.topLevelOperatorView.CachedOutput )
            trackingLayer = ColortableLayer( self.trackingsrc, self.tracking_colortable )
            trackingLayer.name = "Tracking"
            trackingLayer.visible = True
            trackingLayer.opacity = 1.0
            layers.append(trackingLayer)

        elif self.topLevelOperatorView.zeroProvider.Output.ready():
            # provide zeros while waiting for the tracking result
            self.trackingsrc = LazyflowSource( self.topLevelOperatorView.zeroProvider.Output )
            trackingLayer = ColortableLayer( self.trackingsrc, self.tracking_colortable )
            trackingLayer.name = "Tracking"
            trackingLayer.visible = True
            trackingLayer.opacity = 1.0
            layers.append(trackingLayer)

        if "RelabeledImage" in self.topLevelOperatorView.outputs:
            if self.topLevelOperatorView.RelabeledCachedOutput.ready():
                self.objectssrc = LazyflowSource( self.topLevelOperatorView.RelabeledCachedOutput )
            else:
                self.objectssrc = LazyflowSource( self.topLevelOperatorView.zeroProvider.Output )
        else:
            if self.topLevelOperatorView.LabelImage.ready():
                self.objectssrc = LazyflowSource( self.topLevelOperatorView.LabelImage )
        ct = colortables.create_random_16bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        objLayer = ColortableLayer( self.objectssrc, ct )
        objLayer.name = "Objects"
        objLayer.opacity = 1.0
        objLayer.visible = False
        layers.append(objLayer)

        if self.mainOperator.RawImage.ready():
            rawLayer = self.createStandardLayerFromSlot(self.mainOperator.RawImage)
            rawLayer.name = "Raw"
            layers.insert( len(layers), rawLayer )


        if self.topLevelOperatorView.LabelImage.meta.shape:
            maxt = self.topLevelOperatorView.LabelImage.meta.shape[0] - 1
            maxx = self.topLevelOperatorView.LabelImage.meta.shape[1] - 1
            maxy = self.topLevelOperatorView.LabelImage.meta.shape[2] - 1
            maxz = self.topLevelOperatorView.LabelImage.meta.shape[3] - 1

            if not self.mainOperator.Parameters.ready():
                raise Exception("Parameter slot is not ready")

            parameters = self.mainOperator.Parameters.value
            self._setRanges()
            if 'size_range' in parameters:
                self._drawer.to_size.setValue(parameters['size_range'][1]-1)
                self._drawer.from_size.setValue(parameters['size_range'][0])
            else:
                self._drawer.from_size.setValue(0)
                self._drawer.to_size.setValue(10000)

            if 'x_range' in parameters:
                self._drawer.to_x.setValue(parameters['x_range'][1]-1)
                self._drawer.from_x.setValue(parameters['x_range'][0])
            else:
                self._drawer.from_x.setValue(0)
                self._drawer.to_x.setValue(maxx)

            if 'y_range' in parameters:
                self._drawer.to_y.setValue(parameters['y_range'][1]-1)
                self._drawer.from_y.setValue(parameters['y_range'][0])
            else:
                self._drawer.from_y.setValue(0)
                self._drawer.to_y.setValue(maxy)

            if 'z_range' in parameters:
                self._drawer.to_z.setValue(parameters['z_range'][1]-1)
                self._drawer.from_z.setValue(parameters['z_range'][0])
            else:
                self._drawer.from_z.setValue(0)
                self._drawer.to_z.setValue(maxz)

            if 'time_range' in parameters:
                self._drawer.to_time.setValue(parameters['time_range'][1])
                self._drawer.from_time.setValue(parameters['time_range'][0])
            else:
                self._drawer.from_time.setValue(0)
                self._drawer.to_time.setValue(maxt)

            if 'scales' in parameters:
                self._drawer.x_scale.setValue(parameters['scales'][0])
                self._drawer.y_scale.setValue(parameters['scales'][1])
                self._drawer.z_scale.setValue(parameters['scales'][2])
            else:
                self._drawer.x_scale.setValue(1)
                self._drawer.y_scale.setValue(1)
                self._drawer.z_scale.setValue(1)


        return layers


    def _setRanges(self):
        maxt = self.topLevelOperatorView.LabelImage.meta.shape[0] - 1
        maxx = self.topLevelOperatorView.LabelImage.meta.shape[1] - 1
        maxy = self.topLevelOperatorView.LabelImage.meta.shape[2] - 1
        maxz = self.topLevelOperatorView.LabelImage.meta.shape[3] - 1

        from_time = self._drawer.from_time
        to_time = self._drawer.to_time
        from_x = self._drawer.from_x
        to_x = self._drawer.to_x
        from_y = self._drawer.from_y
        to_y = self._drawer.to_y
        from_z = self._drawer.from_z
        to_z = self._drawer.to_z

        from_time.setRange(0, to_time.value()-1)
        to_time.setRange(from_time.value()+1,maxt)

        from_x.setRange(0,to_x.value())
        to_x.setRange(from_x.value(),maxx)

        from_y.setRange(0,to_y.value())
        to_y.setRange(from_y.value(),maxy)

        from_z.setRange(0,to_z.value())
        to_z.setRange(from_z.value(),maxz)


    # TODO Remove the following code together with the labels in the GUI as it
    # is no longer needed. The merger colors are now determined by the track id
    # and therefore by the colormap of the tracking layer.
    def _initColors(self):
        self.mergerColors = colortables.default16_new
        self.mergerColors.insert(0, QColor(0, 0, 0, 0).rgba()) # 0 and 1 must be transparent

    def _labelSetStyleSheet(self, qlabel, qcolor):
        qlabel.setAutoFillBackground(True)
        values = "{r}, {g}, {b}, {a}".format(r = qcolor.red(),
                                     g = qcolor.green(),
                                     b = qcolor.blue(),
                                     a = qcolor.alpha()
                                     )
        qlabel.setStyleSheet("QLabel { color: rgba(0,0,0,255); background-color: rgba("+values+"); }")

    def _loadUiFile(self):
        raise NotImplementedError

    def initAppletDrawerUi(self):
        self._drawer = self._loadUiFile()

        if not ilastik_config.getboolean("ilastik", "debug"):
            self._drawer.exportLabel.hide()
            self._drawer.exportTifButton.hide()

        trackIconPath = os.path.split(__file__)[0] + "/icons/trackIcon.png"
        trackIcon = QIcon(trackIconPath)
        self._drawer.TrackButton.setIcon(trackIcon)

        self._drawer.TrackButton.pressed.connect(self._onTrackButtonPressed)

        self._drawer.from_time.valueChanged.connect(self._setRanges)
        self._drawer.from_x.valueChanged.connect(self._setRanges)
        self._drawer.from_y.valueChanged.connect(self._setRanges)
        self._drawer.from_z.valueChanged.connect(self._setRanges)
        self._drawer.to_time.valueChanged.connect(self._setRanges)
        self._drawer.to_x.valueChanged.connect(self._setRanges)
        self._drawer.to_y.valueChanged.connect(self._setRanges)
        self._drawer.to_z.valueChanged.connect(self._setRanges)


    def _onTrackButtonPressed( self ):
        raise NotImplementedError


    def handleThresholdGuiValuesChanged(self, minVal, maxVal):
        self.mainOperator.MinValue.setValue(minVal)
        self.mainOperator.MaxValue.setValue(maxVal)


    def _setLayerVisible(self, name, visible):
        for layer in self.layerstack:
            if layer.name is name:
                layer.visible = visible

    @threadRouted
    def _criticalMessage(self, prompt):
        QMessageBox.critical(self, "Error", str(prompt), buttons=QMessageBox.Ok)

    def get_object(self, pos5d):
        slicing = tuple(slice(i, i+1) for i in pos5d)
        label = self.mainOperator.LabelImage(slicing).wait()
        return label.flat[0], pos5d[0]
