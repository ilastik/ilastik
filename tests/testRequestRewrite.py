from lazyflow.request.request_rewrite import Request, RequestLock
import time
import random
import nose
import numpy
import h5py
import gc
from functools import partial

import psutil

from lazyflow.utility.tracer import traceLogged

import threading
import sys
import logging
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)

# Test
logger = logging.getLogger("tests.testRequestRewrite")
# Test Trace
traceLogger = logging.getLogger("TRACE." + logger.name)

class TestRequest(object):

    @traceLogged(traceLogger)
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

    @traceLogged(traceLogger)
    def test_callWaitDuringCallback(self):
        """
        When using request.notify_finished(...) to handle request completions, 
        the handler should be allowed to call request.wait() on the request that it's handling.
        """
        def handler(req, result):
            req.wait()
            
        def workFn():
            pass
        
        req = Request(workFn)
        req.notify_finished( partial(handler, req) )
        #req.submit()
        req.wait()
    
    @traceLogged(traceLogger)
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
        

    @traceLogged(traceLogger)
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

        logger.debug("Waiting for requests...")
        req.wait()
        logger.debug("root request finished")
        
        # Handler should have been called once for each request we fired
        assert handlerCounter[0] == requestCounter[0]

        logger.debug("finished testLotsOfSmallRequests")
        
        for r in allRequests:
            assert r.finished

        logger.debug("waited for all subrequests")
    
    @traceLogged(traceLogger)
    def test_cancel_basic(self):
        """
        Start a workload and cancel it.  Verify that it was actually cancelled before all the work was finished.
        """
        counter_lock = threading.RLock()

        def workload():
            time.sleep(0.1)
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
                
                assert False, "Shouldn't get to this line.  This test is designed so that big_workload should be cancelled before it finishes all its work"
                for r in requests:
                    assert not r.cancelled
            except Request.CancellationException:
                got_cancel[0] = True
        
        completed = [False]
        def handle_complete( result ):
            completed[0] = True
        
        req = Request( big_workload )
        req.notify_finished( handle_complete )
        req.submit()
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

    @traceLogged(traceLogger)
    def test_dont_cancel_shared_request(self):
        """
        Test that a request isn't cancelled if it has requests pending for it.
        """

        cancelled_requests = []
        
        def f1():
            time.sleep(1)
            return "RESULT"
        
        r1 = Request(f1)
        r1.notify_cancelled( partial(cancelled_requests.append, 1) )
        
        def f2():
            try:
                return r1.wait()
            except:
                cancelled_requests.append(2)

        r2 = Request(f2)
        
        def f3():
            try:
                return r1.wait()
            except:
                cancelled_requests.append(3)
        
        r3 = Request(f3)
        
        def otherThread():
            r2.wait()

        t = threading.Thread(target=otherThread)
        t.start()
        r3.submit()
        
        time.sleep(0.5)
        
        # By now both r2 and r3 are waiting for the result of r1
        # Cancelling r3 should not cancel r1.
        r3.cancel()

        t.join() # Wait for r2 to finish

        time.sleep(0.5)

        assert r1.started
        assert r1.finished        
        assert not r1.cancelled # Not cancelled, even though we cancelled a request that was waiting for it.
        assert 1 not in cancelled_requests 

        assert r2.started
        assert r2.finished
        assert not r2.cancelled # Not cancelled.
        assert 1 not in cancelled_requests
        assert r2.wait() == "RESULT" 

        assert r3.started
        assert r3.finished
        assert r3.cancelled # Successfully cancelled.
        assert 3 in cancelled_requests

        
    @traceLogged(traceLogger)
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

    @traceLogged(traceLogger)
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
        
        t.join()
    
    @traceLogged(traceLogger)
    def test_failed_request(self):
        """
        A request is "failed" if it throws an exception while executing.
        The exception should be forwarded to ALL waiting requests.
        """
        
        def impossible_workload():
            raise RuntimeError("Can't service your request")
        
        req = Request(impossible_workload)
        
        try:
            req.wait()
        except RuntimeError:
            pass
        else:
            assert False, "Expected an exception from that request, but didn't get it."
    
    @traceLogged(traceLogger)
    def test_failed_request2(self):
        """
        A request is "failed" if it throws an exception while executing.
        The exception should be forwarded to ALL waiting requests, which should re-raise it.
        """

        class CustomRuntimeError(RuntimeError):
            pass
        
        def impossible_workload():
            time.sleep(0.2)
            raise CustomRuntimeError("Can't service your request")
        
        impossible_req = Request(impossible_workload)

        def wait_for_impossible():
            # This request will fail...
            impossible_req.wait()

            # Since there are some exception guards in the code we're testing, 
            #  spit something out to stderr just to be sure this error 
            #  isn't getting swallowed accidentally.
            sys.stderr.write("ERROR: Shouldn't get here.")
            assert False, "Shouldn't get here."

        req1 = Request(wait_for_impossible)
        req2 = Request(wait_for_impossible)
        
        failed_ids = []
        lock = threading.Lock()
        def handle_failed_req(req_id, failure_exc):
            assert isinstance(failure_exc, CustomRuntimeError)
            with lock:
                failed_ids.append(req_id)
        
        req1.notify_failed( partial(handle_failed_req, 1) )
        req2.notify_failed( partial(handle_failed_req, 2) )
        
        req1.submit()
        req2.submit()

        try:
            req1.wait()
        except RuntimeError:
            pass
        else:
            assert False, "Expected an exception from that request, but didn't get it."

        try:
            req2.wait()
        except RuntimeError:
            pass
        else:
            assert False, "Expected an exception from that request, but didn't get it."

        assert 1 in failed_ids
        assert 2 in failed_ids

    @traceLogged(traceLogger)
    def test_old_api_support(self):
        """
        For now, the request_rewrite supports the old interface, too.
        """
        def someWork(destination=None):
            if destination is None:
                destination = [""]
            time.sleep(0.001)
            destination[0] = "Hello,"
            return destination

        callback_result = [ [] ]
        def callback(result):
            callback_result[0] = result[0]

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
        preAllocatedResult = [""]
        req.writeInto(preAllocatedResult)
        req.notify(callback)
        
        # Wait for the result
        assert req.wait()[0] == "Hello, World!"      # Wait for it
        assert callback_result[0] == "Hello, World!" # From the callback

        assert preAllocatedResult[0] == req.wait()[0], "This might fail if the request was started BEFORE writeInto() was called"

        requests = []
        for i in range(10):
            req = Request( partial(test, s = "hallo %d" %i) )
            requests.append(req)

        for r in requests:
            r.wait()
    
    @traceLogged(traceLogger)
    def test_callbacks_before_wait_returns(self):
        """
        If the user adds callbacks to the request via notify_finished() BEFORE the request is submitted,
        then wait() should block for the completion of all those callbacks before returning.
        Any callbacks added AFTER the request has already been submitted are NOT guaranteed 
        to be executed before wait() returns, but they will still be executed.
        """
        def someQuickWork():
            return 42

        callback_results = []
        def slowCallback(n, result):
            time.sleep(0.1)
            callback_results.append(n)
        
        req = Request( someQuickWork )
        req.notify_finished( partial(slowCallback, 1) )
        req.notify_finished( partial(slowCallback, 2) )
        req.notify_finished( partial(slowCallback, 3) )

        result = req.wait()
        assert result == 42
        assert callback_results == [1,2,3], "wait() returned before callbacks were complete! Got: {}".format( callback_results )
        
        req.notify_finished( partial(slowCallback, 4) )
        req.wait()
        assert callback_results == [1,2,3,4], "Callback on already-finished request wasn't executed."
    
    @traceLogged(traceLogger)
    def test_request_timeout(self):
        """
        Test the timeout feature when calling wait() from a foreign thread.
        See wait() for details.
        """
        def slowWorkload():
            time.sleep( 10.0 )
        
        req = Request( slowWorkload )
        try:
            req.wait(0.5)
        except Request.TimeoutException:
            pass
        else:
            assert False, "Expected to get Request.TimeoutException"
    
    @traceLogged(traceLogger)
    def testRequestLock(self):
        """
        Test the special Request-aware lock.
        
        Launch 99 requests and threads that all must fight over access to the same list.
        The list will eventually be 0,1,2...99, and each request will append a single number to the list.
        Each request must wait its turn before it can append it's number and finish.
        """
        req_lock = RequestLock()
        l = [0]
        
        def append_n(n):
            #print "Starting append_{}\n".format(n)
            while True:
                with req_lock:
                    if l[-1] == n-1:
                        #print "***** Appending {}".format(n)
                        l.append(n)
                        return

        # Create 50 requests
        reqs = []
        for i in range(1,100,2):
            req = Request( partial(append_n, i) )
            reqs.append(req)

        # Create 49 threads
        thrds = []
        for i in range(2,100,2):
            thrd = threading.Thread( target=partial(append_n, i) )
            thrds.append(thrd)
        
        # Submit in reverse order to ensure that no request finishes until they have all been started.
        # This proves that the requests really are being suspended.        
        for req in reversed(reqs):
            req.submit()

        # Start all the threads
        for thrd in reversed(thrds):
            thrd.start()
        
        # All requests must finish
        for req in reqs:
            req.wait()

        # All threads should finish
        for thrd in thrds:
            thrd.join()

        assert l == list(range(100)), "Requests and/or threads finished in the wrong order!"

class TestRequestExceptions(object):
    """
    Check for proper behavior when an exception is generated within a request:
    - The worker thread main loop never sees the exception.
    - The exception is propagated to ALL threads/requests that were waiting on the failed request.
    - If a thread/request calls wait() on a request that has already failed, the exception is raised in the caller.
    - Requests have a signal that fires when the request fails due to an exception.
    """
    
    @traceLogged(traceLogger)
    def testWorkerThreadLoopProtection(self):
        """
        The worker threads should not die due to an exception raised within a request.
        """
        for worker in Request.global_thread_pool.workers:
            assert worker.is_alive(), "Something is wrong with this test.  All workers should be alive."

        def always_fails():
            raise Exception()
        
        req = Request(always_fails)
        req.submit()

        try:
            req.wait()
        except:
            pass
        else:
            assert False, "Expected to request to raise an Exception!"
        
        for worker in Request.global_thread_pool.workers:
            assert worker.is_alive(), "An exception was propagated to a worker run loop!"
    
    @traceLogged(traceLogger)
    def testExceptionPropagation(self):
        """
        When an exception is generated in a request, the exception should be propagated to all waiting threads.
        Also, the failure signal should fire.
        """
        class SpecialException(Exception):
            pass
        
        def always_fails():
            time.sleep(0.2)
            raise SpecialException()
        
        req1 = Request(always_fails)


        def wait_for_req1():
            req1.wait()
        
        req2 = Request(wait_for_req1)
        req3 = Request(wait_for_req1)

        signaled_exceptions = []
        def failure_handler(ex):
            signaled_exceptions.append(ex)
            
        req2.notify_failed( failure_handler )
        req3.notify_failed( failure_handler )

        caught_exceptions = []        
        def wait_for_request(req):        
            try:
                req.wait()
            except SpecialException as ex:
                caught_exceptions.append(ex)
            except:
                raise # Got some other exception than the one we expected
            else:
                assert "Expected to get an exception.  Didn't get one."

        th2 = threading.Thread( target=partial( wait_for_request, req2 ) )
        th3 = threading.Thread( target=partial( wait_for_request, req3 ) )
        
        th2.start()
        th3.start()
        
        th2.join()
        th3.join()
        
        assert len(caught_exceptions) == 2, "Expected both requests to catch exceptions."
        assert len(signaled_exceptions) == 2, "Expected both requests to signal failure."

        assert isinstance( caught_exceptions[0], SpecialException ), "Caught exception was of the wrong type."
        assert caught_exceptions[0] == caught_exceptions[1] == signaled_exceptions[0] == signaled_exceptions[1]
        
        # Attempting to wait for a request that has already failed will raise the exception that causes the failure
        wait_for_request(req2)
        
        # Subscribing to notify_failed on a request that's already failed should call the failure handler immediately.
        req2.notify_failed( failure_handler )
        assert len(signaled_exceptions) == 3
        
    def testMemoryLeaks(self):
        """
        As requests become inaccessible, they should be freed immediately, along with any data they held.
        
        Note that objects within greenlet stack frames are not considered by the cyclical garbage collector,
        so we MUST make sure that cycles between requests (e.g. parent/child and blocking/pending) 
        are broken.  Preferably, requests should be deleted early as possible.
        """
        def getMemoryUsageMb():
            # Collect garbage first
            gc.collect()
            vmem = psutil.virtual_memory()
            mem_usage_mb = (vmem.total - vmem.available) / (1000*1000)
            return mem_usage_mb
        
        starting_usage_mb = getMemoryUsageMb()
        def getMemoryIncreaseMb():
            return getMemoryUsageMb() - starting_usage_mb

        resultShape = (500,1000,1000)
        resultSize = numpy.prod(resultShape)
        def getBigArray(directExecute, recursionDepth):
            """
            Simulate the memory footprint of a series of computation steps.
            """
            logger.debug( "Usage delta before depth {}: {} MB".format(recursionDepth, getMemoryIncreaseMb() ) )

            if recursionDepth == 0:
                # A 500GB result
                result = numpy.zeros(shape=resultShape, dtype=numpy.uint8)
            else:
                req = Request( partial(getBigArray, directExecute=directExecute, recursionDepth=recursionDepth-1) )
                if not directExecute:
                    # Force this request to be submitted to the thread pool,
                    # not executed synchronously in this thread.
                    req.submit()
                result = req.wait() + 1
            
            # Note that we expect there to be 2X memory usage here:
            #  1x for our result and 1x for the child, which hasn't been cleaned up yet.
            memory_increase_mb = getMemoryIncreaseMb()
            logger.debug( "Usage delta after depth {}: {} MB".format(recursionDepth, memory_increase_mb ) )
            assert memory_increase_mb < 2.5*resultSize, "Memory from finished requests didn't get freed!"
            
            return result

        # Run tests via a separate function so its stack is cleaned up
        def test_impl(directExecute):
            rootReq = Request( partial( getBigArray, directExecute, recursionDepth=5 ) )
            result = rootReq.wait()
            assert (result == 5).all()

        test_impl(True)
        test_impl(False)

        memory_increase_mb = getMemoryIncreaseMb()
        logger.debug( "Finished test with memory usage delta at: {} MB".format( memory_increase_mb ) )
        assert memory_increase_mb < resultSize, "All requests are finished an inaccessible, but not all memory was released!"


if __name__ == "__main__":

    # Logging is OFF by default when running from command-line nose, i.e.:
    # nosetests thisFile.py)
    # but ON by default if running this test directly, i.e.:
    # python thisFile.py
    logging.getLogger().addHandler( handler )
    logger.setLevel(logging.DEBUG)
    traceLogger.setLevel(logging.DEBUG)

    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)














































