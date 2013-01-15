"""
This module supports serializing a tiny subset of things
into hdf5 files using h5py. usage example:

---
import h5py

f = h5py.File("/tmp/test.h5")
g = h5py.create_group("dump_zone")

g.dumpObject(someObject)

reconstructedObject = g.reconstructObject()
---

To support hdf5 dumping and restoring your
objects must implement the interface of the
H5Dumpable class. I.e. your class should reimplement the following
two methods:

    def dumpToH5G(self, h5g, patchBoard):
        pass

    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        pass

"""
import h5py
import string
import types
import sys
import traceback
import copy
import numpy
try:
    import cPickle as pickle
except:
    import pickle


class H5Dumpable(object):
    """
    Inherit from this class and reimplement the
    dumpToH5G instance method and the reconstructFromH5G
    class method to make your object dumpable.
    (or just ducktype)
    """

    def dumpToH5G(self, h5group):
        """
        This method should save your object to the given h5group
        """
        pass

    @classmethod
    def reconstructFromH5G(cls, h5group):
        """
        This method should construct and return a correctly
        initialized instance of your object from the h5group
        """
        pass

#
# Helper functions
#


def stringToClass(s):
    """
    Return the class object that corresponds to
    the somemodule.submodule.ClassName identifier string
    """
    parts = s.split(".")
    if parts[0] == "__builtin__":
        parts[0] = "__builtins__"
    cls = globals().get(parts[0],None)
    if cls is None:
        cls = __import__(parts[0])
        cls = cls.__dict__
    else:
        if not isinstance(cls, dict):
            cls = cls.__dict__
    for p in parts[1:-1]:
        cls = cls[p].__dict__
    if parts[-1] == "NoneType":
        cls = type(None)
    else:
        cls = cls[parts[-1]]
    return cls

def instanceClassToString(thing):
    """
    Return the complete somemodule.submodule.ClassName identifier
    for the given object instance
    """
    return str(thing.__class__.__module__ + "." + thing.__class__.__name__)

def classToString(thing):
    """
    Return the complete somemodule.submodule.ClassName identifier
    for the given class
    """
    return str(thing.__module__ + "." + thing.__name__)

def dumpObjectToH5G(self, thing, patchBoard = {}):
    """
    Helper method that is injected into the h5py.Group class.

    h5py Group object then have the following instance method:

        group.dumpObject(someObject)

    """

    self.attrs["className"] = instanceClassToString(thing)
    self.attrs["id"] = id(thing)
    if patchBoard.has_key(id(thing)):
        # if the object has already been stored, return
        # this might happen in circular dependencies
        objGroup = self[patchBoard[id(thing)]]
        self.attrs["className"] = "h5dumprestoreReference"
        self.attrs["reference"] = str(objGroup.name)
        return
    else:
        patchBoard[id(thing)] = str(self.name) #save the group in which an object is stored

    if hasattr(thing, "dumpToH5G"):
        thing.dumpToH5G(self, patchBoard)
    else:
        if isinstance(thing,numpy.ndarray):
            self.attrs["dtype"] = thing.dtype.__str__()
            self.attrs["shape"] = thing.shape
            if thing.dtype != object:
                self.create_dataset("ndarray", data = thing)
            else:
                view = thing.ravel()
                for i in range(view.shape[0]):
                    g = self.create_group(str(i))
                    g.dumpObject(view[i], patchBoard)

        elif isinstance(thing, (list,tuple)):
            self.attrs["len"] = len(thing)
            for i,o in enumerate(thing):
                g = self.create_group(str(i))
                g.dumpObject(o, patchBoard)
        elif isinstance(thing, dict):
            for i,o in thing.items():
                g = self.create_group(str(i))
                g.dumpObject(o, patchBoard)
        elif isinstance(thing, type(None)):
            pass
        elif isinstance(thing, numpy.dtype):
            self.attrs["name"] =  thing.name
        elif isinstance(thing, type):
            self.attrs["name"] =  thing.__name__
        elif isinstance(thing, type):
            pass
        elif isinstance(thing, (float, int, str)):
            self.attrs["value"] = thing
        else:
            #try pickling the thing
            try:
                self.attrs["picklevalue"] = pickle.dumps(thing)
            except Exception, e:
                print "ERROR: cannot pickle %r " % ( thing,)
                traceback.print_exception(e)
                sys.exit(1)


def reconstructObjectFromH5G(self, patchBoard = None):
    """
    Helper method that is injected into the h5py.Group class.

    h5py Group object then have the following instance method:

        group.reconstructObject(someObject)

    """
    resultIsNone = False
    if patchBoard is None:
        patchBoard = {}
        self.patchBoard = patchBoard

    #handle circular references
    if patchBoard.has_key(self.attrs["id"]):
        #assert patchBoard[self.attrs["id"]] is not None
        return patchBoard[self.attrs["id"]]

    if self.attrs["className"] == "h5dumprestoreReference":
        origGroup = self[self.attrs["reference"]]
        result = origGroup.reconstructObject(patchBoard)
        patchBoard[self.attrs["id"]] = result

        return result

    cls = stringToClass(self.attrs["className"])
    if hasattr(cls,"reconstructFromH5G"):
        result =  cls.reconstructFromH5G(self, patchBoard)
        assert result is not None, "%r %r" % (self.attrs["className"],self.attrs["className"])
        patchBoard[self.attrs["id"]] = result


    else:
        if cls == numpy.ndarray:
            try:
                dtype = numpy.__dict__[self.attrs["dtype"]]
            except:
                #assume that otherwise the dtype has been an object ?! correct ??
                dtype = object
            if dtype != object:
                arr = self["ndarray"][:]
            else:
                arr = numpy.ndarray(self.attrs["shape"], dtype = object)
                view = arr.ravel()
                for i,g in self.items():
                    view[int(i)] = g.reconstructObject(patchBoard)
            result = arr
            patchBoard[self.attrs["id"]] = result
        elif cls == vigra.VigraArray:
            try:
                dtype = numpy.__dict__[self.attrs["dtype"]]
            except:
                #assume that otherwise the dtype has been an object ?! correct ??
                dtype = object
            if dtype != object:
                arr = self["ndarray"][:]
            else:
                arr = vigra.VigraArray(self.attrs["shape"], dtype = object)
                view = arr.ravel()
                for i,g in self.items():
                    view[int(i)] = g.reconstructObject(patchBoard)
            result = arr
            patchBoard[self.attrs["id"]] = result

        elif cls == list or cls == tuple:
            length = self.attrs["len"]
            temp = range(0,length)
            patchBoard[self.attrs["id"]] = temp
            for i,g in self.items():
                temp[int(i)] = g.reconstructObject(patchBoard)
            if cls == tuple:
                temp = tuple(temp)
            result =  temp
        elif cls == dict:
            temp = {}
            patchBoard[self.attrs["id"]] = temp
            for i,g in self.items():
                temp[str(i)] = g.reconstructObject(patchBoard)
            result =  temp
        elif cls in [float, int, str]:
            result =  self.attrs["value"]
            patchBoard[self.attrs["id"]] = result
        elif cls == type(None):
            resultIsNone = True
            result = None
            #patchBoard[self.attrs["id"]] = None
        elif cls == numpy.dtype:
            result = numpy.__dict__[self.attrs["name"]]
        elif cls == type:
            result = numpy.__dict__[self.attrs["name"]]
        elif cls == True.__class__:
            result = self.attrs["value"]
        else:
            try:
                pickles = self.attrs["picklevalue"]
            except:
                print "ERROR restoring object from file: classname ", self.attrs["className"], cls
                assert 1 == 2
            result = pickle.loads(pickles)


    if not resultIsNone:
        return result
    else:
        return None


def dumpSubObjectsToH5G(self, subObjects, patchBoard):
    for k,v in subObjects.items():
        g = self.create_group(k)
        g.dumpObject(v, patchBoard)

def reconstructSubObjectFromH5G(self, mainObject, subObjects, patchBoard):
    for k,v in subObjects.items():
        g = self[k]
        obj = g.reconstructObject(patchBoard)
        setattr(mainObject, v, obj)




# inject the above two helper methods into
# the h5py Group class :
setattr(h5py.Group,"dumpObject",dumpObjectToH5G)
setattr(h5py.Group,"reconstructObject",reconstructObjectFromH5G)
setattr(h5py.Group,"dumpSubObjects",dumpSubObjectsToH5G)
setattr(h5py.Group,"reconstructSubObjects",reconstructSubObjectFromH5G)




######################################################
#
#    inject h5dumprestore support
#    into vigra.AxisTags
#
#######################################################

import vigra

def dumpAxisTags(self, h5G, patchBoard):
    cp = copy.copy(self)
    length = len(cp)
    cp.dropChannelAxis()
    length2 = len(cp)
    insertChannel = False
    if length != length2:
        insertChannel = True
    h5G.attrs["ndim"] =  length2
    h5G.attrs["hasChannelAxis"] = insertChannel


def reconstructAxisTags(cls, h5G, patchBoard):
    ndim = h5G.attrs["ndim"]
    if h5G.attrs["hasChannelAxis"] == True:
        at = vigra.VigraArray.defaultAxistags(ndim + 1)
    else:
        at = vigra.VigraArray.defaultAxistags(ndim + 1)
        at.dropChannelAxis()
    return at

setattr(vigra.AxisTags,"dumpToH5G",dumpAxisTags)
setattr(vigra.AxisTags,"reconstructFromH5G", types.MethodType(reconstructAxisTags, vigra.AxisTags))


######################################################
#
#    inject h5dumprestore support
#    into vigra.learning.RandomForest
#
#    unfortunately the RandomForest does not support
#    serialization to bytestreams or string so
#    we must use a hackish way to achieve the same.
#
#######################################################

import tempfile

def dumpRF(self, h5G, patchBoard):
    """
    hackish way to save into our own hdf5 group dataset and keep control
    of things, we do not like C/C++ coded hdf5 saving
    routines that do not accept h5py Group objects from python!!!!
    """

    # first, save the RF to a tempfile
    tf = tempfile.NamedTemporaryFile(delete=False)
    self.writeHDF5(tf.name, "RandomForest")
    tf.close()

    arr = numpy.fromfile(tf.name, dtype = numpy.uint8)
    # finally, save into our group
    h5G.create_dataset("classifierh5content", data = arr)

import time

def reconstructRF(cls, h5G, patchBoard):
    """
    hackish way to restore from our own hdf5 group dataset.
    """
    classifierDump = h5G["classifierh5content"].value
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()
    classifierDump.tofile(tf.name)

    classifier = vigra.learning.RandomForest(tf.name, "RandomForest")

    return classifier

#inject the funcitonality into the vigra.learning.RandomForest class
setattr(vigra.learning.RandomForest,"dumpToH5G",dumpRF)
setattr(vigra.learning.RandomForest,"reconstructFromH5G", types.MethodType(reconstructRF, vigra.learning.RandomForest))



if __name__ == '__main__':

    at = vigra.VigraArray.defaultAxistags(4)

    at.dropChannelAxis()
    import svm

    svmmod = svm.svm_model()

    testObjects = [ numpy.zeros((100,20,7),numpy.uint8), at,[at,numpy.zeros((100,20,7),numpy.uint8)], {"pups" : at}, [at, "test", 42, 42.0, {"42" : 42,"test" : ["test"]}], svmmod]

    for o in testObjects:
        f = h5py.File("/tmp/test.h5","w")
        g = f.create_group("/testg")
        g.dumpObject(o)
        o2 = g.reconstructObject()

        print
        print "################"
        print "Original:", o
        print "------"
        print "Result  :", o2
        print o2.__class__

        f.close()

    print "################"
    print "Testing random forest save/restore"

    data = numpy.ndarray((10,3), numpy.float32)
    labels = numpy.ones((10,1), numpy.uint32)
    labels[5:,0] = 2
    rf = vigra.learning.RandomForest()
    rf.learnRF(data, labels)

    f = h5py.File("/tmp/test.h5","w")
    g = f.create_group("/testg")
    g.dumpObject(rf)
    o2 = g.reconstructObject()

    f.close()
