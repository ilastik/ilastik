from __future__ import print_function, absolute_import, nested_scopes, generators, division, with_statement, unicode_literals
import sys

from PyQt5.QtCore import pyqtSignal, QThread, Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QLabel

from ilastik.utility.progress import DefaultProgressVisitor, CommandLineProgressVisitor
from ilastik.utility.gui.threadRouter import ThreadRouter, threadRouted

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

        self.threadRouter = ThreadRouter(self)
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

    @threadRouted
    def __onNewStep(self, description):
        self.currentStep += 1
        self.currentStepProgress.setValue(0)
        self.overallProgress.setValue(self.currentStep)
        self.currentStepLabel.setText(description)
        self.update()

    @threadRouted
    def __onCurrentStepProgressChanged(self, progress):
        timesHundred = round(1000.0*progress)
        timesTen = round(100.0*progress)
        if ( not self.currentStepProgress.value() == timesTen ) and   (timesHundred - 10*timesTen)==0:
            self.currentStepProgress.setValue( timesTen )
            self.update()

    @threadRouted
    def run(self):
        self.trackProgress = TrackProgress(self)
        self.trackProgress.progress.connect(self.__onCurrentStepProgressChanged, Qt.BlockingQueuedConnection)
        self.trackProgress.newStep.connect(self.__onNewStep, Qt.BlockingQueuedConnection)
        self.trackProgress.done.connect(self.onTrackDone)
        self.trackProgress.start()

    @threadRouted
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

