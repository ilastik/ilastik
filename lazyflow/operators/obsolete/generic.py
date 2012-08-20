from lazyflow.graph import *
from lazyflow import roi

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)
from lazyflow.tracer import Tracer

def axisTagObjectFromFlag(flag):

    if flag in ['x','y','z']:
        type=vigra.AxisType.Space
    elif flag=='c':
        type=vigra.AxisType.Channel
    elif flag=='t':
        type=vigra.AxisType.Time
    else:
        print "Requested flag", str(flag)
        raise

    return vigra.AxisTags(vigra.AxisInfo(flag,type))


def axisType(flag):
    if flag in ['x','y','z']:
        return vigra.AxisType.Space
    elif flag=='c':
        return vigra.AxisType.Channels

    elif flag=='t':
        return vigra.AxisType.Time
    else:
        raise


def axisTagsToString(axistags):
    res=[]
    for axistag in axistags:
        res.append(axistag.key)
    return res




def getSubKeyWithFlags(key,axistags,axisflags):
    assert len(axistags)==len(key)
    assert len(axisflags)<=len(key)

    d=dict(zip(axisTagsToString(axistags),key))

    newKey=[]
    for flag in axisflags:
        slice=d[flag]
        newKey.append(slice)

    return tuple(newKey)


def popFlagsFromTheKey(key,axistags,flags):
    d=dict(zip(axisTagsToString(axistags),key))

    newKey=[]
    for flag in axisTagsToString(axistags):
        if flag not in flags:
            slice=d[flag]
            newKey.append(slice)

    return newKey





class OpMultiArraySlicer(Operator):
    """
    Produces a list of image slices along the given axis.
    Same as the slicer operator below, but reduces the dimensionality of the data.
    The sliced axis is discarded in the output image shape.
    """
    inputSlots = [InputSlot("Input"),InputSlot('AxisFlag')]
    outputSlots = [MultiOutputSlot("Slices",level=1)]

    name = "Multi Array Slicer"
    category = "Misc"

    def setupOutputs(self):

        dtype=self.inputs["Input"].dtype
        flag=self.inputs["AxisFlag"].value

        indexAxis=self.inputs["Input"].axistags.index(flag)
        outshape=list(self.inputs["Input"].shape)
        n=outshape.pop(indexAxis)
        outshape=tuple(outshape)

        outaxistags=copy.copy(self.inputs["Input"].axistags)

        del outaxistags[flag]

        self.outputs["Slices"].resize(n)

        for o in self.outputs["Slices"]:
            # Output metadata is a modified copy of the input's metadata
            o.meta.assignFrom( self.Input.meta )
            o.meta.axistags = outaxistags
            o.meta.shape = outshape

    def getSubOutSlot(self, slots, indexes, key, result):

        #print "SLICER: key", key, "indexes[0]", indexes[0], "result", result.shape

        start,stop=roi.sliceToRoi(key,self.outputs["Slices"][indexes[0]].shape)

        oldstart,oldstop=start,stop

        start=list(start)
        stop=list(stop)

        flag=self.inputs["AxisFlag"].value
        indexAxis=self.inputs["Input"].axistags.index(flag)

        start.insert(indexAxis,indexes[0])
        stop.insert(indexAxis,indexes[0])

        newKey=roi.roiToSlice(numpy.array(start),numpy.array(stop))

        ttt = self.inputs["Input"][newKey].allocate().wait()

        writeKey = [slice(None, None, None) for k in key]
        writeKey.insert(indexAxis, 0)
        writeKey = tuple(writeKey)

        result[:]=ttt[writeKey ]#+ (0,)]


class OpMultiArraySlicer2(Operator):
    """
    Produces a list of image slices along the given axis.
    Same as the slicer operator above, but does not reduce the dimensionality of the data.
    The output image shape will have a dimension of 1 for the axis that was sliced.
    """
    #FIXME: This operator return a sigleton in the sliced direction
    #Should be integrated with the above one to have a more consistent notation
    inputSlots = [InputSlot("Input"),InputSlot('AxisFlag')]
    outputSlots = [MultiOutputSlot("Slices",level=1)]

    name = "Multi Array Slicer"
    category = "Misc"

    def __init__(self, *args, **kwargs):
        super(OpMultiArraySlicer2, self).__init__(*args, **kwargs)
        self.inputShape = None

    def setupOutputs(self):
        dtype=self.inputs["Input"].meta.dtype
        flag=self.inputs["AxisFlag"].value

        indexAxis=self.inputs["Input"].meta.axistags.index(flag)
        outshape=list(self.inputs["Input"].meta.shape)
        n=outshape.pop(indexAxis)

        outshape.insert(indexAxis, 1)
        outshape=tuple(outshape)

        outaxistags=copy.copy(self.inputs["Input"].meta.axistags)

        #del outaxistags[flag]

        self.outputs["Slices"].resize(n)

        for i in range(n):
            o = self.outputs["Slices"][i]
            # Output metadata is a modified copy of the input's metadata
            o.meta.assignFrom( self.Input.meta )
            o.meta.axistags = outaxistags
            o.meta.shape = outshape

        inputShape = self.Input.meta.shape
        if self.inputShape != inputShape:
            self.inputShape = inputShape
            for i in range(n):
                self.Slices[i].setDirty(slice(None))

    def getSubOutSlot(self, slots, indexes, key, result):

        outshape = self.outputs["Slices"][indexes[0]].shape


        start,stop=roi.sliceToRoi(key,outshape)
        oldstart,oldstop=start,stop

        start=list(start)
        stop=list(stop)

        flag=self.inputs["AxisFlag"].value
        indexAxis=self.inputs["Input"].axistags.index(flag)

        start.pop(indexAxis)
        stop.pop(indexAxis)

        start.insert(indexAxis,indexes[0])
        stop.insert(indexAxis,indexes[0])


        newKey=roi.roiToSlice(numpy.array(start),numpy.array(stop))

        ttt = self.inputs["Input"][newKey].allocate().wait()
        result[:]=ttt[:]

    def propagateDirty(self, inputSlot, roi):
        if inputSlot == self.AxisFlag:
            # AxisFlag changed.  Everything is dirty
            for i, slot in self.Slices:
                slot.setDirty(slice(None))
        elif inputSlot == self.Input:
            # Mark each of the intersected slices as dirty
            channelAxis = self.Input.meta.axistags.index('c')
            channels = zip(roi.start, roi.stop)[channelAxis]
            for i in range(*channels):
                slot = self.Slices[i]
                sliceRoi = copy.copy(roi)
                sliceRoi.start[channelAxis] = 0
                sliceRoi.stop[channelAxis] = 1
                slot.setDirty(sliceRoi)

class OpMultiArrayStacker(Operator):
    inputSlots = [MultiInputSlot("Images"), InputSlot("AxisFlag"), InputSlot("AxisIndex")]
    outputSlots = [OutputSlot("Output")]

    name = "Multi Array Stacker"
    description = "Stack inputs on any axis, including the ones which are not there yet"
    category = "Misc"

    def setupOutputs(self):
        #This function is needed so that we don't depend on the order of connections.
        #If axis flag or axis index is connected after the input images, the shape is calculated
        #here
        self.setRightShape()

    def setRightShape(self):
        c = 0
        flag = self.inputs["AxisFlag"].value
        axistype = axisType(flag)
        axisindex = self.inputs["AxisIndex"].value

        for inSlot in self.inputs["Images"]:
            inTagKeys = [ax.key for ax in inSlot.axistags]
            if inSlot.partner is not None:
                self.outputs["Output"]._dtype = inSlot.dtype
                self.outputs["Output"]._axistags = copy.copy(inSlot.axistags)
                #indexAxis=inSlot.axistags.index(flag)

                outTagKeys = [ax.key for ax in self.outputs["Output"]._axistags]

                if not flag in outTagKeys:
                    self.outputs["Output"]._axistags.insert(axisindex, vigra.AxisInfo(flag, axisType(flag)))
                if flag in inTagKeys:
                    c += inSlot.shape[inSlot.axistags.index(flag)]
                else:
                    c += 1

        if len(self.inputs["Images"]) > 0:
            newshape = list(self.inputs["Images"][0].shape)
            if flag in inTagKeys:
                #here we assume that all axis are present
                newshape[axisindex]=c
            else:
                newshape.insert(axisindex, c)
            self.outputs["Output"]._shape=tuple(newshape)
        else:
            self.outputs["Output"]._shape = None



    def getOutSlot(self, slot, key, result):
        cnt = 0
        written = 0
        start, stop = roi.sliceToRoi(key, self.outputs["Output"].shape)
        assert (stop<=self.outputs["Output"].shape).all()
        axisindex = self.inputs["AxisIndex"].value
        flag = self.inputs["AxisFlag"].value
        #ugly-ugly-ugly
        oldkey = list(key)
        oldkey.pop(axisindex)
        #print "STACKER: ", flag, axisindex
        #print "requesting an outslot from stacker:", key, result.shape
        #print "input slots total: ", len(self.inputs['Images'])
        requests = []


        for i, inSlot in enumerate(self.inputs['Images']):
            if inSlot.connected():
                req = None
                inTagKeys = [ax.key for ax in inSlot.axistags]
                if flag in inTagKeys:
                    slices = inSlot.shape[axisindex]
                    if cnt + slices >= start[axisindex] and start[axisindex]-cnt<slices and start[axisindex]+written<stop[axisindex]:
                        begin = 0
                        if cnt < start[axisindex]:
                            begin = start[axisindex] - cnt
                        end = slices
                        if cnt + end > stop[axisindex]:
                            end -= cnt + end - stop[axisindex]
                        key_ = copy.copy(oldkey)
                        key_.insert(axisindex, slice(begin, end, None))
                        reskey = [slice(None, None, None) for x in range(len(result.shape))]
                        reskey[axisindex] = slice(written, written+end-begin, None)

                        req = inSlot[tuple(key_)].writeInto(result[tuple(reskey)])
                        written += end - begin
                    cnt += slices
                else:
                    if cnt>=start[axisindex] and start[axisindex] + written < stop[axisindex]:
                        #print "key: ", key, "reskey: ", reskey, "oldkey: ", oldkey
                        #print "result: ", result.shape, "inslot:", inSlot.shape
                        reskey = [slice(None, None, None) for s in oldkey]
                        reskey.insert(axisindex, written)
                        destArea = result[tuple(reskey)]
                        req = inSlot[tuple(oldkey)].writeInto(destArea)
                        written += 1
                    cnt += 1

                if req is not None:
                    requests.append(req)

        for r in requests:
            r.wait()

    def propagateDirty(self, inputSlot, roi):
        if inputSlot == self.AxisFlag or inputSlot == self.AxisIndex:
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown input slot."


class OpSingleChannelSelector(Operator):
    name = "SingleChannelSelector"
    description = "Select One channel from a Multichannel Image"

    inputSlots = [InputSlot("Input"),InputSlot("Index",stype='integer')]
    outputSlots = [OutputSlot("Output")]

    def setupOutputs(self):
        self.outputs["Output"]._dtype =self.inputs["Input"].dtype
        self.outputs["Output"]._shape = self.inputs["Input"].shape[:-1]+(1,)
        self.outputs["Output"]._axistags = self.inputs["Input"].axistags

    def getOutSlot(self, slot, key, result):

        index=self.inputs["Index"].value
        #FIXME: check the axistags for a multichannel image
        assert self.inputs["Input"].shape[-1] > index, ("Requested channel, %d, is out of Range" % index)

        # Only ask for the channel we need
        newKey = key[:-1] + (slice(index,index+1),)

        im=self.inputs["Input"][newKey].wait()
        result[...,0]=im[...,0] # Copy into the (only) channel of our result

    def notifyDirty(self, slot, key):
        if slot == self.Input:
            key = key[:-1] + (slice(0,1,None),)
            self.outputs["Output"].setDirty(key)
        else:
            self.Output.setDirty(slice(None))





class OpSubRegion(Operator):
    name = "OpSubRegion"
    description = "Select a region of interest from an numpy array"

    inputSlots = [InputSlot("Input"), InputSlot("Start"), InputSlot("Stop")]
    outputSlots = [OutputSlot("Output")]

    def setupOutputs(self):
        with Tracer(traceLogger):
            start = self.inputs["Start"].value
            stop = self.inputs["Stop"].value
            assert isinstance(start, tuple)
            assert isinstance(stop, tuple)
            assert len(start) == len(self.inputs["Input"].shape)
            assert len(start) == len(stop)
            assert (numpy.array(stop)>= numpy.array(start)).all()
        
            temp = tuple(numpy.array(stop) - numpy.array(start))
            #drop singleton dimensions
            outShape = ()
            for e in temp:
                if e > 0:
                    outShape = outShape + (e,)
        
            self.outputs["Output"]._shape = outShape
            self.outputs["Output"]._axistags = self.inputs["Input"].axistags
            self.outputs["Output"]._dtype = self.inputs["Input"].dtype

    def getOutSlot(self, slot, key, resultArea):
        with Tracer(traceLogger):
            start = self.inputs["Start"].value
            stop = self.inputs["Stop"].value
    
            temp = tuple()
            for i in xrange(len(start)):
                if stop[i] - start[i] > 0:
                    temp += (stop[i]-start[i],)
    
            readStart, readStop = sliceToRoi(key, temp)
    
    
    
            newKey = ()
            resultKey = ()
            i = 0
            i2 = 0
            for kkk in xrange(len(start)):
                e = stop[kkk] - start[kkk]
                if e > 0:
                    newKey += (slice(start[i2] + readStart[i], start[i2] + readStop[i],None),)
                    resultKey += (slice(0,temp[i2],None),)
                    i +=1
                else:
                    newKey += (slice(start[i2], start[i2], None),)
                    resultKey += (0,)
                i2 += 1
    
            res = self.inputs["Input"][newKey].allocate().wait()
            resultArea[:] = res[resultKey]

    def propagateDirty(self, dirtySlot, roi):
        if dirtySlot == self.Input:
            # Translate the input key to a small subregion key
            smallstart = roi.start - self.Start.value
            smallstop = roi.stop - self.Start.value
            
            # Clip to our output shape
            smallstart = numpy.maximum(smallstart, 0)
            smallstop = numpy.minimum(smallstop, self.Output.meta.shape)

            # If there's an intersection with our output,
            #  propagate dirty region to output
            if ((smallstop - smallstart ) > 0).all():
                self.Output.setDirty( smallstart, smallstop )

class OpMultiArrayMerger(Operator):
    inputSlots = [MultiInputSlot("Inputs"),InputSlot('MergingFunction')]
    outputSlots = [OutputSlot("Output")]

    name = "Merge Multi Arrays based on a variadic merging function"
    category = "Misc"

    def setupOutputs(self):

        shape=self.inputs["Inputs"][0].shape
        axistags=copy.copy(self.inputs["Inputs"][0].axistags)


        self.outputs["Output"]._shape = shape
        self.outputs["Output"]._axistags = axistags
        self.outputs["Output"]._dtype = self.inputs["Inputs"][0].dtype



        for input in self.inputs["Inputs"]:
            assert input.shape==shape, "Only possible merging consistent shapes"
            assert input.axistags==axistags, "Only possible merging same axistags"



    def getOutSlot(self, slot, key, result):

        requests=[]
        for input in self.inputs["Inputs"]:
            requests.append(input[key].allocate())

        data=[]
        for req in requests:
            data.append(req.wait())

        fun=self.inputs["MergingFunction"].value

        result[:]=fun(data)



class OpPixelOperator(Operator):
    name = "OpPixelOperator"
    description = "simple pixel operations"

    inputSlots = [InputSlot("Input"), InputSlot("Function")]
    outputSlots = [OutputSlot("Output")]

    def setupOutputs(self):

        inputSlot = self.inputs["Input"]

        self.function = self.inputs["Function"].value

        self.outputs["Output"]._shape = inputSlot.shape
        self.outputs["Output"]._dtype = inputSlot.dtype
        self.outputs["Output"]._axistags = inputSlot.axistags



    def getOutSlot(self, slot, key, result):


        matrix = self.inputs["Input"][key].allocate().wait()
        matrix = self.function(matrix)

        result[:] = matrix[:]


    def notifyDirty(selfut,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape

    @property
    def dtype(self):
        return self.outputs["Output"]._dtype


class OpMultiInputConcatenater(Operator):
    name = "OpMultiInputConcatenater"
    description = "Combine two or more MultiInput slots into a single MultiOutput slot"

    Inputs = MultiInputSlot(level=2, optional=True)
    Output = MultiOutputSlot(level=1)

    def __init__(self, *args, **kwargs):
        super(OpMultiInputConcatenater, self).__init__(*args, **kwargs)
        self._numInputLists = 0

    def getOutputIndex(self, inputMultiSlot, inputIndex):
        """
        Determine which output index corresponds to the given input multislot and index.
        """
        # Determine the corresponding output index
        outputIndex = 0
        # Search for the input slot
        for index, multislot in enumerate( self.Inputs ):
            if inputMultiSlot != multislot:
                # Not the resized slot.  Skip all its subslots
                outputIndex += len(multislot)
            else:
                # Found the resized slot.  Add the offset and stop here.
                outputIndex += inputIndex
                return outputIndex

        assert False

    def handleInputInserted(self, resizedSlot, inputPosition, totalsize):
        """
        A slot was inserted in one of our inputs.
        Insert a slot in the appropriate location of our output, and connect it to the appropriate input subslot.
        """
        # Determine which output slot this corresponds to
        outputIndex = self.getOutputIndex(resizedSlot, inputPosition)

        # Insert new output slot and connect it up.
        newOutputLength = len( self.Output ) + 1
        self.Output.insertSlot(outputIndex, newOutputLength)
        self.Output[outputIndex].connect( resizedSlot[inputPosition] )

    def handleInputRemoved(self, resizedSlot, inputPosition, totalsize):
        """
        A slot was removed from one of our inputs.
        Remove the appropriate slot from our output.
        """
        # Determine which output slot this corresponds to
        outputIndex = self.getOutputIndex(resizedSlot, inputPosition)

        # Remove the corresponding output slot
        newOutputLength = len( self.Output ) - 1
        self.Output.removeSlot(outputIndex, newOutputLength)

    def setupOutputs(self):
        # This function is merely provided to initialize ourselves if one of our input lists was set up in advance.
        # We don't need to do this expensive rebuilding of the output list unless a new input list was added
        if self._numInputLists == len(self.Inputs):
            return
        
        self._numInputLists = len(self.Inputs)
            
        # First pass to determine output length
        totalOutputLength = 0
        for index, slot in enumerate( self.Inputs ):
            totalOutputLength += len(slot)

        self.Output.resize( totalOutputLength )

        # Second pass to make connections and subscribe to future changes
        outputIndex = 0
        for index, slot in enumerate( self.Inputs ):
            slot.notifyInserted( self.handleInputInserted )
            slot.notifyRemove( self.handleInputRemoved )

            # Connect subslots to output
            for i, s in enumerate(slot):
                self.Output[outputIndex].connect(s)
                outputIndex += 1


    def getSubOutSlot(self, slots, indexes, key, result):
        # Should never be called.  All output slots are directly connected to an input slot.
        assert False


class OpTransposeSlots(Operator):
    """
    Takes an input slot indexed as [i][j] and produces an output slot indexed as [j][i]
    Note: Only works for a slot of level 2.
    """
    Inputs = MultiInputSlot(level=2)
    Outputs = MultiOutputSlot(level=2)
            
    def setupOutputs(self):
        minSize = None
        for i, mslot in enumerate( self.Inputs ):
            if minSize is None:
                minSize = len(mslot)
            else:
                minSize = min( minSize, len(mslot) ) 
        
        self.Outputs.resize(minSize)
        for j, mslot in enumerate( self.Outputs ):
            mslot.resize( len(self.Inputs) )
            for i, oslot in enumerate( mslot ):
                oslot.connect( self.Inputs[i][j] )

    def getSubOutSlot(self, slots, indexes, key, result):
        # Should never be called.  All output slots are directly connected to an input slot.
        assert False




































