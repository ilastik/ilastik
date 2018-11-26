from __future__ import absolute_import
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
#Python
from future import standard_library
standard_library.install_aliases()
from builtins import range
import os
import sys
import threading
import h5py
import numpy
from functools import partial
import logging
logger = logging.getLogger(__name__)

#PyQt
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QFileDialog, QMessageBox, QStackedWidget, QWidget, QMenu
)
#lazyflow
from lazyflow.request import Request

#volumina
from volumina.utility import PreferencesManager

#ilastik
from ilastik.config import cfg as ilastik_config
from ilastik.utility import bind, log_exception
from ilastik.utility.gui import ThreadRouter, threadRouted
from lazyflow.utility.pathHelpers import getPathVariants, PathComponents
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.applets.base.applet import DatasetConstraintError

from .hyperparameterGui import HyperparameterGui, CreateTikTorchModelGui

from .opCNNModelSelection import OpCNNModelSelection


class CNNModelSelectionGui(QWidget):
    """
    Manages all GUI elements in the data selection applet.
    This class itself is the central widget and also owns/manages the applet drawer widgets.
    """

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def centralWidget( self ):
        return self

    def appletDrawer( self ):
        return self._drawer

    def menus( self ):
        """
        Returns a list of of QMenu widgets
        """
        menus = []

        add_model_menu = QMenu("Add Model", parent=self)
        createModel_gui = CreateTikTorchModelGui(self.topLevelOperator)
        createModel_gui.hide()

        def createTikTorchModel():
            createModel_gui.show()

        add_model_menu.addAction("Create TikTorch model").triggered.connect(createTikTorchModel)

        def add_existing_model():
            options = QFileDialog.Options(QFileDialog.ShowDirsOnly)
            folder_name = QFileDialog.getExistingDirectory(self, "Select TikTorch model",
                                                           os.path.expanduser('~'), options)
            self.topLevelOperator.ModelPath.setValue(folder_name)
            x = 8

        add_model_menu.addAction("Add existing TikTorch model").triggered.connect(add_existing_model)            

        menus += [add_model_menu]

        hyperparameter_menu = QMenu("Hyperparameters", parent=self)
        parameter_gui = HyperparameterGui(self.topLevelOperator)
        parameter_gui.hide()

        def set_parameters():
            parameter_gui.show()
            #parameter_gui.exec_()

        hyperparameter_menu.addAction("Set Hyperparameters").triggered.connect(set_parameters)

        menus += [hyperparameter_menu]
        
        return menus


    def viewerControlWidget(self):
        return self._viewerControlWidgetStack

    def setEnabled(self, enabled):
        pass

    def setImageIndex(self, imageIndex):
        pass

    def imageLaneAdded(self, laneIndex):
        pass

    def imageLaneRemoved(self, laneIndex, finalLength):
        pass

    def stopAndCleanUp(self):
        pass

    def allowLaneSelectionChange(self):
        pass

    def __init__(self, parentApplet, dataSelectionOperator, serializer, instructionText):
        """
        Constructor.
        
        :param dataSelectionOperator: The top-level operator.  Must be of type :py:class:`OpMultiLaneDataSelectionGroup`.
        :param serializer: The applet's serializer.  Must be of type :py:class:`DataSelectionSerializer`
        :param instructionText: A string to display in the applet drawer.
        :param guiMode: Either ``GuiMode.Normal`` or ``GuiMode.Batch``.  Currently, there is no difference between normal and batch mode.
        :param max_lanes: The maximum number of lanes that the user is permitted to add to this workflow.  If ``None``, there is no maximum.
        """
        super(CNNModelSelectionGui, self).__init__()
        self._cleaning_up = False
        self.parentApplet = parentApplet

        self._viewerControls = QWidget()
        self.topLevelOperator = dataSelectionOperator
        self.serializer = serializer

        self._initAppletDrawerUic(instructionText)
        
        self._viewerControlWidgetStack = QStackedWidget(self)
        
        opWorkflow = self.topLevelOperator.parent
        assert hasattr(opWorkflow.shell, 'onSaveProjectActionTriggered'), \
            "This class uses the IlastikShell.onSaveProjectActionTriggered function.  Did you rename it?"

    def _initAppletDrawerUic(self, instructionText):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0]+'/'
        self._drawer = uic.loadUi(localDir+"/dataSelectionDrawer.ui")
        self._drawer.instructionLabel.setText( instructionText )
