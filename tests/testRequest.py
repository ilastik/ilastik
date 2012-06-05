from lazyflow.request import Request
import time
import random
import numpy
import h5py

class TestRequest(object):
    @classmethod
    def setupClass(cls):
        pass
    
    @classmethod
    def teardownClass(cls):
        pass
    
    def testBasic(self):
        def someWork():
            time.sleep(0.1)
            #print "producer finished"

        def callback(s):
            pass

        def test(s):
            req = Request(someWork)
            req.notify(callback)
            req.wait()
            time.sleep(0.1)
            print s
            return s
        
        req = Request( test, s = "hallo !")
        req.notify(callback)
        assert req.wait() == "hallo !"

        requests = []
        for i in range(10):
            req = Request( test, s = "hallo %d" %i)
            requests.append(req)
        
        for r in requests:
            r.wait()

    def testLotsOfSmallRequests(self):
        
        def completionHandler( result, req ):
            req.wait()
        
        # This closure randomly chooses to either (a) return immediately or (b) fire off more work
        def someWork(depth, force=False, i=-1):
            print 'depth=', depth, 'i=', i
            if depth > 0 and (force or random.random() > 0.5):
                requests = []
                for i in range(10):
                        req = Request(someWork, depth=depth-1, i=i)
                        req.notify(completionHandler, req=req)
                        requests.append(req)
                
                for r in requests:
                    r.wait()
        
        req = Request(someWork, depth=6, force=True)
        req.wait()
        
        print "finished testLotsOfSmallRequests"

    def testWithH5Py(self):
        maxDepth = 5
        maxBreadth = 10
        
        h5File = h5py.File( 'requestTest.h5', 'w' )
        dataset = h5File.create_dataset( 'test/data', data=numpy.zeros( (maxDepth, maxBreadth), dtype=int ))

        def writeToH5Py(result, index, req):
            dataset[index] += 1
        
        # This closure randomly chooses to either (a) return immediately or (b) fire off more work
        def someWork(depth, force=False, i=0):
            print 'depth=', depth, 'i=', i
            if depth > 0 and (force or random.random() > 0.5):
                requests = []
                for i in range(maxBreadth):
                        req = Request(someWork, depth=depth-1, i=i)
                        req.notify(writeToH5Py, index=(depth-1, i), req=req)
                        requests.append(req)
                
                for r in requests:
                    r.wait()
        
        req = Request(someWork, depth=maxDepth, force=True)
        req.wait()
        h5File.close()
        
        print "finished testWithH5Py"

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})















