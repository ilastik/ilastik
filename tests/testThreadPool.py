import time
import threading
from lazyflow.request.threadPool import ThreadPool

class TestThreadPool(object):
    """
    The ThreadPool does not depend on any particular Request-specific interface; it can be used with any callable.
    This is a simple test to verify that it can execute regular functions.
    """
    
    def testBasic(self):
        assert len(ThreadPool().workers) >= 2, "This test requires at least 2 ThreadPool workers to be active.  Do you only have 1 processor?"
        
        e1 = threading.Event()
        e2 = threading.Event()
        
        def f1():
            e1.set()
        
        def f2():
            e1.wait()
            e2.set()
        
        ThreadPool().wake_up( f2 )
        time.sleep(0.1)
        ThreadPool().wake_up( f1 )
        
        e2.wait()
        
        # This is just to make sure the test is doing what its supposed to.
        assert f1.assigned_worker != f2.assigned_worker

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)

        
            
        