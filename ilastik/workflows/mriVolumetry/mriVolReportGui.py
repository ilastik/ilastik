import os

from PyQt4 import uic
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QWidget, QListWidget, QLabel, QPainter, QColor, QPixmap


class MriVolReportGui( QWidget ):
    """
    Gui for visualizing Report for MriVolumetry
    based on code from Christoph Decker
    """
    def centralWidget( self ):
        return self
    def menus( self ):
        return []
    def appletDrawer( self ):
        return self._drawer
    def reset( self ):
        print "MriVolReportGui.reset(): not implemented"
    def viewerControlWidget(self):
        return self._viewerControlWidgetStack
    def stopAndCleanUp(self):
        pass



    def __init__(self, parentApplet, topLevelOperatorView, 
                 title="MRI Volumetry Report"):
        super(MriVolReportGui, self).__init__()

        self.title = title
        self.parentApplet = parentApplet
        # Region in the lower left
        self._viewerControlWidgetStack = QListWidget(self)
        self.op = topLevelOperatorView
            
        # subscribe to dirty notifications of input data
        # TODO

        # set variables
        # TODO

        # load and initialize user interfaces
        self._initCentralUic()
        self._initAppletDrawerUic()
        

    def _initCentralUic(self):
        """
        Load the ui for the main window
        """
        # create layout
        localDir = os.path.split(__file__)[0]
        uic.loadUi(localDir+"/report_main.ui", self)
        
        self.drawHistogram()

        '''
        self.label.setText('adasdad')
        '''

    def drawHistogram(self):
            
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.white)
        
        painter = QPainter()
        painter.begin(pixmap)

        painter.setBrush(QColor(0, 0, 255, 100))
        painter.drawRect(10, 15, 30, 30)
        painter.end()
        
        self.label.setPixmap(pixmap)
   

    def _initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer
        """
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/report_drawer.ui")


