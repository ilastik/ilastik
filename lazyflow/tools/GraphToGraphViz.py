from lazyflow.graph import *
import subprocess
import os


class Node(object):
    
    def __init__(self, tree, ob):
        self.ob = ob
        self.ID = id(ob)
        self.obtype = None
        self.nextNodes = []
        self.name = None
        self.info = ""
        self.infoFile = ""
        self.tree = tree
    
    def visit(self):    
        if not self.tree.visited(self.ID):
            self._construct()

    def addInfo(self, info):
        self.info += str(info)
        
    def addNext(self, node):
        self.nextNodes.append(node)  
        
    def gettype(self):
        return self.obtype    
        
    def _construct(self):
        pass
    
    def _after_construct(self):
        pass
    
    def _writeInfo(self):
        pass
    

        


class ValNode(Node):
    
    def __init__(self, tree, ob, ID):
        
        Node.__init__(self,tree, ob)
        
        self.ID = ID

        self.name = ob.__class__.__name__
        
        self.infoFile = "val" + str(self.ID) + ".txt" 
        
        self._writeInfo()
        

    def _writeInfo(self):
              
        self.info = "data type: " + str(self.name) + "\n \n"      
        if self.name in ["VigraArray", "NumpyArray", "VigraNumpyArray", "Array", "ndarray"]:
            self.info += "Shape: " + str(self.ob.shape) + "\n"
        elif self.name in ["list", "str"]:
            self.info += "Laenge: " + str(len(self.ob)) + "\n"
            self.info += "\n" + str(self.ob)   
            if self.ob == "Not Connected":
                self.info = "Slot not connected!!!"
        else:
            self.info += "Value: " + str(self.ob)
       

class OpNode(Node):
    
    def __init__(self,tree, ob):
        
        Node.__init__(self,tree,ob)
        
        self.name = ob.__class__.__name__
       
        self.infoFile = "op" + str(self.ID) + ".txt" 
        
        self.parentID = None
        self.isParent = False
        
        self.IOChilds = []
        self.opChilds = []
        
        if isinstance(self.ob._parent, (Operator, OperatorWrapper)):
            self.parentID = id(ob._parent)
                
        if isinstance(self.ob, OperatorWrapper):
            self.obtype = "OperatorWrapper"
        elif isinstance(self.ob, Operator):
            self.obtype = "Operator"
            
        self._writeInfo()
                    
    def _writeInfo(self):
        self.info = "Class Name: " + str(self.name) + "\n"
        self.info += "ID: " + str(self.ID) + "\n"
        self.info += "Object: " + str(self.ob) + "\n"
        self.info+= "=============================== \n \n"  
    
    def _construct(self):
               
        for inputs in self.ob.inputs.itervalues():
            if self.tree.created(id(inputs)):
                nNode = self.tree.getNode(id(inputs))
            else:
                nNode = IONode(self.tree,inputs)
                self.tree.addNode(nNode)
            nNode.operator = self
            self.IOChilds.append(nNode)                        
            self.addNext(nNode)
        for outputs in self.ob.outputs.itervalues():
            if self.tree.created(id(outputs)):
                nNode = self.tree.getNode(id(outputs))
            else:
                nNode = IONode(self.tree,outputs) 
                self.tree.addNode(nNode)
            nNode.operator = self                           
            self.IOChilds.append(nNode)                        
            self.addNext(nNode)

        if self.gettype() == "OperatorWrapper":

            for innerOp in self.ob.innerOperators: 
                if self.tree.created(id(innerOp)):
                    nNode = self.tree.getNode(id(innerOp))
                else:
                    nNode = OpNode(self.tree,innerOp)
                    self.tree.addNode(nNode)
                self.addNext(nNode)
        
        self._after_construct()

    def _after_construct(self):
        for node in self.nextNodes:
            node.visit()
        
        
            
    def getIONodes(self):
        return self.IOChilds
    
    def getOpChildNodes(self):
        return self.opChilds
            
           
class IONode(Node):
    
    def __init__(self,tree,ob):
        
        Node.__init__(self,tree,ob)
         
        
        self.name = ob.name

        self.infoFile = "io" + str(self.ID) + ".txt"     
        
        self.isParent = False
        
        self.subSlots = []        
        self.isSubSlot = False        
        
        self.isOperator = False
        self.isClone = False        
        
        self.operator = None
        self.clones = []
        
        self.partners = []
        
        self.childs = []
        self.isChild = False
        
        self.valNode = None
        
        if isinstance(self.ob, InputSlot):
            self.obtype = "InputSlot"
        elif isinstance(self.ob, MultiInputSlot):
            self.obtype = "MultiInputSlot"
        elif isinstance(self.ob, OutputSlot):
            self.obtype = "OutputSlot"
        elif isinstance(self.ob, MultiOutputSlot):
            self.obtype = "MultiOutputSlot"  
                        
        self._writeInfo()    
        
            
    def _writeInfo(self):
        self.info = "Class Name: " + str(self.ob.__class__.__name__) + "\n"
        self.info += "Name: " + str(self.name) + "\n"
        self.info += "ID: " + str(self.ID) + "\n"
        self.info += "Object: " + str(self.ob) + "\n"
        self.info+= "=============================== \n \n"        
      
    def _construct(self):
               
        if self.gettype() in ["MultiOutputSlot", "MultiInputSlot"]:
            for subSlot in self.ob._subSlots:
                if self.tree.created(id(subSlot)):
                    nNode = self.tree.getNode(id(subSlot))
                    nNode.isSubSlot = True
                else:
                    nNode = IONode(self.tree,subSlot)
                    nNode.isSubSlot = True
                    self.tree.addNode(nNode)
                self.subSlots.append(nNode)
                self.addNext(nNode)                

        if self.gettype() in ["OutputSlot", "MultiOutputSlot"]:
            
            for partner in self.ob.partners:
                if self.tree.created(id(partner)):
                    nNode = self.tree.getNode(id(partner))
                    self.partners.append(nNode)
                    self.addNext(nNode)
                else:
                    if isinstance(partner, (InputSlot, MultiInputSlot, OutputSlot, MultiOutputSlot)):
                        nNode = IONode(self.tree,partner)
                        self.tree.addNode(nNode)
                        self.partners.append(nNode)
                        self.addNext(nNode)
                    else:
                        if self.ob.connected():
                            nNode = ValNode(self.tree,self.ob.value, self.tree.countNodes())
                        else: 
                            nNode = ValNode(self.tree,"Not Connected", self.tree.countNodes())
                        self.tree.addNode(nNode)
                        self.valNode = nNode
                        
        elif self.gettype() in ["InputSlot", "MultiInputSlot"]:

            if self.tree.created(id(self.ob.partner)):
                nNode = self.tree.getNode(id(self.ob.partner))
                self.partners.append(nNode)
                self.addNext(nNode)
            else:
                if isinstance(self.ob.partner, (InputSlot, MultiInputSlot, OutputSlot, MultiOutputSlot)):
                    nNode = IONode(self.tree,self.ob.partner)
                    self.tree.addNode(nNode)
                    self.partners.append(nNode)
                    self.addNext(nNode)
                else:
                    if self.ob.connected():
                        nNode = ValNode(self.tree,self.ob.value, self.tree.countNodes())
                    else: 
                        nNode = ValNode(self.tree,"Not Connected", self.tree.countNodes())
                    self.tree.addNode(nNode)
                    self.valNode = nNode            

        for clone in self.ob._clones:
            if self.tree.created(id(clone)):
                nNode = self.tree.getNode(id(clone))
                nNode.isClone = True
            else:
                nNode = IONode(self.tree,clone)
                nNode.isClone = True
                self.tree.addNode(nNode)
            self.clones.append(nNode)
            self.addNext(nNode)        

            
        if isinstance(self.ob.operator, (Operator, OperatorWrapper)):
            if self.tree.created(id(self.ob.operator)):
                nNode = self.tree.getNode(id(self.ob.operator))
            else:
                nNode = OpNode(self.tree,self.ob.operator)
                self.tree.addNode(nNode)
        else:
            if self.tree.created(id(self.ob.operator)):
                nNode = self.tree.getNode(id(self.ob.operator))
            else:
                nNode = IONode(self.tree,self.ob.operator)
                self.tree.addNode(nNode)
            self.isChild= True
            nNode.isOperator = True
            nNode.childs.append(self)
        
        self.operator = nNode   
        self.addNext(nNode)
        
        self._after_construct()

    def _after_construct(self):
        for node in self.nextNodes:
            node.visit()      
      
    def getChildNodes(self):
        return self.childs
    
    def getPartnerNodes(self):
        return self.partners
        
    def getValNode(self):
        return self.valNode
    


class Tree(object):
    
    def __init__(self, root, moreInfo = False):
        
        self.moreInfo = moreInfo
        self.visitedIDs = []
        self.nodes = {}
        self.opNodes = []
        
        self.rootNode = OpNode(self, root)
        self.addNode(self.rootNode)
        self.rootNode.visit()
        
        self._collectOpNodes()

        self._setParentsProp()
        if self.moreInfo:
            self._getMoreInfo()        

    
    def visited(self, ID):
        if ID in self.visitedIDs:
            return True
        else:
            self.visitedIDs.append(ID)
            return False
            
    def created(self, ID):
        if ID in self.nodes:
            return True
        else:
            return False
    
    def addNode(self, node):
        if node.ID not in self.nodes:
            self.nodes[node.ID] = node
    
    def getNode(self, ID):
        return self.nodes[ID]
        
    def countNodes(self):
        return len(self.nodes)

    def _collectOpNodes(self):
        for node in self.nodes.itervalues():
            if node.gettype() in ["Operator","OperatorWrapper"]:
                self.opNodes.append(node)

      
    def _setParentsProp(self):
        for opNode in self.opNodes:
            if not opNode.parentID==None:
                self.nodes[opNode.parentID].isParent = True
                self.nodes[opNode.parentID].opChilds.append(opNode)
                
    
    def getVisited(self):
        return self.visitedIDs 
    
    def getAllNodes(self):
        return self.nodes
    
    def getRootNode(self):        
        return self.rootNode                    
        
    def getAllOpNodes(self):
        return self.opNodes

                      
    
    def _getMoreInfo(self):
        for node in self.nodes.itervalues():
            
            if node.gettype() in ["Operator","OperatorWrapper"]:
                if node.parentID != None:
                    node.addInfo("Parent of this Operator: \n")
                    node.addInfo("=============================== \n")
                    node.addInfo("  Name: " + str(self.nodes[node.parentID].name) + " // ")                    
                    node.addInfo("ID: " + str(node.parentID) + " // ")
                    node.addInfo("Object: " + str(self.nodes[node.parentID].ob) + " // \n \n")
                node.addInfo("Slots: \n")
                node.addInfo("=============================== \n")
                for s in node.getIONodes():
                    node.addInfo("  Name: " + str(s.name) + " // ")
                    node.addInfo("ID: " + str(s.ID) + " // ")
                    node.addInfo("Object: " + str(s.ob) + " // \n")
                node.addInfo("\n ChildOperators: \n")
                node.addInfo("=============================== \n")
                if node.isParent:
                    for c in node.getOpChildNodes():
                        node.addInfo("  Name: " + str(c.name) + " // ")
                        node.addInfo("ID: " + str(c.ID) + " // ")
                        node.addInfo("Object: " + str(c.ob) + " // \n")
                else: 
                    node.addInfo("no child Operators \n \n ")
                    
            if node.gettype() in ["OutputSlot", "MultiOutputSlot", "InputSlot", "MultiInputSlot"]:
                node.addInfo("Operator of this Slot: \n")
                node.addInfo("=============================== \n")                 
                node.addInfo("  Name: " + str(node.operator.name) + " // ")                    
                node.addInfo("ID: " + str(node.operator.ID) + " // ")
                node.addInfo("Object: " + str(node.operator.ob) + " // \n")
                
                node.addInfo("\n SubSlots: \n")
                node.addInfo("=============================== \n")                
                if node.subSlots != []:
                    for s in node.subSlots:
                        node.addInfo("  Name: " + str(s.name) + " // ")
                        node.addInfo("ID: " + str(s.ID) + " // ")
                        node.addInfo("Object: " + str(s.ob) + " // \n ")
                        node.addInfo("      Operator of this Slot: \n")
                        node.addInfo("        Name: " + str(s.operator.name) + " // ")                    
                        node.addInfo("ID: " + str(s.operator.ID) + " // ")
                        node.addInfo("Object: " + str(s.operator.ob) + " // \n")
                        node.addInfo("      Partners: \n")
                        if s.getPartnerNodes() != []:
                            for p in s.getPartnerNodes():
                                node.addInfo("        Name: " + str(p.name) + " // ")
                                node.addInfo("ID: " + str(p.ID) + " // ")
                                node.addInfo("Object: " + str(p.ob) + " // \n") 
                        else: 
                            node.addInfo("        No Partners! \n")  
                        node.addInfo("      ------------------------------- \n")
                else:
                    node.addInfo("  No SubSlots! \n")
                    
                node.addInfo("\n IOChilds: \n")
                node.addInfo("=============================== \n")
                if node.getChildNodes != []:
                    for c in node.getChildNodes():
                        node.addInfo("  Name: " + str(c.name) + " // ")
                        node.addInfo("ID: " + str(c.ID) + " // ")
                        node.addInfo("Object: " + str(c.ob) + " // \n")
                        node.addInfo("      Operator of this Slot: \n")
                        node.addInfo("        Name: " + str(c.operator.name) + " // ")                    
                        node.addInfo("ID: " + str(c.operator.ID) + " // ")
                        node.addInfo("Object: " + str(c.operator.ob) + " // \n")
                        node.addInfo("      Partners: \n")
                        if c.getPartnerNodes() != []:
                            for p in c.getPartnerNodes():
                                node.addInfo("        Name: " + str(p.name) + " // ")
                                node.addInfo("ID: " + str(p.ID) + " // ")
                                node.addInfo("Object: " + str(p.ob) + " // \n") 
                        else: 
                            node.addInfo("        No Partners! \n")
                        node.addInfo("      ------------------------------- \n")
                else: 
                    node.addInfo("  No IOChilds! \n")
                    
                node.addInfo("\n (IOChilds[] == SubSlots[])")
                if (node.getChildNodes() == node.subSlots):
                    node.addInfo(" = True \n")
                else:
                    node.addInfo(" = False \n")
                    
                node.addInfo("\n Partners: \n")
                node.addInfo("=============================== \n")
                if node.getPartnerNodes() != []:
                    for p in node.getPartnerNodes():
                        node.addInfo("  Name: " + str(p.name) + " // ")
                        node.addInfo("ID: " + str(p.ID) + " // ")
                        node.addInfo("Object: " + str(p.ob) + " // \n")  
                        node.addInfo("      Operator of this Slot: \n")
                        node.addInfo("        Name: " + str(p.operator.name) + " // ")                    
                        node.addInfo("ID: " + str(p.operator.ID) + " // ")
                        node.addInfo("Object: " + str(p.operator.ob) + " // \n")
                else: 
                    node.addInfo("  No Partners! \n \n")
                node.addInfo("\n Connected Values: \n")
                node.addInfo("=============================== \n")
                if node.getValNode() != None:                
                    node.addInfo(str(node.getValNode().info))
                else:
                    node.addInfo("No Connected Value \n")
                                   

class GraphStructutre(object):
    
    def __init__(self, op):

        self.op = op
        self.trees = []

    def getStructure(self, moreInfo = False):
        
        self.trees.append(Tree(self.op, moreInfo))
        
    def write(self, onlyBasics = True):
        self.clusternum = 0
        if onlyBasics:            
            f = open("gB.dot", 'w')
        else:
            f = open("gC.dot", 'w')
        f.write("digraph G {\n")
        f.write("compound = true;\n")
        
        if onlyBasics:
            self._writeLegendBasics(f)
            self.URL = "file://"+ os.getcwd() + "/Debug_B/"
            self.debugFilesPath = "Debug_B/"
        else:
            self._writeLegendComplex(f)
            self.URL = "file://"+ os.getcwd() + "/Debug_C/"
            self.debugFilesPath = "Debug_C/"
        

        f.write("subgraph clusterN {\n")
                
        for tree in self.trees:
            self._writeDebugFiles(tree)
            self._write(f, tree, onlyBasics)
            
        f.write("} \n") 
           
        f.write("} \n")
        f.close()
        
        print "Writing g.svg file...."
        print "Working Directory: ", os.getcwd()
        if onlyBasics:
            print subprocess.call(["dot",  "-Tsvg", "gB.dot", "-o", "gB.svg"])
        else:
            print subprocess.call(["dot",  "-Tsvg", "gC.dot", "-o", "gC.svg"])
        print "Writing finished..."        
       
                
    def _writeInputSlot_C(self,f,node, ios, onlyBasics):
        if onlyBasics or not (ios.isSubSlot or ios.isChild):
            f.write('node_%d [color = green, style = filled, fillcolor = palegreen, shape=diamond,URL = "%s",comment = "%s", label=%s];\n' % (ios.ID,self.URL+ios.infoFile,ios.ID,ios.name)) 
            f.write("node_%d -> node_%d [lhead=cluster%d, color = green, style = bold, arrowhead = crow]\n" % (ios.ID,node.ID,node.ID))                                    
            if ios.getValNode() != None:
                self._writeValue(f, ios, ios.getValNode())

    def _writeInputSlot_N(self, f, node, ios, onlyBasics):
        if onlyBasics or not (ios.isSubSlot or ios.isChild):
            f.write('node_%d [color = green, style = filled, fillcolor = palegreen,shape=diamond, URL = "%s",comment = "%s", label=%s];\n' % (ios.ID,self.URL+ios.infoFile,ios.ID,ios.name)) 
            f.write("node_%d -> node_%d [style = bold,color = green, arrowhead = crow]\n" % (ios.ID,node.ID))                                    
            if ios.getValNode() != None:
                self._writeValue(f, ios, ios.getValNode())
            
    def _writeOutputSlot_C(self, f, node, ios, onlyBasics):
        if onlyBasics or not (ios.isSubSlot or ios.isChild):
            f.write('node_%d [color = red, style = filled, fillcolor = tomato,shape=octagon,URL = "%s",comment = "%s", label=%s];\n' % (ios.ID,self.URL+ios.infoFile,ios.ID,ios.name)) 
            f.write("node_%d -> node_%d [ltail=cluster%d,color = red, style = bold, arrowhead = crow]\n" % (node.ID, ios.ID,node.ID))                            
            if ios.getValNode() != None:
                self._writeValue(f, ios, ios.getValNode())
    
    def _writeOutputSlot_N(self, f, node, ios, onlyBasics):
        if onlyBasics or not (ios.isSubSlot or ios.isChild):
            f.write('node_%d [color = red, style = filled, fillcolor = tomato,shape=octagon,  URL = "%s",comment = "%s",label=%s];\n' % (ios.ID,self.URL+ios.infoFile,ios.ID, ios.name)) 
            f.write('node_%d -> node_%d [style = bold, color = red, arrowhead = crow]\n' % (node.ID, ios.ID)) 
            if ios.getValNode() != None:
                self._writeValue(f, ios, ios.getValNode())

    def _writeMultiInputSlot_C(self, f, node, ios, onlyBasics = True):
        if onlyBasics:        
            f.write('node_%d [color = green, style = filled, fillcolor = palegreen,shape=diamond, peripheries = 3,URL = "%s", comment = "%s", label=%s];\n' % (ios.ID,self.URL+ios.infoFile,ios.ID,ios.name)) 
            f.write("node_%d -> node_%d [lhead=cluster%d, color = green, style = bold, arrowhead = crow]\n" % (ios.ID, node.ID,node.ID))         
            if ios.getValNode() != None:
                self._writeValue(f, ios, ios.getValNode())               
        else:                        
            f.write("subgraph cluster%d { \n" %(ios.ID)) 
            f.write('URL = "%s";\n' % (self.URL + ios.infoFile))
            f.write('comment = "%s";\n' % (str(ios.ID)))  
            f.write('style = "bold,filled";\n')
            f.write("color = green;\n")
            f.write("label = %s;\n" %ios.name)
            f.write("fillcolor = palegreen;\n") 
            f.write("cluster%d [style = invis];\n" % ios.ID)
            for sSlot in ios.subSlots:
                if sSlot.gettype() == "MultiInputSlot":
                    self._writeMultiInputSlot_c(f,node,ios,onlyBasics)
                else: 
                    f.write('node_%d [color = green, style = filled, fillcolor = palegreen,shape=diamond,  URL = "%s",comment = "%s",label=%s];\n' % (sSlot.ID,self.URL+sSlot.infoFile,sSlot.ID, sSlot.name)) 
                    if sSlot.getValNode() != None:
                        self._writeValue(f, sSlot, sSlot.getValNode())
            f.write("} \n")
            if not ios.isSubSlot:
                f.write("cluster%d -> node_%d [ltail = cluster%d, lhead=cluster%d, color = green, style = bold, arrowhead = crow]\n" % (ios.ID, node.ID,ios.ID,node.ID))                 
                    
    def _writeMultiInputSlot_N(self, f, node, ios, onlyBasics = True):
        if onlyBasics:
            f.write('node_%d [color = green, style = filled, fillcolor = palegreen,shape=diamond, peripheries = 3, URL = "%s", comment = "%s", label=%s];\n' % (ios.ID,self.URL+ios.infoFile,ios.ID,ios.name)) 
            f.write("node_%d -> node_%d [style = bold, color = green,arrowhead = crow]\n" % (ios.ID, node.ID))     
            if ios.getValNode() != None:
                self._writeValue(f, ios, ios.getValNode())
        else:                        
            f.write("subgraph cluster%d { \n" %(ios.ID)) 
            f.write('URL = "%s";\n' % (self.URL + ios.infoFile))
            f.write('comment = "%s";\n' % (str(ios.ID)))  
            f.write('style = "bold,filled";\n')
            f.write("color = green;\n")
            f.write("label = %s;\n" %ios.name)
            f.write("fillcolor = palegreen;\n") 
            f.write("cluster%d [style = invis];\n" % ios.ID)                
            for sSlot in ios.subSlots:
                if sSlot.gettype() == "MultiInputSlot":
                    self._writeMultiInputSlot_N(f,node,ios,onlyBasics)
                else: 
                    f.write('node_%d [color = green, style = filled, fillcolor = palegreen,shape=diamond,  URL = "%s",comment = "%s",label=%s];\n' % (sSlot.ID,self.URL+sSlot.infoFile,sSlot.ID, sSlot.name)) 
                    if sSlot.getValNode() != None:
                        self._writeValue(f, sSlot, sSlot.getValNode())
            f.write("} \n")
            if not ios.isSubSlot:
                f.write("cluster%d -> node_%d [ltail = cluster%d, style = bold,color = green, arrowhead = crow]\n" % (ios.ID,node.ID, ios.ID))             
            
    def _writeMultiOutputSlot_C(self, f, node, ios, onlyBasics = True):
        if onlyBasics:
            f.write('node_%d [color = red, style = filled, fillcolor = tomato,shape=tripleoctagon, URL = "%s",comment = "%s",label=%s];\n' % (ios.ID,self.URL+ios.infoFile,ios.ID,ios.name))  
            f.write("node_%d -> node_%d [ltail=cluster%d,color = red, style = bold, arrowhead = crow]\n" % (node.ID, ios.ID, node.ID))                            
            if ios.getValNode() != None:
                self._writeValue(f, ios, ios.getValNode())
        else:                        
            f.write("subgraph cluster%d { \n" %(ios.ID)) 
            f.write('URL = "%s";\n' % (self.URL + ios.infoFile))
            f.write('comment = "%s";\n' % (str(ios.ID)))  
            f.write('style = "bold,filled";\n')
            f.write("color = red;\n")
            f.write("label = %s;\n" %ios.name)
            f.write("fillcolor = tomato;\n") 
            f.write("cluster%d [style = invis];\n" % ios.ID)
            for sSlot in ios.subSlots:
                if sSlot.gettype() == "MultiOutputSlot":
                    self._writeMultiOutputSlot_C(f,node,ios,onlyBasics)
                else: 
                    f.write('node_%d [color = red, style = filled, fillcolor = tomato,shape=octagon,  URL = "%s",comment = "%s",label=%s];\n' % (sSlot.ID,self.URL+sSlot.infoFile,sSlot.ID, sSlot.name)) 
                    if sSlot.getValNode() != None:
                        self._writeValue(f, sSlot, sSlot.getValNode())
            f.write("} \n")   
            if not ios.isSubSlot:
                f.write("node_%d -> cluster%d [lhead =cluster%d, ltail=cluster%d, color = red, style = bold, arrowhead = crow]\n" % (node.ID, ios.ID, ios.ID,node.ID))                 
        
            
    def _writeMultiOutputSlot_N(self, f, node, ios, onlyBasics = True):
        if onlyBasics:        
            f.write('node_%d [color = red, style = filled, fillcolor = tomato,shape=tripleoctagon, URL = "%s",comment = "%s",label=%s];\n' % (ios.ID,self.URL+ios.infoFile,ios.ID, ios.name))   
            f.write("node_%d -> node_%d [style = bold,color = red,  arrowhead = crow]\n" % (node.ID, ios.ID))                            
            if ios.getValNode() != None:
                self._writeValue(f, ios, ios.getValNode())
        else:                        
            f.write("subgraph cluster%d { \n" %(ios.ID)) 
            f.write('URL = "%s";\n' % (self.URL + ios.infoFile))
            f.write('comment = "%s";\n' % (str(ios.ID)))  
            f.write('style = "bold,filled";\n')
            f.write("color = red;\n")
            f.write("label = %s;\n" %ios.name)
            f.write("fillcolor = tomato;\n") 
            f.write("cluster%d [style = invis];\n" % ios.ID)
            for sSlot in ios.subSlots:
                if sSlot.gettype() == "MultiOutputSlot":
                    self._writeMultiOutputSlot_N(f,node,ios,onlyBasics)
                else: 
                    f.write('node_%d [color = red, style = filled, fillcolor = tomato,shape=octagon,  URL = "%s",comment = "%s",label=%s];\n' % (sSlot.ID,self.URL+sSlot.infoFile,sSlot.ID, sSlot.name)) 
                    if sSlot.getValNode() != None:
                        self._writeValue(f, sSlot, sSlot.getValNode())
            f.write("} \n") 
            if not ios.isSubSlot:
                f.write("node_%d -> cluster%d [lhead = cluster%d,color = red, style = bold, arrowhead = crow]\n" % (node.ID, ios.ID, ios.ID))                 
            
    def _writeValue(self, f,ios, vNode):
        f.write('node_%d [color = yellow, style = filled, fillcolor = khaki,shape=circle, URL = "%s",comment = "%s", label=%s];\n' % (vNode.ID,self.URL+vNode.infoFile,vNode.ID, vNode.name))
        f.write("node_%d -> node_%d [style = bold,color = yellow, arrowhead = crow, weight = 100]\n" % (vNode.ID,ios.ID  ))              
       
    
    def _writeSlotsOfP(self, f, node, onlyBasics = True):
        for ios in node.getIONodes():                 
            if ios.gettype() == "MultiInputSlot":
                self._writeMultiInputSlot_C(f,node,ios, onlyBasics)
            elif ios.gettype() == "MultiOutputSlot":
                self._writeMultiOutputSlot_C(f,node,ios, onlyBasics)
            elif ios.gettype() == "InputSlot":
                self._writeInputSlot_C(f, node, ios,onlyBasics)
            elif ios.gettype() == "OutputSlot":                            
                self._writeOutputSlot_C(f, node, ios,onlyBasics)                    

    def _writeSlots(self, f, node, onlyBasics = True):
        for ios in node.getIONodes():
            if ios.gettype() == "MultiInputSlot":
                self._writeMultiInputSlot_N(f,node,ios, onlyBasics)
            elif ios.gettype() == "MultiOutputSlot":
                self._writeMultiOutputSlot_N(f,node,ios, onlyBasics)
            elif ios.gettype() == "InputSlot":
                self._writeInputSlot_N(f,node,ios,onlyBasics)
            elif ios.gettype() == "OutputSlot":                            
                self._writeOutputSlot_N(f,node,ios,onlyBasics)  
                
    def _writeSimpleOperator(self, f, node,onlyBasics = True, param = False):
        self.clusternum += 1
        f.write("subgraph cluster%d { \n" %(self.clusternum-1)) 
        f.write('URL = "%s";\n' % (self.URL + node.infoFile))
        f.write('comment = "%s";\n' % (str(node.ID)))  
        f.write("style = filled;\n")
        f.write("color = blue;\n")
        f.write("label = %s;\n" %node.name)
        if param:
            f.write("fillcolor = deepskyblue;\n")
            f.write('node_%d [shape=box, URL = "%s", comment = "%s",label=%s, style = filled,bold, \
                    fillcolor = lightblue, color = red];\n' % (node.ID, self.URL + node.infoFile, node.ID, node.name))                        
        else:
            f.write("fillcolor = lightblue;\n")
            f.write('node_%d [shape=box,URL = "%s", comment = "%s", label=%s, style = filled,bold, \
                fillcolor = deepskyblue, color = red];\n' % (node.ID, self.URL + node.infoFile,node.ID, node.name))
                    
        self._writeSlots(f, node, onlyBasics)
        f.write("} \n")
        
    def _writeComplexOperator(self, f, node, onlyBasics = True, param = False):
        self.clusternum += 1
        f.write("subgraph cluster%d { \n" %(self.clusternum-1))
        f.write('URL = "%s";\n' % (self.URL + node.infoFile))
        f.write('comment = "%s";\n' % (str(node.ID)))                  
        f.write("style = filled;\n")
        f.write("color = blue;\n")
        f.write("fillcolor = lightblue;\n")
        f.write("label = %s;\n" %node.name)
        self._writeSlotsOfP(f, node, onlyBasics)
        self.clusternum += 1
        f.write("subgraph cluster%d { \n" %(node.ID))
        f.write('URL = "%s";\n' % (self.URL + node.infoFile))
        f.write('comment = "%s";\n' % (str(node.ID)))   
        f.write('style = "filled,bold";\n')
        if param:
            f.write("color = red;\n")
            f.write("fillcolor = deepskyblue;\n")
        else:
            f.write("color = red;\n")
            f.write("fillcolor = lightblue;\n")                 
        f.write("label = %s;\n" %node.name)
        f.write("node_%d [style = invis ];\n" %(node.ID))                    
        
        self._writeChilds(f, node, onlyBasics, not param)
        f.write("} \n")
        f.write("} \n")  
             
    def _writeChilds(self, f, parentNode, onlyBasics = True, param = False):    
        for node in parentNode.getOpChildNodes():
            if node.isParent: 
                self._writeComplexOperator(f,node,onlyBasics, param)
            else:
                self._writeSimpleOperator(f,node,onlyBasics, param)


    def _write(self, f, tree, onlyBasics = True):
        for node in tree.getAllOpNodes(): 
            if node.isParent and node.parentID == None:
                self._writeComplexOperator(f,node, onlyBasics, param = True)
            elif node.isParent==False and node.parentID == None:               
                self._writeSimpleOperator(f, node, onlyBasics)
        if onlyBasics:                
            self._writeIOConnections_B(f,tree)  
        else:
            self._writeIOConnections_C(f,tree)   
    
    
    def _writeIOConnections_C(self, f,tree):
        for opNode in tree.getAllOpNodes(): 
            for ios in opNode.getIONodes():
                self._writeSingleIOConnections_C(f,opNode, ios)

    def _writeSingleIOConnections_C(self,f,opNode,ios):
      
        if ios.gettype() == "OutputSlot":  
            for partner in ios.getPartnerNodes():                  
                if partner.gettype() =="InputSlot":
                    f.write("node_%d -> node_%d [style = bold]\n" % (ios.ID, partner.ID))
                if partner.gettype() == "OutputSlot":
                    if (partner.operator.ID == opNode.parentID):
                        f.write("node_%d -> node_%d [ltail = cluster%d, style = bold, weight = 200]\n" % (partner.ID, ios.ID, partner.operator.ID))     
                    elif (partner.operator.parentID == opNode.ID):
                        f.write("node_%d -> node_%d [ltail = cluster%d, style = bold, weight = 200]\n" % (ios.ID, partner.ID, partner.operator.ID))                                                        
        elif ios.gettype() =="InputSlot":
            for partner in ios.getPartnerNodes():
                if partner.gettype() == "InputSlot":
                    if (partner.operator.ID == opNode.parentID):
                        f.write("node_%d -> node_%d [ltail = cluster%d, style = bold, weight = 200]\n" % (partner.ID, ios.ID, partner.operator.ID))     
                    elif (partner.operator.parentID == opNode.ID):
                        f.write("node_%d -> node_%d [ltail = cluster%d, style = bold, weight = 200]\n" % (ios.ID, partner.ID, partner.operator.ID)) 
        elif ios.gettype() in ["MultiOutputSlot", "MultiInputSlot"]:         
            for sSlot in ios.subSlots:
                self._writeSingleIOConnections_C(f,opNode, sSlot)
            
              
    def _writeIOConnections_B(self, f,tree):
        for opNode in tree.getAllOpNodes(): 
            for ios in opNode.getIONodes():
                for partner in ios.getPartnerNodes():
                    if partner.operator.gettype() in ["MultiInputSlot","InputSlot","MultiOutputSlot", "OutputSlot"]:                                                                 
                        self._writeIOChildStructure(f, partner.operator, ios) 
                    else:
                        if ios.gettype() in ["MultiOutputSlot", "OutputSlot"]:
                            if partner.gettype() in ["MultiInputSlot","InputSlot"]:
                                f.write("node_%d -> node_%d [style = bold]\n" % (ios.ID, partner.ID))
                            if partner.gettype() in ["MultiOutputSlot", "OutputSlot"]:
                                if (partner.operator.ID == opNode.parentID):
                                    f.write("node_%d -> node_%d [ltail = cluster%d, style = bold, weight = 200]\n" % (partner.ID, ios.ID, partner.operator.ID))     
                                elif (partner.operator.parentID == opNode.ID):
                                    f.write("node_%d -> node_%d [ltail = cluster%d, style = bold, weight = 200]\n" % (ios.ID, partner.ID, partner.operator.ID))                                                        
                        elif ios.gettype() in ["MultiInputSlot","InputSlot"]:
                            if partner.gettype() in ["MultiInputSlot","InputSlot"]:
                                if (partner.operator.ID == opNode.parentID):
                                    f.write("node_%d -> node_%d [ltail = cluster%d, style = bold, weight = 200]\n" % (partner.ID, ios.ID, partner.operator.ID))     
                                elif (partner.operator.parentID == opNode.ID):
                                    f.write("node_%d -> node_%d [ltail = cluster%d, style = bold, weight = 200]\n" % (ios.ID, partner.ID, partner.operator.ID))         


    def _writeIOChildStructure(self,f,partner,ios): 
        if partner.operator.gettype() in ["MultiInputSlot","InputSlot","MultiOutputSlot", "OutputSlot"]:
            self._writeIOChildStructure(f, partner.operator, ios)
        else:            
            if ios.gettype() in ["MultiInputSlot","InputSlot"]:
                f.write("node_%d -> node_%d [style = bold, color = orange];\n" % (ios.ID, partner.ID))
            else: 
                f.write("node_%d -> node_%d [style = bold, color = orange];\n" % (partner.ID, ios.ID))
                                                

    def _writeDebugFiles(self,tree):
        if not os.access(self.debugFilesPath, os.F_OK):
            os.mkdir(self.debugFilesPath)
        for nID, node in tree.getAllNodes().iteritems():
            f = open(self.debugFilesPath + node.infoFile, 'w')
            f.write(str(node.info))
            f.close()

    def _writeLegendBasics(self, f):
        f.write("subgraph clusterL {\n") 
        f.write("color = blue; \n")
        f.write("style = bold;\n")
        f.write("nodesep = equally;\n")
        f.write("a [style = invis]; b [style = invis];c [style = invis];d [style = invis];\n")
        f.write("e [style = invis];f [style = invis];g [style = invis];\n")
        f.write("a->b [style = invis]; b->c [style = invis]; c->d [style = invis];d->e [style = invis];\n")
        f.write("e->f [style = invis];f->g [style = invis]; \n")
        f.write("g->h [style = invis];h->i [style = invis]; i->j [style = invis];j->k [style = invis];k->l [style = invis]; \n")
        f.write('{rank = same; a ;%s [shape=box,style = filled, fillcolor = lightblue, color = blue];}\n' % ("Operator"))        
        f.write('{rank = same; b ;%s [shape=box,style = filled, fillcolor = deepskyblue, color = red];}\n' % ('"interior of Operator"'))         
        f.write('{rank = same; c ; %s [color = green, style = filled, fillcolor = palegreen,shape=diamond];}\n' % ("InputSlot")) 
        f.write('{rank = same; d ;%s [color = green, style = filled, fillcolor = palegreen,shape=diamond, peripheries = 3];}\n' % ("MultiInpuSlot")) 
        f.write('{rank = same; e ;%s [color = red, style = filled, fillcolor = tomato,shape=octagon];}\n' % ("OutputSlot")) 
        f.write('{rank = same; f ;%s [color = red, style = filled, fillcolor = tomato,shape=octagon, peripheries = 3];}\n' % ("MultiOutputSlot"))         
        f.write('{rank = same; g ;%s [color = yellow, style = filled, fillcolor = khaki,shape=circle];}\n' % ('"Input Values"')) 
        
        f.write('{rank = same; h[style = invis]; v1[style = invis]; v2 [shape = plaintext, label =%s] ;}\n' % ('"Value to InputSlot"'))
        f.write('{rank = same; i[style = invis]; i1[style = invis]; i2 [shape = plaintext, label =%s] ;}\n' % ('"InputSlot to Operator"'))
        f.write('{rank = same; j[style = invis]; o1[style = invis]; o2 [shape = plaintext, label =%s] ;}\n' % ('"Operator to OutputSlot"'))
        f.write('{rank = same; k[style = invis]; c1[style = invis]; c2 [shape = plaintext, label =%s] ;}\n' % ('"OutputSlot to InputSlot"'))
        f.write('{rank = same; l[style = invis]; s1[style = invis]; s2 [shape = plaintext, label =%s] ;}\n' % ('"OutputSlot to InputSlot with IOSlot operators between"'))
        
        f.write('v1 -> v2 [style = bold, color = yellow ,arrowhead = crow];\n')        
        f.write('i1 -> i2 [style = bold, color = green, arrowhead = crow];\n')        
        f.write('o1 -> o2 [style = bold, color = red, arrowhead = crow];\n')        
        f.write('c1 -> c2 [style = bold, color = black];\n')        
        f.write('s1 -> s2 [style = bold, color = orange];\n')        
        
        f.write("}\n")
        
    def _writeLegendComplex(self, f):
        f.write("subgraph clusterL {\n") 
        f.write("color = blue; \n")
        f.write("style = bold;\n")
        f.write("nodesep = equally;\n")
        f.write("a [style = invis]; b [style = invis];c [style = invis];d [style = invis];\n")
        f.write("e [style = invis];f [style = invis];g [style = invis];\n")
        f.write("a->b [style = invis]; b->c [style = invis]; c->d [style = invis];d->e [style = invis];\n")
        f.write("e->f [style = invis];f->g [style = invis]; \n")
        f.write("g->h [style = invis];h->i [style = invis]; i->j [style = invis];j->k [style = invis];\n")
        f.write('{rank = same; a ;%s [shape=box,style = filled, fillcolor = lightblue, color = blue];}\n' % ("Operator"))        
        f.write('{rank = same; b ;%s [shape=box,style = filled, fillcolor = deepskyblue, color = red];}\n' % ('"interior of Operator"'))         
        f.write('{rank = same; c ; %s [color = green, style = filled, fillcolor = palegreen,shape=diamond];}\n' % ("InputSlot")) 
        f.write('{rank = same; d ;%s [color = green, style = filled, fillcolor = palegreen,shape=box];}\n' % ("MultiInpuSlot")) 
        f.write('{rank = same; e ;%s [color = red, style = filled, fillcolor = tomato,shape=octagon];}\n' % ("OutputSlot"))  
        f.write('{rank = same; f ;%s [color = red, style = filled, fillcolor = tomato,shape=box];}\n' % ("MultiOutputSlot"))         
        f.write('{rank = same; g ;%s [color = yellow, style = filled, fillcolor = khaki,shape=circle];}\n' % ('"Input Values"'))  
        
        f.write('{rank = same; h[style = invis]; v1[style = invis]; v2 [shape = plaintext, label =%s] ;}\n' % ('"Value to InputSlot"'))
        f.write('{rank = same; i[style = invis]; i1[style = invis]; i2 [shape = plaintext, label =%s] ;}\n' % ('"InputSlot to Operator"'))
        f.write('{rank = same; j[style = invis]; o1[style = invis]; o2 [shape = plaintext, label =%s] ;}\n' % ('"Operator to OutputSlot"'))
        f.write('{rank = same; k[style = invis]; c1[style = invis]; c2 [shape = plaintext, label =%s] ;}\n' % ('"OutputSlot to InputSlot"'))
        
        f.write('v1 -> v2 [style = bold, color = yellow ,arrowhead = crow];\n')        
        f.write('i1 -> i2 [style = bold, color = green, arrowhead = crow];\n')        
        f.write('o1 -> o2 [style = bold, color = red, arrowhead = crow];\n')        
        f.write('c1 -> c2 [style = bold, color = black];\n')        
        
        f.write("}\n")




        
        
    
        
        

            
    
        
    
    
