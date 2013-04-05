from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import Qt, QObject, QEvent, QChildEvent, QTimerEvent
from PyQt4.QtGui import QApplication, QMouseEvent, QGraphicsSceneMouseEvent, QWindowStateChangeEvent, QCursor, QComboBox

from objectNameUtils import get_fully_qualified_name
from eventSerializers import event_to_string

import threading
import logging
logger = logging.getLogger(__name__)

class QEventFlusher(QObject):
    SetEvent = QEvent.Type(QEvent.registerEventType())

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._state = threading.Event()

    def event(self, e):
        if e.type() == QEventFlusher.SetEvent:
            assert threading.current_thread().name == "MainThread"
            self.set()
            return True
        return False

    def eventFilter(self, watched, event):
        return self.event(event)

    def set(self):
        QApplication.sendPostedEvents()
        QApplication.processEvents()
        QApplication.flush()
        assert not self._state.is_set()
        self._state.set()
        
    def clear(self):
        self._state.clear()

    def wait(self):
        assert threading.current_thread().name != "MainThread"
        self._state.wait()

class Signaler(QObject):
    sig = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)

def post_event(obj, event):
    assert threading.current_thread().name != "MainThread"
    QApplication.postEvent(obj, event)
    
    assert QApplication.instance().thread() == obj.thread()
    
    flusher = QEventFlusher()
    flusher.moveToThread( obj.thread() )
    flusher.setParent( QApplication.instance() )

    signaler = Signaler()
    signaler.sig.connect( flusher.set, Qt.QueuedConnection )
    signaler.sig.emit()
    flusher.wait()
    flusher.clear()

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
    """
    Records spontaneous events from the UI and serializes them as strings that can be evaluated in Python.
    """
    def __init__(self, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self._captured_events = []

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
        return False

    def _shouldSaveEvent(self, event):
        if isinstance(event, QMouseEvent):
            # Ignore most mouse movement events if the user isn't pressing anything.
            if event.type() == QEvent.MouseMove \
                and int(event.button()) == 0 \
                and int(event.buttons()) == 0 \
                and int(event.modifiers()) == 0:
                # Somewhat hackish (and slow), but we have to record mouse movements during combo box usage.
                widgetUnderCursor = QApplication.instance().widgetAt( QCursor.pos() )
                if widgetUnderCursor is not None and widgetUnderCursor.objectName() == "qt_scrollarea_viewport":
                    return has_ancestor(widgetUnderCursor, QComboBox)
                return False
            else:
                return True
        # Ignore non-spontaneous events
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
def play_commands():\n
    import PyQt4.QtCore
    from PyQt4.QtCore import Qt, QEvent
    import PyQt4.QtGui
    from ilastik.utility.gui.eventRecorder.objectNameUtils import get_named_object
    from ilastik.utility.gui.eventRecorder.eventRecorder import verify_object, post_event
""")
        for eventstr, objname in self._captured_events:
            fileobj.write("""
    obj = get_named_object('{objname}')
    verify_object(obj, '{objname}')
    event = {eventstr}
    post_event(obj, event)
""".format( **locals() )
)

    