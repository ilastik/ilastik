import numpy
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow import stype, rtype 

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

    inputSlots = [InputSlot('Input', stype=stype.ArrayLike)]
    outputSlots = [OutputSlot('Output', stype=stype.Opaque, rtype=rtype.SubRegion)]

    def notifyConnectAll(self):
        self.outputs["Output"]._shape = self.Input.shape

    def execute( self, slot, roi, result ):
        cc = self.Input.get(roi).wait()
        objs = objects_from_connected_components(cc, background = 0)
        print "FIXME: correct for absolute coordinate shift"
        return objs
        
class OpObjectPiper( Operator ):
    name = "ObjectPiper"

    inputSlots = [InputSlot('Input', stype=stype.Opaque, rtype=None)]
    outputSlots = [OutputSlot('Output', stype=stype.Opaque, rtype=None)]

    def execute( self, slot, roi, result ):
        objects = self.Input().wait()
        result = filter(roi, objects)
        return result

if __name__ == '__main__':
    cc = numpy.load("cc.npy")    
    g = Graph()
    extractor = OpObjectExtractor( g )
    piper = OpObjectPiper( g )

    piper.Input.connect( extractor.Output )
    extractor.Input.setValue(cc)
    print extractor.Output.shape
    objs = extractor.Output(pslice=numpy.s_[:,100:101,:]).wait()

    #objs = piper.Output().wait()
    print objs
