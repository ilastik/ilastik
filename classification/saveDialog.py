from PyQt4.QtGui import QDialog, QFileDialog, QRegExpValidator, QPalette
from PyQt4.QtCore import QRegExp, Qt
from PyQt4 import uic
import os
from opStackWriter import OpStackWriter
from lazyflow.operators.ioOperators import OpH5Writer 


class SaveDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        self.initUic()

    def initUic(self):
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        uic.loadUi(p+"saveDialog.ui", self)
        
        self.folderPath = os.path.abspath(__file__)
        self.folderPath = self.folderPath.split("/")
        self.folderPath = self.folderPath[0:-1]
        self.folderPath = "/".join(self.folderPath)
        
        self.setFilePathToLabel()
        self.buttonSelectPath.clicked.connect(self.on_buttonSelectPathClicked)
        self.comboBoxFileTypes.currentIndexChanged.connect(self.on_comboBoxFileTypesChanged)
        self.lineEditFileName.textEdited.connect(self.on_lineEditFileNameChanged)
        self.lineEditVolumeShape.textEdited.connect(self.on_lineEditVolumeShapeChanged)
        
    def on_lineEditFileNameChanged(self, text):
        self.setFilePathToLabel()

    def on_buttonSelectPathClicked(self):
            self.folderPath = QFileDialog.getExistingDirectory(self, "Select Folder", os.path.abspath(__file__))
            self.setFilePathToLabel()
    
    def on_comboBoxFileTypesChanged(self, int):
        self.setFilePathToLabel()
        
    def on_lineEditVolumeShapeChanged(self, text):
        lineStr = str(self.lineEditVolumeShape.displayText())
        if lineStr == "" or not lineStr.endswith("%c"):
            self.setLineEditVolumeShape()
        self.lineEditVolumeShapeValidation()
        
    def lineEditVolumeShapeValidation(self):
        r = self.lineEditVolumeShape.validator().regExp()
        r.indexIn(self.lineEditVolumeShape.displayText())
        j = 0
        isValid = 0
        for i in range(r.captureCount()):
            if not i % 4:
                if not r.cap(i+1).isEmpty() and not r.cap(i+3).isEmpty():
                    if int(r.cap(i+1)) >= 0 and int(r.cap(i+1)) <=  int(r.cap(i+3)) and int(r.cap(i+3)) <= self.workflow.images.outputs["Outputs"][0].shape[j]: 
                        isValid+=1 
                j+=1
        p = self.lineEditVolumeShape.palette()
        if isValid==j:
            p.setColor(QPalette.Base, Qt.white)
        else:
            p.setColor(QPalette.Base, Qt.red)
        self.lineEditVolumeShape.setPalette(p)
        
        
    def setRegExToLineEditVolumeShape(self):
        regString = ""
        for i in range(len(self.workflow.images.outputs["Outputs"][0].axistags)):
            regString = regString + "([0-9]*)(-)([0-9]*)(%" + self.workflow.images.outputs["Outputs"][0].axistags[i].key + ")"
        r = QRegExp(regString)
        self.lineEditVolumeShape.setValidator(QRegExpValidator(r, self.lineEditVolumeShape))
        
    def createKeyForSubvolume(self):
        r = self.lineEditVolumeShape.validator().regExp()
        r.indexIn(self.lineEditVolumeShape.displayText())
        j = 0
        key = []
        for i in range(r.captureCount()):
            if not i % 4:
                key.append(slice(int(r.cap(i+1)), int(r.cap(i+3))-1))
                j+=1
        return key
    
    def createKeyForSubvolumeH5(self):
        r = self.lineEditVolumeShape.validator().regExp()
        r.indexIn(self.lineEditVolumeShape.displayText())
        j = 0
        start = []
        stop = []
        for i in range(r.captureCount()):
            if not i % 4:
                start.append(int(r.cap(i+1)))
                stop.append(int(r.cap(i+3)))
                j+=1
        return [start, stop]
        
    
    def setLineEditVolumeShape(self):
        text = ""
        for i in range(len(self.workflow.images.outputs["Outputs"][0].shape)):
            text = text + "0-" + str(self.workflow.images.outputs["Outputs"][0].shape[i]) + "%" + str(self.workflow.images.outputs["Outputs"][0].axistags[i].key)
        self.lineEditVolumeShape.setText(text)
            
        
        
    def setFilePathToLabel(self):
        self.labelFolderPath.setText(self.folderPath + "/" + self.lineEditFileName.displayText() + "." + self.comboBoxFileTypes.currentText())
        
    
    def setVolumeInfoToLabel(self):
        text = ""
        for i in range(len(self.workflow.images.outputs["Outputs"][0].shape)):
            text = text + "%s : %d    " % (self.workflow.images.outputs["Outputs"][0].axistags[i].key, self.workflow.images.outputs["Outputs"][0].shape[i])
        self.labelVolumeInfo.setText(text)

    def setWorkflow(self, workflow, graph):
        self.workflow = workflow
        self.graph = graph
        self.setVolumeInfoToLabel()
        self.setLineEditVolumeShape()
        self.setRegExToLineEditVolumeShape()
        self.lineEditVolumeShapeValidation()

    
    def exec_(self):
        if QDialog.exec_(self) == QDialog.Accepted:
            if self.radioButtonStack.isChecked():
                key = self.createKeyForSubvolume()
                writer = OpStackWriter(self.graph)
                writer.inputs["input"].connect(self.workflow.images.outputs["Outputs"][0])
                writer.inputs["Filepath"].setValue(str(self.folderPath + "/" + self.lineEditFileName.displayText()))
                writer.inputs["Filetype"].setValue(str(self.comboBoxFileTypes.currentText()))
                writer.outputs["WritePNGStack"][key].allocate().wait()
            if self.radioButtonH5.isChecked():
                h5Key = self.createKeyForSubvolumeH5()
                writerH5 = OpH5Writer(self.graph)
                writerH5.inputs["filename"].setValue(str(self.folderPath + "/" + self.lineEditFileName.displayText() + ".h5"))
                writerH5.inputs["hdf5Path"].setValue("")
                writerH5.inputs["input"].connect(self.workflow.images.outputs["Outputs"][0])
                writerH5.inputs["blockShape"].setValue(5)
                writerH5.inputs["dataType"].setValue("uint8")
                writerH5.inputs["roi"].setValue(h5Key)
                writerH5.inputs["normalize"].setValue([0,255])
                writerH5.outputs["WriteImage"][:].allocate().wait()
                
                

                
            
            
            return
        else:
            return "Cancel"
        
if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    app = QApplication(list())
    d = SaveDialog()
    d.show()
    app.exec_()
