import time
import threading
from lazyflow.request.threadPool import ThreadPool

class TestThreadPool(object):
    """
    The ThreadPool does not depend on any particular Request-specific interface; it can be used with any callable.
    This is a simple test to verify that it can execute regular functions.
    """
    
    @classmethod
    def setupClass(cls):
        cls.thread_pool = ThreadPool(num_workers = 4)
    
    def testBasic(self):        
        e1 = threading.Event()
        e2 = threading.Event()
        
        def f1():
            e1.set()
        
        def f2():
            e1.wait()
            e2.set()
        
        TestThreadPool.thread_pool.wake_up( f2 )
        time.sleep(0.1)
        TestThreadPool.thread_pool.wake_up( f1 )
        
        e2.wait()
        
        # This is just to make sure the test is doing what its supposed to.
        assert f1.assigned_worker != f2.assigned_worker

    def testAssignmentConsistency(self):
        """
        If a callable is woken up (executed) more than once from the ThreadPool, it will execute on the same thread every time.
        (This is a useful guarantee for e.g. greenlet-based callables.)
        """
        e = threading.Event()
        f_thread_ids = []
        def f():
            f_thread_ids.append( threading.current_thread() )
            e.set()
        
        # First time
        e.clear()
        self.thread_pool.wake_up( f )
        e.wait()
        
        # Second time, same callable
        e.clear()
        self.thread_pool.wake_up( f )
        e.wait()
        assert f_thread_ids[0] == f_thread_ids[1], "Callable should always execute on the same worker thread!"

        # Another example: Now do the same thing, but with a (wrapped) generator as the callable
        gen_thread_ids = []
        def gen():
            while True:
                gen_thread_ids.append( threading.current_thread() )
                yield e.set()

        class WrappedGenerator(object):
            def __init__(self, generator):
                self.generator = generator
            
            def __call__(self):
                return self.generator.next()

        # First time
        g = WrappedGenerator( gen() )
        e.clear()
        self.thread_pool.wake_up( g )
        e.wait()
        
        # Second time, same callable
        e.clear()
        self.thread_pool.wake_up( g )
        e.wait()
        assert gen_thread_ids[0] == gen_thread_ids[1], "Callable should always execute on the same worker thread!"


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)

