###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2015, the ilastik developers
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
from functools import partial
import collections
import operator
import time
import os
import numpy
import vigra

#Qt
from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal, Qt, QEvent, QObject
from PyQt4.QtGui import QDialog, QFileDialog, QMessageBox, QSpinBox, QTableWidget, QLabel

#volumina
from volumina.widgets.multiStepProgressDialog import MultiStepProgressDialog

import logging
logger = logging.getLogger(__name__)
from volumina.utility import log_exception, PreferencesManager

from ilastik.applets.dataSelection.dataSelectionGui import DataSelectionGui

#lazyflow
import lazyflow
from lazyflow.graph import Graph
from lazyflow.request import Request
from lazyflow.roi import TinyVector, roiToSlice, roiFromShape
from lazyflow.operators.ioOperators import OpInputDataReader, OpStackLoader
from lazyflow.operators.opReorderAxes import OpReorderAxes


def import_labeling_layer(layer, parent_widget=None):
    """
    Prompt the user for layer import settings, and perform the layer import.
    """
    sourceTags = [True for l in layer.datasources]
    for i, source in enumerate(layer.datasources):
        if not hasattr(source, "dataSlot"):
             sourceTags[i] = False
    if not any(sourceTags):
        raise RuntimeError("can not import to a non-lazyflow data source (layer=%r, datasource=%r)" % (type(layer), type(layer.datasources[0])) )

    dataSlots = [slot.dataSlot for (slot, isSlot) in
                 zip(layer.datasources, sourceTags) if isSlot is True]
    for slot in dataSlots:
        assert isinstance(slot, lazyflow.graph.Slot), "slot is of type %r" % (type(slot))
        assert isinstance(slot.getRealOperator(), lazyflow.graph.Operator), "slot's operator is of type %r" % (type(slot.getRealOperator()))

    # TODO: *Finish* make generic, not carving specific, if possible?
    opLabels = parent_widget._labelingSlots.labelInput.getRealOperator() #dataSlots[0].getRealOperator().parent
    writeSeeds = parent_widget._labelingSlots.labelInput

    # TODO: use ilastik.shell.projectManager to get project related path?
    # Find the directory of the most recently opened image file
    mostRecentImageFile = PreferencesManager().get( 'DataSelection', 'recent image' )
    if mostRecentImageFile is not None:
        defaultDirectory = os.path.split(mostRecentImageFile)[0]
    else:
        defaultDirectory = os.path.expanduser('~')

    fileNames = DataSelectionGui.getImageFileNamesToOpen(parent_widget, defaultDirectory)
    fileNames = map(str, fileNames)

    if not fileNames:
        return

    # Create an operator to do the work
    opImport = OpInputDataReader( parent=opLabels )

    opImport.WorkingDirectory.setValue(defaultDirectory)
    opImport.FilePath.setValue(fileNames[0] if len(fileNames) == 1 else
                               os.path.pathsep.join(fileNames))

    # The reader assumes xyzc order, so we must transpose the data.
    opReorderAxes = OpReorderAxes( parent=opImport )
    opReorderAxes.Input.connect( opImport.Output )

    try:

        readData = opReorderAxes.Output[:].wait()

        img_shape_diff = TinyVector(writeSeeds.meta.shape) - TinyVector(readData.shape)
        is_img_subset = not any(map(lambda x: x < 0, img_shape_diff))

        #expect import is subset
        if not is_img_subset:
            QMessageBox.critical(parent_widget, "Import shape too large",
                                             "Import shape is not a subset of original input stack.")
            return

        # expect x, y shape to match original shape
        if any(img_shape_diff[:3]) or any(img_shape_diff[-1:]):
            QMessageBox.critical(parent_widget, "Shape does not match",
                                             "X,Y shape must match original input stack.")
            return

        if any(img_shape_diff):
            # User has choices: Use this dialog to collect settings
            settingsDlg = LabelImportOptionsDlg( parent_widget, img_shape_diff, opReorderAxes.Output, writeSeeds )
            # If user didn't accept, exit now.
            if ( settingsDlg.exec_() == LabelImportOptionsDlg.Accepted ):
                img_offset = settingsDlg.img_offset
            else:
                return
        else:
            img_offset = img_shape_diff

        img_shape = roiFromShape(readData.shape)
        img_start = TinyVector(img_shape[0]) + img_offset
        img_end = TinyVector(img_shape[1]) + img_offset
        img_slice = roiToSlice(img_start, img_end)

        # TODO: ensure that labels are cleared (optional setting)
        #opCarving.clearCurrentLabeling()

        writeSeeds[img_slice] = readData[:]

        #opCarving.Segmentation.setDirty()
        #opCarving.Trigger.setDirty()

    finally:
        # Clean up our temporary operators
        opReorderAxes.cleanUp()
        opImport.cleanUp()


"""
    '''
    # Alternate input UI (for image stacks)
    stackDlg = StackFileSelectionWidget(parent_widget)
    stackDlg.exec_()
    if stackDlg.result() != QDialog.Accepted :
        return
    fileNames = stackDlg.selectedFiles
    '''

    '''
    # For now, we require a single file
    if len(fileNames) > 1:
        QMessageBox.critical(parent_widget, "Too many files",
                                         "Labels must be contained in a single hdf5 volume.")
        return
    '''

    if len(fileNames) == 1:
        '''
        # Create an operator to do the work
        opImport = OpInputDataReader( parent=opCarving )

        opImport.WorkingDirectory.setValue(defaultDirectory)
        opImport.FilePath.setValue(fileNames[0])

        # The reader assumes xyzc order, so we must transpose the data.
        opReorderAxes = OpReorderAxes( parent=opImport )
        opReorderAxes.Input.connect( opImport.Output )
        '''
        '''
        # Another Per-slice image import method
        filename = fileNames[0]

        imgs_count = vigra.impex.numberImages(filename)
        for img_idx in range(imgs_count):
            img = vigra.readImage(filename, dtype=dtype, index=img_idx)

            img_shape = roiFromShape(img.shape)
            img_slice = roiToSlice(img_shape[0], img_shape[1])

            z = numpy.zeros(img_shape[1], dtype=dtype)
            z[img_slice] = img[img_slice]

            seedsSlice = (slice(0,1),) + (img_slice[0], img_slice[1], slice(img_idx, img_idx+1)) + (slice(0,1),)
            opCarving.WriteSeeds[seedsSlice] = z[(numpy.newaxis,) + img_slice + (numpy.newaxis,)]

        # Volume image import method
        imgs_count = vigra.impex.numberImages(filename)
        img = vigra.readVolume(filename, dtype=dtype)

        img_shape = roiFromShape(img.shape)
        img_slice = roiToSlice(img_shape[0], img_shape[1])

        z = numpy.zeros(img_shape[1], dtype=dtype)
        z[img_slice] = img[img_slice]

        opCarving.WriteSeeds[(slice(0,1),) + img_slice] = z[(numpy.newaxis,) + img_slice]

        '''
    elif len(fileNames) > 1:
        '''
        # Create an operator to do the work
        opImport = OpStackLoader( parent=opCarving )

        opImport.globstring.setValue(os.path.pathsep.join(fileNames))

        # The reader assumes xyzc order, so we must transpose the data.
        opReorderAxes = OpReorderAxes( parent=opImport )
        opReorderAxes.Input.connect( opImport.stack )
        '''

        '''
        # Another Per-slice image import method
        dtype = opCarving.WriteSeeds.meta.dtype
        img_idx = 0

        for filename in fileNames:
            img = vigra.readImage(filename, dtype=dtype, index=0)

            img_shape = roiFromShape(img.shape)
            img_slice = roiToSlice(img_shape[0], img_shape[1])

            z = numpy.zeros(img_shape[1], dtype=dtype)
            z[img_slice] = img[img_slice]

            seedSlice = (slice(0,1),) + (img_slice[0], img_slice[1], slice(img_idx, img_idx+1)) + (slice(0,1),)
            opCarving.WriteSeeds[seedSlice] = z[(numpy.newaxis,) + img_slice + (numpy.newaxis,)]
            img_idx += 1
        '''
    #else:
    #    return # user cancelled
"""


#**************************************************************************
# LabelImportHelper
#**************************************************************************
class LabelImportHelper(QObject):
    """
    Executes a layer export in the background, shows a progress dialog, and displays errors (if any).
    """
    # This signal is used to ensure that request 
    #  callbacks are executed in the gui thread
    _forwardingSignal = pyqtSignal( object )

    def _handleForwardedCall(self, fn):
        # Execute the callback
        fn()
    
    def __init__(self, parent):
        super( LabelImportHelper, self ).__init__(parent)
        self._forwardingSignal.connect( self._handleForwardedCall )

    def run(self, opImport):
        """
        Start the import and return immediately (after showing the progress dialog).
        
        :param opImport: The import object to execute.
                         It must have a 'run_import()' method and a 'progressSignal' member.
        """
        progressDlg = MultiStepProgressDialog(parent=self.parent())
        progressDlg.setNumberOfSteps(1)

        def _forwardProgressToGui(progress):
            self._forwardingSignal.emit( partial( progressDlg.setStepProgress, progress ) )

        def _onFinishImport( *args ): # Also called on cancel
            self._forwardingSignal.emit( progressDlg.finishStep )
    
        def _onFail( exc, exc_info ):
            log_exception( logger, "Failed to import layer.", exc_info=exc_info )
            msg = "Failed to import layer due to the following error:\n{}".format( exc )
            self._forwardingSignal.emit( partial(QMessageBox.critical, self.parent(), "Import Failed", msg) )
            self._forwardingSignal.emit( progressDlg.setFailed )

        opImport.progressSignal.subscribe( _forwardProgressToGui )

        # Use a request to execute in the background
        req = Request( opImport.run_import )
        req.notify_cancelled( _onFinishImport )
        req.notify_finished( _onFinishImport )
        req.notify_failed( _onFail )

        # Allow cancel.
        progressDlg.rejected.connect( req.cancel )

        # Start the import
        req.submit()

        # Execute the progress dialog
        # (We can block the thread here because the QDialog spins up its own event loop.)
        progressDlg.exec_()


#**************************************************************************
# LabelImportOptionsDlg
#**************************************************************************
class LabelImportOptionsDlg(QDialog):

    def __init__(self, parent, axisRanges, dataInputSlot, writeSeedsSlot):
        """
        Constructor.

        :param parent: The parent widget
        :param axisRanges: A vector of per-axis maximum values.
        :param dataInputSlot: Slot with imported data
        :param writeSeedsSlot: Slot for writing data to
        """
        super( LabelImportOptionsDlg, self ).__init__(parent)

        localDir = os.path.split(__file__)[0]
        uic.loadUi( os.path.join( localDir, "dataImportOptionsDlg.ui" ), self)

        self._axisRanges = axisRanges
        self._dataInputSlot = dataInputSlot
        self._writeSeedsSlot = writeSeedsSlot

        self._okay_conditions = {}
        self._boxes = collections.OrderedDict()
        self.img_offset = [0] * len(axisRanges)

        # Init child widgets
        self._initMetaInfoWidgets()
        self._initInsertPositionWidget()
        # TODO: show list of files in input stack
        # self._initSourceFilesList()

        # See self.eventFilter()
        self.installEventFilter(self)

    def eventFilter(self, watched, event):
        # Ignore 'enter' keypress events, since the user may just be entering settings.
        # The user must manually click the 'OK' button to close the dialog.
        if watched == self and \
           event.type() == QEvent.KeyPress and \
           ( event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return):
            return True
        return False

    def _set_okay_condition(self, name, status):
        self._okay_conditions[name] = status
        all_okay = all( self._okay_conditions.values() )
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled( all_okay )


    #**************************************************************************
    # Input/Output Meta-info (display only)
    #**************************************************************************
    def _initMetaInfoWidgets(self):
        ## Input/output meta-info display widgets
        dataInputSlot = self._dataInputSlot
        self.inputMetaInfoWidget.initSlot( dataInputSlot )
        writeSeedsSlot = self._writeSeedsSlot
        self.labelMetaInfoWidget.initSlot( writeSeedsSlot )

    #**************************************************************************
    # Insertion Position
    #**************************************************************************
    def _initInsertPositionWidget(self):
        dataImportSlot = self._dataInputSlot
        inputAxes = dataImportSlot.meta.getAxisKeys()

        shape = dataImportSlot.meta.shape

        axisRanges = self._axisRanges
        insertPos = [0] * len(axisRanges)
        maxValues = axisRanges

        self._initInsertPositionTableWithExtents(inputAxes, maxValues)

        self.positionWidget.itemChanged.connect( self._handleItemChanged )

    def _initInsertPositionTableWithExtents(self, axes, mx):
        positionTbl = self.positionWidget

        positionTbl.setColumnCount( 2 )
        positionTbl.setHorizontalHeaderLabels(["insert at", "max"])
        positionTbl.resizeColumnsToContents()
        tagged_insert = collections.OrderedDict( zip(axes, [0]*len(axes)) )
        tagged_max = collections.OrderedDict( zip(axes, mx) )
        self._tagged_insert = tagged_insert
        positionTbl.setRowCount( len(tagged_insert) )
        positionTbl.setVerticalHeaderLabels( tagged_insert.keys() )

        self._boxes.clear()

        for row, (axis_key, extent) in enumerate(tagged_max.items()):
            # Init min/max spinboxes
            default_insert = tagged_insert[axis_key] or 0
            default_max = tagged_max[axis_key] or extent

            insertBox = QSpinBox(self)
            maxBox = QLabel(str(default_max), self)

            insertBox.setValue(0)
            insertBox.setMinimum(0)
            insertBox.setMaximum(extent)
            insertBox.setEnabled( tagged_insert[axis_key] is not None )
            if insertBox.isEnabled():
                insertBox.setValue( default_insert )

            # TODO: maxBox shouldn't be in tab list (but it still is)
            maxBox.setTextInteractionFlags(Qt.NoTextInteraction)
            maxBox.setFocusPolicy(Qt.NoFocus)
            maxBox.setEnabled(False)

            insertBox.valueChanged.connect( self._updatePosition )

            positionTbl.setCellWidget( row, 0, insertBox )
            positionTbl.setCellWidget( row, 1, maxBox )

            self._boxes[axis_key] = (insertBox, maxBox)

        positionTbl.resizeColumnsToContents()

    def _updatePosition(self):
        insert_boxes, max_boxes = zip( *self._boxes.values() )
        box_inserts = map( QSpinBox.value, insert_boxes )

        self.img_offset = box_inserts

    def _handleItemChanged(self, item):
        if len(self._boxes) == 0:
            return
        pos_boxes, max_boxes = zip( *self._boxes.values() )


