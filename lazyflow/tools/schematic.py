from schematic_abc import DrawableABC, ConnectableABC, ConnectionABC
import svg
import numpy
from functools import partial

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

    def size(self):
        return self.drawAt("", (0,0))
    
    def drawAt(self, canvas, upperLeft):
        x,y = upperLeft
        cx = x + self.Radius
        cy = y + self.Radius
        canvas += svg.circle(cx=cx, cy=cy, r=self.Radius, fill='white', stroke='black', class_=self.name)
        
        lowerRight = (x + 2*self.Radius, y + 2 * self.Radius)
        return lowerRight
    
    def inputPointOffset(self):
        return (0, self.Radius)
    
    def outputPointOffset(self):
        return (2*self.Radius, self.Radius)

class SvgMultiSlot(DrawableABC, ConnectableABC):
    Padding = 3 # Padding between subslots (unless subslots are level 0)

    def __init__(self, mslot):
        self.level = mslot.level
        self.subslots = []
        for i, slot in enumerate(mslot):
            self.subslots.append( createSvgSlot(slot) )
        
        self._size = self._generate_code()
        self.mslot = mslot

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
        canvas += svg.rect(x=upperLeft[0], y=upperLeft[1], width=width, height=height, stroke='black', fill='transparent')

        self._code = canvas
        return lowerRight
        
    def inputPointOffset(self):
        return ( 0, self.size()[1]/2 )
    
    def outputPointOffset(self):
        return ( self.size()[0], self.size()[1]/2 )

def hasAncestor(x, parent):
    if x.parent == parent:
        return True
    elif x.parent is None:
        return False
    else:
        return hasAncestor(x.parent, parent)

def isDownStream(op1, op2, parent):
    for islot in op1.inputs.values():
        if islot.partner is None:
            continue
        upStreamOp = islot.partner.getRealOperator()
        if upStreamOp is op2:
            return True # A is downstream from B
        elif hasAncestor(upStreamOp, parent):
            if isDownStream(upStreamOp, op2, parent):
                return True
    return False

def streamPos(parent, a,b):
    # A and B must both be owned by the parent, otherwise they aren't comparable
    if not hasAncestor(a, parent) or not hasAncestor(b, parent):
        return 0
    if isDownStream(a, b, parent):
        return 1
    if isDownStream(b, a, parent):
        return -1
    return 0

def sortByPos(l, parent):
    sorted_l = []
    for nextOp in l:
        i = 0
        for i, op in enumerate(sorted_l):
            pos = streamPos(parent, nextOp, op)
            if pos == 1:
                break
        sorted_l.insert(i, nextOp)
    
#    sorted_l2 = []
#    for nextOp in sorted_l:
#        i = 0
#        for i, op in enumerate(sorted_l2):
#            pos = streamPos(parent, nextOp, op)
#            if pos == -1:
#                break
#        sorted_l2.insert(i, nextOp)

    return sorted_l


class SvgOperator( DrawableABC ):
    TitleHeight = 15
    PaddingBetweenSlots = 5
    PaddingBetweenInternalOps = 10
        
    def __init__(self, op):
        self.op = op

        self.inputs = {}
        for key, slot in enumerate(self.op.inputs.values()):
            self.inputs[key] = createSvgSlot( slot )

        self.outputs = {}
        for key, slot in enumerate(self.op.outputs.values()):
            self.outputs[key] = createSvgSlot( slot )
            
        self._size = self._generate_code()

    def size(self):
        return self._size

    def getInputSize(self):
        inputWidth = 0
        inputHeight = self.PaddingBetweenSlots * (len(self.inputs)+1)
        for svgSlot in self.inputs.values():
            slotSize = svgSlot.size()
            inputWidth = max(inputWidth, slotSize[0])
            inputHeight += slotSize[1]
        return (inputWidth, inputHeight)

    def getOutputSize(self):
        outputWidth = 0
        outputHeight = self.PaddingBetweenSlots * (len(self.outputs)+1)
        for svgSlot in self.outputs.values():
            slotSize = svgSlot.size()
            outputWidth = max(outputWidth, slotSize[0])
            outputHeight += slotSize[1]
        return (outputWidth, outputHeight)

    def drawAt(self, canvas, upperLeft):
        block = partial(svg.tagblock, canvas)
        with block( svg.group, class_=self.op.name, transform="translate({},{})".format(*upperLeft) ):
            canvas += self._code

    def _generate_code(self):
        upperLeft = (0,0)
        canvas = svg.IndentingStringIO("")
        x, y = upperLeft

        inputSize = self.getInputSize()
        outputSize = self.getOutputSize()

        child_ordering = {}
        if len(self.op._children) > 0:
            # Draw child operators
            sorted_children = sorted( self.op._children, cmp=partial(streamPos, self) )
            #sorted_children = sorted( reversed(sorted_children), cmp=partial(streamPos, self) )
            #sorted_children = sortByPos(self.op._children, self)
    
            child_ordering[0] = [sorted_children[0]]
            col_index = 0
            for child, next_child in zip(sorted_children[0:-1], sorted_children[1:]):
                if isDownStream(next_child, child, self):
                    col_index += 1
                    child_ordering[col_index] = []
                child_ordering[col_index].append(next_child)
    
            print [child.name for child in sorted_children]
            for col in sorted(child_ordering.keys()):
                print col, ":", [child.name for child in child_ordering[col]]
        
        r = self.TitleHeight - 2
        rect_x = upperLeft[0] + inputSize[0]
        rect_y = upperLeft[1]

        child_x = rect_x + r
        child_y = rect_y + 2*r
        max_child_y = child_y
        max_child_x = child_x + self.PaddingBetweenInternalOps
        for col_index, col_children in sorted( child_ordering.items() ):
            for child in col_children:
                svgChild = SvgOperator(child)
                svgChild.drawAt(canvas, (child_x, child_y) )
                lowerRight = (svgChild.size()[0] + child_x, svgChild.size()[1] + child_y)
                max_child_x = max(lowerRight[0], max_child_x)
                child_y = lowerRight[1] + self.PaddingBetweenInternalOps
            
            max_child_x += self.PaddingBetweenInternalOps
            max_child_y = max(max_child_y, child_y)
            child_x = max_child_x
            child_y = rect_y + 2*r

        rect_width = max_child_x - rect_x
        rect_width = max( rect_width, 2*self.PaddingBetweenInternalOps )
        rect_width = max( rect_width, 9*len(self.op.name) ) # Correct width depends on font...
        rect_width += r

        rect_height = max_child_y - rect_y
        rect_height = max(rect_height, outputSize[1])
        rect_height = max(rect_height, inputSize[1])
        rect_height += 2*r
        rect_height = max( rect_height, 50 )

        # Draw outer rectangle
        canvas += svg.rect(x=rect_x, y=rect_y, width=rect_width, height=rect_height, rx=r, ry=r, stroke='black', stroke_width=2, style='fill-opacity:0' )
        path_d = 'M {startx} {y} L {endx} {y} Z'.format(startx=rect_x, y=rect_y+r+2, endx=rect_x+rect_width)
        canvas += svg.path(d=path_d, stroke='black', stroke_width=1)

        block = partial(svg.tagblock, canvas)
        with block(svg.text, x=rect_x+rect_width/2, y=rect_y+r, text_anchor='middle'):
            canvas += self.op.name + '\n'

        # Draw inputs
        y += self.TitleHeight
        for slot in self.inputs.values():
            size = slot.size()
            slot.drawAt( canvas, (x+(inputSize[0]-size[0]),y) )
            y += size[1] + self.PaddingBetweenSlots

        # Draw outputs
        x, y = upperLeft
        x += rect_width + inputSize[0]
        y += self.TitleHeight
        for slot in self.outputs.values():
            size = slot.size()
            slot.drawAt( canvas, (x,y) )
            y += size[1] + self.PaddingBetweenSlots
        
        lowerRight_x = upperLeft[0] + rect_width + inputSize[0] + outputSize[0]
        lowerRight_y = upperLeft[1] + rect_height

        self._code = canvas
        return (lowerRight_x, lowerRight_y)
            
    def getRectWidth(self):
        return 100
         
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

    from lazyflow.graph import OperatorWrapper
    from lazyflow.operators.ioOperators import OpInputDataReader
    opInput = OpInputDataReader(graph=graph)
    opInput.FilePath.setValue("/magnetic/synapse_small.npy")

    opTest = OperatorWrapper( OpInputDataReader, graph=graph )
    opTest.FilePath.resize(2)
    opTest.FilePath[0].setValue("/magnetic/synapse_small.npy")
    opTest.FilePath[1].setValue("/magnetic/gigacube.h5/volume/data")

    svgOp = SvgOperator(opTest)
    
    block = partial(svg.tagblock, canvas)
    with block( svg.svg, x=0, y=0, width=1000, height=1000 ):
        svgOp.drawAt(canvas, (10, 10) )
#        slot = SvgMultiSlot(3)
#        
#        slot.resize(3)
#        for i in range(3):
#            slot[i].resize(5)
#            for j in range(5):
#                slot[i][j].resize(j+1)
#            slot.drawAt(canvas, (0,0) )
    
    #print canvas.getvalue()
    f = file("/Users/bergs/Documents/svgfiles/canvas.html", 'w')
    f.write( canvas.getvalue() )
    f.close()
