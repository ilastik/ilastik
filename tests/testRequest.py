from lazyflow.request import Request
import time
import random
import numpy
import h5py

import threading

class TestRequest(object):
    
    @classmethod
    def setupClass(cls):
        pass

    @classmethod
    def teardownClass(cls):
        pass
    
    def test_OutputFailMessage(self):
        assert False, "Strange bugs are causing these tests to hang.  Uncomment each of the tests in this file and get them to work!"

#    def test_basic(self):
#        def someWork():
#            time.sleep(0.001)
#            #print "producer finished"
#
#        def callback(s):
#            pass
#
#        def test(s):
#            req = Request(someWork)
#            req.notify(callback)
#            req.wait()
#            time.sleep(0.001)
#            print s
#            return s
#
#        req = Request( test, s = "hallo !")
#        req.notify(callback)
#        assert req.wait() == "hallo !"
#
#        requests = []
#        for i in range(10):
#            req = Request( test, s = "hallo %d" %i)
#            requests.append(req)
#
#        for r in requests:
#            r.wait()
#
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
#            print 'depth=', depth, 'i=', i
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
#
#    def test_callWaitDuringCallback(self):
#        """
#        When using request.notify(...) to handle request completions, the handler should be allowed to call request.wait().
#        Currently, this causes a hang somewhere in request.py.
#        """
#        def handler(result, req):
#            return
#            req.wait()
#            
#        def workFn():
#            pass
#        
#        req = Request(workFn)
#        req.notify( handler, req=req )
#        req.wait()
#
#    def test_lotsOfSmallRequests(self):
#        handlerCounter = [0]
#        handlerLock = threading.Lock()
#        
#        def completionHandler( result, req ):
#            handlerLock.acquire()
#            handlerCounter[0] += 1
#            handlerLock.release()
#
#        requestCounter = [0]
#        requestLock = threading.Lock()            
#        # This closure randomly chooses to either (a) return immediately or (b) fire off more work
#        def someWork(depth, force=False, i=-1):
#            #print 'depth=', depth, 'i=', i
#            if depth > 0 and (force or random.random() > 0.5):
#                requests = []
#                for i in range(10):
#                    req = Request(someWork, depth=depth-1, i=i)
#                    req.notify(completionHandler, req=req)
#                    requests.append(req)
#                    
#                    requestLock.acquire()
#                    requestCounter[0] += 1
#                    requestLock.release()
#
#                for r in requests:
#                    r.wait()
#
#        req = Request(someWork, depth=6, force=True)
#        req.wait()
#        
#        # Handler should have been called once for each request we fired
#        assert handlerCounter[0] == requestCounter[0]
#
#        print "finished testLotsOfSmallRequests"

        
if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
