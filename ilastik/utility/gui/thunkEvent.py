###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
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
    """
    GUI objects can instantiate an instance of this class and then start using it to 
    post ``ThunkEvents``, which execute a given callable in the GUI event loop.
    The callable will NOT be called synchronously.  It will be called when the QT 
    event system eventually passes the event to the GUI object's event filters.

    In the following example, ``C.setCaption()`` can be called from ANY thread safely.
    The widget's text will ONLY be updated in the main thread, at some point in the future.
    
    .. code-block:: python
    
       class C(QObject):
           def __init__(self, parent):
               QObject.__init__(self, parent=parent)
               self.thunkEventHandler = ThunkEventHandler(self)
        
        
           def setCaption(self, text):
               self.thunkEventHandler.post( self.mywidget.setText, text )    
    """
    def __init__(self, parent):
        """
        Create a ThunkEventHandler that installs itself in the event loop for ``parent``.
        """
        QObject.__init__(self, parent)
        parent.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        if event.type() == ThunkEvent.EventType:
            # Execute the event
            event()
            return True
        else:
            return False

    def post(self, func, *args):
        """
        Post an event to the GUI event system that will eventually execute the given function with the given arguments.
        This is implemented using ``QApplication.post()``
        """
        ThunkEvent.post(self.parent(), func, *args)
    
    def send(self, func, *args):
        """
        Send an event to the GUI event system that will eventually execute the given function with the given arguments.
        Note that this is done using ``QApplication.send()``, which may not be what you wanted.
        """
        ThunkEvent.send(self.parent(), func, *args)