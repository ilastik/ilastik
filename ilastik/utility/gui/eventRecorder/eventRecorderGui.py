import os

from PyQt4 import uic
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QWidget, QIcon

from eventRecorder import EventRecorder

from ilastik.shell.gui.iconMgr import ilastikIcons

class EventRecorderGui(QWidget):
    
    def __init__(self, parent=None):
        super( EventRecorderGui, self ).__init__(parent)
        uiPath = os.path.join( os.path.split(__file__)[0], 'eventRecorderGui.ui' )
        uic.loadUi(uiPath, self)

        self.startButton.clicked.connect( self._onStart )
        self.pauseButton.clicked.connect( self._onPause )
        self.saveButton.clicked.connect( self._onSave )
        self.insertCommentButton.clicked.connect( self._onInsertComment )
        
        self._recorder = None
        
        self.pauseButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.insertCommentButton.setEnabled( False )
        self.newCommentEdit.setEnabled(True)
        self.commentsDisplayEdit.setReadOnly(True)

        self.startButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.pauseButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.saveButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.startButton.setIcon( QIcon(ilastikIcons.Play) )
        self.pauseButton.setIcon( QIcon(ilastikIcons.Pause) )
        self.saveButton.setIcon( QIcon(ilastikIcons.Stop) )

    def _onStart(self):
        self._recorder = EventRecorder( parent=self )
        self.startButton.setEnabled(False)
        self.pauseButton.setEnabled(True)
        if self.newCommentEdit.toPlainText() != "":
            self._onInsertComment()
        self._onPause()
        self.saveButton.setEnabled(True)

    def _onPause(self):
        if self._recorder.paused:
            # Unpause the recorder
            self._recorder.unpause()
            self.pauseButton.setText( "Pause" )
            self.pauseButton.setChecked( False )
            self.insertCommentButton.setEnabled( False )
        else:
            # Pause the recorder
            self._recorder.pause()
            self.pauseButton.setText( "Unpause" )
            self.pauseButton.setChecked( True )
            self.insertCommentButton.setEnabled( True )

    def _onSave(self):
        # If we are actually playing a recording right now, then the "Stop Recording" action gets triggered as the last step.
        # Ignore it.
        if self._recorder is None:
            return

        if not self._recorder.paused:
            self._onPause()
        with open('/tmp/recording.py', 'w') as f:
            self._recorder.writeScript(f)
            
        self.pauseButton.setEnabled(False)
        self.startButton.setEnabled(True)

    def _onInsertComment(self):
        comment = self.newCommentEdit.toPlainText()
        self._recorder.insertComment( comment )
        self.commentsDisplayEdit.appendPlainText("--------------------------------------------------")
        self.commentsDisplayEdit.appendPlainText( comment )
        self.newCommentEdit.clear()







