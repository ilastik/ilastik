from PyQt4.QtCore import pyqtSignal, pyqtSlot, SLOT
from PyQt4.QtCore import Qt, QObject, QEvent, QChildEvent, QTimer, QTimerEvent, QThread
from PyQt4.QtGui import QApplication, QMouseEvent, QGraphicsSceneMouseEvent, QWheelEvent, QKeyEvent, QMoveEvent, QWindowStateChangeEvent, QAction, QActionEvent, QPaintEvent

import time
import threading

def assign_default_object_name( obj ):
    parent = obj.parent()
    if parent is None:
        # We just name the object after it's type and hope for the best.
        obj.setObjectName( obj.__class__.__name__ )
    else:
        index = parent.children().index( obj )
        newname = "child_{}_{}".format( index, obj.__class__.__name__ )
        existing_names = map( QObject.objectName, parent.children() )
        assert newname not in existing_names
        obj.setObjectName( newname )

def get_fully_qualified_name(obj):
    parent = obj.parent()
    objName = obj.objectName()
    if objName == "":
        assign_default_object_name(obj)
        objName = obj.objectName()
        
    if parent is None:
        return objName
    return "{}.".format( get_fully_qualified_name(parent) ) + objName

def locate_immediate_child(parent, childname):
    if parent is None:
        siblings = QApplication.topLevelWidgets()
    else:
        siblings = parent.children()

    for child in siblings:
        if child.objectName() == "":
            assign_default_object_name(child)
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

def get_named_object(full_name):
    return locate_descendent(None, full_name)

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

@register_serializer(QWindowStateChangeEvent)
def QWindowStateChangeEvent_to_string(windowStateChangeEvent):
    return "QWindowStateChangeEvent(0x{:x})".format( int(windowStateChangeEvent.oldState()) )

@register_serializer(QActionEvent)
def QActionEvent_to_string(actionEvent):
    action = actionEvent.action()
    parentName = get_fully_qualified_name(action.parent())
    actionStr = "QAction('{}', get_named_object('{}'))".format( action.text(), parentName )
    
    # Can we safely ignore the 'before' field?
    # Let's hope so...
    # before = actionEvent.before()
    return "QActionEvent({}, {})".format( actionEvent.type(), actionStr )

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
            #assert threading.current_thread().name == "MainThread"
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
    obj.installEventFilter(syncher)

    count = 1
    while count > 0:
        print "count:",count
        count -= 1
        QApplication.postEvent(obj, QEvent(QDummy.SetEvent), -100)
        syncher.wait()
        syncher.clear()
        
        print "Signaling..."
        signaler = Signaler()
        signaler.sig.connect( syncher.set, Qt.QueuedConnection )
        signaler.sig.emit()
        syncher.wait()
        syncher.clear()
        time.sleep(0)
        
    obj.removeEventFilter(syncher)

    syncher = QDummy()
    syncher.moveToThread( QApplication.instance().thread() )

    count = 1
    while count > 0:
        print "count:",count
        count -= 1
        QApplication.postEvent(syncher, QEvent(QDummy.SetEvent), -100)
        syncher.wait()
        syncher.clear()
        
        print "Signaling..."
        signaler = Signaler()
        signaler.sig.connect( syncher.set, Qt.QueuedConnection )
        signaler.sig.emit()
        syncher.wait()
        syncher.clear()
        time.sleep(0)

def verify_object(obj, objname):
    assert obj is not None, "Couldn't find object: {}".format(objname)

class EventRecorder( QObject ):
    syncEvent = None

    def __init__(self, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self._captured_events = []
        if EventRecorder.syncEvent is None:
            EventRecorder.syncEvent = QDummy(parent=self)

    QEvent_Style = 91
    IgnoredEventTypes = set( [ QEvent.Paint, QEvent_Style, QEvent.KeyboardLayoutChange, QEvent.WindowDeactivate, QEvent.ActivationChange ] )
    IgnoredEventClasses = (QChildEvent, QTimerEvent, QGraphicsSceneMouseEvent, QWindowStateChangeEvent)

    def eventFilter(self, watched, event):
        if self._shouldSaveEvent(event):
            try:
                eventstr = event_to_string(event)
            except KeyError:
                eventstr = str(event)

            if self._shouldSaveEvent(event):
                self._captured_events.append( (eventstr, get_fully_qualified_name(watched)) )
                print "Got event:", eventstr, "in", get_fully_qualified_name(watched)
        return False

    def _shouldSaveEvent(self, event):
        # Special cases:
        if isinstance(event, QMouseEvent):
            # Ignore mouse movements if the user isn't pressing anything
            if int(event.button()) == 0 and int(event.modifiers()) == 0:
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

    