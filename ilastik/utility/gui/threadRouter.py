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
import threading
from functools import partial, wraps
from PyQt4.QtCore import QObject, pyqtSignal, Qt

class ThreadRouter(QObject):
    """
    Create an instance of this class called 'threadRouter' to enable the :py:func:`@threadRouted<threadRouted>` decorator for methods of your object.
    """
    routeToParent = pyqtSignal(object)
    
    # The main window of the app should set this to True when the 
    #  app is shutting down and thus no gui events should be processed any more.
    app_is_shutting_down = False

    def __init__(self, parent):
        """
        Construct a threadRouter object.  You must call it ``self.threadRouter``.
        
        :param parent: The parent object, which whose thread will be used for all :py:func:`@threadRouted<threadRouted>` functions.
        """
        assert parent is not None, "Can't use ThreadRouter without a parent QObject."
        QObject.__init__(self, parent=parent)
        self.ident = threading.current_thread().ident
        self.routeToParent.connect( self.handleRoutedFunc, Qt.BlockingQueuedConnection )
    
    def handleRoutedFunc(self, f):
        return f()
    
def threadRouted(func):
    """
    Decorator that routes calls to the given member function into the object's parent thread.
    If a member function ``f`` is decorated with ``@threadRouted``, all calls to ``f`` will execute in the GUI thread.
    The calling thread will block while ``f`` is executing, so the call will appear synchronous.
    This mechanism is slow, and should only be used for functions that MUST execute in the GUI thread. 
    
    .. note:: Objects that use the @threadRouted decorator MUST have a :py:class:`ThreadRouter` member called ``self.threadRouter``
    """
    @wraps(func)
    def routed(*args, **kwargs):
        if ThreadRouter.app_is_shutting_down:
            return
        
        assert len(args) > 0
        obj = args[0]
        assert isinstance(obj, QObject)
        assert hasattr(obj, 'threadRouter'), "Can't use the @threadRouted decorator unless your object has a member called self.threadRouter"

        # If we're already in the parent thread, then we can call the function directly
        if obj.threadRouter.ident == threading.current_thread().ident:
            val = func(*args, **kwargs)
            # We rely on Qt signals (below) so it is an error to 
            #  use @threadRouted with a function that gives a return value
            assert val is None, "Can't return a value from an @threadRouted function."
        
        # Otherwise, we rely on the Qt BlockingQueuedConnection 
        #  signal behavior to transfer the call to the parent thread. 
        else:
            obj.threadRouter.routeToParent.emit( partial(func, *args, **kwargs) )
                 
    routed.__wrapped__ = func # Emulate python 3 behavior of @wraps
    return routed
            
if __name__ == "__main__":
    import time
    from PyQt4.QtGui import QApplication

    class TestObject(QObject):
        
        def __init__(self):
            QObject.__init__(self)
            self.threadRouter = ThreadRouter(self)

        @threadRouted
        def printThreadId(self):
            time.sleep(0.5)
            print "thread id = ", threading.current_thread().ident

    app = QApplication([])
    
    o = TestObject()
    
    def test():
        print "thread id = ", threading.current_thread().ident
        o.printThreadId()
        print "Finished."
    
    th = threading.Thread(target=test)
    th.start()
    
    app.exec_()
    