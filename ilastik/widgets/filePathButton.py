import os
from PyQt4.QtGui import QToolButton, QSizePolicy

class FilePathButton(QToolButton):
    """
    A QToolButton for displaying a filepath (with a suffix).
    If the button is resized and the text is too long to fit, the path is automatically abbreviated by replacing intermediate paths with '...'
    """
    
    def __init__(self, filepath, suffix, parent=None):
        """
        filepath: The path to show.  Will be abbreviated if necessary to fit within the button.
        suffix: Always appended to the button text. Never abbreviated.
        """
        super( FilePathButton, self ).__init__(parent)
        self._filepath = filepath
        self._suffix = suffix

        # Determine the shortest possible text we could display,
        #  and use it to set our minimum width
        drive = os.path.splitdrive(self._filepath)[0]
        self.setText( drive + '/.../' + os.path.split(self._filepath)[1] + self._suffix )
        self.setMinimumWidth( self.minimumSizeHint().width() )
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        
        # By default, show the full path
        self.setText( self._filepath + self._suffix )
        self.setToolTip( self.text() )
    
    def resizeEvent( self, event ):
        # Start with the full path
        short_filepath = self._filepath
        self.setText( self._filepath + self._suffix )
        ideal_width = self.minimumSizeHint().width()

        # Keep removing intermediate directories until the text fits inside the new width
        while event.size().width() < ideal_width:
            drive, short_filepath = os.path.splitdrive(short_filepath)
            dirpath, filename = os.path.split(short_filepath)

            dir_names = dirpath.split(os.sep)[1:]
            if len(dir_names) == 0 or (len(dir_names) == 1 and dir_names[0] == '...'):
                # This path is already as short as possible.  Give up.
                return
            
            if dir_names and dir_names[0] == '...':
                dir_names = dir_names[1:]
            dir_names = [''] + ['...'] + dir_names[1:]
            dirpath = os.sep.join( dir_names )
            
            # Always include drive
            short_filepath = drive + os.path.join( dirpath, filename )
            self.setText( short_filepath + self._suffix )
            ideal_width = self.minimumSizeHint().width()

if __name__ == "__main__":
    from PyQt4.QtGui import QApplication, QWidget, QVBoxLayout
    
    app = QApplication([])

    SIMULATE_WINDOWS = True
    if SIMULATE_WINDOWS:
        import ntpath
        os.sep = ntpath.sep
        os.path = ntpath
        
        buttons = []
        buttons.append( FilePathButton( r"c:\some\long\path\to\the\file.txt", " (Don't abbreviate this suffix)") )
        buttons.append( FilePathButton( r"file.txt", " (some suffix)") )
        buttons.append( FilePathButton( "\\some\\long\\path\\to\\the\\", " (some suffix)") )
    else:
        buttons = []
        buttons.append( FilePathButton( "/some/long/path/to/the/file.txt", " (Don't abbreviate this suffix)") )
        buttons.append( FilePathButton( "file.txt", " (some suffix)") )
        buttons.append( FilePathButton( "/some/long/path/to/the/", " (some suffix)") )

    layout = QVBoxLayout()
    for button in buttons:
        # Typically, the button chooses a minimum size that is appropriate for its shortest possible text
        # But for this little test we force an even smaller minimum size so we can test multiple paths at once...
        button.setMinimumWidth(10)
        layout.addWidget(button)

    widget = QWidget()
    widget.setLayout(layout)
    widget.show()
    
    app.exec_()
