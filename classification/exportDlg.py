from PyQt4.QtGui import QDialog, QFileDialog, QRegExpValidator, QPalette, QDialogButtonBox
from PyQt4.QtCore import QRegExp, Qt
from PyQt4 import uic
import os
from opStackWriter import OpStackWriter
from lazyflow.operators.ioOperators import OpH5Writer 
from lazyflow.roi import TinyVector

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        self.initUic()

    def initUic(self):
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        uic.loadUi(p+"exporterDlg.ui", self)
        
        self.checkBoxDummyList = [self.checkBoxDummy1, self.checkBoxDummy2, self.checkBoxDummy3, self.checkBoxDummy4, \
                                  self.checkBoxDummy5, self.checkBoxDummy6]
        self.lineEditInputShapeList = [self.lineEditInputShapeT, self.lineEditInputShapeX, self.lineEditInputShapeY, \
                                    self.lineEditInputShapeZ, self.lineEditInputShapeC]
        self.lineEditOutputShapeList = [self.lineEditOutputShapeT, self.lineEditOutputShapeX, self.lineEditOutputShapeY, \
                                     self.lineEditOutputShapeZ, self.lineEditOutputShapeC]
        
        #=======================================================================
        # connections
        #=======================================================================
        self.pushButtonPath.clicked.connect(self.on_pushButtonPathClicked)
        self.radioButtonH5.clicked.connect(self.on_radioButtonH5Clicked)
        self.radioButtonStack.clicked.connect(self.on_radioButtonStackClicked)
        self.comboBoxStackFileType.currentIndexChanged.connect(self.comboBoxStackFileTypeChanged)
        self.checkBoxDummy1.stateChanged.connect(self.on_checkBoxDummyClicked)
        self.checkBoxDummy2.stateChanged.connect(self.on_checkBoxDummyClicked)
        self.checkBoxDummy3.stateChanged.connect(self.on_checkBoxDummyClicked)
        self.checkBoxDummy4.stateChanged.connect(self.on_checkBoxDummyClicked)
        self.checkBoxDummy5.stateChanged.connect(self.on_checkBoxDummyClicked)
        self.checkBoxDummy6.stateChanged.connect(self.on_checkBoxDummyClicked)
        self.checkBoxNormalize.stateChanged.connect(self.on_checkBoxNormalizeClicked)
        self.lineEditOutputShapeX.textEdited.connect(self.lineEditOutputShapeChanged)
        self.lineEditOutputShapeY.textEdited.connect(self.lineEditOutputShapeChanged)
        self.lineEditOutputShapeZ.textEdited.connect(self.lineEditOutputShapeChanged)
        self.lineEditOutputShapeT.textEdited.connect(self.lineEditOutputShapeChanged)
        self.lineEditOutputShapeC.textEdited.connect(self.lineEditOutputShapeChanged)
        #=======================================================================
        # style
        #=======================================================================
        self.on_radioButtonH5Clicked()
        self.on_checkBoxNormalizeClicked(0)
        
        folderPath = os.path.abspath(__file__)
        folderPath = folderPath.split("/")
        folderPath = folderPath[0:-1]
        folderPath.append("Untitled.h5")
        folderPath = "/".join(folderPath)
        self.setLineEditFilePath(folderPath)
        
        
#===============================================================================
# set input data informations
#===============================================================================
    def setInput(self, input, graph):
        self.input = input
        self.graph = graph
        self.setVolumeShapeInfo()
        self.setRegExToLineEditOutputShape()
        self.setDefaultComboBoxHdf5DataType()
        
    def setVolumeShapeInfo(self):
        for i in range(len(self.input.shape)):
            self.lineEditInputShapeList[i].setText("0 - %d" % (int(self.input.shape[i])-1))
            self.lineEditOutputShapeList[i].setText("0 - %d" % (int(self.input.shape[i])-1))
            
    def setRegExToLineEditOutputShape(self):
        r = QRegExp("([0-9]*)(-|\W)+([0-9]*)")
        for i in self.lineEditOutputShapeList:
            i.setValidator(QRegExpValidator(r, i))
            
    def setDefaultComboBoxHdf5DataType(self):
        dtype = str(self.input.dtype)
        for i in range(self.comboBoxHdf5DataType.count()):
            if dtype == str(self.comboBoxHdf5DataType.itemText(i)):
                self.comboBoxHdf5DataType.setCurrentIndex(i)
#===============================================================================
# file
#===============================================================================
    def on_pushButtonPathClicked(self):
        oldPath = self.lineEditFilePath.displayText()
        fileDlg = QFileDialog()
        newPath = str(fileDlg.getSaveFileName(self, "Save File", str(self.lineEditFilePath.displayText())))
        if newPath == "":
            newPath = oldPath
        self.lineEditFilePath.setText(newPath)
        self.correctFilePathSuffix()
    
    def correctFilePathSuffix(self):
        path = str(self.lineEditFilePath.displayText())
        path = path.split("/")
        if self.radioButtonH5.isChecked():
            filetype = "h5"
        if self.radioButtonStack.isChecked():
            filetype = str(self.comboBoxStackFileType.currentText())
        if not path[-1].endswith("."+filetype):
            if "." not in path[-1]:
                path[-1] = path[-1] + "." + filetype
            else:
                path[-1] = path[-1].split(".")
                path[-1] = path[-1][0:-1]
                path[-1].append(filetype)
                path[-1] = ".".join(path[-1])
        path = "/".join(path)
        self.lineEditFilePath.setText(path)
        
#===============================================================================
# output formats
#===============================================================================
    def on_radioButtonH5Clicked(self):
        self.widgetOptionsHDF5.setVisible(True)
        self.widgetOptionsStack.setVisible(False)
        self.correctFilePathSuffix()
        
    def on_radioButtonStackClicked(self):
        self.widgetOptionsHDF5.setVisible(False)
        self.widgetOptionsStack.setVisible(True)
        self.correctFilePathSuffix()
        
#===============================================================================
# options
#===============================================================================
    def on_checkBoxNormalizeClicked(self, int):
        if int == 0:
            self.spinBoxNormalizeStart.setDisabled(True)
            self.spinBoxNormalizeStop.setDisabled(True)
        else:
            self.spinBoxNormalizeStart.setDisabled(False)
            self.spinBoxNormalizeStop.setDisabled(False)
            
    def on_checkBoxDummyClicked(self):
        checkedList = []
        for i in range(len(self.checkBoxDummyList)):
            if self.checkBoxDummyList[i].isChecked():
                checkedList.append(str(self.checkBoxDummyList[i].text()))
        return checkedList
    
    def comboBoxStackFileTypeChanged(self, int):
        self.correctFilePathSuffix()
    #===========================================================================
    # lineEditOutputShape    
    #===========================================================================
    def lineEditOutputShapeListValidation(self):
        isValid = True
        for i in range(len(self.lineEditOutputShapeList)):
            r = self.lineEditOutputShapeList[i].validator().regExp()
            r.indexIn(self.lineEditOutputShapeList[i].displayText())
            p = self.lineEditOutputShapeList[i].palette()
            if r.cap(1) == "" or r.cap(2) == "" or r.cap(3) == "" or \
            int(r.cap(1)) > int(r.cap(3)) or int(r.cap(3)) > int(self.input.shape[i])-1:
                p.setColor(QPalette.Base, Qt.red)
                p.setColor(QPalette.Text,Qt.white)
                isValid = False
            else:
                p.setColor(QPalette.Base, Qt.white)
                p.setColor(QPalette.Text,Qt.black)
            self.lineEditOutputShapeList[i].setPalette(p)
        if isValid:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def setLineEditFilePath(self, filePath):
        self.lineEditFilePath.setText(filePath)
        
    def lineEditOutputShapeChanged(self):
        self.lineEditOutputShapeListValidation()
        
#===============================================================================
# create values
#===============================================================================
    def createNormalizeValue(self):
        if self.checkBoxNormalize.isChecked():
            return [int(self.spinBoxNormalizeStart.value()) , int(self.spinBoxNormalizeStop.value())]
        else:
            return -1
    
    def createKeyForOutputShape(self):
        key = []
        for i in range(len(self.lineEditOutputShapeList)):
            r = self.lineEditOutputShapeList[i].validator().regExp()
            r.indexIn(self.lineEditOutputShapeList[i].displayText())
            key.append(slice(int(r.cap(1)), int(r.cap(3)), 1))
        return key
        
    
    def createRoiForOutputShape(self):
        start = []
        stop = []
        for i in range(len(self.lineEditOutputShapeList)):
            r = self.lineEditOutputShapeList[i].validator().regExp()
            r.indexIn(self.lineEditOutputShapeList[i].displayText())
            start.append(int(r.cap(1)))
            stop.append(int(r.cap(3)))
        return [TinyVector(start), TinyVector(stop)]



    def exec_(self):
        if QDialog.exec_(self) == QDialog.Accepted:
            if self.radioButtonStack.isChecked():
                key = self.createKeyForOutputShape()
                writer = OpStackWriter(self.graph)
                writer.inputs["input"].connect(self.input)
                writer.inputs["filepath"].setValue(str(self.lineEditFilePath.displayText()))
                writer.inputs["dummy"].setValue(["zt"])
                writer.outputs["WritePNGStack"][key].allocate().wait()
                
            if self.radioButtonH5.isChecked():
                h5Key = self.createRoiForOutputShape()
                print h5Key, "###############################################"
                writerH5 = OpH5Writer(self.graph)
                writerH5.inputs["filename"].setValue(str(self.lineEditFilePath.displayText()))
                writerH5.inputs["hdf5Path"].setValue(str(self.lineEditHdf5Path.displayText()))
                writerH5.inputs["input"].connect(self.input)
                writerH5.inputs["blockShape"].setValue(int(self.spinBoxHdf5BlockShape.value()))
                writerH5.inputs["dataType"].setValue(str(self.comboBoxHdf5DataType.currentText()))
                writerH5.inputs["roi"].setValue(h5Key)
                writerH5.inputs["normalize"].setValue(self.createNormalizeValue())
                writerH5.outputs["WriteImage"][:].allocate().wait()
    
        
        
        
            
        
if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    app = QApplication(list())
    d = ExportDialog()
    d.show()
    app.exec_()