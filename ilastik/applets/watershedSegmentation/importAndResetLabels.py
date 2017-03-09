###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2017, the ilastik developers
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
##############################################################################

#######################################################
#######################################################
#######################################################

#               THIS FILE IS NOT USED ANYMORE

#######################################################
#######################################################
#######################################################
#######################################################

'''
# in watershedSegmentationGui
# init the class to import and reset Labels
self.importAndResetLabels = ImportAndResetLabels (
        op.CorrectedSeedsIn,
        op.SeedsExist.value,
        op.UseCachedLabels.value,
        self._labelControlUi.labelListModel, 
        self._LabelPipeline.opLabelArray,
        op.LabelNames, 
        op.LabelColors, 
        op.PmapColors
        )
# 1. First import seeds, and connect slot
# 2. then look at their pixelValues (including looking at their channels) 
#   in pixelValueDisplaying
# import the Labels from CorrectedSeedsIn, if possible
self.importAndResetLabels.importLabelsFromSlot()

# use the Cache of the CorrectedSeedsOut for the next Time, the watershed applet will be reloaded
op.UseCachedLabels.setValue(True)
'''

import numpy as np
import volumina.colortables as colortables
from PyQt4.Qt import pyqtSlot
from PyQt4.QtGui import QMessageBox
import logging
logger = logging.getLogger(__name__)

class ImportAndResetLabels(object):
    """
    class that handles the import of slot-data into Labels and into a label-cache
    as well as the deletion of this data from Cache

    """
    def __init__(self, 
                slot, 
                isSlotContentNotEmpty, 
                #slotCache,
                useSlotCache,
                labelListModel, 
                opLabelArray, 
                LabelNames, 
                LabelColors, 
                PmapColors, 
                colortable = colortables.create_random_8bit_zero_transparent(),
                LabelDefaultListName="Seed", 
                resetLayerName="Seeds", 
                outputLayerName="Corrected Seeds Out"):
        """
        :param slot:        the labels will be reset to the data 
            that is included in this slot
        :type slot: InputSlot or OutputSlot
        :param isSlotContentNotEmpty: if the initial input slot for the label input was empty or not
            even if it was set to a default value afterwards
        :type isSlotContentNotEmpty: bool
        :param useSlotCache:    to indicate if True: use the cached Label data, 
            and if False: use the Labels/Data of 'slot'
            This has only effect on the importLabelsFromSlot function
        :type useSlotCache: bool
        :param labelListModel: the list in which the labels, there name, color, number etc is saved
            e.g. self._labelControlUi.labelListModel 
        :type labelListModel: LabelListModel or LabelListModelWithNumber
        :param opLabelArray:    Operator where the Labels are Saved in Arrays;
            used for deleting Labels out of the cache and to read in labels to the cache
            member functions of opLabelArray used: clearLabel, ingestData
            e.g.  topLevelOperatorView.opLabelPipeline.opLabelArray
        :type opLabelArray: operator
        :param LabelNames: Slot that contains the names of the Labels
            When importing Labels, new Labels are added here 
            GUI-only (not part of the pipeline, but saved to the project)
        :type LabelNames: OutputSlot
        :param LabelColors: Slot that contains the Colors, with which the labels shall be drawn
            When importing Labels, new LabelsColors from the colortable are added here 
            GUI-only (not part of the pipeline, but saved to the project)
        :type LabelColors: OutputSlot
        :param PmapColors: Slot that contains the Colors, that is related to a Label; 
            When importing Labels, new LabelsColors from the colortable are added here 
            GUI-only (not part of the pipeline, but saved to the project)
        :type PmapColors: OutputSlot
        :param colortable: list of colors, that is used for LabelColors and PmapColors
        :type colortable: list of QColors
        :param LabelDefaultListName: give a default name, that is displayed in the labelListModel, 
            when importing new labels
        :type LabelDefaultListName: str
        :param resetLayerName: name of the Layer, that is displayed in the setupLayer that 
            shows the original data, to which this operator will be reset 
            (only used for the MessageBox-question to really reset)
        :type resetLayerName: str
        :param outputLayerName: name of the Layer, that is displayed in the setupLayer that 
            shows the output data, including all added labels 
            (only used for the MessageBox-question to really reset)
        :type outputLayerName: str

        (self can be the class: WatershedSegmentationGui)
        """
        #:param slotCache:       InputSlot or OutputSlot the labels can be read from 
            #this is necessary for using the cached data, after a project is reset, so that the user changes
            #mustn't be saved in a file for reloading it

        #variable initialization
        self._slot                  = slot
        self._isSlotContentNotEmpty = isSlotContentNotEmpty
        #self._slotCache             = slotCache
        self._useSlotCache          = useSlotCache
        self._labelListModel        = labelListModel
        self._opLabelArray          = opLabelArray
        self._LabelNames            = LabelNames
        self._LabelColors           = LabelColors
        self._PmapColors            = PmapColors
        self._colortable            = colortable
        self._LabelDefaultListName  = LabelDefaultListName
        self._resetLayerName        = resetLayerName
        self._outputLayerName       = outputLayerName

    ############################################################
    # Labelmanagement: Import, Delete, Reset
    ############################################################

    def removeLabelsFromList(self):
        """
        Remove every Label that is in the labelList
        """

        '''
        import time
        print "start remove Labels"
        start = time.time()
        end = time.time()
        print  "removed Labels: "+ str(end - start)
        '''

        # this function could be improved drastically
        self._opLabelArray.clearAllLabels( )
        rows = self._labelListModel.rowCount()
        for i in range( rows ):
            self._labelListModel.removeRowWithoutEmittingSignal(0)



    def removeLabelsFromCacheAndList(self):
        """
        Remove every Label that is in the labelList and its value from cache.
        Doesn't effect Cached-values that don't have a Label in the LabelList. But this should never happen
        """
        rows = self._labelListModel.rowCount()

        for i in range( rows ):
            #get the value/number of the label, that is now the first one in the list
            #value = self._labelControlUi.labelListModel.__getitem__(0)._number
            value = self._labelListModel[0].number

            # make this faster
            #delete the label with the value x from cache, means reset value x to zero 
            self._opLabelArray.clearLabel( value )
            #alternatively use:
            #op.opLabelPipeline.DeleteLabel.setValue( 2 )

            #remove the Label with value x from the list of available Labels
            #always take first one for simplicity
            self._labelListModel.removeRow(0)



    def importLabels(self, slot):
        """
        original version from: pixelClassificationGui.importLabels
        Add the data included in the slot to the LabelArray by ingestData
        Only use this when the colors and Labels are reset. 
        The LabelColors, Pmaps and ListNames are reset and added with the default 
        properties to the list and slots
        

        :param slot:        slot with the data, that includes the Labeldata
        """
        # Load the data into the cache
        # Returns: the max label found in the slot.
        new_max = self._opLabelArray.ingestData( slot )

        # Add to the list of label names 
        new_names = map( lambda x: self._LabelDefaultListName + " {}".format(x), 
                                         range(1, new_max+1) )
        #add the new Labelnames
        self._LabelNames.setValue(new_names)

        #set the colorvalue and the color that is displayed in the labellist to the correct color

        # Use the given colortable that is used everywhere else
        # means: for new labels, for layer displaying etc
        default_colors = self._colortable
        self._LabelColors.setValue( default_colors[:new_max] )
        self._PmapColors.setValue( default_colors[:new_max] )


    def importLabelsFromSlot(self):
        """
        handles whether to import Labels from cache or from 
        the reset-slot
        
        """
        if (self._useSlotCache):
            logger.info( "Use the cached Labels and do nothing")
        else:
            self._importLabelsFromSlot(self._slot)


    def _importLabelsFromSlot(self, slot):
        """
        import the Labels from the slot given.
        So there is an option to import from cache or from data selection input slot
        :param slot: the slot, from where to import
        """
        #if no Seeds are supplied, do nothing
        if self._isSlotContentNotEmpty:
            self.importLabels( slot )
        else:
            logger.debug("In importLabelsFromSlot: No data supplied, so no labels are imported")


    @pyqtSlot()
    def resetLabelsToSlot(self):
        """
        wipe the LabelList
        import Labels from Slot which overrides the cache
        use the self._slot for reset
        """
        #decision box with yes or no
        msgBox = QMessageBox()
        msgBox.setText('Are you sure to delete all progress in ' + self._outputLayerName 
                + ' and reset to ' + self._resetLayerName + '?')
        msgBox.addButton(QMessageBox.Yes)
        msgBox.addButton(QMessageBox.No)
        #msgBox.addButton(QPushButton('Yes'), QMessageBox.YesRole)
        #msgBox.addButton(QPushButton('No'), QMessageBox.NoRole)
        #msgBox.addButton(QPushButton('Cancel'), QMessageBox.RejectRole)
        ret = msgBox.exec_()

        if (ret == QMessageBox.Yes):
            if self._isSlotContentNotEmpty:
                #removing from Cache not necessary, because in importLabelsFromSlot 
                #we override the cache, and therefore it is faster
                #self.removeLabelsFromCacheAndList()
                self.removeLabelsFromList()

                #this works only if the self._slot is not empty/full of zeros
                #then we have to delete from cache and from labelList
            else:
                self.removeLabelsFromCacheAndList()

            # Finally, import the labels from the original slot
            self._importLabelsFromSlot(self._slot)
