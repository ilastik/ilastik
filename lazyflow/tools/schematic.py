from schematic_abc import DrawableABC, ConnectableABC, ConnectionABC
import svg

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
        d = 2*self.Radius
        return (d,d)
    
    def drawAt(self, canvas, upperLeft):
        x,y = upperLeft
        cx = x + self.Radius
        cy = y + self.Radius
        canvas += svg.circle(cx=cx, cy=cy, r=self.Radius, fill='white', stroke='black')
    
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

    def resize(self, n):
        if len(self.subslots) > n:
            self.subslots = self.subslots[0:n]
        while len(self.subslots) < n:
            if self.level > 1:
                self.subslots.append( SvgMultiSlot(self.level-1) )
            else:
                self.subslots.append( SvgSlot() )

    def size(self):
        if self.subslots:
            width = self.subslots[0].size()[0] + 2*self.Padding
        else:
            width = (SvgSlot.Radius + 2*self.Padding)

        if self.level > 1:
            height = self.Padding * (len(self) + 1)
        else:
            height = self.Padding * 2
        for slot in self.subslots:
            height += slot.size()[1]
        return (width, height)
    
    def drawAt(self, canvas, upperLeft):
        # Draw our outer rectangle
        x,y = upperLeft
        width, height = self.size()
        canvas += svg.rect(x=x, y=y, width=width, height=height, stroke='black', fill='white')
        y += self.Padding
        x += self.Padding

        # Draw each subslot, separated by some padding
        for slot in self.subslots:
            slot.drawAt(canvas, (x,y))
            y += slot.size()[1]
            # No padding between level-0 subslots
            if self.level > 1:
                y += self.Padding
        
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
        width = self.getRectWidth()
        height = 2 * self.TitleHeight
        
        inputSize = self.getInputSize()
        outputSize = self.getOutputSize()
        
        width += inputSize[0] + outputSize[0]
        height += max(inputSize[1], outputSize[1])
        return (width, height)

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
        size = self.size()
        rect_width=self.getRectWidth()
        height = size[1]
        r = self.TitleHeight - 2

        rect_x = x + self.getInputSize()[0]
        rect_y = y

        canvas += svg.rect(x=rect_x, y=rect_y, width=rect_width, height=height, rx=r, ry=r, stroke='black', stroke_width=2, fill='white' )
        path_d = 'M {startx} {y} L {endx} {y} Z'.format(startx=rect_x, y=rect_y+r+2, endx=rect_x+rect_width)
        canvas += svg.path(d=path_d, stroke='black', stroke_width=1)

        with block(svg.text, x=rect_x+rect_width/2, y=y+r, text_anchor='middle'):
            canvas += self.op.name + '\n'

        x, y = upperLeft
        y += self.TitleHeight
        inputSize = self.getInputSize()
        for slot in self.inputs.values():
            size = slot.size()
            slot.drawAt( canvas, (x+(inputSize[0]-size[0]),y) )
            y += size[1] + self.PaddingBetweenSlots

        x, y = upperLeft
        x += rect_width + inputSize[0]
        y += self.TitleHeight
        for slot in self.outputs.values():
            size = slot.size()
            slot.drawAt( canvas, (x,y) )
            y += size[1] + self.PaddingBetweenSlots

            
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
