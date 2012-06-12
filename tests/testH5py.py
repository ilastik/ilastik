import threading
from functools import partial

import numpy
import h5py
import greenlet

def readFromGroup( h5Group, path ):
    shape = numpy.array(h5Group[path].shape)

    # Choose a random lower bound in the lower half-space    
    lb = (numpy.random.rand(len(shape))*shape/2).astype(int)

    # Choose a random upper bound in the upper half-space    
    ub = (numpy.random.rand(len(shape))*shape/2).astype(int) + shape/2

    # Combine into a slicing we can index with    
    sl = map(slice, lb, ub)

    sample = h5Group[path][tuple(sl)]
    print sample.shape

def prepare_testfile(shape, filename):
    f = h5py.File(filename, 'w')
    f.create_dataset('test_dataset', data=numpy.random.rand(*shape))
    f.close()

def test_multithread(filename):
    f = h5py.File(filename)

    threads = []
    for i in range(100):
        threads.append(threading.Thread( target=partial(readFromGroup, f, 'test_dataset') ))
        threads[-1].start()
    
    for i in range(10):
        threads[i].join()
    
    f.close()

def readInGreenlet(h5Group, path, next_greenlet, i):
    readFromGroup(h5Group, path)
    if next_greenlet is not None:
        next_greenlet.switch()

def test_greenlet(f):
    greenlets = []
    next_greenlet=None
    for i in range(10):
        gr = greenlet.greenlet( partial(readInGreenlet, f, 'test_dataset', next_greenlet, i) )
        greenlets.append(gr)
        next_greenlet=greenlets[i]

    # Each greenlet switches to the previous one...
    greenlets[-1].switch()
    

def test_multithread_greenlet(files):
    threads = []
    for i in range(10):
        threads.append(threading.Thread( target=partial(test_greenlet, files[i%2]) ))
        threads[-1].start()
    
    for i in range(10):
        threads[i].join()

if __name__ == "__main__":
    shape = (10,100,100,100)

    filename1 = 'test1.h5'
    prepare_testfile(shape, filename1)

    filename2 = 'test2.h5'
    prepare_testfile(shape, filename2)

    f1 = h5py.File(filename1)
    f2 = h5py.File(filename2)
    
    #test_greenlet(f)
    test_multithread_greenlet([f1, f2])

    f1.close()
    f2.close()

    #test_multithread(filename)
