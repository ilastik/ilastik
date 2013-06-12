from lazyflow.graph import Operator, InputSlot, OutputSlot

class OpSplitBodyPostprocessing(Operator):
    
    RavelerLabels = InputSlot()
    MST = InputSlot()
    
    FragmentedBodies = OutputSlot(level=1)
    FilteredFragmentedBodies = OutputSlot(level=1)
    WatershedFilledBodies = OutputSlot(level=1) # (Fragmented)
    FinalSegmentation = OutputSlot()
    
    # Parse list of saved objects to determine list of raveler labels
    
    # For each raveler body:
    # - Generate seed image:
    #  - Overlay fragments (reverse order)
    #  - Run cc (labelImageWithBackground)
    #  - Use OpFilterLabels to eliminate small pixels (set to 0)
    # - Run watershed:
    #  - seed image is as above
    #  - Boundary indicator is the pixel probabilities, but with all non-body pixels "masked out" by setting them to 2.0
    #  - Use terminate=StopAtThreshold, max_cost=2.0

    # Generate final volume:    
    # - Start with untouched raveler bodies
    # - Accumulate post-processed fragment images
    #  - relabel each fragment image (i.e. add a constant) to ensure no duplicate labels (including original raveler IDs!)


    def __init__(self, *args, **kwargs):
        super( OpSplitBodyPostprocessing, self ).__init__(*args, **kwargs)
        
        
    def setupOutputs(self):
        