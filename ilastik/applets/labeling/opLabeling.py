###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpCompressedUserLabelArray
from ilastik.utility.operatorSubView import OperatorSubView
from ilastik.utility import OpMultiLaneWrapper

class OpLabelingTopLevel( Operator ):
    """
    Top-level operator for the labelingApplet base class.
    Provides all the slots needed by the labeling GUI, but any operator that provides the necessary slots can also be used with the LabelingGui.
    """
    name = "OpLabelingTopLevel"

    # Input slots
    InputImages = InputSlot(level=1) #: Original input data.
    LabelInputs = InputSlot(level=1) #: Input for providing label data from an external source
    
    LabelsAllowedFlags = InputSlot(level=1, stype='bool') #: Specifies which images are permitted to be labeled 
    LabelEraserValue = InputSlot(value=255) #: The label value that signifies the 'eraser', i.e. voxels to clear labels from
    LabelDelete = InputSlot() #: When this input is set to a value, all labels of that value are deleted from the operator's data.

    # Output slots
    LabelImages = OutputSlot(level=1) #: Stored labels from the user
    NonzeroLabelBlocks = OutputSlot(level=1) #: A list if slices that contain non-zero label values

    LabelNames = OutputSlot()
    LabelColors = OutputSlot()

    def __init__(self, blockDims = None, *args, **kwargs):
        super( OpLabelingTopLevel, self ).__init__( *args, **kwargs )

        # Use a wrapper to create a labeling operator for each image lane
        self.opLabelLane = OpMultiLaneWrapper( OpLabelingSingleLane, operator_kwargs={'blockDims' : blockDims}, parent=self )

        # Special connection: Label Input must get its metadata (shape, axistags) from the main input image.
        self.LabelInputs.connect( self.InputImages )

        # Connect external inputs -> internal inputs
        self.opLabelLane.InputImage.connect( self.InputImages )
        self.opLabelLane.LabelInput.connect( self.LabelInputs )
        self.opLabelLane.LabelsAllowedFlag.connect( self.LabelsAllowedFlags )
        self.opLabelLane.LabelEraserValue.connect( self.LabelEraserValue )
        self.opLabelLane.LabelDelete.connect( self.LabelDelete )

        # Initialize the delete input to -1, which means "no label".
        # Now changing this input to a positive value will cause label deletions.
        # (The deleteLabel input is monitored for changes.)
        self.LabelDelete.setValue(-1)

        # Connect internal outputs -> external outputs
        self.LabelImages.connect( self.opLabelLane.LabelImage )
        self.NonzeroLabelBlocks.connect( self.opLabelLane.NonzeroLabelBlocks )
        
        self.LabelColors.setValue( [] )
        self.LabelNames.setValue( [] )


    def propagateDirty(self, slot, subindex, roi):
        # Nothing to do here: All outputs are directly connected to 
        #  internal operators that handle their own dirty propagation.
        pass

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass
    
    def setupOutputs(self):
        self.LabelNames.meta.dtype = object
        self.LabelNames.meta.shape = (1,)
        self.LabelColors.meta.dtype = object
        self.LabelColors.meta.shape = (1,)

    ###
    # MultiLaneOperatorABC
    ###

    def addLane(self, laneIndex):
        """
        Add an image lane.
        """
        numLanes = len(self.InputImages)
        assert laneIndex == numLanes, "Lanes must be appended"

        # Just resize one of our multi-inputs.
        # The others will resize automatically
        self.InputImages.resize(numLanes+1)

    def removeLane(self, laneIndex, finalLength):
        """
        Remove an image lane.
        """
        numLanes = len(self.InputImages)
        self.InputImages.removeSlot(laneIndex, numLanes-1)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)

class OpLabelingSingleLane( Operator ):
    """
    This is a single-lane operator that can be used with the labeling applet gui.
    It is basically a wrapper around the ``OpCompressedUserLabelArray`` (lazyflow), 
    with the 'shape' and 'blockshape' input slots taken care of for you.
    """
    name="OpLabelingSingleLane"

    # Input slots
    InputImage = InputSlot() #: Original input data.
    LabelInput = InputSlot(optional = True) #: Input for providing label data from an external source
    
    LabelsAllowedFlag = InputSlot(stype='bool') #: Specifies which images are permitted to be labeled 
    LabelEraserValue = InputSlot(value=255) #: The label value that signifies the 'eraser', i.e. voxels to clear labels from
    LabelDelete = InputSlot(value=-1) #: When this input is set to a value, all labels of that value are deleted from the operator's data.

    # Output slots
    LabelImage = OutputSlot() #: Stored labels from the user
    NonzeroLabelBlocks = OutputSlot() #: A list if slices that contain non-zero label values

    # These are used in the single-lane case.
    # When using the multi-lane operator (above),
    #  its LabelNames and LabelColors slots are used instead.    
    LabelNames = OutputSlot()
    LabelColors = OutputSlot()
    
    def __init__(self, blockDims = None, *args, **kwargs):
        """
        Instantiate all internal operators and connect them together.
        """
        super(OpLabelingSingleLane, self).__init__( *args, **kwargs )

        # Configuration options
        if blockDims is None:
            blockDims = { 't' : 1, 'x' : 100, 'y' : 100, 'z' : 100, 'c' : 1 } 
        assert isinstance(blockDims, dict)
        self._blockDims = blockDims

        # Create internal operator
        self.opLabelArray = OpCompressedUserLabelArray( parent=self )
        self.opLabelArray.Input.connect( self.LabelInput )
        self.opLabelArray.eraser.connect(self.LabelEraserValue)
        self.opLabelArray.deleteLabel.connect(self.LabelDelete)
        
        # Connect our internal outputs to our external outputs
        self.LabelImage.connect( self.opLabelArray.Output )
        self.NonzeroLabelBlocks.connect( self.opLabelArray.nonzeroBlocks )
        
        self.LabelNames.setValue([])
        self.LabelColors.setValue([])
        
    def setupOutputs(self):
        self.LabelNames.meta.dtype = object
        self.LabelNames.meta.shape = (1,)
        self.LabelColors.meta.dtype = object
        self.LabelColors.meta.shape = (1,)
        self.setupCache(self._blockDims)

    def setupCache(self, blockDims):
        # Set the blockshapes for each input image separately, depending on which axistags it has.
        axisOrder = map(lambda tag: tag.key, self.InputImage.meta.axistags )
        
        ## Label Array blocks
        blockShape = tuple( blockDims[k] for k in axisOrder )
        self.opLabelArray.blockShape.setValue( blockShape )

    def cleanUp(self):
        self.LabelInput.disconnect()
        super( OpLabelingSingleLane, self ).cleanUp()

    def propagateDirty(self, slot, subindex, roi):
        # Nothing to do here: All outputs are directly connected to 
        #  internal operators that handle their own dirty propagation.
        pass

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

