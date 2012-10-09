import threading
from functools import partial, wraps
from PyQt4.QtCore import QObject, pyqtSignal, Qt

class ThreadRouter(QObject):
    routeToParent = pyqtSignal(object)

    def __init__(self, parent):
        QObject.__init__(self, parent=parent)
        self.ident = threading.current_thread().ident
        self.routeToParent.connect( self.handleRoutedFunc, Qt.BlockingQueuedConnection )
    
    def handleRoutedFunc(self, f):
        return f()
    
def threadRouted(func):
    """
    Decorator that routes calls to the given member function into the object's parent thread.
    Note: Objects that use the threadRouted decorator MUST have a ThreadRouter member called "threadRouter"
    """
    @wraps(func)
    def routed(*args, **kwargs):
        assert len(args) > 0
        obj = args[0]
        assert isinstance(obj, QObject)
        assert hasattr(obj, 'threadRouter'), "Can't use the @threadRouted decorator unless your object has a member called self.threadRouter"

        # If we're already in the parent thread, then we can call the function directly
        if obj.threadRouter.ident == threading.current_thread().ident:
            func(*args, **kwargs)
        
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
    