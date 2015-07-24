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
from functools import partial
from PyQt4.QtGui import QColor, QFileDialog, QMessageBox, QMenu, QWidgetAction, QLabel

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
from volumina.utility import encode_from_qstring
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

        if self.mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = self.mainOperator.LabelImage.meta.shape

        # get the applet reference from the workflow (needed for the progressSignal)
        self.applet = self.mainOperator.parent.parent.trackingApplet


    def setupLayers( self ):
        layers = []

        if "MergerOutput" in self.topLevelOperatorView.outputs:
            ct = colortables.create_default_8bit()
            for i in range(7):
                ct[i] = self.mergerColors[i].rgba()

            if self.topLevelOperatorView.MergerCachedOutput.ready():
                self.mergersrc = LazyflowSource( self.topLevelOperatorView.MergerCachedOutput )
            else:
                self.mergersrc = LazyflowSource( self.topLevelOperatorView.ZeroOutput )

            mergerLayer = ColortableLayer( self.mergersrc, ct )
            mergerLayer.name = "Merger"
            mergerLayer.visible = False
            layers.append(mergerLayer)

        ct = colortables.create_random_16bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        ct[1] = QColor(128,128,128,255).rgba() # misdetections have id 1 and will be indicated by grey

        if self.topLevelOperatorView.CachedOutput.ready():
            self.trackingsrc = LazyflowSource( self.topLevelOperatorView.CachedOutput )
            trackingLayer = ColortableLayer( self.trackingsrc, ct )
            trackingLayer.name = "Tracking"
            trackingLayer.visible = True
            trackingLayer.opacity = 1.0
            layers.append(trackingLayer)

        elif self.topLevelOperatorView.zeroProvider.Output.ready():
            # provide zeros while waiting for the tracking result
            self.trackingsrc = LazyflowSource( self.topLevelOperatorView.zeroProvider.Output )
            trackingLayer = ColortableLayer( self.trackingsrc, ct )
            trackingLayer.name = "Tracking"
            trackingLayer.visible = True
            trackingLayer.opacity = 1.0
            layers.append(trackingLayer)

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
            self.editor.dataShape = self.topLevelOperatorView.LabelImage.meta.shape

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


    def _initColors(self):
        self.mergerColors = [ QColor(c) for c in LabelingGui._createDefault16ColorColorTable()[1:] ]
        self.mergerColors[0] = QColor(0,0,0,0) # 0 and 1 must be transparent
        self.mergerColors[1] = QColor(0,0,0,0)

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

        self._drawer.TrackButton.pressed.connect(self._onTrackButtonPressed)
        self._drawer.exportButton.pressed.connect(self._onExportButtonPressed)
        self._drawer.exportTifButton.pressed.connect(self._onExportTifButtonPressed)

        self._drawer.from_time.valueChanged.connect(self._setRanges)
        self._drawer.from_x.valueChanged.connect(self._setRanges)
        self._drawer.from_y.valueChanged.connect(self._setRanges)
        self._drawer.from_z.valueChanged.connect(self._setRanges)
        self._drawer.to_time.valueChanged.connect(self._setRanges)
        self._drawer.to_x.valueChanged.connect(self._setRanges)
        self._drawer.to_y.valueChanged.connect(self._setRanges)
        self._drawer.to_z.valueChanged.connect(self._setRanges)



    def _onExportButtonPressed(self):
        options = QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog

        directory = encode_from_qstring(QFileDialog.getExistingDirectory(self, 'Select Directory',os.path.expanduser("~"), options=options))

        if directory is None or len(str(directory)) == 0:
            logger.info( "cancelled." )
            return

        def _handle_progress(x):
            self.applet.progressSignal.emit(x)

        def _export():
            self.applet.busy = True
            self.applet.appletStateUpdateRequested.emit()

            t_from = None
            # determine from_time (it could has been changed in the GUI meanwhile)            
            for t_from, label2color_at in enumerate(self.mainOperator.label2color):
                if len(label2color_at) == 0:
                    continue
                else:
                    break

            if t_from is None:
                self._criticalMessage("There is nothing to export.")
                return

            t_from = int(t_from)

            logger.info( "Saving first label image..." )
            key = []
            for idx, flag in enumerate(axisTagsToString(self.mainOperator.LabelImage.meta.axistags)):
                if flag is 't':
                    key.append(slice(t_from,t_from+1))
                elif flag is 'c':
                    key.append(slice(0,1))
                else:
                    key.append(slice(0,self.mainOperator.LabelImage.meta.shape[idx]))


            roi = SubRegion(self.mainOperator.LabelImage, key)
            labelImage = self.mainOperator.LabelImage.get(roi).wait()
            labelImage = labelImage[0,...,0]

            try:
                # write_events([], str(directory), t_from, labelImage)

                events = self.mainOperator.EventsVector.value
                logger.info( "Saving events..." )
                logger.info( "Length of events " + str(len(events)) )

                num_files = float(len(events))

                for i in sorted(events.keys()):
                    events_at = events[i]
                    i = int(i)
                    t = t_from + i
                    key[0] = slice(t,t+1)
                    roi = SubRegion(self.mainOperator.LabelImage, key)
                    labelImage = self.mainOperator.LabelImage.get(roi).wait()
                    labelImage = labelImage[0,...,0]
                    if self.withMergers:
                        write_events(events_at, str(directory), t, labelImage, self.mainOperator.mergers)
                    else:
                        write_events(events_at, str(directory), t, labelImage)
                    _handle_progress(i/num_files * 100)
            except IOError as e:
                self._criticalMessage("Cannot export the tracking results. Maybe these files already exist. "\
                                      "Please delete them or choose a different directory.")
                return

        def _handle_finished(*args):
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()
            self._drawer.exportButton.setEnabled(True)
            self.applet.progressSignal.emit(100)

        def _handle_failure( exc, exc_info ):
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()
            msg = "Exception raised during export.  See traceback above.\n"
            log_exception( logger, msg, exc_info=exc_info )
            self.applet.progressSignal.emit(100)
            self._drawer.exportButton.setEnabled(True)

        self._drawer.exportButton.setEnabled(False)
        self.applet.progressSignal.emit(0)
        req = Request( _export )
        req.notify_failed( _handle_failure )
        req.notify_finished( _handle_finished )
        req.submit()


    def _onExportTifButtonPressed(self):
        options = QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog

        directory = encode_from_qstring(QFileDialog.getExistingDirectory(self, 'Select Directory',os.path.expanduser("~"), options=options))

        if directory is None or len(str(directory)) == 0:
            logger.info( "cancelled." )
            return

        logger.info( 'Saving results as tiffs...' )

        label2color = self.mainOperator.label2color
        lshape = list(self.mainOperator.LabelImage.meta.shape)

        def _handle_progress(x):
            self.applet.progressSignal.emit(x)

        def _export():
            num_files = float(len(label2color))
            for t, label2color_at in enumerate(label2color):
                if len(label2color_at) == 0:
                    continue
                logger.info( 'exporting tiffs for t = ' + str(t) )

                roi = SubRegion(self.mainOperator.LabelImage, start=[t,] + 4*[0,], stop=[t+1,] + list(lshape[1:]))
                labelImage = self.mainOperator.LabelImage.get(roi).wait()
                relabeled = relabel(labelImage[0,...,0],label2color_at)
                for i in range(relabeled.shape[2]):
                    out_im = relabeled[:,:,i]
                    out_fn = str(directory) + '/vis_t' + str(t).zfill(4) + '_z' + str(i).zfill(4) + '.tif'
                    vigra.impex.writeImage(np.asarray(out_im,dtype=np.uint32), out_fn)

                _handle_progress(t/num_files * 100)
            logger.info( 'Tiffs exported.' )

        def _handle_finished(*args):
            self._drawer.exportTifButton.setEnabled(True)
            self.applet.progressSignal.emit(100)

        def _handle_failure( exc, exc_info ):
            msg = "Exception raised during export.  See traceback above.\n"
            log_exception( logger, msg, exc_info )
            self.applet.progressSignal.emit(100)
            self._drawer.exportTifButton.setEnabled(True)

        self._drawer.exportTifButton.setEnabled(False)
        self.applet.progressSignal.emit(0)
        req = Request( _export )
        req.notify_failed( _handle_failure )
        req.notify_finished( _handle_finished )
        req.submit()


    def _onLineageFileNameButton(self):
        options = QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |= QFileDialog.DontUseNativeDialog
        fn = QFileDialog.getSaveFileName(self, 'Save Lineage Trees', os.getenv('HOME'), options=options)
        if fn is None:
            logger.info( "cancelled." )
            return
        self._drawer.lineageFileNameEdit.setText(str(fn))


    def _onLineageTreeButtonPressed(self):
        fn = self._drawer.lineageFileNameEdit.text()

        width = self._drawer.widthBox.value()
        height = self._drawer.heightBox.value()
        if width == 0:
            width = None
        if height == 0:
            height = None
        circular = self._drawer.circularBox.isChecked()
        withAppearing = self._drawer.withAppearingBox.isChecked()

        from_t = self._drawer.lineageFromBox.value()
        to_t = self._drawer.lineageToBox.value()

        logger.info( "Computing Lineage Trees..." )
        self._createLineageTrees(str(fn), width=width, height=height, circular=circular, withAppearing=withAppearing, from_t=from_t, to_t=to_t)
        logger.info( 'Lineage Trees saved.' )


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
