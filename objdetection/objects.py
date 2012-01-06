import numpy
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot

class Object:
    def __repr__( self ):
        s = "Object:\n"
        for attr in dir(self):
            if not attr.startswith('__'):
                s += attr + ': '+str(getattr(self,attr)) + "\n"
        return s

def objects_from_connected_components( cc, background=None ):
    labels = numpy.unique(cc)
    labels = labels[labels != background] if background else labels
    
    ret = []
    for label in labels:
        obj = Object()
        obj.location = numpy.mean(numpy.vstack(numpy.where(cc == label)), axis=1)
        ret.append(obj)
    return ret    

class OpObjectExtractor( Operator ):
    name = "OpObjectExtractor"

    inputSlots = [InputSlot('Input')]
    outputSlots = [OutputSlot('Output', array_destination=False)]

    def notifyConnectAll(self):
        self.outputs["Output"]._shape = self.Input.shape

    def getOutSlot( self, slot, key, result ):
        cc = self.Input[key].allocate().wait()
        objs = objects_from_connected_components(cc, background = 0)
        print "extractor result type", type(result)
        result[0] = objs
        
if __name__ == '__main__':
    cc = numpy.load("cc.npy")    
    g = Graph()
    extractor = OpObjectExtractor( g )
    extractor.Input.setValue(cc)
    objs = extractor.Output[:].wait()
    print objs
