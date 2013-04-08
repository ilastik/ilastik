import os
import datetime

from PyQt4 import uic
from PyQt4.QtCore import Qt, QSettings
from PyQt4.QtGui import QWidget, QIcon, QFileDialog

from eventRecorder import EventRecorder

class EventRecorderGui(QWidget):
    
    def __init__(self, parent=None):
        super( EventRecorderGui, self ).__init__(parent)
        uiPath = os.path.join( os.path.split(__file__)[0], 'eventRecorderGui.ui' )
        uic.loadUi(uiPath, self)

        self.setWindowTitle("Event Recorder")

        self.startButton.clicked.connect( self._onStart )
        self.pauseButton.clicked.connect( self._onPause )
        self.saveButton.clicked.connect( self._onSave )
        self.insertCommentButton.clicked.connect( self._onInsertComment )
        
        self._recorder = None
        
        self.pauseButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.newCommentEdit.setEnabled(True)
        self.commentsDisplayEdit.setReadOnly(True)

        self.startButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.pauseButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.saveButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        from ilastik.shell.gui.iconMgr import ilastikIcons
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
            # Auto-add the comment (if any)
            if self.newCommentEdit.toPlainText() != "":
                self._onInsertComment()
            # Unpause the recorder
            self._recorder.unpause()
            self.pauseButton.setText( "Pause" )
            self.pauseButton.setChecked( False )
        else:
            # Pause the recorder
            self._recorder.pause()
            self.pauseButton.setText( "Unpause" )
            self.pauseButton.setChecked( True )

    def _onSave(self):
        # If we are actually playing a recording right now, then the "Stop Recording" action gets triggered as the last step.
        # Ignore it.
        if self._recorder is None:
            return

        if not self._recorder.paused:
            self._onPause()

        self.startButton.setEnabled(True)
        
        settings = QSettings("Ilastik", "Event Recorder")
        variant = settings.value("recordings_directory")
        if not variant.isNull():
            default_dir = str( variant.toString() )
        else:
            import ilastik
            ilastik_module_root = os.path.split(ilastik.__file__)[0]
            ilastik_repo_root = os.path.split( ilastik_module_root )[0]
            default_dir = os.path.join( ilastik_repo_root, "tests" )

        now = datetime.datetime.now()
        timestr = "{:04d}{:02d}{:02d}-{:02d}{:02d}".format( now.year, now.month, now.minute, now.hour, now.second )
        default_script_path = os.path.join( default_dir, "recording-{timestr}.py".format( timestr=timestr ) )
            
        dlg = QFileDialog(self, "Save Playback Script", default_script_path, "Ilastik event playback scripts (*.py)")
        dlg.setObjectName("event_recorder_save_dlg")
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setOptions( QFileDialog.Options(QFileDialog.DontUseNativeDialog) )
        dlg.exec_()
        
        # If the user cancelled, stop now
        if dlg.result() == QFileDialog.Rejected:
            return
    
        script_path = str(dlg.selectedFiles()[0])
        
        # Remember the directory as our new default
        default_dir = os.path.split(script_path)[0]
        settings.setValue( "recordings_directory", default_dir )
        
        with open(script_path, 'w') as f:
            self._recorder.writeScript(f)
            
    def _onInsertComment(self):
        comment = self.newCommentEdit.toPlainText()
        self._recorder.insertComment( comment )
        self.commentsDisplayEdit.appendPlainText("--------------------------------------------------")
        self.commentsDisplayEdit.appendPlainText( comment )
        self.newCommentEdit.clear()







