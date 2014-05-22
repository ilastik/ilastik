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
import warnings

from lazyflow.graph import OperatorWrapper
from ilastik.workflows.objectClassification.objectClassificationWorkflow import ObjectClassificationWorkflowBinary
from ilastik.applets.blockwiseObjectClassification import BlockwiseObjectClassificationApplet, OpBlockwiseObjectClassification, BlockwiseObjectClassificationBatchApplet
from ilastik.applets.dataSelection import DataSelectionApplet

class BlockwiseObjectClassificationWorkflow(ObjectClassificationWorkflowBinary):
    """
    This workflow adds an extra applet to the non-blockwise object classification workflow.
    """
    def __init__( self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs ):
        super( BlockwiseObjectClassificationWorkflow, self ).__init__( shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs )

        ### INTERACTIVE ###

        # Create applet
        self.blockwiseObjectClassificationApplet = BlockwiseObjectClassificationApplet( self, "Blockwise Object Classification", "Blockwise Object Classification" )
        
        # Expose for shell
        self._applets.append(self.blockwiseObjectClassificationApplet)

        ### BATCH ###

        # Create applets for batch workflow
        self.rawBatchInputApplet = DataSelectionApplet( self,
                                                     "Raw Batch Input Selections",
                                                     "RawBatchDataSelection",
                                                     supportIlastik05Import=False,
                                                     batchDataGui=True)

        # Create applets for batch workflow
        self.binaryBatchInputApplet = DataSelectionApplet( self,
                                                     "Binary Batch Input Selections",
                                                     "BinaryBatchDataSelection",
                                                     supportIlastik05Import=False,
                                                     batchDataGui=True)

        self.batchResultsApplet = BlockwiseObjectClassificationBatchApplet(self, "Batch Output Locations")

        # Expose in shell        
        self._applets.append(self.rawBatchInputApplet)
        self._applets.append(self.binaryBatchInputApplet)
        self._applets.append(self.batchResultsApplet)

        # Connect batch workflow (NOT lane-based)
        self._initBatchWorkflow()


    def connectLane(self, laneIndex):
        super( self.__class__, self ).connectLane( laneIndex )

        # Get the correct lane from each operator
        opTrainingTopLevel = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator.getLane(laneIndex)

        # Wire up the pipeline for this lane
        opBlockwiseObjectClassification.RawImage.connect( opTrainingTopLevel.RawImages )
        opBlockwiseObjectClassification.BinaryImage.connect( opTrainingTopLevel.BinaryImages )
        opBlockwiseObjectClassification.Classifier.connect( opTrainingTopLevel.Classifier )
        opBlockwiseObjectClassification.LabelsCount.connect( opTrainingTopLevel.LabelsCount )

    def _initBatchWorkflow(self):
        # Access applet operators from the training workflow
        opTrainingTopLevel = self.objectClassificationApplet.topLevelOperator
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator

        # Access the batch INPUT applets
        opRawBatchInput = self.rawBatchInputApplet.topLevelOperator
        opBinaryBatchInput = self.binaryBatchInputApplet.topLevelOperator
        
        # Connect the blockwise classification operator
        opBatchClassify = OperatorWrapper( OpBlockwiseObjectClassification, parent=self )
        opBatchClassify.RawImage.connect( opRawBatchInput.Image )
        opBatchClassify.BinaryImage.connect( opBinaryBatchInput.Image )
        opBatchClassify.Classifier.connect( opTrainingTopLevel.Classifier )
        opBatchClassify.LabelsCount.connect( opTrainingTopLevel.LabelsCount )
        opBatchClassify.BlockShape3dDict.connect( opBlockwiseObjectClassification.BlockShape3dDict )
        opBatchClassify.HaloPadding3dDict.connect( opBlockwiseObjectClassification.HaloPadding3dDict )
        
        self.opBatchClassify = opBatchClassify
        
        # Connect the batch OUTPUT applet
        opBatchOutput = self.batchResultsApplet.topLevelOperator
        opBatchOutput.DatasetPath.connect( opRawBatchInput.ImageName )
        opBatchOutput.RawImage.connect( opRawBatchInput.Image )
        opBatchOutput.ImageToExport.connect( opBatchClassify.PredictionImage )

    def getHeadlessOutputSlot(self, slotId):
        if slotId == "BatchPredictionImage":
            return self.opBatchClassify.PredictionImage
        
        raise Exception("Unknown headless output slot")
    
