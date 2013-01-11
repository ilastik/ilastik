import numpy
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice, block_view
import copy


class OpThreshold(Operator):
    #Threshold one channel agains the rest. To be used for threshoding probability maps
    #after classification
    name = "OpThreshold"
    description = "Threshold one channel against the rest"
    category = "Learning"
    
    inputSlots = [InputSlot("Input"),InputSlot("Channel",stype='integer'),InputSlot("Threshold")]
    outputSlots = [OutputSlot("Output")]
    
    def setupOutputs(self):
        inputSlot = self.inputs["Input"]
        
        self.outputs["Output"].meta.shape = inputSlot.meta.shape[:-1]+(1,)
        self.outputs["Output"].meta.dtype = numpy.uint8
        self.outputs["Output"].meta.axistags = inputSlot.meta.axistags
    
    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start,roi.stop)
        shape = self.inputs["Input"].meta.shape
        rstart, rstop = sliceToRoi(key, shape)  
        rstop[-1] = shape[-1]
        rkey = roiToSlice(rstart,rstop)
        pred = self.inputs["Input"][rkey].allocate().wait()
        
        ch = self.inputs["Channel"].value
        th = self.inputs["Threshold"].value
        result[...,0] = numpy.where(pred[...,ch]>th, 1, 0)
        
class OpConnectedComponents(Operator):
    #perform connected components. By default, cc is done with background label 0, i.e.
    #objects of label 0 are not counted.
    
    name = "OpConnectedComponents"
    description = "Connected components"
    category = "Learning"
    
    inputSlots = [InputSlot("Input"), InputSlot("Neighborhood"), InputSlot("Background")]
    outputSlots = [OutputSlot("Output")]
    
    def notifySubConnect(self, slots, indexes):
        #FIXME: trying to set a default value here. Is it the right way?
        print "in NotifySubConnect"
        if self.inputs["Input"].connected():
            inputSlot = self.inputs["Input"]
            self.outputs["Output"].meta.shape = inputSlot.meta.shape
            self.outputs["Output"].meta.dtype = numpy.uint32
            self.outputs["Output"].meta.axistags= inputSlot.meta.axistags
            if not self.inputs["Neighborhood"].connected():
                if inputSlot.meta.axistags.axisTypeCount(vigra.AxisType.NonChannel)==3:
                    self.inputs["Neighborhood"].setValue(26)
                elif inputSlot.meta.axistags.axisTypeCount(vigra.AxisType.NonChannel)==2:
                    self.inputs["Neighborhood"].setValue(8)
            if not self.inputs["Background"].connected():
                self.inputs["Background"].setValue(0)
    
    def setupOutputs(self):
        print "in notify connect all"
        inputSlot = self.inputs["Input"]
        if inputSlot.meta.axistags is None:
            print "no axistags"
        else:
            print inputSlot.meta.axistags
        self.outputs["Output"].meta.shape = inputSlot.meta.shape
        self.outputs["Output"].meta.dtype = numpy.uint32
        self.outputs["Output"].meta.axistags= inputSlot.meta.axistags
        
    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start,roi.stop)
        
        timeAxis = None
        channelAxis = None
        newkey = [slice(None, None, None) for x in key]
        tags = self.inputs["Input"].meta.axistags
        if tags.axisTypeCount(vigra.AxisType.Time)!=0:
            timeAxis = tags.index('t')
        if tags.axisTypeCount(vigra.AxisType.Channels)!=0:
            channelAxis = tags.index('c')
        newkey[timeAxis] = key[timeAxis]
        newkey[channelAxis] = key[channelAxis]
        
        #we have to allocate everything on the space axis, but only
        #the requested stuff on the channel and time axis
        image = self.inputs["Input"][newkey].allocate().wait()
        
        timekeys = []
        channelkeys = []
        writekeys = []
        
        if timeAxis is not None:
            #we have a time axis
            for i in range(image.shape[timeAxis]):
                newkey = copy.copy(key)
                newkey = list(newkey)
                newkey[timeAxis] = i
                timekeys.append(tuple(newkey))
        else:
            timekeys.append(key)
        
        if channelAxis is not None:
            #channelwise...
            for timekey in timekeys:
                for c in range(image.shape[channelAxis]):
                    newkey = copy.copy(timekey)
                    newkey = list(newkey)
                    newkey[channelAxis] = c
                    channelkeys.append(tuple(newkey))
                    writekey = [slice(None, None, None) for x in newkey]
                    if timeAxis is not None:
                        writekey[timeAxis] = newkey[timeAxis]
                    writekey[channelAxis] = newkey[channelAxis]
                    writekeys.append(writekey)
        else:
            channelkeys = timekeys
            writekeys = [[slice(None, None, None) for x in channelkeys[0]] for x in channelkeys]
            
        ndim = len(image[channelkeys[0]].shape)
        neighborhood = self.inputs["Neighborhood"].value
        bg = self.inputs["Background"].value
        if ndim==2:            
            for ik, readkey in enumerate(channelkeys):
                #compute everything here, then copy out the right part
                if bg!=-1:
                    temp = vigra.analysis.labelImageWithBackground(image[readkey], neighborhood, bg)
                else:
                    temp = vigra.analysis.labelImage(image[readkey], neighborhood)
                result[writekeys[ik]] = temp[:]
                    
        elif ndim==3:
            for ik, readkey in enumerate(channelkeys):
                if bg!=-1:
                    temp = vigra.analysis.labelVolumeWithBackground(image[readkey], neighborhood, bg)
                else:
                    temp = vigra.analysis.labelVolume(image[readkey], neighborhood)
                
                print "total number of components for this time and channel:", readkey, numpy.max(temp)
                result[writekeys[ik]] = temp[:]
        else:
            print "ERROR: unsupported number of dimensions", ndim
            return
            
        #nei = self.inputs["Neighborhood"].value
        #if len(image.shape)==2 and nei!=4 and nei!=8:
            #print "Neighborhood value of ", nei, "not possible in 2d"
            #self.inputs["Neighborhood"].setValue(4)
        #elif len(image.shape)==3 and nei!=6 and nei!=26:
            #print "Neighborhood value of ", nei, "not possible in 3d"
            #self.inputs["Neighborhood"].setValue(6)
        #elif len(image.shape)==4:
            ##we have a time dimension, we can't handle it yet
            #image = image[0,...]
        #image = numpy.asarray(image, dtype = numpy.uint8)
        #print image.shape, image.dtype
        #neighborhood = self.inputs["Neighborhood"].value
        #bg = self.inputs["Background"].value
        #temp = None
        ##if image.axistags.axisTypeCount(vigra.AxisType.NonChannel)==3:
        #if len(image.shape)>2:
            #if bg!=-1:            
                #temp = vigra.analysis.labelVolumeWithBackground(image, neighborhood, bg)
            #else:
                #temp = vigra.analysis.labelVolume(image, neighborhood)
        ##elif image.axistags.axisTypeCount(vigra.AxisType.NonChannel)==2:
        #else:
            #if bg!=-1:
                #temp = vigra.analysis.labelImageWithBackground(image, neighborhood, bg)
            #else:
                #temp = vigra.analysis.labelImage(image, neighborhood)
        
        #print key
        #print temp.shape
        #print result.shape
        #result[0, :, :, :, 0] = temp[key[1:-1]]
        
        
