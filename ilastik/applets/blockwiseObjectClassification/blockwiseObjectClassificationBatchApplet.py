from ilastik.applets.batchIo import BatchIoApplet

class BlockwiseObjectClassificationBatchApplet( BatchIoApplet ):
    """
    This a specialization of the generic batch results applet that
    provides a special viewer for object predictions.
    """    
    def getMultiLaneGui(self):
        if self._gui is None:
            # Gui is a special subclass of the generic gui
            from blockwiseObjectClassificationBatchGui import BlockwiseObjectClassificationBatchGui
            self._gui = BlockwiseObjectClassificationBatchGui( self._topLevelOperator, self.guiControlSignal, self.progressSignal, self._title )
        return self._gui

