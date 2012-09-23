from schematic_abc import DrawableABC, ConnectableABC, ConnectionABC
import svg
import numpy

def createSvgSlot(slot):
    if slot.level > 0:
        return SvgMultiSlot(slot)
    else:
        return SvgSlot(slot)        

class SvgSlot(DrawableABC, ConnectableABC):
    Radius = 5

    def __init__(self, slot):
        self.name = slot.name 

    def size(self):
        return self.drawAt("", (0,0))
    
    def drawAt(self, canvas, upperLeft):
        x,y = upperLeft
        cx = x + self.Radius
        cy = y + self.Radius
        canvas += svg.circle(cx=cx, cy=cy, r=self.Radius, fill='white', stroke='black')
        
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

    def __getitem__(self, i):
        return self.subslots[i]
    
    def __len__(self):
        return len(self.subslots)
    
    def size(self):
        return self.drawAt("", (0,0))
    
    def drawAt(self, canvas, upperLeft):
        x,y = upperLeft
        y += self.Padding
        x += self.Padding

        lowerRight = (x,y)

        # Draw each subslot, separated by some padding
        for slot in self.subslots:
            lowerRight = slot.drawAt(canvas, (x,y))
            y = lowerRight[1]
            # No padding between level-0 subslots
            if self.level > 1:
                y += self.Padding

        lowerRight = (lowerRight[0] + self.Padding, y + self.Padding )

        # Draw our outer rectangle
        width = lowerRight[0] - upperLeft[0]
        height = lowerRight[1] - upperLeft[1]
        canvas += svg.rect(x=upperLeft[0], y=upperLeft[1], width=width, height=height, stroke='black', fill='transparent')

        return lowerRight
        
    def inputPointOffset(self):
        return ( 0, self.size()[1]/2 )
    
    def outputPointOffset(self):
        return ( self.size()[0], self.size()[1]/2 )

class SvgOperator( DrawableABC ):
    TitleHeight = 15
    PaddingBetweenSlots = 5
        
    def __init__(self, op):
        self.op = op

        self.inputs = {}
        for key, slot in enumerate(self.op.inputs.values()):
            self.inputs[key] = createSvgSlot( slot )

        self.outputs = {}
        for key, slot in enumerate(self.op.outputs.values()):
            self.outputs[key] = createSvgSlot( slot )

    def size(self):
        return self.drawAt("", (0,0))

    def getInputSize(self):
        inputWidth = 0
        inputHeight = self.PaddingBetweenSlots * (len(self.inputs)-1)
        for svgSlot in self.inputs.values():
            slotSize = svgSlot.size()
            inputWidth = max(inputWidth, slotSize[0])
            inputHeight += slotSize[1]
        return (inputWidth, inputHeight)


    def getOutputSize(self):
        outputWidth = 0
        outputHeight = self.PaddingBetweenSlots * (len(self.outputs)-1)
        for svgSlot in self.outputs.values():
            slotSize = svgSlot.size()
            outputWidth = max(outputWidth, slotSize[0])
            outputHeight += slotSize[1]
        return (outputWidth, outputHeight)

    def drawAt(self, canvas, upperLeft):
        x, y = upperLeft

        # Draw inputs
        y += self.TitleHeight
        inputSize = self.getInputSize()
        for slot in self.inputs.values():
            size = slot.size()
            slot.drawAt( canvas, (x+(inputSize[0]-size[0]),y) )
            y += size[1] + self.PaddingBetweenSlots

        # Draw outer rectangle
        r = self.TitleHeight - 2
        rect_x = upperLeft[0] + self.getInputSize()[0]
        rect_y = upperLeft[1]
        rect_width=self.getRectWidth()
        height = max(self.getInputSize()[1], self.getOutputSize()[1]) + 2*r

        canvas += svg.rect(x=rect_x, y=rect_y, width=rect_width, height=height, rx=r, ry=r, stroke='black', stroke_width=2, fill='transparent' )
        path_d = 'M {startx} {y} L {endx} {y} Z'.format(startx=rect_x, y=rect_y+r+2, endx=rect_x+rect_width)
        canvas += svg.path(d=path_d, stroke='black', stroke_width=1)

        with block(svg.text, x=rect_x+rect_width/2, y=rect_y+r, text_anchor='middle'):
            canvas += self.op.name + '\n'

        # Draw outputs
        x, y = upperLeft
        x += rect_width + inputSize[0]
        y += self.TitleHeight
        for slot in self.outputs.values():
            size = slot.size()
            slot.drawAt( canvas, (x,y) )
            y += size[1] + self.PaddingBetweenSlots
        
        totalSize = numpy.add( self.getInputSize(), self.getOutputSize() )
        totalSize [0] += self.getRectWidth()
        return tuple(totalSize)
            
    def getRectWidth(self):
        return 100
         
if __name__ == "__main__":
    from functools import partial
    canvas = svg.SvgCanvas("")

    from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
    
    class OpTest(Operator):
        InputA = InputSlot()
        InputB = InputSlot(level=1)
        Output = OutputSlot()
    
    graph=Graph()
    opTest = OpTest(graph=graph)
    opTest.InputB.resize(3)

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
    
    print canvas.getvalue()
    f = file("/Users/bergs/Documents/svgfiles/canvas.html", 'w')
    f.write( canvas.getvalue() )
    f.close()
