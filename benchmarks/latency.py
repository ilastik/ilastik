import threading
import time
import lazyflow
from lazyflow.graph import *
from lazyflow import operators


g = Graph()

mcount = 30000
lock = threading.Lock()
event = threading.Event()


class A(threading.Thread):
  def run(self):
    for i in range(1,mcount):
      event.set()
      lock.acquire()
      event.wait()
      event.clear()
      try:
        lock.release()
      except:
        pass
    try:
      lock.release()
    except:
      pass
    event.set()
  
class B(threading.Thread):
  def run(self):
    for i in range(1,mcount):
      lock.acquire()
      event.wait()
      event.clear()
      try:
        lock.release()
      except:
        pass
      event.set()
    try:
      lock.release()
    except:
      pass
    event.set()




class C(object):
  def __init__(self,shape,dtype=numpy.uint8):
    self.array = numpy.ndarray(shape,dtype)

  def __getitem__(self,key):
    return self.array[key]


c = operators.OpArrayCache(g)
p = operators.OpArrayPiper(g)

arr = numpy.ndarray((100,100,100),numpy.uint8)

c.inputs["Input"].setValue(arr)
p.connect(Input = c.outputs["Output"])

t1 = time.time()
for i in range(0,mcount):
  res = numpy.ndarray((1,),numpy.uint8)
t2 = time.time()
print "\n\n"
print "PYTHON NUMPY ALLOC OVERHEAD:    %f seconds for %d iterations" % (t2-t1,mcount)
print "                                %fus latency" % ((t2-t1)*1e6/mcount,)


t1 = time.time()
for i in range(0,mcount):
  res = arr[1:2,1:2,1:2]
t2 = time.time()
print "\n\n"
print "PYTHON NUMPY CALL OVERHEAD:     %f seconds for %d iterations" % (t2-t1,mcount)
print "                                %fus latency" % ((t2-t1)*1e6/mcount,)


c = C((100,100,100),numpy.uint8)
t1 = time.time()
for i in range(0,mcount):
  res = c[1:2,1:2,1:2]
t2 = time.time()
print "\n\n"
print "PYTHON DYN DISPATCH OVERHEAD:   %f seconds for %d iterations" % (t2-t1,mcount)
print "                                %fus latency" % ((t2-t1)*1e6/mcount,)

a = A()
b = B()

t1 = time.time()
a.start()
b.start()
a.join()
b.join()
t2 = time.time()
print "\n\n"
print "PYTHON THREAD SWITCH OVERHEAD:  %f seconds for %d iterations" % (t2-t1,mcount)
print "                                %fus latency" % ((t2-t1)*1e6/mcount,)




t1 = time.time()
requests = []
for i in range(0,mcount):
  r = p.outputs["Output"][3,3,3].allocate().wait()
t2 = time.time()
print "\n\n"
print "LAZYFLOW SYNC WAIT OVERHEAD:    %f seconds for %d iterations" % (t2-t1,mcount)
print "                                %fus latency" % ((t2-t1)*1e6/mcount,)


t1 = time.time()
requests = []
for i in range(0,mcount):
  r = p.outputs["Output"][3,3,3].allocate()
  requests.append(r)

for r in requests:
  r.wait()
t2 = time.time()
print "\n\n"
print "LAZYFLOW ASYNC WAIT OVERHEAD:   %f seconds for %d iterations" % (t2-t1,mcount)
print "                                %fus latency" % ((t2-t1)*1e6/mcount,)

