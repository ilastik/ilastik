from lazyflow.graph import *
import context


class OpContextHistogram(Operator):
    name = "ContextHistogram"
    description = "Compute histograms in the neighborhoods of different sizes"
       
    inputSlots = [InputSlot("PMaps"),InputSlot("Radii"), InputSlot("BinsCount",stype='integer'), \
                  InputSlot("LabelsCount",stype='integer')]
    outputSlots = [OutputSlot("Output")]   

    def notifyConnectAll(self):

        nclasses=self.inputs["LabelsCount"].value
        radii=self.inputs["Radii"].value
        nbins = self.inputs["BinsCount"].value
        
        self.outputs["Output"]._dtype = self.inputs["PMaps"].dtype
        
        assert len(self.inputs["PMaps"].shape) == 3 , "not implemented for 3D"
        
        h,w,c=self.inputs["PMaps"].shape
        
        self.outputs["Output"]._axistags = copy.copy(self.inputs["PMaps"].axistags)
        self.outputs["Output"]._shape = (h, w, len(radii)*nbins*c)
        
    def getOutSlot(self, slot, key, result):
        #FIXME: we don't really need that
        pmaps = self.inputs["PMaps"][:].allocate().wait()
        
        radii=self.inputs["Radii"].value        
        radii=numpy.array(radii,dtype=numpy.uint32)
        
        nbins = self.inputs["BinsCount"].value
        print "We are in the business"
        print radii, radii.dtype
        print nbins
        
        context.contextHistogram2D(radii, nbins, pmaps, result)