from PyQt4.QtGui import QDialog, QFileDialog, QRegExpValidator, QPalette
from PyQt4.QtCore import QRegExp, Qt
from PyQt4 import uic
import os
from opStackWriter import OpStackWriter
from lazyflow.operators.ioOperators import OpH5Writer 


class ExportDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        self.initUic()

    def initUic(self):
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        uic.loadUi(p+"exportDlg.ui", self)
        
        self.pushButtonPath.clicked.connect(self.on_pushButtonPathClicked)
        self.lineEditSubvolume.textEdited.connect(self.lineEditSubvolumeChanged)
        self.radioButtonH5.clicked.connect(self.on_radioButtonH5Clicked)
        self.radioButtonStack.clicked.connect(self.on_radioButtonStackClicked)
        self.comboBoxStackFileType.currentIndexChanged.connect(self.comboBoxStackFileTypeChanged)
        
        self.groupBoxStackOptions.setVisible(False)
        
        self.populateDlg()
        
    def comboBoxStackFileTypeChanged(self, int):
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
        
    def on_radioButtonStackClicked(self):
        self.groupBoxStackOptions.setVisible(True)
        self.groupBoxH5Options.setVisible(False)
        self.correctFilePathSuffix()
        
    def on_radioButtonH5Clicked(self):
        self.groupBoxH5Options.setVisible(True)
        self.groupBoxStackOptions.setVisible(False)
        self.correctFilePathSuffix()
        
    def lineEditSubvolumeChanged(self, text):
        lineStr = str(self.lineEditSubvolume.displayText())
        if lineStr == "" or not lineStr.endswith("%c"):
            self.setLineEditSubvolume()
        self.lineEditSubvolumeValidation()
        
    def populateDlg(self):
        self.folderPath = os.path.abspath(__file__)
        self.folderPath = self.folderPath.split("/")
        self.folderPath = self.folderPath[0:-1]
        self.folderPath.append("Untitled.h5")
        self.folderPath = "/".join(self.folderPath)
        self.setLineEditFilePath(self.folderPath)
        
    def setWorkflow(self, workflow, graph):
        self.workflow = workflow
        self.graph = graph
        self.setVolumeShapeInfo()
        self.setLineEditSubvolume()
        self.setRegExToLineEditSubvolume()
        self.lineEditSubvolumeValidation()
        self.setDefaultComboBoxHdf5DataType()
        
    def setDefaultComboBoxHdf5DataType(self):
        dtype = str(self.workflow.images.outputs["Outputs"][0].dtype)
        for i in range(self.comboBoxHdf5DataType.count()):
            if dtype == str(self.comboBoxHdf5DataType.itemText(i)):
                self.comboBoxHdf5DataType.setCurrentIndex(i)
        
    def lineEditSubvolumeValidation(self):
        r = self.lineEditSubvolume.validator().regExp()
        r.indexIn(self.lineEditSubvolume.displayText())
        j = 0
        isValid = 0
        for i in range(r.captureCount()):
            if not i % 4:
                if not r.cap(i+1).isEmpty() and not r.cap(i+3).isEmpty():
                    if int(r.cap(i+1)) >= 0 and int(r.cap(i+1)) <=  int(r.cap(i+3)) and int(r.cap(i+3)) <= self.workflow.images.outputs["Outputs"][0].shape[j]: 
                        isValid+=1 
                j+=1
        p = self.lineEditSubvolume.palette()
        if isValid==j:
            p.setColor(QPalette.Base, Qt.white)
        else:
            p.setColor(QPalette.Base, Qt.red)
        self.lineEditSubvolume.setPalette(p)
        
    def setRegExToLineEditSubvolume(self):
        regString = ""
        for i in range(len(self.workflow.images.outputs["Outputs"][0].axistags)):
            regString = regString + "([0-9]*)(-)([0-9]*)(%" + self.workflow.images.outputs["Outputs"][0].axistags[i].key + ")"
        r = QRegExp(regString)
        self.lineEditSubvolume.setValidator(QRegExpValidator(r, self.lineEditSubvolume))
        
    def setLineEditSubvolume(self):
        text = ""
        for i in range(len(self.workflow.images.outputs["Outputs"][0].shape)):
            text = text + "0-" + str(self.workflow.images.outputs["Outputs"][0].shape[i]) + "%" + str(self.workflow.images.outputs["Outputs"][0].axistags[i].key)
        self.lineEditSubvolume.setText(text)
        
    def setVolumeShapeInfo(self):
        text = ""
        for i in range(len(self.workflow.images.outputs["Outputs"][0].shape)):
            text = text + "%s : %d    " % (self.workflow.images.outputs["Outputs"][0].axistags[i].key, self.workflow.images.outputs["Outputs"][0].shape[i])
        self.labelShape.setText(text)
        
    def setLineEditFilePath(self, filePath):
        self.lineEditFilePath.setText(filePath)
        
    def on_pushButtonPathClicked(self):
        oldPath = self.lineEditFilePath.displayText()
        fileDlg = QFileDialog()
        newPath = str(fileDlg.getSaveFileName(self, "Save File", str(self.lineEditFilePath.displayText())))
        if newPath == "":
            newPath = oldPath
        self.lineEditFilePath.setText(newPath)
        self.correctFilePathSuffix()
        
    def createRoiForSubvolume(self):
        r = self.lineEditSubvolume.validator().regExp()
        r.indexIn(self.lineEditSubvolume.displayText())
        j = 0
        start = []
        stop = []
        for i in range(r.captureCount()):
            if not i % 4:
                start.append(int(r.cap(i+1)))
                stop.append(int(r.cap(i+3)))
                j+=1
        return [start, stop]
    
    def createKeyForSubvolume(self):
        r = self.lineEditSubvolume.validator().regExp()
        r.indexIn(self.lineEditSubvolume.displayText())
        j = 0
        key = []
        for i in range(r.captureCount()):
            if not i % 4:
                key.append(slice(int(r.cap(i+1)), int(r.cap(i+3))-1))
                j+=1
        return key
    
    def createNormalizeValue(self):
        if self.groupBoxNormalize.isChecked():
            start = int(self.spinBoxNormalizeStart.value()) 
            stop = int(self.spinBoxNormalizeStop.value())
        else:
            start = 0
            stop = 255
        
        return [start, stop]
    
    
    def exec_(self):
        if QDialog.exec_(self) == QDialog.Accepted:
            if self.radioButtonStack.isChecked():
                key = self.createKeyForSubvolume()
                writer = OpStackWriter(self.graph)
                writer.inputs["input"].connect(self.workflow.images.outputs["Outputs"][0])
                writer.inputs["filepath"].setValue(str(self.lineEditFilePath.displayText()))
                writer.outputs["WritePNGStack"][key].allocate().wait()
                
            if self.radioButtonH5.isChecked():
                h5Key = self.createRoiForSubvolume()
                writerH5 = OpH5Writer(self.graph)
                writerH5.inputs["filename"].setValue(str(self.lineEditFilePath.displayText()))
                writerH5.inputs["hdf5Path"].setValue(str(self.lineEditHdf5Path.displayText()))
                writerH5.inputs["input"].connect(self.workflow.images.outputs["Outputs"][0])
                writerH5.inputs["blockShape"].setValue(int(self.spinBoxHdf5BlockShape.value()))
                writerH5.inputs["dataType"].setValue(str(self.comboBoxHdf5DataType.currentText()))
                writerH5.inputs["roi"].setValue(h5Key)
                writerH5.inputs["normalize"].setValue(self.createNormalizeValue())
                writerH5.outputs["WriteImage"][:].allocate().wait()

        
if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    app = QApplication(list())
    d = ExportDialog()
    d.setVolumeShapeInfo([4,30,25,42,2])
    d.show()
    app.exec_()
