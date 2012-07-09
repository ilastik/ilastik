from lazyflow.request_rewrite import Request, global_thread_pool
import time
import random
import numpy
import h5py
from functools import partial

import threading
import sys
import logging
logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
#handler = logging.StreamHandler(sys.stdout)
#formatter = logging.Formatter('%(levelname)s %(name)s %(message)s')
#handler.setFormatter(formatter)
#logger.addHandler(handler)

class TestRequest(object):
    
    @classmethod
    def setupClass(cls):
        pass

    @classmethod
    def teardownClass(cls):
        global_thread_pool.stop()
    
    def test_basic(self):
        """
        Fire a couple requests and check the answer they give.
        """
        def someWork():
            time.sleep(0.001)
            return "Hello,"

        callback_result = ['']
        def callback(result):
            callback_result[0] = result

        def test(s):
            req = Request(someWork)
            req.notify_finished(callback)
            s2 = req.wait()
            time.sleep(0.001)
            return s2 + s

        req = Request( partial(test, s = " World!") )
        req.notify_finished(callback)
        
        # Wait for the result
        assert req.wait() == "Hello, World!"         # Wait for it
        assert req.wait() == "Hello, World!"         # It's already finished, should be same answer
        assert callback_result[0] == "Hello, World!" # From the callback

        requests = []
        for i in range(10):
            req = Request( partial(test, s = "hallo %d" %i) )
            requests.append(req)

        for r in requests:
            r.wait()

#    def test_withH5Py(self):
#        """
#        We have suspicions that greenlet and h5py don't interact well with eachother.
#        This tests basic functionality.
#        TODO: Expand it for better coverage.
#        """
#        maxDepth = 5
#        maxBreadth = 10
#
#        h5File = h5py.File( 'requestTest.h5', 'w' )
#        dataset = h5File.create_dataset( 'test/data', data=numpy.zeros( (maxDepth, maxBreadth), dtype=int ))
#
#        def writeToH5Py(result, index, req):
#            dataset[index] += 1
#
#        # This closure randomly chooses to either (a) return immediately or (b) fire off more work
#        def someWork(depth, force=False, i=0):
#            #print 'depth=', depth, 'i=', i
#            if depth > 0 and (force or random.random() > 0.5):
#                requests = []
#                for i in range(maxBreadth):
#                    req = Request(someWork, depth=depth-1, i=i)
#                    req.notify(writeToH5Py, index=(depth-1, i), req=req)
#                    requests.append(req)
#
#                for r in requests:
#                    r.wait()
#
#        req = Request(someWork, depth=maxDepth, force=True)
#        req.wait()
#        h5File.close()
#
#        print "finished testWithH5Py"

    def test_callWaitDuringCallback(self):
        """
        When using request.notify_finished(...) to handle request completions, the handler should be allowed to call request.wait() on the request that it's handling.
        """
        def handler(req, result):
            return
            req.wait()
            
        def workFn():
            pass
        
        req = Request(workFn)
        req.notify_finished( partial(handler, req) )
        req.wait()
    
    def test_block_during_calback(self):
        """
        It is valid for request finish handlers to fire off and wait for requests.
        This tests that feature.
        """
        def workload():
            time.sleep(0.1)
            return 1
        
        total_result = [0]
        def handler(result):
            req = Request(workload)
            total_result[0] = result + req.wait() # Waiting on some other request from WITHIN a request callback

        req = Request( workload )
        req.notify_finished( handler )
        assert req.wait() == 1
        assert total_result[0] == 2
        

    def test_lotsOfSmallRequests(self):
        """
        Fire off some reasonably large random number of nested requests.
        Mostly, this test ensures that the requests all complete without a hang.
        """
        handlerCounter = [0]
        handlerLock = threading.Lock()
        
        def completionHandler( result, req ):
            logger.debug( "Handing completion {}".format(result) )
            handlerLock.acquire()
            handlerCounter[0] += 1
            handlerLock.release()
            req.calledHandler = True

        requestCounter = [0]
        requestLock = threading.Lock()            
        allRequests = []
        # This closure randomly chooses to either (a) return immediately or (b) fire off more work
        def someWork(depth, force=False, i=-1):
            #print 'depth=', depth, 'i=', i
            if depth > 0 and (force or random.random() > 0.5):
                requests = []
                for i in range(10):
                    req = Request( partial(someWork, depth=depth-1, i=i) )
                    req.notify_finished( partial(completionHandler, req=req) )
                    requests.append(req)
                    allRequests.append(req)
                    
                    requestLock.acquire()
                    requestCounter[0] += 1
                    requestLock.release()

                for r in requests:
                    r.wait()
                
            return requestCounter[0]

        req = Request( partial(someWork, depth=4, force=True) )

        logger.info("Waiting for requests...")
        req.wait()
        logger.info("root request finished")
        
        # Handler should have been called once for each request we fired
        assert handlerCounter[0] == requestCounter[0]

        logger.info("finished testLotsOfSmallRequests")
        
        for r in allRequests:
            assert r.finished

        logger.info("waited for all subrequests")
    
    def test_cancel(self):
        """
        Start a workload and cancel it.  Verify that it was actually cancelled before all the work was finished.
        """
        counter_lock = threading.RLock()

        def workload():
            time.sleep(0.01)
            return 1
        
        got_cancel = [False]
        workcounter = [0]
        def big_workload():
            try:
                requests = []
                for i in range(100):
                    requests.append( Request(workload) )
                
                for r in requests:
                    workcounter[0] += r.wait()
                
                assert False, "This test is designed so that big_workload should be cancelled before it finishes all its work"
                for r in requests:
                    assert not r.cancelled
            except Request.CancellationException:
                got_cancel[0] = True
        
        completed = [False]
        def handle_complete( result ):
            completed[0] = True
        
        req = Request( big_workload )
        req.notify_finished( handle_complete )
        time.sleep(.5)
        req.cancel()
        
        assert req.cancelled
        
        time.sleep(2)
        assert not completed[0]
        assert got_cancel[0]
        
        # Make sure this test is functioning properly:
        # The cancellation should have occurred in the middle (not before the request even got started)
        # If not, then adjust the timing of the cancellation, above.
        assert workcounter[0] != 0
        assert workcounter[0] != 100
        
    def test_early_cancel(self):
        """
        If you try to wait for a request after it's already been cancelled, you get a InvalidRequestException.
        """
        def f():
            pass
        req = Request(f)
        req.cancel()
        try:
            req.wait()
        except Request.InvalidRequestException:
            pass
        else:
            assert False, "Expected a Request.InvalidRequestException because we're waiting for a request that's already been cancelled."

    def test_uncancellable(self):
        """
        If a request is being waited on by a regular thread, it can't be cancelled.
        """
        def workload():
            time.sleep(0.1)
            return 1

        def big_workload():
            result = 0
            requests = []
            for i in range(10):
                requests.append( Request(workload) )
            
            for r in requests:
                result += r.wait()
            return result

        req = Request(big_workload)
        def attempt_cancel():
            time.sleep(1)
            req.cancel()

        # Start another thread that will try to cancel the request.
        # It won't have any effect because we're already waiting for it in a non-request thread.
        t = threading.Thread(target=attempt_cancel)
        t.start()
        result = req.wait()
        assert result == 10
    
    def test_old_api_support(self):
        def someWork(destination=None):
            if destination is None:
                destination = [""]
            time.sleep(0.001)
            destination[0] = "Hello,"
            return destination

        callback_result = ['']
        def callback(result):
            callback_result[0] = result

        def test(s, destination=None,):
            req = Request(someWork)
            req.onFinish(callback)
            s2 = req.wait()[0]
            time.sleep(0.001)
            if destination is None:
                destination = [""]
            destination[0] = s2 + s
            return destination

        req = Request( partial(test, s = " World!") )
        result = [""]
        req.writeInto(result)
        req.notify(callback)
        
        # Wait for the result
        assert req.wait()[0] == "Hello, World!"      # Wait for it
        assert callback_result[0][0] == "Hello, World!" # From the callback
        assert result[0] == req.wait()[0]

        requests = []
        for i in range(10):
            req = Request( partial(test, s = "hallo %d" %i) )
            requests.append(req)

        for r in requests:
            r.wait()

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
