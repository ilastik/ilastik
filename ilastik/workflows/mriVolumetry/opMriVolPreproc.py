from lazyflow.graph import Operator, InputSlot, OutputSlot



class OpMriVolPreprocOLD( Operator ):
    name = "opMriVolPrepoc5d"
    
    RawInput = InputSlot(optional=True) # Display only
    Input = InputSlot() # Prediction image
    Sigma = InputSlot(stype='float', value=1.0)

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpMriVolPreprocOLD, self).__init__(*args, **kwargs)


    def setupOutputs(self):
        print 'Do smoothing'
        

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."
        
    def propagateDirty(self, slot, subindex, roi):
        print 'dirty'
        pass # Nothing to do...

