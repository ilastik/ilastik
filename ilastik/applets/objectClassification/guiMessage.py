from PyQt4 import QtGui, QtCore



class GuiDialog(QtGui.QMessageBox):

    title = "Warning"
    
    _icon = QtGui.QMessageBox.Warning

    def __init__(self, parent=None):
        super(GuiDialog, self).__init__(parent)


    def showDialog(self, blocking=True):
        self._setup()
        self.setModal(blocking)
        self.show()

    def _setup(self):
        self.setWindowTitle(self.title)
        self.setText(self.getMessage())
        if self.hasDetails():
            self.setDetailedText(self.getDetails())
        okButton = self.addButton(QtGui.QMessageBox.Ok)
        self.icon = self._icon

    def getMessage(self):
        """
        Main content for message box, should be overridden.
        """ 
        return "Lorem Ipsum!"

    def hasDetails(self):
        """
        Should be overridden.
        """
        return False

    def getDetails(self):
        """
        Main content for message box, should be overridden.
        """ 
        return "More Lorem Ipsum!"

class LabelsChangedDialog(GuiDialog):
    oldLabelsLost = {'partial':[], '???':[]}
    newLabelsLost = {'???':[]}
    
    def hasDetails(self):
        return True

    def getMessage(self):
        return "Some of your labels could not be transferred."

    def getDetails(self):
        return "\n".join([str(a) for a in [self.oldLabelsLost, self.newLabelsLost]])


class Example(QtGui.QWidget):
    _a = False
    
    def __init__(self):
        super(Example, self).__init__()
        
        self.initUI()
        
    def initUI(self):


        qbtn = QtGui.QPushButton('Show', self)
        qbtn.clicked.connect(self.showIt)
        qbtn.resize(qbtn.sizeHint())
        qbtn.move(50, 50)

        qbtn2 = QtGui.QPushButton('Quit', self)
        qbtn2.clicked.connect(QtCore.QCoreApplication.instance().quit)
        qbtn2.resize(qbtn.sizeHint())
        qbtn2.move(100, 50)
        
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Danger,Danger!')
        self.move(500,500)
        self.show()

    def showIt(self):
        d = LabelsChangedDialog(self)
        d.showDialog(blocking=self._a)
        self._a = not self._a

        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ex = Example()


    sys.exit(app.exec_())
    
