from schematic_abc import DrawableABC, ConnectableABC
import svg
import numpy
from functools import partial
import itertools

# Reverse lookup of lazyflow slots to svg slots
slot_registry = {}
op_registry = {}

def generateSvgFileForOperator(svgPath, op, detail):
    global slot_registry
    global op_registry

    slot_registry = {}
    op_registry = {}
    
    svgOp = SvgOperator(op, max_child_depth=detail)
    
    canvas = svg.SvgCanvas("")
    block = partial(svg.tagblock, canvas)
    with block( svg.svg, x=0, y=0, width=7000, height=2000 ):
        canvas += svg.inkscapeDefinitions()
        svgOp.drawAt(canvas, (10, 10) )
        svgOp.drawConnections(canvas)
    
    with file(str(svgPath), 'w') as f:
        f.write( canvas.getvalue() )

def createSvgSlot(slot):
    """
    Factory for creating a single-slot or multi-slot.
    """
    if slot.level > 0:
        return SvgMultiSlot(slot)
    else:
        return SvgSlot(slot)        

class SvgSlot(DrawableABC, ConnectableABC):
    Radius = 5

    def __init__(self, slot):
        self.name = slot.name 
        self._slot = slot
        slot_registry[self._slot] = self
        
    def size(self):
        return self.drawAt("", (0,0))
    
    def drawAt(self, canvas, upperLeft):
        x,y = upperLeft
        cx = x + self.Radius
        cy = y + self.Radius
        canvas += svg.circle(cx=cx, cy=cy, r=self.Radius, 
                             fill='white', stroke='black', class_=self.name, id_=self.key())
        
        lowerRight = (x + 2*self.Radius, y + 2 * self.Radius)
        return lowerRight
    
    def key(self):
        return hex(id(self._slot))
    
    def partnerKey(self):
        return hex(id(self._slot.partner))

    def drawConnectionToPartner(self, canvas):
        if self._slot.partner in slot_registry:
            myIdStr = '#' + self.key()
            partnerIdStr = '#' + self.partnerKey()
            pathName = "pathTo" + self.key()
            canvas += svg.connector_path( id_=pathName, inkscape__connection_start=partnerIdStr, inkscape__connection_end=myIdStr )

class SvgMultiSlot(DrawableABC, ConnectableABC):
    Padding = 3 # Padding between subslots (unless subslots are level 0)

    def __init__(self, mslot):
        self.level = mslot.level
        self.subslots = []
        for i, slot in enumerate(mslot):
            self.subslots.append( createSvgSlot(slot) )
        
        self.mslot = mslot
        self._size = self._generate_code()
        self.name = self.mslot.name

        slot_registry[self.mslot] = self

    def key(self):
        return hex(id(self.mslot))

    def partnerKey(self):
        return hex(id(self.mslot.partner))

    def __getitem__(self, i):
        return self.subslots[i]
    
    def __len__(self):
        return len(self.subslots)
    
    def size(self):
        return self._size
    
    def drawAt(self, canvas, upperLeft):
        block = partial(svg.tagblock, canvas)
        with block( svg.group, class_=self.mslot.name, transform="translate({},{})".format(*upperLeft) ):
            canvas += self._code

    def drawConnectionToPartner(self, canvas):
        if self.mslot.partner in slot_registry:
            myIdStr = '#' + self.key()
            partnerIdStr = '#' + self.partnerKey()
            pathName = "pathTo" + self.key()
            canvas += svg.connector_path( id_=pathName, inkscape__connection_start=partnerIdStr, inkscape__connection_end=myIdStr )
        else:
            # Try subslot connections
            for slot in self.subslots:
                slot.drawConnectionToPartner(canvas)

    def _generate_code(self):
        """
        Generate the text for drawing this multislot at (0,0)
        """        
        canvas = svg.IndentingStringIO("")
        upperLeft = (0,0)
        x,y = upperLeft
        y += self.Padding
        x += self.Padding

        lowerRight = (x,y)

        # Draw each subslot, separated by some padding
        for slot in self.subslots:
            slot.drawAt(canvas, (x,y))
            lowerRight = (x + slot.size()[0], y + slot.size()[1])
            y = lowerRight[1]
            # No padding between level-0 subslots
            if self.level > 1:
                y += self.Padding

        if len(self.subslots) == 0:
            lowerRight = (x + 2*SvgSlot.Radius + self.Padding, y + self.Padding )
        else:
            lowerRight = (lowerRight[0] + self.Padding, y + self.Padding )

        # Draw our outer rectangle
        width = lowerRight[0] - upperLeft[0]
        height = lowerRight[1] - upperLeft[1]
        canvas += svg.rect(x=upperLeft[0], y=upperLeft[1], width=width, height=height, 
                           stroke='black', stroke_width=1, style='fill-opacity:0', id_=self.key() )

        self._code = canvas
        return lowerRight

class SvgOperator( DrawableABC ):
    TitleHeight = 15
    MinPaddingBetweenSlots = 10
    PaddingBetweenInternalOps = 50
    PaddingForSlotName = 100
        
    def __init__(self, op, max_child_depth):
        self.op = op
        self.max_child_depth = max_child_depth

        self.inputs = {}
        for key, slot in enumerate(self.op.inputs.values()):
            self.inputs[key] = createSvgSlot( slot )

        self.outputs = {}
        for key, slot in enumerate(self.op.outputs.values()):
            self.outputs[key] = createSvgSlot( slot )
            
        self._size = self._generate_code()
        op_registry[self.op] = self

    def size(self):
        return self._size

    def getInputSize(self):
        inputWidth = 0
        inputHeight = self.MinPaddingBetweenSlots * (len(self.inputs)+1)
        for svgSlot in self.inputs.values():
            slotSize = svgSlot.size()
            inputWidth = max(inputWidth, slotSize[0])
            inputHeight += slotSize[1]
        return (inputWidth, inputHeight)

    def getOutputSize(self):
        outputWidth = 0
        outputHeight = self.MinPaddingBetweenSlots * (len(self.outputs)+1)
        for svgSlot in self.outputs.values():
            slotSize = svgSlot.size()
            outputWidth = max(outputWidth, slotSize[0])
            outputHeight += slotSize[1]
        return (outputWidth, outputHeight)

    def drawAt(self, canvas, upperLeft):
        block = partial(svg.tagblock, canvas)
        with block( svg.group, class_=self.op.name, transform="translate({},{})".format(*upperLeft) ):
            canvas += self._code

    def drawConnections(self, canvas):
        for slot in self.op.inputs.values() + self.op.outputs.values():
            assert slot in slot_registry
            slot_registry[slot].drawConnectionToPartner(canvas)
        
        for child in self.op.children:
            if child in op_registry:
                op_registry[child].drawConnections(canvas)

    def _generate_code(self):
        upperLeft = (0,0)
        canvas = svg.IndentingStringIO("")
        x, y = upperLeft

        title_text = self.op.name

        inputSize = self.getInputSize()
        outputSize = self.getOutputSize()

        child_ordering = {}
        for child in self.op.children:
            col = get_column_within_parent(child)
            if col not in child_ordering:
                child_ordering[col] = []
            child_ordering[col].append(child)
    
        r = self.TitleHeight - 2
        rect_x = upperLeft[0] + inputSize[0]
        rect_y = upperLeft[1]

        child_x = rect_x + r + self.PaddingForSlotName + self.PaddingBetweenInternalOps
        child_y = rect_y + 2*r
        max_child_y = child_y
        max_child_x = child_x 
        if len(self.op.children) > 0:
            if self.max_child_depth == 0:
                title_text += '*' # Asterisk in the title indicates that this operator has children that are not shown
            else:
                svgChildren = {}
                columnHeights = []
                for col_index, col_children in sorted( child_ordering.items() ):
                    columnHeights.append(0)
                    svgChildren[col_index] = []
                    for child in col_children:
                        svgChild = SvgOperator(child, self.max_child_depth-1)
                        columnHeights[col_index] += svgChild.size()[1]
                        svgChildren[col_index].append(svgChild)

                maxColumnHeight = max(columnHeights)

                columnExtraPadding = []
                for col_index, col_svg_children in sorted( svgChildren.items() ):
                    columnExtraPadding.append( maxColumnHeight )
                    for svgChild in col_svg_children:
                        columnExtraPadding[col_index] -= svgChild.size()[1]

                for col_index, col_children in sorted( svgChildren.items() ):
                    for svgChild in col_children:
                        child_y += (self.PaddingBetweenInternalOps + columnExtraPadding[col_index]/len(col_children)) / 2
                        svgChild.drawAt( canvas, (child_x, child_y) )
                        lowerRight = (svgChild.size()[0] + child_x, svgChild.size()[1] + child_y)
                        max_child_x = max(lowerRight[0], max_child_x)
                        child_y = lowerRight[1] + self.PaddingBetweenInternalOps + columnExtraPadding[col_index]/len(col_children)

                    max_child_x += self.PaddingBetweenInternalOps
                    max_child_y = max(max_child_y, child_y)
                    child_x = max_child_x
                    child_y = rect_y + 2*r
        
                max_child_x += self.PaddingForSlotName + self.PaddingBetweenInternalOps

        def max_slot_name_length(slots):
            m = 0
            for slot in slots:
                m = max(m, len(slot.name))
            return m
        
        max_input_name = max_slot_name_length(self.op.inputs.values())
        max_output_name = max_slot_name_length(self.op.outputs.values())

        rect_width = max_child_x - rect_x
        rect_width = max( rect_width, 2*self.PaddingBetweenInternalOps )
        rect_width = max( rect_width, 9*len(self.op.name) ) # Correct width depends on font...
        rect_width = max( rect_width, 9*(max_input_name + max_output_name) )
        rect_width += r

        rect_height = max_child_y - rect_y
        rect_height = max(rect_height, outputSize[1])
        rect_height = max(rect_height, inputSize[1])
        rect_height += 2*r
        rect_height = max( rect_height, 50 )

        # Draw outer rectangle
        canvas += svg.rect(x=rect_x, y=rect_y, width=rect_width, height=rect_height, rx=r, ry=r, 
                           inkscape__connector_avoid="false", stroke='black', stroke_width=2, style='fill-opacity:0' )
        path_d = 'M {startx} {y} L {endx} {y} Z'.format(startx=rect_x, y=rect_y+r+2, endx=rect_x+rect_width)
        canvas += svg.path(d=path_d, stroke='black', stroke_width=1)

        block = partial(svg.tagblock, canvas)
        with block(svg.text, x=rect_x+rect_width/2, y=rect_y+r, text_anchor='middle'):
            canvas += title_text + '\n'

        # Add extra padding between input slots if there's room (i.e. spread out the inputs to cover the entire left side)
        inputSlotPadding = (rect_height - self.getInputSize()[1]) / (len(self.inputs)+1)
        
        # Draw inputs
        y += 1.5*self.TitleHeight + inputSlotPadding
        for slot in self.inputs.values():
            size = slot.size()
            slot_x, slot_y = (x+(inputSize[0]-size[0]),y)
            slot.drawAt( canvas, (slot_x, slot_y) )
            y += size[1] + inputSlotPadding

            text_x, text_y = (slot_x + size[0] + 5, slot_y + size[1]/2)
            with block(svg.text, x=text_x, y=text_y, text_anchor='start'):
                canvas += slot.name + '\n'

        # Add extra padding between output slots if there's room (i.e. spread out the inputs to cover the entire right side)
        outputSlotPadding = (rect_height - self.getOutputSize()[1]) / (len(self.outputs)+1)

        # Draw outputs
        x, y = upperLeft
        x += rect_width + inputSize[0]
        y += 1.5*self.TitleHeight + outputSlotPadding
        for slot in self.outputs.values():
            size = slot.size()
            text_x, text_y = (x - 5, y + size[1]/2)
            slot.drawAt( canvas, (x,y) )
            y += size[1] + outputSlotPadding

            with block(svg.text, x=text_x, y=text_y, text_anchor='end'):
                canvas += slot.name + '\n'
        
        lowerRight_x = upperLeft[0] + rect_width + inputSize[0] + outputSize[0]
        lowerRight_y = upperLeft[1] + rect_height

        self._code = canvas
        return (lowerRight_x, lowerRight_y)
            

memoized_columns = {}
def get_column_within_parent( op ):
    assert op.parent is not None
    if op in memoized_columns:
        return memoized_columns[op]
    
    max_column = 0
    for slot in op.inputs.values():
        if slot.partner is None:
            continue
        upstream_op = slot.partner.getRealOperator()
        if upstream_op is not op.parent and upstream_op is not op:
            assert upstream_op.parent is op.parent
            max_column = max( max_column, get_column_within_parent(upstream_op)+1 )

    memoized_columns[op] = max_column
    return max_column

if __name__ == "__main__":
    canvas = svg.SvgCanvas("")

    from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
    
    class OpChild(Operator):
        name = "OpChild"
        
        InputX = InputSlot()
        InputY = InputSlot()
        Output = OutputSlot()
    
    class OpTest(Operator):
        name = "OpTest"
        
        InputA = InputSlot()
        InputB = InputSlot(level=1)
        Output = OutputSlot()
        
        def __init__(self, *args, **kwargs):
            super(OpTest, self).__init__(*args, **kwargs)
            self.internal0 = OpChild(graph=self.graph, parent=self)
            self.internal1 = OpChild(graph=self.graph, parent=self)
            self.internal2 = OpChild(graph=self.graph, parent=self)
            self.internal3 = OpChild(graph=self.graph, parent=self)
            self.internal4 = OpChild(graph=self.graph, parent=self)

            self.internal0.name = "Op0"
            self.internal1.name = "Op1"
            self.internal2.name = "Op2"
            self.internal3.name = "Op3"
            self.internal4.name = "Op4"
            
            #self.internal0.InputX.connect(self.internal1.Output)
            self.internal2.InputY.connect(self.internal0.Output)
            self.internal2.InputX.connect(self.internal1.Output)
            self.internal3.InputX.connect(self.internal2.Output)
            self.internal4.InputX.connect(self.internal2.Output)

#            assert isDownStream(self.internal2, self.internal0, self)
#            assert isDownStream(self.internal2, self.internal1, self)
#            #assert isDownStream(self.internal1, self.internal0, self)
#            assert isDownStream(self.internal3, self.internal1, self)

    graph=Graph()
#    opTest = OpTest(graph=graph)
#    opTest.InputB.resize(3)

#    from lazyflow.graph import OperatorWrapper
#    from lazyflow.operators.ioOperators import OpInputDataReader
#    opInput = OpInputDataReader(graph=graph)
#    opInput.FilePath.setValue("/magnetic/synapse_small.npy")
#
#    opTest = OperatorWrapper( OpInputDataReader, graph=graph )
#    opTest.FilePath.resize(2)
#    opTest.FilePath[0].setValue("/magnetic/synapse_small.npy")
#    opTest.FilePath[1].setValue("/magnetic/gigacube.h5/volume/data")
#
#    svgOp = SvgOperator(opTest, max_child_depth=1)

    class OpSum(Operator):
        InputA = InputSlot()
        InputB = InputSlot()
        
        Output = OutputSlot()
    
        def setupOutputs(self):
            assert self.InputA.meta.shape == self.InputB.meta.shape, "Can't add images of different shapes!"
            self.Output.meta.assignFrom(self.InputA.meta)
    
        def execute(self, slot, subindex, roi, result):
            a = self.InputA.get(roi).wait()
            b = self.InputB.get(roi).wait()
            result[...] = a+b
            return result

    class OpMultiSum(Operator):
        Inputs = InputSlot(level=1)
        Output = OutputSlot()
    
        def setupOutputs(self):
            expectedShape = self.Inputs[0].meta.shape
            for slot in self.Inputs:
                assert slot.meta.shape == expectedShape, "Can't add images of different shapes!"
            self.Output.meta.assignFrom(self.Inputs[0].meta)
    
        def execute(self, slot, subindex, roi, result):
            result[...] = numpy.zeros(result.shape)
            for slot in self.Inputs:
                result[...] += slot.get(roi).wait()
            return result

    from lazyflow.operators import OpArrayPiper
    from lazyflow.graph import OperatorWrapper
    opGenericMultiOut = OperatorWrapper( OpArrayPiper, graph=graph )
    opGenericMultiOut.Input.resize(3)
    opGenericMultiOut.name = "OpSomeProvider"
    svgOp1 = SvgOperator(opGenericMultiOut, max_child_depth=0)

    opSum = OpMultiSum(graph=graph)
    opSum.Inputs.resize(3)
    svgOp = SvgOperator(opSum, max_child_depth=1)

    class OpThreshold(Operator):
        ThresholdLevel = InputSlot()
        Input = InputSlot()
        Output = OutputSlot()
        
        def setupOutputs(self):
            self.Output.meta.assignFrom(self.Input.meta)
            self.Output.meta.dtype = numpy.uint8

        def execute(self, slot, subindex, roi, result):
            thresholdLevel = self.ThresholdLevel.value
            inputData = self.Input.get(roi).wait()
            result[...] = inputData > thresholdLevel
            return result

        def propagateDirty(self, slot, subindex, roi):
            pass

    opThreshold = OpThreshold(graph=graph)
    svgOp = SvgOperator(opThreshold, max_child_depth=1)    
    
#    class OpMultiThreshold(Operator):
#        ThresholdLevel = InputSlot()
#        Inputs = InputSlot(level=1)
#        Outputs = OutputSlot(level=1)
#        
#        def setupOutputs(self):
#            self.Output.meta.assignFrom(self.Input.meta)
#            self.Output.meta.dtype = numpy.uint8
#
#        def execute(self, slot, subindex, roi, result):
#            thresholdLevel = self.ThresholdLevel.value
#            inputData = self.Input.get(roi).wait()
#            result[...] = inputData > thresholdLevel
#            return result
#
#    opMultiThreshold = OpMultiThreshold(graph=graph)
#    opMultiThreshold.Inputs.resize(3)
#    opMultiThreshold.Outputs.resize(3)
#    svgOp = SvgOperator(opMultiThreshold, max_child_depth=1)    

#    class OpMultiThreshold(Operator):
#        ThresholdLevel = InputSlot()
#        Inputs = InputSlot(level=1)
#        Outputs = OutputSlot(level=1)
#        
#        def __init__(self, *args, **kwargs):
#            # Initialize base class
#            super(OpMultiThreshold, self).__init__(*args, **kwargs)
#            # Initialize our list of internal operators
#            self.internalOps = []
#        
#        def setupOutputs(self):
#            # Clean up any previously created internal operators
#            for slot in self.Outputs:
#                slot.disconnect()
#            for op in self.internalOps:
#                op.cleanUp()
#
#            self.internalOps = []
#            self.Outputs.resize( len(self.Inputs) )
#
#            # Create an internal thresholding operator for each input image
#            for i in range( len(self.Inputs) ):
#                singleImageOp = OpThreshold( parent=self )
#                singleImageOp.ThresholdLevel.connect( self.ThresholdLevel )
#                singleImageOp.Input.connect( self.Inputs[i] )
#                self.Outputs[i].connect( singleImageOp.Output )
#                
#                self.internalOps.append( singleImageOp )
#
#        def execute(self, slot, subindex, roi, result):
#            pass # Nothing to do here: our output will forward all requests to the internal operators
#
#        def propagateDirty(self, slot, subindex, roi):
#            pass # Nothing to do here: our internal operators handle dirty propagation on their own
#
#    opMultiThreshold = OpMultiThreshold(graph=graph)
#    opMultiThreshold.ThresholdLevel.setValue(3)
#    opMultiThreshold.Inputs.resize(3)
#    for slot in opMultiThreshold.inputs.values():
#        slot.setValue(1)
#    svgOp = SvgOperator(opMultiThreshold, max_child_depth=1)    

    opMultiThreshold = OperatorWrapper( OpThreshold, graph=graph, promotedSlotNames=['Input'] )
    opMultiThreshold.Input.resize(2)
    svgOp = SvgOperator(opMultiThreshold, max_child_depth=1)    

    block = partial(svg.tagblock, canvas)
    with block( svg.svg, x=0, y=0, width=1000, height=1000 ):
        canvas += svg.inkscapeDefinitions()
#        svgOp1.drawAt(canvas, (10, 10) )
        svgOp.drawAt(canvas, (10, 10) )
        svgOp.drawConnections(canvas)
#        slot = SvgMultiSlot(3)
#        
#        slot.resize(3)
#        for i in range(3):
#            slot[i].resize(5)
#            for j in range(5):
#                slot[i][j].resize(j+1)
#            slot.drawAt(canvas, (0,0) )
    
    #print canvas.getvalue()
    f = file("/Users/bergs/Documents/svgfiles/canvas.svg", 'w')
    f.write( canvas.getvalue() )
    f.close()
