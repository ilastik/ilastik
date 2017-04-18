from PyQt4.QtCore import *
from PyQt4.QtGui import *

from hytra.util.progressbar import DefaultProgressVisitor


class TrackProgress(QThread):
    done = pyqtSignal()
    progress = pyqtSignal(float)
    newStep = pyqtSignal(str)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)

    def run(self):
        pass

class TrackProgressDialog(QDialog):
    finished = pyqtSignal()

    def __init__(self, parent=None, numStages=1):
        QDialog.__init__(self, parent)

        self.currentStep = 0
        self.progress = None

        l = QVBoxLayout()
        self.setLayout(l)

        self.overallProgress = QProgressBar()
        self.overallProgress.setRange(0, numStages)
        self.overallProgress.setFormat("step %v of "+str(numStages))

        self.currentStepProgress = QProgressBar()
        self.currentStepProgress.setRange(0, 100)
        self.currentStepProgress.setFormat("%p %")

        self.overallLabel = QLabel("Overall progress")
        self.currentStepLabel = QLabel("Current step")

        l.addWidget(self.overallLabel)
        l.addWidget(self.overallProgress)
        l.addWidget(self.currentStepLabel)
        l.addWidget(self.currentStepProgress)
        l.maximumSize()

        self.update()

    def __onNewStep(self, description):
        self.currentStep += 1
        self.currentStepProgress.setValue(0)
        self.overallProgress.setValue(self.currentStep)
        self.currentStepLabel.setText(description)
        self.update()

    def __onCurrentStepProgressChanged(self, progress):
        self.currentStepProgress.setValue( round(100.0*progress) )
        self.update()

    def run(self):
        self.trackProgress = TrackProgress(self)
        self.trackProgress.progress.connect(self.__onCurrentStepProgressChanged, Qt.BlockingQueuedConnection)
        self.trackProgress.newStep.connect(self.__onNewStep, Qt.BlockingQueuedConnection)
        self.trackProgress.done.connect(self.onTrackDone)
        self.trackProgress.start()

    def onTrackDone(self):
        self.trackProgress.wait() # Join the extractor thread so its safe to immediately destroy the window
        self.finished.emit()
        self.close()

class GuiProgressVisitor(DefaultProgressVisitor):
    def __init__(self,progressWindow=None):
        self.progressWindow = progressWindow

    def showState(self,name):
        self.progressWindow.trackProgress.newStep.emit(name)

    def showProgress(self,pos):
        self.progressWindow.trackProgress.progress.emit(pos)

