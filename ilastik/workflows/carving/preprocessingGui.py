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
import os
import logging
logger = logging.getLogger(__name__)

#PyQt
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtGui import QIcon

#ilastik
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.utility import bind, log_exception
from ilastik.utility.gui import ThreadRouter, threadRouted
from .preprocessingViewerGui import PreprocessingViewerGui

class PreprocessingGui(QMainWindow):
    def __init__(self, parentApplet, topLevelOperatorView):
        super(PreprocessingGui,self).__init__()
        
        self.parentApplet = parentApplet
        self.drawer = None
        self.threadRouter = ThreadRouter(self)
        self.guiMode = 1
        self.topLevelOperatorView = topLevelOperatorView
        self.initAppletDrawerUic()
        self.centralGui = PreprocessingViewerGui(parentApplet, self.topLevelOperatorView)
        
    def initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]+'/'
        # (We don't pass self here because we keep the drawer ui in a separate object.)
        self.drawer = uic.loadUi(localDir+"/preprocessingDrawer.ui")
        
        # FIXME: for 0.6, we do not want to allow these options below
        self.drawer.watershedSourceCombo.hide()
        self.drawer.invertWatershedSourceCheckbox.hide()
        self.drawer.watershedSourceInputLabel.hide()
        
        # Set up radiobox layout
        self.filterbuttons = [self.drawer.filter1,
                                self.drawer.filter2,
                                self.drawer.filter3,
                                self.drawer.filter4,
                                self.drawer.filter5]

        self.correspondingSigmaMins = [0.9,0.9,0.6,0.1,0.1]

        # Set up our handlers
        for f in self.filterbuttons:
            f.clicked.connect(self.handleFilterChanged)

        # Init widget appearance
        self.drawer.runButton.setIcon( QIcon(ilastikIcons.Play) )
        self.drawer.watershedSourceCombo.addItem("Input Data", userData="input")
        self.drawer.watershedSourceCombo.addItem("Filter Output", userData="filtered")
        self.drawer.watershedSourceCombo.addItem("Raw Data (if available)", userData="raw")

        # Initialize widget values
        self.updateDrawerFromOperator()

        # Event handlers: everything is handled once the run button is clicked, not live
        self.drawer.runButton.clicked.connect(self.handleRunButtonClicked)

        self.drawer.watershedSourceCombo.currentIndexChanged.connect( self.handleWatershedSourceChange )
        self.drawer.invertWatershedSourceCheckbox.toggled.connect( self.handleInvertWatershedSourceChange )
        self.drawer.writeprotectBox.stateChanged.connect(self.handleWriterprotectStateChanged)

        self.parentApplet.appletStateUpdateRequested.subscribe(self.processingFinished)

        #FIXME: for release 0.6, disable this (the reset button made the gui even more complicated)            
        #self.drawer.resetButton.clicked.connect(self.topLevelOperatorView.reset)

        # Slot change handlers (in case the operator is somehow changed *outside* the gui, such as by the workflow.
        self.topLevelOperatorView.Filter.notifyDirty(self.updateDrawerFromOperator)
        self.topLevelOperatorView.Sigma.notifyDirty(self.updateDrawerFromOperator)
        self.topLevelOperatorView.WatershedSource.notifyDirty(self.updateDrawerFromOperator)
        self.topLevelOperatorView.InvertWatershedSource.notifyDirty(self.updateDrawerFromOperator)

    def updateDrawerFromOperator(self, *args):
        self.filterbuttons[self.topLevelOperatorView.Filter.value].setChecked(True)
        self.filterChoice = [f.isChecked() for f in self.filterbuttons].index(True)
        self.drawer.sigmaSpin.setValue(self.topLevelOperatorView.Sigma.value)
        sourceSetting = self.topLevelOperatorView.WatershedSource.value
        comboIndex = self.drawer.watershedSourceCombo.findData( sourceSetting )
        self.drawer.watershedSourceCombo.setCurrentIndex( comboIndex )
        self.drawer.invertWatershedSourceCheckbox.setChecked( self.topLevelOperatorView.InvertWatershedSource.value )

    def handleFilterChanged(self):
        choice =  [f.isChecked() for f in self.filterbuttons].index(True)
        self.filterChoice = choice
        #update lower bound for sigma
        self.drawer.sigmaSpin.setMinimum(self.correspondingSigmaMins[choice])


    def handleWatershedSourceChange(self, index):
        data = self.drawer.watershedSourceCombo.itemData(index)
        self.topLevelOperatorView.WatershedSource.setValue( str(data) )

    def handleInvertWatershedSourceChange(self, checked):
        self.topLevelOperatorView.InvertWatershedSource.setValue( checked )

    def processingFinished(self):
        """Method makes sure finished processing is communicated visually

        After processing is finished it is checked whether one of the result
        layers is visible. If not, finished processing is communicated by
        showing the watershed layer.
        """
        layerStack = self.centralGui.editor.layerStack
        watershedIndex = layerStack.findMatchingIndex(
            lambda x: x.name == 'Watershed'
            )
        filteredIndex = layerStack.findMatchingIndex(
            lambda x: x.name == 'Filtered Data'
            )

        # Only do something if none of the result layers is visible
        if not layerStack[watershedIndex].visible:
            if not layerStack[filteredIndex].visible:
                layerStack[watershedIndex].visible = True

    @threadRouted 
    def onFailed(self, exception, exc_info):
        log_exception( logger, exc_info=exc_info )
        QMessageBox.critical(self, "error", str(exception))
    
    def handleRunButtonClicked(self):
        self.setWriteprotect()
        self.topLevelOperatorView.Filter.setValue(self.filterChoice)
        self.topLevelOperatorView.SizeRegularizer.setValue(self.drawer.sizeRegularizerSpin.value())
        self.topLevelOperatorView.Sigma.setValue(self.drawer.sigmaSpin.value())
        self.topLevelOperatorView.ReduceTo.setValue(self.drawer.reduceToSpin.value())
        self.topLevelOperatorView.DoAgglo.setValue(self.drawer.doAggloCheckBox.isChecked())

        r = self.topLevelOperatorView.PreprocessedData[:]
        r.notify_failed(self.onFailed)
        r.notify_finished( bind(self.parentApplet.appletStateUpdateRequested) )
        r.submit()
        
    def handleWriterprotectStateChanged(self):
        iswriteprotect = self.drawer.writeprotectBox.checkState()
        for f in self.filterbuttons:
            f.setEnabled(not iswriteprotect)
        self.drawer.sigmaSpin.setEnabled(not iswriteprotect)
        self.drawer.watershedSourceCombo.setEnabled(not iswriteprotect)
        self.drawer.invertWatershedSourceCheckbox.setEnabled( not iswriteprotect )
        self.drawer.runButton.setEnabled(not iswriteprotect)

        self.drawer.sizeRegularizerSpin.setEnabled(not iswriteprotect)
        self.drawer.reduceToSpin.setEnabled(not iswriteprotect)
        self.drawer.doAggloCheckBox.setEnabled(not iswriteprotect)
    
    def enableWriteprotect(self,ew):
        self.drawer.writeprotectBox.setEnabled(ew)
    
    def setWriteprotect(self):
        self.drawer.writeprotectBox.setChecked(True)
    
    def setFilter(self,s,propagate = False):
        self.filterbuttons[s].setChecked(True)
        self.handleFilterChanged()
    
    def setSigma(self,sigma):
        self.drawer.sigmaSpin.setValue(sigma)
    
    def enableReset(self,er):
        pass
        #TODO: re-enable this after the 0.6 release
        #self.drawer.resetButton.setEnabled(er)
    
    def centralWidget( self ):
        return self.centralGui
    
    def appletDrawer( self ):
        return self.drawer
        
    def menus( self ):
        return []
        
    def viewerControlWidget(self):
        return self.centralGui.viewerControlWidget()
    
    def setImageIndex(self,imageIndex):
        pass

    def imageLaneAdded(self,imageIndex):
        pass

    def imageLaneRemoved(self,laneIndex,finalLength):
        pass

    def stopAndCleanUp(self):
        self.centralGui.stopAndCleanUp()
