#clang c++
cimport cython
import cython
import numpy as np

from libcpp.queue cimport queue  
from libcpp.deque cimport deque
from libcpp.vector cimport vector

# "cimport" is used to import special compile-time information
# about the numpy module (this is stored in a file numpy.pxd which is
# currently part of the Cython distribution).
cimport numpy as np
# We now need to fix a datatype for our arrays. I've used the variable
# DTYPE for this, which is assigned to the usual NumPy runtime
# type info object.
DTYPE_i32 = np.int32
DTYPE_f32 = np.float32
# "ctypedef" assigns a corresponding compile-time type to DTYPE_t. For
# every type in the numpy module there's a corresponding compile-time
# type with a _t-suffix.
ctypedef np.int32_t DTYPE_t_i32
ctypedef np.float32_t DTYPE_t_f32
                                                                                                  
cdef fused integer_t:
  int
  char
  long

cdef fused value_t:
  char
  int
  float
  double

cdef struct neighborhood_t_t:
  int a
  int b
  float val


cdef struct coordinate_t_t:
  int x
  int y
  int z

cdef inline int int_max(int a, int b): return a if a >= b else b
cdef inline int int_min(int a, int b): return a if a <= b else b

@cython.boundscheck(False) # turn of bounds-checking for entire function
def seededTurboWS(np.ndarray[np.int32_t, ndim=3, mode="strided"] seeds,
                  np.ndarray[value_t, ndim=3, mode="strided"] involume, int queueCount = 255):
  """
  do a turbo watershed from the seeds in place
  
  Copyright 2011 Christoph Straehle cstraehl@iwr.uni-heidelberg.de

  Arguments:
  seeds -- a 3D np.int32 seed image
  volume  -- a 3D np.float32 scalar volume

  Returns:
  a 3D np.int32 label image, i.e. the mopdified seed argument
  """
 
  cdef np.ndarray[np.float32_t, ndim=3] volume = involume.astype(np.float32)
  assert (seeds.shape == volume.shape, "Seeds  and volume  must have same shape !" )

  cdef int sizeX = seeds.shape[0]
  cdef int sizeY = seeds.shape[1]
  cdef int sizeZ = seeds.shape[2]

  cdef int x,y,z = 0

  cdef float scaling

  # determine maximum label
  cdef float volMax = volume[0,0,0]
  cdef float volMin = volume[0,0,0]                             
  for x in range(0,sizeX):
    for y in range(0,sizeY):
      for z in range(0,sizeZ):
        if volume[x,y,z] < volMin:
          volMin = volume[x,y,z]
        if volume[x,y,z] > volMax:
          volMax = volume[x,y,z]                             
  scaling = (queueCount-1)/(volMax-volMin)

  cdef vector[deque[coordinate_t_t]] hqueue
  cdef coordinate_t_t tempCoord, tempCoord2
  hqueue.resize(queueCount)
  
  for x in range(0,sizeX):
    for y in range(0,sizeY):
      for z in range(0,sizeZ):
        if seeds[x,y,z] != 0:
          tempCoord.x = x
          tempCoord.y = y
          tempCoord.z = z
          hqueue[0].push_back(tempCoord)
  
  cdef int waterLevel = 0
  cdef int curLevel = 0
  cdef int bestNeighborLevel = queueCount
  cdef int bestNeighborLabel = 0


  cdef int iterations = 0
  for waterLevel in range(0,queueCount):
    #print "Waterlevel %d, previous iterations: %d" % (waterLevel, iterations)
    #terations = 0
    while not hqueue[waterLevel].empty():
      tempCoord = hqueue[waterLevel].front()
      tempCoord2 = tempCoord
      hqueue[waterLevel].pop_front()
      bestNeighborLevel = queueCount+1
      iterations += 1

      if  seeds[tempCoord2.x,tempCoord2.y,tempCoord2.z] == 0 or waterLevel == 0:
        if tempCoord.x > 0:
          if seeds[tempCoord.x - 1, tempCoord.y, tempCoord.z] != 0:
            if (volume[tempCoord.x - 1, tempCoord.y,tempCoord.z] - volMin)*scaling < bestNeighborLevel:
              bestNeighborLevel =  <int>((volume[tempCoord.x -1, tempCoord.y,tempCoord.z] - volMin)*scaling)
              bestNeighborLabel = seeds[tempCoord.x -1, tempCoord.y,tempCoord.z] 
          else:
            tempCoord.x -= 1
            curLevel = <int>((volume[tempCoord.x, tempCoord.y,tempCoord.z] - volMin)*scaling)
            curLevel = int_max(curLevel,waterLevel)
            hqueue[curLevel].push_back(tempCoord)
            tempCoord.x += 1
        
        if tempCoord.y > 0:
          if seeds[tempCoord.x, tempCoord.y - 1, tempCoord.z] != 0:
            if (volume[tempCoord.x, tempCoord.y-1,tempCoord.z] - volMin)*scaling < bestNeighborLevel:
              bestNeighborLevel =  <int>((volume[tempCoord.x, tempCoord.y-1,tempCoord.z] - volMin)*scaling)
              bestNeighborLabel = seeds[tempCoord.x, tempCoord.y-1,tempCoord.z] 
          else:
            tempCoord.y -= 1
            curLevel = <int>((volume[tempCoord.x, tempCoord.y,tempCoord.z] - volMin)*scaling)
            curLevel = int_max(curLevel,waterLevel)
            hqueue[curLevel].push_back(tempCoord)
            tempCoord.y += 1

        if tempCoord.z > 0:
          if seeds[tempCoord.x, tempCoord.y, tempCoord.z-1] != 0:
            if (volume[tempCoord.x, tempCoord.y,tempCoord.z-1] - volMin)*scaling < bestNeighborLevel:
              bestNeighborLevel =  <int>((volume[tempCoord.x, tempCoord.y,tempCoord.z-1] - volMin)*scaling)
              bestNeighborLabel = seeds[tempCoord.x, tempCoord.y,tempCoord.z-1] 
          else:
            tempCoord.z -= 1
            curLevel = <int>((volume[tempCoord.x, tempCoord.y,tempCoord.z-1] - volMin)*scaling)
            curLevel = int_max(curLevel,waterLevel)
            hqueue[curLevel].push_back(tempCoord)
            tempCoord.z += 1

        
        
        if tempCoord.x < sizeX-1:
          if seeds[tempCoord.x + 1, tempCoord.y, tempCoord.z] != 0:
            if (volume[tempCoord.x + 1, tempCoord.y,tempCoord.z] - volMin)*scaling < bestNeighborLevel:
              bestNeighborLevel =  <int>((volume[tempCoord.x +1, tempCoord.y,tempCoord.z] - volMin)*scaling)
              bestNeighborLabel = seeds[tempCoord.x +1, tempCoord.y,tempCoord.z] 
          else:
            tempCoord.x += 1
            curLevel = <int>((volume[tempCoord.x, tempCoord.y,tempCoord.z] - volMin)*scaling)
            curLevel = int_max(curLevel,waterLevel)
            hqueue[curLevel].push_back(tempCoord)
            tempCoord.x -= 1
        
        if tempCoord.y < sizeY-1:
          if seeds[tempCoord.x, tempCoord.y + 1, tempCoord.z] != 0:
            if (volume[tempCoord.x, tempCoord.y+1,tempCoord.z] - volMin)*scaling < bestNeighborLevel:
              bestNeighborLevel =  <int>((volume[tempCoord.x, tempCoord.y+1,tempCoord.z] - volMin)*scaling)
              bestNeighborLabel = seeds[tempCoord.x, tempCoord.y+1,tempCoord.z] 
          else:
            tempCoord.y += 1
            curLevel = <int>((volume[tempCoord.x, tempCoord.y,tempCoord.z] - volMin)*scaling)
            curLevel = int_max(curLevel,waterLevel)
            hqueue[curLevel].push_back(tempCoord)
            tempCoord.y -= 1

        if tempCoord.z < sizeZ-1:
          if seeds[tempCoord.x, tempCoord.y, tempCoord.z+1] != 0:
            if (volume[tempCoord.x, tempCoord.y,tempCoord.z+1] - volMin)*scaling < bestNeighborLevel:
              bestNeighborLevel =  <int>((volume[tempCoord.x, tempCoord.y,tempCoord.z+1] - volMin)*scaling)
              bestNeighborLabel = seeds[tempCoord.x, tempCoord.y,tempCoord.z+1] 
          else:
            tempCoord.z += 1
            curLevel = <int>((volume[tempCoord.x, tempCoord.y,tempCoord.z] - volMin)*scaling)
            curLevel = int_max(curLevel,waterLevel)
            hqueue[curLevel].push_back(tempCoord)
            tempCoord.z -= 1
        
        seeds[tempCoord2.x,tempCoord2.y,tempCoord2.z] = bestNeighborLabel
  
  print "DID ITERATIONS: %d" % iterations
  return seeds


def buildAdjacencyGraph(np.ndarray[np.int32_t, ndim=3, mode="strided"] labelMap ,
                        np.ndarray[value_t, ndim=3, mode="strided"] edgeMapIn):
  """
  builds the adjacency graph structure for an image.

  Copyright 2011 Christoph Straehle cstraehl@iwr.uni-heidelberg.de

  Arguments:
  labelMap -- a 3D np.int32 label image
  edgeMap  -- a 3D np.float32 edge indicator image

  Returns:
  a coo matrix as a tuple (coo_ind, coo_data) (see scipy.sparse) 
  """

  cdef np.ndarray[np.float32_t, ndim=3] edgeMap = edgeMapIn.astype(np.float32)

  cdef int sizeX = labelMap.shape[0]
  cdef int sizeY = labelMap.shape[1]
  cdef int sizeZ = labelMap.shape[2]

  cdef int x,y,z,a,b

  # determine maximum label
  cdef int maxLabel = 0
  for x in range(0,sizeX):
    for y in range(0,sizeY):
      for z in range(0,sizeZ):
        maxLabel = int_max(maxLabel,labelMap[x,y,z])  

  bbb = np.zeros((maxLabel+1,), dtype=np.int32)
  cdef np.ndarray[dtype=DTYPE_t_i32,ndim=1] neighborCount = bbb

  cdef int totalNeighborhoods = 0

  # count the number of labels
  for x in range(0,sizeX):
    for y in range(0,sizeY):
      for z in range(0,sizeZ):
        if x < sizeX-1:
          a = labelMap[x,y,z]
          b = labelMap[x+1,y,z]
          if a > b:
            neighborCount[a] = neighborCount[a]+1
            totalNeighborhoods += 1
          if b > a:
            neighborCount[b] = neighborCount[b]+1
            totalNeighborhoods += 1
        if y < sizeY-1:
          a = labelMap[x,y,z]
          b = labelMap[x,y+1,z]
          if a > b:
            neighborCount[a] = neighborCount[a]+1
            totalNeighborhoods += 1
          if b > a:
            neighborCount[b] = neighborCount[b]+1
            totalNeighborhoods += 1
        if z < sizeZ-1:
          a = labelMap[x,y,z]
          b = labelMap[x,y,z+1]
          if a > b:
            neighborCount[a] = neighborCount[a]+1
            totalNeighborhoods += 1
          if b > a:
            neighborCount[b] = neighborCount[b]+1
            totalNeighborhoods += 1

  cdef np.ndarray[dtype=np.int32_t,ndim=1] neighborOffset, offsetBackup
  neighborOffset = np.cumsum(neighborCount).astype(np.int32)
  neighborOffset[1:] = neighborOffset[:-1]
  neighborOffset[0] = 0
  offsetBackup = neighborOffset.copy()

  neighborhood_t = np.dtype([('a', np.int32), ('b', np.int32), ('val', np.float32)])

  bbb = np.ndarray((totalNeighborhoods+1,),dtype=neighborhood_t)
  cdef np.ndarray[dtype=neighborhood_t_t, ndim=1]  neighbors = bbb

  print "count", totalNeighborhoods
  print "sum", np.sum(neighborCount)


  cdef float av,bv
  # add everything to the neighborhood array
  for x in range(0,sizeX):
    for y in range(0,sizeY):
      for z in range(0,sizeZ):
        if x < sizeX-1:
          a = labelMap[x,y,z]
          b = labelMap[x+1,y,z]
          av = edgeMap[x,y,z]
          bv = edgeMap[x+1,y,z]
          if a > b:
            neighbors[neighborOffset[a]].val = (av+bv)/2.0
            neighbors[neighborOffset[a]].b = b
            neighbors[neighborOffset[a]].a = a
            neighborOffset[a]+=1
          if b > a:
            neighbors[neighborOffset[b]].val  =  (av+bv)/2.0 
            neighbors[neighborOffset[b]].b = a
            neighbors[neighborOffset[b]].a = b
            neighborOffset[b]+=1

        if y < sizeY-1:
          a = labelMap[x,y,z]
          b = labelMap[x,y+1,z]
          av = edgeMap[x,y,z]
          bv = edgeMap[x,y+1,z]
          if a > b:
            neighbors[neighborOffset[a]].val  = (av+bv)/2.0
            neighbors[neighborOffset[a]].b = b
            neighbors[neighborOffset[a]].a = a
            neighborOffset[a]+=1
          if b > a:
            neighbors[neighborOffset[b]].val  =  (av+bv)/2.0 
            neighbors[neighborOffset[b]].b = a
            neighbors[neighborOffset[b]].a = b
            neighborOffset[b]+=1

        if z < sizeZ-1:
          a = labelMap[x,y,z]
          b = labelMap[x,y,z+1]
          av = edgeMap[x,y,z]
          bv = edgeMap[x,y,z+1]
          if a > b:
            neighbors[neighborOffset[a]].val  = (av+bv)/2.0
            neighbors[neighborOffset[a]].b = b
            neighbors[neighborOffset[a]].a = a
            neighborOffset[a]+=1
          if b > a:
            neighbors[neighborOffset[b]].val  =  (av+bv)/2.0 
            neighbors[neighborOffset[b]].b = a
            neighbors[neighborOffset[b]].a = b
            neighborOffset[b]+=1


  cdef int nsize
  cdef int nMaxCount = neighbors.shape[0]
  cdef int lastA = -1
  cdef int lastB = -1
  cdef int i

  neighborOffset = offsetBackup[:]
  # cdef np.ndarray[dtype=neighborhood_t_t, ndim=1]  tempn

  # sort teh neighborhood information
  for i in range(neighborOffset.shape[0]-1):
    neighbors[neighborOffset[i]:neighborOffset[i+1]].sort(order=('b','val'))
    # neighbors[neighborOffset[i]:neighborOffset[i+1]]=tempn[:]

  temp = neighbors[neighborOffset[-1]:].sort(order=('b','val'))
  # neighbors[neighborOffset[-1]:]=temp

  nsize = 0
  lastA = -1
  lastB = -1
  # determine size of coo matrix
  for i in range(nMaxCount):
    if neighbors[i].a != lastA or neighbors[i].b != lastB:
      lastA = neighbors[i].a
      lastB = neighbors[i].b
      nsize += 1

  print "SIZE:", nsize

  bbb = np.ndarray((nsize,2),dtype=np.int32)
  cdef np.ndarray[dtype=np.int32_t, ndim=2]  coo_ind = bbb
  bbb = np.ndarray((nsize,),dtype=np.float32)
  cdef np.ndarray[dtype=np.float32_t, ndim=1]  coo_data = bbb

  cdef int j
  j = 0
  lastA = -1
  lastB = -1
  # FINALLY, construct the true graph
  for i in range(neighbors.shape[0]):
    if neighbors[i].a != lastA or neighbors[i].b != lastB:
      lastA = neighbors[i].a
      lastB = neighbors[i].b
      coo_ind[j,0] = lastA
      coo_ind[j,1] = lastB
      coo_data[j] = neighbors[i].val
      j += 1


  # returnthe tediously obtained results
  return (neighbors.shape[0],coo_ind,coo_data)



cdef struct edge:
  int From
  int To
  float weight

cdef struct vertex:
  vector[edge] edges


cdef buildGraphFromCOO(int vertex_count, 
                      np.ndarray[dtype=np.int32_t, ndim=2] coo_ind,
                      np.ndarray[dtype=np.float32_t, ndim=1] coo_data):
  """
  Build custom adjacency graph from
  COO matrix
  """

  cdef vector[vertex] vertices
  vertices.resize(vertex_count)

  cdef int i,j
  cdef edge e
  for i in range(coo_ind.shape[0]):
   
    e.From = coo_ind[i,0]
    e.To = coo_ind[i,1]
    e.weight = coo_data[i]

    vertices[e.From].edges.push_back(e)

    e.From = coo_ind[i,1]
    e.To = coo_ind[i,0]
    vertices[e.From].edges.push_back(e)

  return vertices



