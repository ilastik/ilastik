import re
import abc
import collections

from ilastik.utility import Singleton

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
            
        assert description is not None, "Coundn't find the shortcut you're trying to update."
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

