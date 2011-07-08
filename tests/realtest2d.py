import vigra
import h5py
import numpy
import time
import add_context_functions as fun
from vigra import context


nx = 3
ny = 3
nc = 2
dummypred = numpy.zeros((nx, ny, nc), dtype=numpy.float32)
radii = numpy.array([1, 2], dtype=numpy.uint32)
nnew = 8*2*nc*radii.shape[0]
res = numpy.zeros((nx, ny, nnew), dtype=numpy.float32)
for x in range(nx):
    for y in range(ny):
        dummypred[x, y, 0] = x*2+y
        dummypred[x, y, 1] = x+y+100

#dummy = vigra.VigraArray(dummypred.shape, axistags=vigra.VigraArray.defaultAxistags(3)).astype(dummypred.dtype)
#dummy[:]=dummypred[:]
print dummy.dtype,dummy.shape,type(dummy)
print "here", dummypred.shape
vigra.context.starContext2Dmulti(radii, dummypred, res)
print res

print "first test"
passed1 = True

print dummypred[0:3, 0:3, 0]
print res[1, 1, 0:8]
print res[0, 0, 0:8]
print dummypred[0, 2, 0]
print res[0, 2, 0:8]

if numpy.any(dummypred[0, 0:3, 0]!=res[1, 1, 0:3]):
    print "wrong 1"
    passed1 = False

if (dummypred[1, 0, 0]!=res[1, 1, 3] or dummypred[1, 2, 0]!=res[1, 1, 4]):
    print "wrong 2"
    passed1 = False
    
if numpy.any(dummypred[2, 0:3, 0]!=res[1, 1, 5:8]):
    print "wrong 3"
    passed1 = False
    

print "\nsecond test"

#print dummypred[0:5, 0:5, 0]
#print res[1, 1, 8:16]
passed2 = True
if sum(res[1, 1, 8:16])!=4:
    print "wrong 4"
    passed2 = False
    print sum(res[1, 1, 8:16])
    
#print res[2, 2, 8:16]
if res[2, 2, 8]!=3:
    print "wrong 5"
    passed2 = False
    print res[2, 2, 8]
    
if passed1:
    print "First test passed"
else:
    print "First test failed"
    
if passed2:
    print "Second test passed"
else:
    print "Second test failed"
