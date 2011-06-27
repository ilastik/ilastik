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
sys.path.append("/home/cstraehl/Projects/eclipse-workspace/graph")


import string
from lazyflow.graph import *
from lazyflow.operators.vigraOperators import *
from openalea.core import *



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



for o in Operators.operators.values():
    print "Generating OpenAlea function for Operator ",o
    print type(o)
    

    inputArgs = []
    outputArgs = []
    for slot in o.inputSlots:
        inputArgs.append(slot.name)
    for slot in o.outputSlots:
        outputArgs.append(slot.name)

    doConnections = []
    for slot in o.inputSlots:
        doConnections.append("o.inputs['%s'].connect(%s)" % (slot.name,slot.name))
    
    
    assignmentsLeft = []    
    for slot in o.outputSlots:
        assignmentsLeft.append(slot.name)
    
    assignmentsRight = []
    for slot in o.outputSlots:
        assignmentsRight.append("o.outputs['%s']" % (slot.name,) )

    if len(assignmentsLeft) > 0:
        
        code = """\n
def OA_FUNC_%s(%s):
    o = %s(globalGraph) #create Operator
    print o
    %s #doConnections
    %s = %s #set return values
    return %s #return outputSlots
    """ % (o.__name__,string.join(inputArgs,","),o.__name__,string.join(doConnections,"\n    "), string.join(assignmentsLeft,","),string.join(assignmentsRight,","),string.join(assignmentsLeft,","))
    
        print code    
    
        exec code
    else:
        code = """\n
def OA_FUNC_%s(%s):
    o = %s(globalGraph)
    print o
    %s #doConnections
    print o
    """ % (o.__name__,string.join(inputArgs,","),o.__name__,string.join(doConnections,"\n    "))
            
        exec code
        
    
    #ourMod.__dict__["OA_FUNC_" + o.name] = eval ("OA_FUNC_" + o.name)
