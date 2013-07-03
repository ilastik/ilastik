import os

from PyQt4 import uic
from PyQt4.QtGui import QWidget

from datasetDetailedInfoTableModel import DatasetDetailedInfoTableModel

class DataDetailViewerWidget( QWidget ):
    def __init__(self, parent, topLevelOperator, roleIndex):
        super( DataDetailViewerWidget, self ).__init__(parent)
        self.topLevelOperator = topLevelOperator
        self._roleIndex = roleIndex
        
        localDir = os.path.split(__file__)[0]+'/'
        uic.loadUi(localDir+"/dataDetailViewerWidget.ui", self)

        self.datasetDetailTableView.setModel( DatasetDetailedInfoTableModel( self, self.topLevelOperator, self._roleIndex ) )

