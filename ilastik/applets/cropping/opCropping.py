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
from lazyflow.operators import OpCompressedUserCropArray
from ilastik.utility.operatorSubView import OperatorSubView
#from ilastik.utility import OpMultiLaneWrapper

class OpCroppingTopLevel( Operator ):
    """
    Top-level operator for the croppingApplet base class.
    Provides all the slots needed by the cropping GUI, but any operator that provides the necessary slots can also be used with the CroppingGui.
    """
    name = "OpCroppingTopLevel"

    # Input slots
    InputImages = InputSlot(level=1) #: Original input data.
    CropInputs = InputSlot(level=1) #: Input for providing crop data from an external source
    
    CropsAllowedFlags = InputSlot(level=1, stype='bool') #: Specifies which images are permitted to be croped 
    CropEraserValue = InputSlot(value=255) #: The crop value that signifies the 'eraser', i.e. voxels to clear crops from
    CropDelete = InputSlot() #: When this input is set to a value, all crops of that value are deleted from the operator's data.

    # Output slots
    #CropImages = OutputSlot(level=1) #: Stored crops from the user
    NonzeroCropBlocks = OutputSlot(level=1) #: A list if slices that contain non-zero crop values

    CropNames = OutputSlot()
    CropColors = OutputSlot()

    def __init__(self, blockDims = None, *args, **kwargs):
        super( OpCroppingTopLevel, self ).__init__( *args, **kwargs )

        # Use a wrapper to create a cropping operator for each image lane
    #    self.opCropLane = OpMultiLaneWrapper( OpCroppingSingleLane, operator_kwargs={'blockDims' : blockDims}, parent=self )
        self.opCropLane = OpCroppingSingleLane ( parent=self, blockDims=blockDims )

        # Special connection: Crop Input must get its metadata (shape, axistags) from the main input image.
        self.CropInputs.connect( self.InputImages )

        # Connect external inputs -> internal inputs
        self.opCropLane.InputImage.connect( self.InputImages )
        self.opCropLane.CropInput.connect( self.CropInputs )
        self.opCropLane.CropsAllowedFlag.connect( self.CropsAllowedFlags )
        self.opCropLane.CropEraserValue.connect( self.CropEraserValue )
        self.opCropLane.CropDelete.connect( self.CropDelete )

        # Initialize the delete input to -1, which means "no crop".
        # Now changing this input to a positive value will cause crop deletions.
        # (The deleteCrop input is monitored for changes.)
        self.CropDelete.setValue(-1)

        # Connect internal outputs -> external outputs
        #self.CropImages.connect( self.opCropLane.CropImage )
        self.NonzeroCropBlocks.connect( self.opCropLane.NonzeroCropBlocks )

        self.CropColors.setValue( [] )
        self.CropNames.setValue( [] )

    def propagateDirty(self, slot, subindex, roi):
        # Nothing to do here: All outputs are directly connected to 
        #  internal operators that handle their own dirty propagation.
        pass

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass
    
    def setupOutputs(self):
        self.CropNames.meta.dtype = object
        self.CropNames.meta.shape = (1,)

        self.CropColors.meta.dtype = object
        self.CropColors.meta.shape = (1,)

        self.PmapColors.meta.dtype = object
        self.PmapColors.meta.shape = (1,)

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()

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

class OpCroppingSingleLane( Operator ):
    """
    This is a single-lane operator that can be used with the cropping applet gui.
    It is basically a wrapper around the ``OpCompressedUserCropArray`` (lazyflow), 
    with the 'shape' and 'blockshape' input slots taken care of for you.
    """
    name="OpCroppingSingleLane"

    # Input slots
    InputImage = InputSlot() #: Original input data.
    CropInput = InputSlot(optional = True) #: Input for providing crop data from an external source
    
    CropsAllowedFlag = InputSlot(stype='bool') #: Specifies which images are permitted to be croped 
    CropEraserValue = InputSlot(value=255) #: The crop value that signifies the 'eraser', i.e. voxels to clear crops from
    CropDelete = InputSlot(value=-1) #: When this input is set to a value, all crops of that value are deleted from the operator's data.

    # Output slots
    CropImage = OutputSlot() #: Stored crops from the user
    NonzeroCropBlocks = OutputSlot() #: A list if slices that contain non-zero crop values ###xxx check this, not needed

    # These are used in the single-lane case.
    # When using the multi-lane operator (above),
    #  its CropNames and CropColors slots are used instead.    
    CropNames = OutputSlot()
    CropColors = OutputSlot()

    def __init__(self, blockDims = None, *args, **kwargs):
        """
        Instantiate all internal operators and connect them together.
        """
        super(OpCroppingSingleLane, self).__init__( *args, **kwargs )

        # Configuration options
        if blockDims is None:
            blockDims = { 't' : 1, 'x' : 100, 'y' : 100, 'z' : 100, 'c' : 1 } 
        assert isinstance(blockDims, dict)
        self._blockDims = blockDims

        # Create internal operator
        self.opCropArray = OpCompressedUserCropArray( parent=self )
        self.opCropArray.Input.connect( self.CropInput )
        self.opCropArray.eraser.connect(self.CropEraserValue)
        self.opCropArray.deleteCrop.connect(self.CropDelete)
        
        # Connect our internal outputs to our external outputs
        self.CropImage.connect( self.opCropArray.Output )
        self.NonzeroCropBlocks.connect( self.opCropArray.nonzeroBlocks )

        self.CropNames.setValue([])
        self.CropColors.setValue([])

    def setupOutputs(self):
        self.CropNames.meta.dtype = object
        self.CropNames.meta.shape = (1,)
        self.CropColors.meta.dtype = object
        self.CropColors.meta.shape = (1,)
        self.setupCache(self._blockDims)

    def setupCache(self, blockDims):
        # Set the blockshapes for each input image separately, depending on which axistags it has.
        axisOrder = map(lambda tag: tag.key, self.InputImage.meta.axistags )
        
        ## Crop Array blocks
        blockShape = tuple( blockDims[k] for k in axisOrder )
        self.opCropArray.blockShape.setValue( blockShape )

    def cleanUp(self):
        self.CropInput.disconnect()
        super( OpCroppingSingleLane, self ).cleanUp()

    def propagateDirty(self, slot, subindex, roi):
        # Nothing to do here: All outputs are directly connected to 
        #  internal operators that handle their own dirty propagation.
        pass

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

