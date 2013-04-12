"""
This module implements the basic flow graph
of the lazyflow module.

Basic usage example:

---
import numpy
import lazyflow.graph
from lazyflow.operators.operators import  OpArrayPiper


g = lazyflow.graph.Graph()

operator1 = OpArrayPiper(graph=g)
operator2 = OpArrayPiper(graph=g)

operator1.inputs["Input"].setValue(numpy.zeros((10,20,30), dtype=numpy.uint8))

operator2.inputs["Input"].connect(operator1.outputs["Output"])

result = operator2.outputs["Output"][:].wait()
---

"""

#Python
import sys
import copy
import functools
import collections
import itertools
import threading
import logging

#third-party
import psutil
if (int(psutil.__version__.split(".")[0]) < 1 and
    int(psutil.__version__.split(".")[1]) < 3):
    print ("Lazyflow: Please install a psutil python module version"
           " of at least >= 0.3.0")
    sys.exit(1)

#SciPy
import numpy

#lazyflow
from lazyflow import rtype
from lazyflow.request import Request
from lazyflow.stype import ArrayLike
from lazyflow.utility import slicingtools, Tracer, OrderedSignal, Singleton
from lazyflow.slot import InputSlot, OutputSlot, Slot
from lazyflow.operator import Operator, InputDict, OutputDict, OperatorMetaClass
from lazyflow.operatorWrapper import OperatorWrapper
from lazyflow.metaDict import MetaDict

#this class serves as a parent for nodes
#for now, it is to be kept for future use (Stuart)
class Graph(object):
    pass
