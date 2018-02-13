from __future__ import division
from past.utils import old_div
import collections

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QPushButton, QWidget, QLabel, QTableWidget, QTableWidgetItem, QGridLayout
from PyQt5.QtGui import QColor
import re

# Overload QTableWidgetItem class to allow comparisons of float instead of strings
class QTableWidgetItemWithFloatSorting(QTableWidgetItem):
    def __lt__(self, other):
        if ( isinstance(other, QTableWidgetItem) ):
            my_value = self.data(Qt.EditRole)
            other_value = other.data(Qt.EditRole)
            return my_value < other_value

        return super(QTableWidgetItemWithFloatSorting, self).__lt__(other)


class VariableImportanceDialog(QDialog):
    def __init__(self, named_importances, *args, **kwargs):
        super(VariableImportanceDialog, self).__init__(*args, **kwargs)
        self.setWindowTitle("Variable Importance Table")
        self.setMinimumWidth(700)
        self.setMinimumHeight(800)

        layout = QGridLayout() 
        layout.setContentsMargins(10, 10, 10, 10)
               
        if named_importances:
            # Show variable importance table
            rows = len(list(named_importances.items()))
            columns = 5
            table = QTableWidget(rows, columns)   
            table.setHorizontalHeaderLabels(['Variable Name', 'Class #0', 'Class #1', 'Overall', 'Gini'])
            table.verticalHeader().setVisible(False)      
            
            importances_mins = list(map(min, list(zip(*list(named_importances.values())))))
            importances_maxs = list(map(max, list(zip(*list(named_importances.values())))))
            
            for i, (variable, importances) in enumerate(named_importances.items()):     
                # Remove non-ASCII characters to get rid of the sigma character in the variable names.
                variable = re.sub(r'[^\x00-\x7F]+','s', variable)
                
                item = QTableWidgetItem(variable)
                item.setFlags( Qt.ItemIsSelectable |  Qt.ItemIsEnabled )
                table.setItem(i, 0, item)

                for j, importance in enumerate(importances):
                    # Get color based on the importance value
                    val = importances[j]
                    imin = importances_mins[j]
                    imax = importances_maxs[j]
                    range = importances_maxs[j] - importances_mins[j]
                    color = int( 255 - old_div(( (val-imin) * 200), range) )    

                    # Load items as strings
                    item = QTableWidgetItemWithFloatSorting(str("{: .05f}".format(importance)))
                    item.setFlags( Qt.ItemIsSelectable |  Qt.ItemIsEnabled )
                    item.setBackground(QColor(color,255,color))
                    table.setItem(i, j+1, item)
                    
            table.resizeColumnsToContents()  
            
            table.setSortingEnabled(True)
            table.sortByColumn(3, Qt.DescendingOrder)  # Sort by overall importance

            layout.addWidget(table, 1, 0, 3, 2)  
            
        else:
            # Classifier is not trained. Show warning message.
            msg = ('To enable this feature, you must choose the following classifier type via the menu Advanced > Classifier:\n\n'
                   '"Parallel Random Forest Classifier with Variable Importance (VIGRA)"\n\n'
                   '...and then RETRAIN your classifier (press "Live Update").')
            warningLabel = QLabel(msg)
            warningLabel.setAlignment(Qt.AlignCenter)
            warningLabel.setWordWrap(True) 
            layout.addWidget(warningLabel, 3, 0, 1 ,2)

        # Create and add close button
        closeButton = QPushButton("Close")
        closeButton.clicked.connect(self.close)
        layout.addWidget(closeButton, 4, 1)
        
        self.setLayout(layout)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    named_importances = { 'feature_1' : [1.2,4.3,3.1,4.8], 'feature_2' : [7.4,3.4,5.5,5.9], 'feature_3' : [1,2,3.5,5.2] , 'feature_4' : [1.9,9.1,2.5,7.1] , 'feature_5' : [6.4,2.0,8.5,1.1]  }

    app = QApplication([])
    mainWindow = QWidget()
    varImpDlg = VariableImportanceDialog(named_importances, mainWindow)
    #varImpDlg = VariableImportanceDialog(None, mainWindow)
    varImpDlg.show()
    varImpDlg.raise_()
    
    app.exec_()
    



