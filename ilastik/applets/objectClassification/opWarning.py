from lazyflow.graph import Operator, InputSlot, OutputSlot, Graph
from lazyflow.stype import Opaque


class OpWarning(Operator):
    '''
    This operator provides an output slot for warning messages. The output is a dictionary 
    with keys 'title', 'description' and 'details', suitable for use in a GUI message box.
    
    Usage:
      * Let your class inherit from OpWarning
      * redirect setupOutputs() to super() (see example)
      * call self.setWarning()
      * let others query your messages through the Warnings slot
    '''
    name = "OpWarning"
    
    _warningDict = {'title': None, 'description': None, 'details': None}
    
    # the output slot 
    #TODO unclear if this is the right type
    Warnings = OutputSlot(stype=Opaque)
    
    def setupOutputs(self):
        self.Warnings.meta.shape = (1,)

    def propagateDirty(self, slot, subindex, roi):
        pass
    
    def setWarning(self, title=None, description=None, details=None):
        self._warningDict['title'] = title
        self._warningDict['description'] = description
        self._warningDict['details'] = details
        self.Warnings._value = self._warningDict
        self.Warnings.setDirty()
        
        



class OpTestImplementation(OpWarning):
    name = "OpTestImplementation"
    
    def setupOutputs(self):
        super(OpTestImplementation, self).setupOutputs()
    
    def execute(self, slot, subindex, roi, result):
        pass
        
    def propagateDirty(self, slot, subindex, roi):
        pass
    


if __name__ == "__main__":
    # test the warning operator class
    
    # our operator is a lone wolf, but needs some pseudo-graph as parent
    op = OpTestImplementation(graph=Graph())
    
    def handleDirty(*args, **kwargs):
        print("New messages arrived:")
        w = op.Warnings[:].wait()
        print(w)
        
    op.Warnings.notifyDirty(handleDirty) 
    
    # do stuff ...
    
    op.setWarning(title="Hello World!", description="Hello again!", details="Even more hellos!")
    
    # marvel at your printed warning 
    