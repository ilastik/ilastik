from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import Qt, QObject, QEvent, QChildEvent, QTimer, QTimerEvent, QThread
from PyQt4.QtGui import QApplication, QMouseEvent, QGraphicsSceneMouseEvent, QWheelEvent, \
                        QKeyEvent, QMoveEvent, QWindowStateChangeEvent, QAction, \
                        QActionEvent, QPaintEvent, QCursor, QComboBox, QResizeEvent

import time
import threading
import logging
logger = logging.getLogger(__name__)

def assign_default_object_name( obj ):
    parent = QObject.parent(obj)
    if parent is None:
        # We just name the object after it's type and hope for the best.
        obj.setObjectName( obj.__class__.__name__ )
    else:
        index = parent.children().index( obj )
        newname = "child_{}_{}".format( index, obj.__class__.__name__ )
        existing_names = map( QObject.objectName, parent.children() )
        assert newname not in existing_names
        obj.setObjectName( newname )

def has_unique_name(obj):
    parent = QObject.parent(obj)
    if parent is None:
        return True # We assume that top-level widgets have unique names, which should usually be true.
    obj_name = obj.objectName()
    for child in parent.children():
        if child is not obj and child.objectName() == obj_name:
            return False
    return True

def normalize_child_names(parent):
    """
    Make sure no two children of parent have the same name.
    If two children have the same name, only rename the second one.
    """
    existing_names = set()
    for child in parent.children():
        if child.objectName() in existing_names:
            assign_default_object_name(child)
        existing_names.add( child.objectName() )

def get_fully_qualified_name(obj):
    """
    Return a fully qualified object name of the form someobject.somechild.somegrandchild.etc
    Before returning, this function renames any children that don't have unique names.

    Note: The name uniqueness check and renaming algorithm are terribly inefficient, 
          but it doesn't seem to slow things down much.  We could improve this later if necessary.
    """
    parent = QObject.parent(obj)
    objName = obj.objectName()
    if objName == "":
        assign_default_object_name(obj)
    if not has_unique_name(obj):
        normalize_child_names(parent)
    
    objName = obj.objectName()

    if parent is None:
        return objName
    
    fullname = "{}.".format( get_fully_qualified_name(parent) ) + objName

    # Make sure no siblings have the same name!
    for sibling in parent.children():
        if sibling != obj:
            assert sibling.objectName() != objName, "Detected multiple objects with full name: {}".format( fullname )

    return fullname

def locate_immediate_child(parent, childname):
    if parent is None:
        siblings = QApplication.topLevelWidgets()
    else:
        siblings = parent.children()

    for child in siblings:
        if child.objectName() == "":
            assign_default_object_name(child)
        if not has_unique_name(child):
            normalize_child_names(parent)
        if child.objectName() == childname:
            return child
    return None

def locate_descendent(parent, full_name):
    names = full_name.split('.')
    assert names[0] != ''
    child = locate_immediate_child(parent, names[0])
    if len(names) == 1:
        return child
    else:
        return locate_descendent( child, '.'.join(names[1:]) )

def get_named_object(full_name, timeout=10.0):
    obj = locate_descendent(None, full_name)
    while obj is None and timeout > 0.0:
        time.sleep(1.0)
        timeout -= 1.0
        obj = locate_descendent(None, full_name)
    return obj

event_serializers = {}
event_deserializers = {}
def register_serializer(eventType):
    def _dec(f):
        event_serializers[eventType] = f
        return f
    return _dec

#def register_deserializer(*eventTypes):
#    def _dec(f):
#        for eventType in eventTypes:
#            event_deserializers[eventType] = f
#        return f
#    return _dec

@register_serializer(QMouseEvent)
def QMouseEvent_to_string(mouseEvent):
    return "QMouseEvent({}, {}, {}, Qt.MouseButtons(0x{:x}), Qt.KeyboardModifiers(0x{:x}))".format( mouseEvent.type(), mouseEvent.pos(), mouseEvent.button(), int(mouseEvent.buttons()), int(mouseEvent.modifiers()) )

@register_serializer(QWheelEvent)
def QWheelEvent_to_string(wheelEvent):
    return "QWheelEvent({}, {}, Qt.MouseButtons(0x{:x}), Qt.KeyboardModifiers(0x{:x}), {})".format( wheelEvent.pos(), wheelEvent.delta(), int(wheelEvent.buttons()), int(wheelEvent.modifiers()), wheelEvent.orientation() )

@register_serializer(QKeyEvent)
def QKeyEvent_to_string(keyEvent):
    text = str(keyEvent.text())
    text = text.replace('\n', '\\n')
    text = '"""' + text + '"""'
    return "QKeyEvent({}, 0x{:x}, Qt.KeyboardModifiers(0x{:x}), {}, {}, {})".format( keyEvent.type(), keyEvent.key(), int(keyEvent.modifiers()), text, keyEvent.isAutoRepeat(), keyEvent.count() )

@register_serializer(QMoveEvent)
def QMoveEvent_to_string(moveEvent):
    return "QMoveEvent({}, {})".format( moveEvent.pos(), moveEvent.oldPos() )

@register_serializer(QResizeEvent)
def QResizeEvent_to_string(resizeEvent):
    return "QResizeEvent({}, {})".format( resizeEvent.size(), resizeEvent.oldSize() )

@register_serializer(QWindowStateChangeEvent)
def QWindowStateChangeEvent_to_string(windowStateChangeEvent):
    return "QWindowStateChangeEvent(0x{:x})".format( int(windowStateChangeEvent.oldState()) )

#@register_serializer(QActionEvent)
#def QActionEvent_to_string(actionEvent):
#    action = actionEvent.action()
#    parentName = get_fully_qualified_name(action.parent())
#    actionStr = "QAction('{}', get_named_object('{}'))".format( action.text(), parentName )
#    
#    # Can we safely ignore the 'before' field?
#    # Let's hope so...
#    # before = actionEvent.before()
#    return "QActionEvent({}, {})".format( actionEvent.type(), actionStr )

@register_serializer(QEvent)
def QEvent_to_string(event):
    return "QEvent({})".format( event.type() )

#@register_deserializer(QMouseEvent)
def string_to_QEvent(s):
    e = eval( s )
    assert isinstance(e, QEvent)

def event_to_string(e):
    return event_serializers[type(e)](e)

class QDummy(QObject):
    SetEvent = QEvent.Type(QEvent.registerEventType())

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._state = threading.Event()

    def event(self, e):
        if e.type() == QDummy.SetEvent:
            assert threading.current_thread().name == "MainThread"
            self.set()
            return True
        return False

    def eventFilter(self, watched, event):
        return self.event(event)

    #@pyqtSlot()
    def set(self):
        QApplication.sendPostedEvents()
        QApplication.processEvents()
        QApplication.flush()
        print "setting"
        assert not self._state.is_set()
        self._state.set()
        
    def clear(self):
        print "Clearing..."
        self._state.clear()

    def wait(self):
        assert threading.current_thread().name != "MainThread"
        print "Waiting..."
        self._state.wait()

class Signaler(QObject):
    sig = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)

def post_event(obj, event):
    assert threading.current_thread().name != "MainThread"
    QApplication.postEvent(obj, event)
    QThread.yieldCurrentThread()
    
    assert QApplication.instance().thread() == obj.thread()
    
    syncher = QDummy()
    syncher.moveToThread( obj.thread() )
    syncher.setParent( QApplication.instance() )
    #obj.installEventFilter(syncher)

    count = 1
    while count > 0:
        count -= 1

#        print "count:",count
#        QApplication.postEvent(obj, QEvent(QDummy.SetEvent), -100)
#        syncher.wait()
#        syncher.clear()
        
        print "Signaling..."
        signaler = Signaler()
        signaler.sig.connect( syncher.set, Qt.QueuedConnection )
        signaler.sig.emit()
        syncher.wait()
        syncher.clear()
        time.sleep(0)
        
    #obj.removeEventFilter(syncher)

def verify_object(obj, objname):
    assert obj is not None, "Couldn't find object: {}".format(objname)

def has_ancestor(obj, object_type):
    parent = QObject.parent( obj )
    if parent is None:
        return False
    if isinstance( parent, object_type ):
        return True
    return has_ancestor( parent, object_type )

class EventRecorder( QObject ):
    syncEvent = None

    def __init__(self, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self._captured_events = []
        if EventRecorder.syncEvent is None:
            EventRecorder.syncEvent = QDummy(parent=self)

    QEvent_Style = 91
    IgnoredEventTypes = set( [ QEvent.Paint, QEvent_Style, QEvent.KeyboardLayoutChange, QEvent.WindowActivate, QEvent.WindowDeactivate, QEvent.ActivationChange ] )
    IgnoredEventClasses = (QChildEvent, QTimerEvent, QGraphicsSceneMouseEvent, QWindowStateChangeEvent)

    def eventFilter(self, watched, event):
        if self._shouldSaveEvent(event):
            try:
                eventstr = event_to_string(event)
            except KeyError:
                logger.warn("Don't know how to record event: {}".format( str(event) ))
                print "Don't know", str(event)
            else:
                self._captured_events.append( (eventstr, get_fully_qualified_name(watched)) )
#            print "Got event:", eventstr, "in", get_fully_qualified_name(watched)
#            widgetUnderCursor = QApplication.instance().widgetAt( QCursor.pos() )
#            if widgetUnderCursor is not None:
#                print "Cursor is over", get_fully_qualified_name(widgetUnderCursor)
        return False

    def _shouldSaveEvent(self, event):
        # Special cases:
        if isinstance(event, QMouseEvent):
            if event.type() == QEvent.MouseMove \
                and int(event.button()) == 0 \
                and int(event.buttons()) == 0 \
                and int(event.modifiers()) == 0:
                # Ignore most mouse movement events if the user isn't pressing anything.
                # Somewhat hackish (and slow), but we have to record mouse movements during combo box usage.
                widgetUnderCursor = QApplication.instance().widgetAt( QCursor.pos() )
                if widgetUnderCursor is not None and widgetUnderCursor.objectName() == "qt_scrollarea_viewport":
                    return has_ancestor(widgetUnderCursor, QComboBox)
                return False
            else:
                return True
        if not event.spontaneous():
            return False
        if event.type() in self.IgnoredEventTypes:
            return False
        if isinstance(event, self.IgnoredEventClasses):
            return False
        return True

    def start(self):
        QApplication.instance().installEventFilter( self )

    def stop(self):
        QApplication.instance().removeEventFilter( self )

    def writeScript(self, fileobj):
        fileobj.write(
"""
print 'LOADING RECORDING!!'
def play_commands():\n
    import PyQt4.QtCore
    import PyQt4.QtGui
    from ilastik.shell.gui.eventRecorder import *
""")
        for eventstr, objname in self._captured_events:
            fileobj.write("""
    obj = get_named_object('{objname}')
    verify_object(obj, '{objname}')
    event = {eventstr}
    post_event(obj, event)
""".format( **locals() )
)

    