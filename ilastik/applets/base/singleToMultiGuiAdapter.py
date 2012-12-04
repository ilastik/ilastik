class SingleToMultiGuiAdapter( object ):
    """
    Utility class used by the StandardApplet to wrap several single-image 
    GUIs into one multi-image GUI, which is what the shell/Applet API requires.
    """
    def __init__(self, singleImageGuiFactory, topLevelOperator):
        self.singleImageGuiFactory = singleImageGuiFactory
        self._imageIndex = None
        self._guis = {}
        self.topLevelOperator = topLevelOperator

    def currentGui(self):
        """
        Return the single-image GUI for the currently selected image lane.
        If it doesn't exist yet, create it.
        """
        if self._imageIndex is None:
            return None
        # Create first if necessary
        if self._imageIndex not in self._guis:
            self._guis[self._imageIndex] = self.singleImageGuiFactory( self._imageIndex )
        return self._guis[self._imageIndex]

    def appletDrawer(self):
        """
        Return the applet drawer of the current single-image gui.
        """
        if self.currentGui() is not None:
            return self.currentGui().appletDrawer()
        else:
            from PyQt4.QtGui import QWidget
            return QWidget()

    def centralWidget( self ):
        """
        Return the central widget of the currently selected single-image gui.
        """
        if self.currentGui() is None:
            return None
        return self.currentGui().centralWidget()

    def menus(self):
        """
        Return the menus of the currently selected single-image gui.
        """
        if self.currentGui() is None:
            return None
        return self.currentGui().menus()
    
    def viewerControlWidget(self):
        """
        Return the viewer control widget for the currently selectd single-image gui.
        """
        if self.currentGui() is None:
            return None
        return self.currentGui().viewerControlWidget()
    
    def setImageIndex(self, imageIndex):
        """
        Called by the shell when the user has changed the currently selected image lane.
        """
        self._imageIndex = imageIndex

    def stopAndCleanUp(self):
        """
        Called by the workflow when the project is closed and the GUIs are about to be discarded.
        """
        for gui in self._guis.values():
            gui.stopAndCleanUp()
