from PyQt4.QtCore import QObject, QEvent
from PyQt4.QtGui import QApplication
from functools import partial

class ThunkEvent( QEvent ):
    """
    A QEvent subclass that holds a callable which can be executed by its listeners.
    Sort of like a "queued connection" signal.
    """
    EventType = QEvent.Type(QEvent.registerEventType())

    def __init__(self, func, *args):
        QEvent.__init__(self, self.EventType)
        if len(args) > 0:
            self.thunk = partial(func, *args)
        else:
            self.thunk = func
    
    def __call__(self):
        self.thunk()

    @classmethod
    def post(cls, handlerObject, func, *args):
        e = ThunkEvent( func, *args )
        QApplication.postEvent(handlerObject, e)

    @classmethod
    def send(cls, handlerObject, func, *args):
        e = ThunkEvent( func, *args )
        QApplication.sendEvent(handlerObject, e)

class ThunkEventHandler( QObject ):
    def __init__(self, parent):
        QObject.__init__(self, parent)
        parent.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        if event.type() == ThunkEvent.EventType:
            # Execute the event
            event()
            return True
        else:
            return False

    def post(self, *args):
        ThunkEvent.post(self.parent(), *args)
    
    def send(self, *args):
        ThunkEvent.send(self.parent(), *args)