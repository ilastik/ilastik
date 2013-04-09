import threading
from functools import partial

import os
import numpy
import h5py
import greenlet

class TestH5Py(object):
    """
    This test does NOT test anything ilastik, but instead tests h5py in conjunction with greenlet.
    """

    def test(self):
        shape = (2,100,100,6) # Make this bigger to try hammering hdf5 with bigger data accesses...

        filename1 = 'test1.h5'
        self.prepare_tstfile(shape, filename1)
    
        filename2 = 'test2.h5'
        self.prepare_tstfile(shape, filename2)
    
        f1 = h5py.File(filename1)
        f2 = h5py.File(filename2)
        
        self.tst_multithread_greenlet([f1, f2])
    
        f1.close()
        f2.close()
        
        os.remove(filename1)
        os.remove(filename2)

    
    def readFromGroup(self, h5Group, path ):
        shape = numpy.array(h5Group[path].shape)
    
        # Choose a random lower bound in the lower half-space    
        lb = (numpy.random.rand(len(shape))*shape/2).astype(int)
    
        # Choose a random upper bound in the upper half-space    
        ub = (numpy.random.rand(len(shape))*shape/2).astype(int) + shape/2
    
        # Combine into a slicing we can index with    
        sl = map(slice, lb, ub)
    
        sample = h5Group[path][tuple(sl)]
        #print sample.shape
    
    def prepare_tstfile(self, shape, filename):
        f = h5py.File(filename, 'w')
        f.create_dataset('test_dataset', data=numpy.random.rand(*shape))
        f.close()
    
    def tst_multithread(self, filename):
        f = h5py.File(filename)
    
        threads = []
        for i in range(100):
            threads.append(threading.Thread( target=partial(self.readFromGroup, f, 'test_dataset') ))
            threads[-1].start()
        
        for i in range(10):
            threads[i].join()
        
        f.close()
    
    def readInGreenlet(self, h5Group, path, next_greenlet, i):
        self.readFromGroup(h5Group, path)
        if next_greenlet is not None:
            next_greenlet.switch()
    
    def tst_greenlet(self, f):
        greenlets = []
        next_greenlet=None
        for i in range(10):
            gr = greenlet.greenlet( partial(self.readInGreenlet, f, 'test_dataset', next_greenlet, i) )
            greenlets.append(gr)
            next_greenlet=greenlets[i]
    
        # Each greenlet switches to the previous one...
        greenlets[-1].switch()
        
    
    def tst_multithread_greenlet(self, files):
        threads = []
        for i in range(10):
            threads.append(threading.Thread( target=partial(self.tst_greenlet, files[i%2]) ))
            threads[-1].start()
        
        for i in range(10):
            threads[i].join()

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)

    if not ret: sys.exit(1)
