import re
import abc
import collections

from PyQt4.QtGui import QDialog, QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, \
                        QLabel, QLineEdit, QPushButton, QSpacerItem, QKeySequence

from ilastik.utility import Singleton, PreferencesManager

def _has_attribute( cls, attr ):
    return any(attr in B.__dict__ for B in cls.__mro__)

def _has_attributes( cls, attrs ):
    return all(_has_attribute(cls, a) for a in attrs)

class ObjectWithToolTipABC(object):
    """
    Defines an ABC for objects that have toolTip() and setToolTip() members.
    Note: All QWidgets already implement this ABC.
    
    When a shortcut is registered with the shortcut manager, clients can (optionally) 
    provide an object that updates the tooltip text for the shortcut.
    That object must adhere to this interface.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def toolTip(self):
        raise NotImplementedError()
    
    @abc.abstractmethod
    def setToolTip(self, tip):
        raise NotImplementedError()
    
    @classmethod
    def __subclasshook__(cls, C):
        if cls is ObjectWithToolTipABC:
            return _has_attributes(C, ['toolTip', 'setToolTip'])
        return NotImplemented

class ShortcutManager(object):
    """
    Singleton object.
    Maintains a global list of shortcuts.
    If an object is provided when the shortcut is registered, the object's tooltip is updated to show the shortcut keys.
    """
    __metaclass__ = Singleton
    
    PreferencesGroup = "Keyboard Shortcuts"

    @property
    def shortcuts(self):
        return self._shortcuts

    def __init__(self):
        self._shortcuts = collections.OrderedDict()
    
    def register(self, group, description, shortcut, objectWithToolTip=None):
        """
        Register a shortcut with the shortcut manager.
        
        group - The GUI category of this shortcut
        description - A description of the shortcut action (shows up as default tooltip text)
        shortcut - A QShortcut
        objectWithToolTip - (optional) If provided, used to update the tooltip text with the shortcut keys. (See ABC above)
        """
        assert description is not None
        assert objectWithToolTip is None or isinstance(objectWithToolTip, ObjectWithToolTipABC)

        if not group in self._shortcuts:
            self._shortcuts[group] = collections.OrderedDict()
        self._shortcuts[group][shortcut] = (description, objectWithToolTip)
        
        # If we've got user preferences for this shortcut, apply them now.
        groupKeys = PreferencesManager().get( self.PreferencesGroup, group )
        if groupKeys is not None and description in groupKeys:
            keyseq = groupKeys[description]
            shortcut.setKey( keyseq )
        
        self.updateToolTip( shortcut )

    def unregister(self, shortcut):
        """
        Remove the shortcut from the manager.
        Note that this does NOT disable the shortcut.
        """
        for group in self._shortcuts:
            if shortcut in self._shortcuts[group]:
                del self._shortcuts[group][shortcut]
                break

    def setDescription(self, shortcut, description):
        for group in self._shortcuts:
            if shortcut in self._shortcuts[group]:
                (oldDescription, objectWithToolTip) = self._shortcuts[group][shortcut]
                self._shortcuts[group][shortcut] = (description, objectWithToolTip)
                self.updateToolTip(shortcut)

    def updateToolTip(self, shortcut):
        """
        If this shortcut is associated with an object with tooltip text, 
            the tooltip text is updated to include the shortcut key.

        For example, a button with shortcut 'b' and tooltip "Make it happen!"
            is modified to have tooltip text "Make it happen! [B]"
        """
        description = None
        for group in self._shortcuts:
            if shortcut in self._shortcuts[group]:
                (description, objectWithToolTip) = self._shortcuts[group][shortcut]
                break
            
        assert description is not None, "Couldn't find the shortcut you're trying to update."
        if objectWithToolTip is None:
            return

        oldText = str(objectWithToolTip.toolTip())
        newKeyText = str('[' + shortcut.key().toString() + ']')
        
        if oldText == "":
            oldText = description

        if re.search("\[.*\]", oldText) is None:
            newText = oldText + ' ' + newKeyText
        else:
            newText = re.sub("\[.*\]", newKeyText, oldText)
        
        objectWithToolTip.setToolTip( newText )
    
    def storeToPreferences(self):
        # Auto-save after we're done setting prefs
        with PreferencesManager() as prefsMgr:
            for group, shortcutDict in self.shortcuts.items():
                groupKeys = {}
                for shortcut, (desc, obj) in shortcutDict.items():
                    groupKeys[desc] = shortcut.key() # QKeySequence is pickle-able
                prefsMgr.set( self.PreferencesGroup, group, groupKeys )

class ShortcutManagerDlg(QDialog):
    def __init__(self, *args, **kwargs):
        super(ShortcutManagerDlg, self).__init__(*args, **kwargs)
        self.setWindowTitle("Shortcut Preferences")
        self.setMinimumWidth(500)

        mgr = ShortcutManager() # Singleton
        
        tempLayout = QVBoxLayout()

        # Create a LineEdit for each shortcut,
        # and keep track of them in a dict
        shortcutEdits = dict()
        for group, shortcutDict in mgr.shortcuts.items():
            grpBox = QGroupBox(group)
            l = QGridLayout(self)
            for i, (shortcut, (desc, obj)) in enumerate(shortcutDict.items()):
                l.addWidget(QLabel(desc), i,0)
                edit = QLineEdit(str(shortcut.key().toString()))
                l.addWidget(edit, i,1)
                shortcutEdits[shortcut] = edit
            grpBox.setLayout(l)
            tempLayout.addWidget(grpBox)

        # Add ok and cancel buttons
        buttonLayout = QHBoxLayout()
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect( self.reject )
        okButton = QPushButton("OK")
        okButton.clicked.connect( self.accept )
        okButton.setDefault(True)
        buttonLayout.addSpacerItem(QSpacerItem(10, 0))
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(okButton)
        tempLayout.addLayout(buttonLayout)
        
        self.setLayout(tempLayout)
        
        # Show the window
        result = self.exec_()
        
        # If the user didn't hit "cancel", apply his changes to the manager's shortcuts
        if result == QDialog.Accepted:
            for shortcut, edit in shortcutEdits.items():
                oldKey = shortcut.key()
                newKey = str(edit.text())
                shortcut.setKey( QKeySequence(newKey) )
                
                # If the user typed an invalid shortcut, then keep the old value
                if shortcut.key().isEmpty():
                    shortcut.setKey(oldKey)
                
                # Make sure the tooltips get updated.
                mgr.updateToolTip(shortcut)
                
            mgr.storeToPreferences()
                

if __name__ == "__main__":
    from PyQt4.QtGui import QShortcut, QKeySequence
    from functools import partial

    from PyQt4.QtGui import QApplication, QPushButton, QWidget
    app = QApplication([])

    mainWindow = QWidget()

    def showShortcuts():
        mgrDlg = ShortcutManagerDlg(mainWindow)
        
        for group, shortcutDict in mgr.shortcuts.items():
            print group + ":"
            for i, (shortcut, (desc, obj)) in enumerate(shortcutDict.items()):
                print desc + " : " + str(shortcut.key().toString())

    mainLayout = QVBoxLayout()
    btn = QPushButton("Show shortcuts")
    btn.clicked.connect( showShortcuts )
    mainLayout.addWidget(btn)
    mainWindow.setLayout(mainLayout)
    mainWindow.show()    

    def trigger(name):
        print "Shortcut triggered:",name
    
    def registerShortcuts(mgr):
        scA = QShortcut( QKeySequence("1"), mainWindow, member=partial(trigger, "A") )
        mgr.register( "Group 1",
                      "Shortcut 1A",
                      scA,
                      None )        
    
        scB = QShortcut( QKeySequence("2"), mainWindow, member=partial(trigger, "B") )
        mgr.register( "Group 1",
                      "Shortcut 1B",
                      scB,
                      None )        
    
        scC = QShortcut( QKeySequence("3"), mainWindow, member=partial(trigger, "C") )
        mgr.register( "Group 2",
                      "Shortcut 2C",
                      scC,
                      None )

    mgr = ShortcutManager()
    registerShortcuts(mgr)

    app.exec_()
    
    
    # Simulate a new session by making a new instance of the manager
    ShortcutManager.instance = None # Force the singleton to reset
    mgr2 = ShortcutManager()
    assert id(mgr) != id(mgr2), "Why didn't the singleton reset?"

    registerShortcuts(mgr2)

    # Check to make sure the shortcuts loaded from disc match those from the first "session"
    
    for group, shortcutDict in mgr.shortcuts.items():
        assert group in mgr2.shortcuts

    descriptionToKeys_1 = {}
    for group, shortcutDict in mgr.shortcuts.items():
        for shortcut, (desc, obj) in shortcutDict.items():
            descriptionToKeys_1[desc] = shortcut.key().toString()

    descriptionToKeys_2 = {}
    for group, shortcutDict in mgr2.shortcuts.items():
        for shortcut, (desc, obj) in shortcutDict.items():
            descriptionToKeys_2[desc] = shortcut.key().toString()
    
    assert descriptionToKeys_1 == descriptionToKeys_2
    print descriptionToKeys_1
    print descriptionToKeys_2









