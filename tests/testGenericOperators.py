import vigra
import threading
from lazyflow.graph import *
import copy

from lazyflow.operators.operators import OpArrayPiper 
from lazyflow.operators.vigraOperators import *
from lazyflow.operators.valueProviders import *
from lazyflow.operators.classifierOperators import *
from lazyflow.operators.generic import *

from lazyflow import operators
import numpy
from numpy.testing import *




if __name__=="__main__":
    
    
    g = Graph(numThreads = 10, softMaxMem = 2000*1024**2)
           
    
    
    op1=OpArrayPiper(g)
    op1.inputs["Input"].setValue(numpy.zeros((2,2))+10)
    
    op2=OpArrayPiper(g)
    op2.inputs["Input"].setValue(numpy.zeros((2,2))+20)
     
    multi=Op20ToMulti(g)
    
    multi.inputs["Input00"].connect(op1.outputs["Output"])
    multi.inputs["Input01"].connect(op2.outputs["Output"]) 
    
    

    
    merge=OpMultiArrayMerger(g)
    merge.inputs["Inputs"].connect(multi.outputs["Outputs"])
    merge.inputs["MergingFunction"].setValue(sum)
    
    
    res=merge.outputs["Output"][:].allocate().wait()
    
    assert (res==30).all()