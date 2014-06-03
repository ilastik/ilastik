import collections
import numpy
from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.operators import OpArrayCache, OpMaskedWatershed, OpPixelOperator, OpSingleChannelSelector, OpSelectLabel, OpMultiArrayMerger

from ilastik.applets.labeling import OpLabelingSingleLane

#import skimage
#skimage.segmentation.relabel_sequential

class OpSeededWatershed(OpLabelingSingleLane):
    # Image inputs
    UndersegmentedLabels = InputSlot()
    Probabilities = InputSlot()
    
    # Value slots
    FreezeCache = InputSlot(value=True)
    SplittingLabelId = InputSlot(value=0) # 0 is a special case: nothing selected
    WatershedSource = InputSlot(value='probabilities') # Choices: 'probabilities', 'grayscale'
    AvailableLabelIds = InputSlot() # Should be a list of the label ids that can be safely used for newly split fragments

    FocusCoordinates = InputSlot(optional=True) # e.g. setValue( {"x" : 0, "y" : 0, "z" : 0} )

    # Outputs
    InvertedProbability = OutputSlot()
    SelectedMask = OutputSlot()
    CachedWatershed = OutputSlot()
    FinalSegmentation = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpSeededWatershed, self ).__init__(*args, **kwargs)

        # See setupOutputs for inversion function
        self._opInvertGrayscale = OpPixelOperator( parent=self )
        self._opInvertGrayscale.Input.connect( self.InputImage )
        
        # We assume the membranes predictions are on channel 0
        self._opSelectBoundaryChannel = OpSingleChannelSelector( parent=self )
        self._opSelectBoundaryChannel.Index.setValue(0)
        self._opSelectBoundaryChannel.Input.connect( self.Probabilities )

        # For easier viewing, we invert the pixelwise probability.
        self._opInvertProbability = OpPixelOperator( parent=self )
        self._opInvertProbability.Input.connect( self._opSelectBoundaryChannel.Output )
        self.InvertedProbability.connect( self._opInvertProbability.Output )

        # Produce the mask
        self._opSelectLabel = OpSelectLabel( parent=self )
        self._opSelectLabel.Input.connect( self.UndersegmentedLabels )
        self._opSelectLabel.SelectedLabel.connect( self.SplittingLabelId )
        self.SelectedMask.connect( self._opSelectLabel.Output )

        # Watershed        
        self._opMaskedWatershed = OpMaskedWatershed( parent=self )
        self._opMaskedWatershed.Mask.connect( self._opSelectLabel.Output )
        self._opMaskedWatershed.Seeds.connect( self.opLabelArray.Output ) # From superclass member

        # Cache
        self._opCache = OpArrayCache( parent=self )
        self._opCache.fixAtCurrent.connect( self.FreezeCache )
        self._opCache.Input.connect( self._opMaskedWatershed.Output )
        self._opCache.name = "watershed-cache"

        # Watershed output
        self.CachedWatershed.connect( self._opCache.Output )        

        def relabel_watershed_output(a):
            available_ids = self.AvailableLabelIds.value
            watershed_labels = range(1, len(available_ids), 1)
            mapping = dict( zip( watershed_labels, available_ids ) )
            return update_labels( a, mapping )
        self._opRelabel = OpPixelOperator( parent=self )
        self._opRelabel.Function.setValue( relabel_watershed_output )
        self._opRelabel.Input.connect( self._opCache.Output )

        # Produce a new image in which the
        def replace_body( ( original, new ) ):
            return numpy.where( new, new, original )
        self._opReplaceBody = OpMultiArrayMerger( parent=self )
        self._opReplaceBody.MergingFunction.setValue( replace_body )
        self._opReplaceBody.Inputs.resize(2)
        self._opReplaceBody.Inputs[0].connect( self.UndersegmentedLabels )
        self._opReplaceBody.Inputs[1].connect( self._opRelabel.Output )

        # Final segmentation output
        self.FinalSegmentation.connect( self._opReplaceBody.Output )

    def setupOutputs(self):
        assert self.InputImage.meta.getAxisKeys() == list('txyzc'),\
            "This applet assumes that all slots are 5D txyzc"
        self._opCache.blockShape.setValue( self.InputImage.meta.shape )
        super( OpSeededWatershed, self ).setupOutputs()

        # Set up the grayscale inversion function
        grayscale_drange = self._opInvertGrayscale.Input.meta.drange
        assert grayscale_drange[0] == 0
        def invert_grayscale(a):
            a[:] = grayscale_drange[1] - a
            return a
        self._opInvertGrayscale.Function.setValue( invert_grayscale )
        
        # Set up the probability inversion function
        probability_drange = self._opInvertProbability.Input.meta.drange
        assert probability_drange[0] == 0.0
        def invert_probability(a):
            a[:] = probability_drange[1] - a
            return a
        self._opInvertProbability.Function.setValue( invert_probability )
        
        # Switch between using the grayscale and using the pixel probabilities
        ws_source = self.WatershedSource.value
        if ws_source == 'grayscale':
            self._opMaskedWatershed.Input.connect( self._opInvertGrayscale.Output )
        elif ws_source == 'probabilities':
            self._opMaskedWatershed.Input.connect( self._opSelectBoundaryChannel.Output )
        else:
            assert False, "Invalid watershed source: {}".format( ws_source )

    def propagateDirty(self, inputSlot, subindex, roi):
        super( OpSeededWatershed, self ).propagateDirty(inputSlot, subindex, roi)
        self.CachedWatershed.setDirty()

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here"

def update_labels( label_img, mapping_update ):
    """
    Given a label_image and a dict of old labels to new labels,
    return a copy of label_image in which labels have been replaced according to the mapping.
    Any labels that are not present in the mapping will remain untouched.
    
    Unlike sklearn.segmentation.relabel_sequential(), this function does not use excessive 
    memory if the image label values happen to be large.
    """
    # Note that numpy.unique() returns a sorted list
    unique_labels = numpy.unique( label_img )
    consecutivized_labels = numpy.searchsorted( unique_labels, label_img )

    mapping_update = collections.OrderedDict( sorted(mapping_update.items()) )

    # We must ensure that mapping_update contains no keys that aren't actually in the image
    unused_update_keys = filter( lambda k: k not in unique_labels,
                                 mapping_update.keys() )
    for key in unused_update_keys:
        del mapping_update[key]

    replacement_indexes = numpy.searchsorted( unique_labels, mapping_update.keys() )
    
    # Replace labels that map to new values
    unique_labels[(replacement_indexes,)] = mapping_update.values()
    return unique_labels[ consecutivized_labels ]

if __name__ == "__main__":
    a = numpy.indices( (5,5) ).sum(0)
    b = replace_labels( a, { 2 : 20, 4 : 40, 500 : -1 } )
    print b
    