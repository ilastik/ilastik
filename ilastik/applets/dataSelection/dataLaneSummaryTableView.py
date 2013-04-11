from PyQt4.QtCore import Qt
from PyQt4.QtGui import QTableView

from dataLaneSummaryTableModel import DataLaneSummaryTableModel

class DataLaneSummaryTableView(QTableView):
    def __init__(self, parent):
        super( DataLaneSummaryTableView, self ).__init__(parent)

