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
###############################################################################
from builtins import range
import os
import logging
from collections import OrderedDict
from functools import partial
logger = logging.getLogger(__name__)

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QTabWidget, QVBoxLayout, QPushButton, QHBoxLayout, \
                        QLabel, QSpacerItem, QSizePolicy, QListWidget, QMessageBox

from lazyflow.request import Request
from volumina.utility import PreferencesManager
from ilastik.utility import log_exception
from ilastik.utility.gui import ThreadRouter, threadRouted
from ilastik.applets.dataSelection.dataSelectionGui import DataSelectionGui # We borrow the file selection window function.

class BatchProcessingGui( QTabWidget ):
    """
    """
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def centralWidget( self ):
        return self

    def appletDrawer(self):
        return self._drawer

    def menus( self ):
        return []

    def viewerControlWidget(self):
        return QWidget(parent=self) # No viewer, so no viewer controls.

    # This applet doesn't care what image is selected in the interactive flow
    def setImageIndex(self, index): pass
    def imageLaneAdded(self, laneIndex): pass
    def imageLaneRemoved(self, laneIndex, finalLength): pass

    def allowLaneSelectionChange(self):
        return False

    def stopAndCleanUp(self):
        # We don't have any complex things to clean up (e.g. no layer viewers)
        pass

    ###########################################
    ###########################################
    
    def __init__(self, parentApplet):
        super(BatchProcessingGui, self).__init__()
        self.parentApplet = parentApplet
        self.threadRouter = ThreadRouter(self) # For using @threadRouted
        self._drawer = None
        self.initMainUi()
        self.initAppletDrawerUi()
        self.export_req = None

    def initMainUi(self):
        role_names = self.parentApplet.dataSelectionApplet.topLevelOperator.DatasetRoles.value
        self.list_widgets = []
        
        # Create a tab for each role
        for role_index, role_name in enumerate(role_names):
            select_button = QPushButton("Select " + role_name + " Files...", 
                                        clicked=partial(self.select_files, role_index) )
            clear_button = QPushButton("Clear " + role_name + " Files",
                                       clicked=partial(self.clear_files, role_index) )
            button_layout = QHBoxLayout()
            button_layout.addWidget(select_button)
            button_layout.addSpacerItem( QSpacerItem(0,0,hPolicy=QSizePolicy.Expanding) )
            button_layout.addWidget(clear_button)
            button_layout.setContentsMargins(0, 0, 0, 0)
            
            button_layout_widget = QWidget()
            button_layout_widget.setLayout(button_layout)
            button_layout_widget.setSizePolicy( QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum) )

            list_widget = QListWidget(parent=self)
            list_widget.setSizePolicy( QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) )
            self.list_widgets.append( list_widget )

            tab_layout = QVBoxLayout()
            tab_layout.setContentsMargins(0, 0, 0, 0)
            tab_layout.addWidget( button_layout_widget )
            tab_layout.addWidget( list_widget )
            
            layout_widget = QWidget(parent=self)
            layout_widget.setLayout(tab_layout)
            self.addTab(layout_widget, role_name)

    def initAppletDrawerUi(self):
        instructions_label = QLabel("Select the input files for batch processing\n"
                                    "using the controls on the right.\n"
                                    "\n"
                                    "The results will be exported according\n"
                                    "to the same settings you chose in the\n"
                                    "interactive export page above.")

        self.run_button = QPushButton("Process all files", clicked=self.run_export)
        self.cancel_button = QPushButton("Cancel processing", clicked=self.cancel_batch_processing)
        self.cancel_button.setVisible(False)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(instructions_label)
        layout.addWidget(self.run_button)
        layout.addWidget(self.cancel_button)

        self._drawer = QWidget(parent=self)
        self._drawer.setLayout(layout)
        
    def select_files(self, role_index):
        preference_name = 'recent-dir-role-{}'.format(role_index)
        recent_processing_directory = PreferencesManager().get( 'BatchProcessing', 
                                                                preference_name, 
                                                                default=os.path.normpath('~') )
        file_paths = DataSelectionGui.getImageFileNamesToOpen(self, recent_processing_directory)
        if file_paths:
            recent_processing_directory = os.path.dirname(file_paths[0])
            PreferencesManager().set( 'BatchProcessing', preference_name, recent_processing_directory )
        
            self.list_widgets[role_index].clear()
            self.list_widgets[role_index].addItems(file_paths)

    def clear_files(self, role_index):
        self.list_widgets[role_index].clear()
    
    def run_export(self):
        role_names = self.parentApplet.dataSelectionApplet.topLevelOperator.DatasetRoles.value

        # Prepare file lists in an OrderedDict
        role_path_dict = OrderedDict()
        role_path_dict[0] = BatchProcessingGui.get_all_item_strings(self.list_widgets[0])
        num_datasets = len(role_path_dict[0])

        for role_index, list_widget in enumerate(self.list_widgets[1:], start=1):
            role_path_dict[role_index] = BatchProcessingGui.get_all_item_strings(self.list_widgets[role_index])
            assert len(role_path_dict[role_index]) <= num_datasets, \
                "Too many files given for role: '{}'".format( role_names[role_index] )
            if len(role_path_dict[role_index]) < num_datasets:
                role_path_dict[role_index] += [None] * (num_datasets-len(role_path_dict[role_index]))

        # Run the export in a separate thread
        export_req = Request(partial(self.parentApplet.run_export, role_path_dict))
        export_req.notify_failed(self.handle_batch_processing_failure)
        export_req.notify_finished(self.handle_batch_processing_finished)
        export_req.notify_cancelled(self.handle_batch_processing_cancelled)
        self.export_req = export_req

        self.parentApplet.busy = True
        self.parentApplet.appletStateUpdateRequested()
        self.cancel_button.setVisible(True)
        self.run_button.setEnabled(False)

        # Start the export        
        export_req.submit()

    def handle_batch_processing_complete(self):
        """
        Called after batch processing completes, no matter how it finished (failed, cancelled, whatever).
        Can be overridden in subclasses.
        """
        pass

    def cancel_batch_processing(self):
        assert self.export_req, "No export is running, how were you able to press 'cancel'?"
        self.export_req.cancel()

    @threadRouted
    def handle_batch_processing_finished(self, *args):
        self.parentApplet.busy = False
        self.parentApplet.appletStateUpdateRequested()
        self.export_req = None
        self.cancel_button.setVisible(False)
        self.run_button.setEnabled(True)
        self.handle_batch_processing_complete()

    @threadRouted
    def handle_batch_processing_failure(self, exc, exc_info):
        msg = "Error encountered during batch processing:\n{}".format( exc )
        log_exception( logger, msg, exc_info )
        self.handle_batch_processing_finished()
        self.handle_batch_processing_complete()
        QMessageBox.critical(self, "Batch Processing Error", msg)

    @threadRouted
    def handle_batch_processing_cancelled(self):
        self.handle_batch_processing_finished()
        self.handle_batch_processing_complete()
        QMessageBox.information(self, "Batch Processing Cancelled.", "Batch Processing Cancelled.")

    @staticmethod
    def get_all_item_strings(list_widget):
        """
        Utility function.
        Return all items in the given QListWidget as a list of strings.
        """
        all_item_strings = []
        for row in range(list_widget.count()):
            all_item_strings.append( str(list_widget.item(row).text()) )
        return all_item_strings
            
