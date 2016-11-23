
class ImportAndResetLabels(object):
    #TODO
    def __init__(self, slot, isSlotContentNotEmpty, labelModelList, resetLayerName="Seeds", outputLayerName="Corrected Seeds Out"):
        """
        :param slot:       InputSlot or OutputSlot the labels will be reset to the data 
            that is included in this slot
        :param labelListModel: the list in which the labels, there name, color, number etc is saved
            e.g. self._labelControlUi.labelListModel 
        :param resetLayerName: str name of the Layer, that is displayed in the setupLayer that 
            shows the original data, to which this operator will be reset 
            (only used for the MessageBox-question to really reset)
        :param outputLayerName: str name of the Layer, that is displayed in the setupLayer that 
            shows the output data, including all added labels 
            (only used for the MessageBox-question to really reset)
        :param isSlotContentNotEmpty: Boolean if the initial input slot for the label input was empty or not
            even if it was set to a default value afterwards

        """

        #variable initialization
        self._slot = slot
        self._labelListModel = labelListModel
        self._pixelValueCheckBox = pixelValueCheckBox
        self._statusBar = quadViewStatusBar
        self._isSlotContentNotEmpty = isSlotContentNotEmpty



    ############################################################
    # Labelmanagement: Import, Delete, Reset
    ############################################################

    def removeLabelsFromList(self):
        """
        Remove every Label that is in the labelList
        """
        rows = self._labelListModel.rowCount()
        for i in range( rows ):
            self._labelListModel.removeRow(0)

    def removeLabelsFromCacheAndList(self):
        """
        Remove every Label that is in the labelList and its value from cache.
        Doesn't effect Cached-values that don't have a Label in the LabelList. But this should never happen
        """
        #TODO
        op = self.topLevelOperatorView
        rows = self.labelListModel.rowCount()

        for i in range( rows ):
            #get the value/number of the label, that is now the first one in the list
            #value = self._labelControlUi.labelListModel.__getitem__(0)._number
            value = self._labelListModel[0].number

            #delete the label with the value x from cache, means reset value x to zero 
        #TODO
            op.opLabelPipeline.opLabelArray.clearLabel( value )
            #alternatively use:
            #op.opLabelPipeline.DeleteLabel.setValue( 2 )

            #remove the Label with value x from the list of available Labels
            #always take first one for simplicity
            self._labelListModel.removeRow(0)



    def importLabels(self, slot):
        """
        original version from: pixelClassificationGui.importLabels
        Add the data included in the slot to the LabelArray by ingestData
        Add as many Labels as long as the tallest Label-Number and the ones before have a 
        Label to draw with

        :param slot:        slot with the data, that includes the seeds
        """
        op = self.topLevelOperatorView 
        # Load the data into the cache
        # Returns: the max label found in the slot.
        new_max = op.opLabelPipeline.opLabelArray.ingestData( slot )

        # Add to the list of label names if there's a new max label with correct colors
        old_names = op.LabelNames.value
        old_max = len(old_names)
        if new_max > old_max:
            new_names = old_names + map( lambda x: "Seed {}".format(x), 
                                         range(old_max+1, new_max+1) )
            #add the new Labelnames
            op.LabelNames.setValue(new_names)

            #set the colorvalue and the color that is displayed in the labellist to the correct color

            # Use the 8bit colortable that is used everywhere else
            # means: for new labels, for layer displaying etc
            default_colors = self._colortable
            label_colors = op.LabelColors.value
            pmap_colors = op.PmapColors.value
            
            #correct the color here
            op.LabelColors.setValue( label_colors + default_colors[old_max:new_max] )
            op.PmapColors.setValue( pmap_colors + default_colors[old_max:new_max] )

            #for debug reasons
            #colors
            '''
            print "\n\n"
            print "old_max=", old_max, "; new_max=", new_max
            for i in range(old_max, new_max):
                color = QColor(default_colors[i])
                intern_color = QColor(self._colortable[i])
                print i, ": ", color.red(),", ", color.green(),", ",  color.blue()
                print  i, ": ", intern_color.red(),", ", intern_color.green(),", ",  intern_color.blue()
            print "\n\n"
            '''

    '''
    def print_colortable(self, color):
        """
        only used for debugging
        """
        print "\n\n"
        for i in range(13):
            intern_color = QColor(color[i])
            print  i, ": ", intern_color.red(),", ", intern_color.green(),", ",  intern_color.blue()
        print "\n\n"
    '''


    def importLabelsFromSlot(self):
        """
        import the Labels from self._slot
        """
        #if no Seeds are supplied, do nothing
        if self._isSlotContentNotEmpty:
            self.importLabels( self._slot )
        else:
            logger.debug("In importLabelsFromSlot: No data supplied, so no labels are imported")


    @pyqtSlot()
    def resetLabelsToCorrectedSeedsIn(self):
        """
        wipe the LabelList
        import Labels from CorrectedSeedsIn Slot which overrides the cache
        """
        #decision box with yes or no
        msgBox = QMessageBox()
        msgBox.setText('Are you sure to delete all progress in ' + outputLayerName 
                + ' and reset to ' + resetLayerName + '?')
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

            # Finally, import the labels
            self.importLabelsFromSlot()
