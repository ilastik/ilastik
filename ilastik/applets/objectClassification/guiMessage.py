from PyQt4 import QtGui, QtCore
from lazyflow.graph import Graph, Operator, InputSlot
from lazyflow.stype import Opaque
from opObjectClassification import OpBadObjectsToWarningMessage

from ilastik.utility.gui import ThunkEventHandler


class GuiDialog(QtGui.QMessageBox):

    title = "Warning"
    text = None
    info = None
    details = None
    
    _icon = QtGui.QMessageBox.Warning

    def __init__(self, parent=None):
        super(GuiDialog, self).__init__(parent)
        self.thunkEventHandler = ThunkEventHandler(self)

    def showDialog(self, blocking=False):
        self._blocking = blocking
        self.thunkEventHandler.post(self._showDialog)
        
    def _showDialog(self):
        # must be called from GUI thread!
        self._setup()
        self.setModal(self._blocking)
        self.show()

    def _setup(self):
        def nn(a):
            return a if a is not None else ""
        self.setWindowTitle(nn(self.getTitle()))
        self.setText(nn(self.getMessage()))
        self.setInformativeText(nn(self.getInfo()))
        if self.hasDetails():
            self.setDetailedText(nn(self.getDetails()))
            
        self.icon = self._icon

    def getMessage(self):
        """
        Main content for message box.
        """ 
        return self.text
    
    def getTitle(self):
        """
        Title for message box.
        """ 
        return self.title
    
    def getInfo(self):
        """
        Informative content for message box.
        """ 
        return self.info

    def hasDetails(self):
        """
        
        """
        return self.details is not None

    def getDetails(self):
        """
        Details for message box.
        """ 
        return self.details
    


class LabelsChangedDialog(GuiDialog):
    labelsLost = {'conflict':[],'partial':[],'full':[]}
    messages = {'full': "These labels were lost completely:", 'partial': "These labels were lost partially:", 'conflict': "These new labels conflicted:"}
    defaultMessage = "These labels could not be transferred:"
    
    _sep = "\t"
    
    def hasDetails(self):
        return True

    def getMessage(self):
        return "Some of your labels could not be transferred."

    def getDetails(self):
        cases = []
        for k in self.labelsLost.keys():
            if len(self.labelsLost[k])>0:
                msg = self.messages[k] if k in self.messages.keys() else self.defaultMessage
                axis = self._sep.join(["X", "Y", "Z"])
                coords = "\n".join([self._sep.join(["{:<8.1f}".format(i) for i in item]) for item in self.labelsLost[k]])
                cases.append("\n".join([msg,axis,coords]))
        return "\n\n".join(cases)


    
class OpGuiDialog(Operator):
    name = "OpGuiDialog"
    Input = InputSlot(stype=Opaque)
    dialog = None

    def setupOutputs(self):
        super(OpGuiDialog, self).setupOutputs()
    
    def execute(self, slot, subindex, roi, result):
        pass
        
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input and self.dialog is not None:
            #TODO what if the dialog was not set up correctly?
            d = self.Input[:].wait()
            self.dialog.title = d['title']
            self.dialog.text = d['text']
            self.dialog.info = d['info']
            self.dialog.details = d['details']
            self.dialog.showDialog()
            

#  ### EXAMPLE USAGE ###

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
        case = 2
        
        if case == 1: # LabelsChangedDialog
            d = LabelsChangedDialog(self)
            d.labelsLost['partial'] = [(15,7.5,1000), (700000,12.55,23)]
            d.showDialog(blocking=self._a)
            self._a = not self._a
            
            
        elif case == 2: # OpWarning
            opwarn = OpBadObjectsToWarningMessage(graph=Graph())
            opdialog = OpGuiDialog(graph=Graph())
            opdialog.inputslot.connect(opwarn.WarningMessage)
            opdialog.dialog = GuiDialog(self)
            opwarn.BadObjects.setValue("Hello World!")
            
            
        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ex = Example()


    sys.exit(app.exec_())
    
