# -*- python -*-
#
#       image : geometric transformation filters
#
#       Copyright 2006-2009 INRIA - CIRAD - INRA  
#
#       File author(s): Eric Moscardi <eric.moscardi@sophia.inria.fr>
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
# 
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
################################################################################
"""Node declaration for image
"""

__license__ = "Cecill-C"
__revision__ = " $Id:  $ "

import sys
sys.path.append("/home/lfiaschi/graph-christoph")


import string
from lazyflow.graph import *
from lazyflow.operators.vigraOperators import *
from lazyflow.operators.operators import *
from lazyflow.operators.valueProviders import *
from lazyflow.operators.classifierOperators import *
from lazyflow.operators.generic import *
from openalea.core import *
from openalea.image_wralea import IImage

import lazyflowoperators

__all__ = []



class ILFSlot(IInterface):
    pass



try:
    if globalGraph is not None:
        pass
except:
    globalGraph = Graph()
    openaleaWraps = []



Operators.registerOperatorSubclasses()

modname = globals()['__name__']
ourMod = sys.modules[modname]
ourDict = ourMod.__dict__
print "### True module name : ", modname, " ###"
__name__ = "ourstuff"


for o in Operators.operators.values():
    print "Wrapping Operator ",o,"for OpenAlea"
    print type(o)
    
    factoryInputs = []
    for slot in o.inputSlots:
        itype = None
        if slot.stype == "string":
            itype = IStr()
        elif slot.stype == "filestring":
            itype = IFileStr()
        elif slot.stype == "sequence":
            itype = ISequence()
        elif slot.stype == "integer":
            itype = IInt()
        elif slot.stype == "float":
            itype = IFloat()
        factoryInputs.append( dict(name = slot.name, interface = itype) )

    factoryOutputs= []
    for slot in o.outputSlots:
        itype = None
        if slot.stype == "string":
            itype = IStr()
        elif slot.stype == "filestring":
            itype = IFileStr()
        elif slot.stype == "sequence":
            itype = ISequence()
        elif slot.stype == "integer":
            itype = IInt()
        elif slot.stype == "float":
            itype = IFloat()
        factoryOutputs.append( dict(name = slot.name, interface = itype) )    
    
    tempfac = Factory(name = o.name,
                description = o.description,
                category = "Lazyflow." + o.category,
                nodemodule = "lazyflowoperators",
                nodeclass = "OA_FUNC_" + o.__name__,
                inputs = list(factoryInputs),
                outputs = list(factoryOutputs),
                )

    ourDict[o.name] = tempfac

    __all__.append(o.name)
