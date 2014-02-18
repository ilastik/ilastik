# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

import sys
import argparse
import logging
logger = logging.getLogger(__name__)

import numpy

from ilastik.workflow import Workflow

from ilastik.applets.pixelClassification import PixelClassificationApplet, PixelClassificationDataExportApplet
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelectionNoCache
from ilastik.applets.pixelClassification.opPixelClassification import OpPredictionPipelineNoCache

from lazyflow.roi import TinyVector
from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.generic import OpTransposeSlots, OpSelectSubslot

class PixelClassificationWorkflow(Workflow):
    
    workflowName = "Pixel Classification"
    workflowDescription = "This is obviously self-explanatory."
    defaultAppletIndex = 1 # show DataSelection by default
    
    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, shell, headless, workflow_cmdline_args, appendBatchOperators=True, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super( PixelClassificationWorkflow, self ).__init__( shell, headless, graph=graph, *args, **kwargs )
        self._applets = []
        self._workflow_cmdline_args = workflow_cmdline_args

        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right"

        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument('--filter', help="pixel feature filter implementation.", choices=['Original', 'Refactored', 'Interpolated'], default='Original')
        parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)
        self.filter_implementation = parsed_args.filter
        
        # Applets for training (interactive) workflow 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet( self,
                                                        "Input Data",
                                                        "Input Data",
                                                        supportIlastik05Import=True,
                                                        batchDataGui=False,
                                                        instructionText=data_instructions )
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data'] )

        self.featureSelectionApplet = FeatureSelectionApplet(self, "Feature Selection", "FeatureSelections", self.filter_implementation)

        self.pcApplet = PixelClassificationApplet(self, "PixelClassification")
        opClassify = self.pcApplet.topLevelOperator

        self.dataExportApplet = PixelClassificationDataExportApplet(self, "Prediction Export")
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.PmapColors.connect( opClassify.PmapColors )
        opDataExport.LabelNames.connect( opClassify.LabelNames )
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )

        # Expose for shell
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        self._applets.append(self.dataExportApplet)

        self._batch_input_args = None
        self._batch_export_args = None

        self.batchInputApplet = None
        self.batchResultsApplet = None
        if appendBatchOperators:
            # Create applets for batch workflow
            self.batchInputApplet = DataSelectionApplet(self, "Batch Prediction Input Selections", "Batch Inputs", supportIlastik05Import=False, batchDataGui=True)
            self.batchResultsApplet = PixelClassificationDataExportApplet(self, "Batch Prediction Output Locations", isBatch=True)
    
            # Expose in shell        
            self._applets.append(self.batchInputApplet)
            self._applets.append(self.batchResultsApplet)
    
            # Connect batch workflow (NOT lane-based)
            self._initBatchWorkflow()

            if unused_args:
                # We parse the export setting args first.  All remaining args are considered input files by the input applet.
                self._batch_export_args, unused_args = self.batchResultsApplet.parse_known_cmdline_args( unused_args )
                self._batch_input_args, unused_args = self.batchInputApplet.parse_known_cmdline_args( unused_args )
    
        if unused_args:
            logger.warn("Unused command-line args: {}".format( unused_args ))

    def connectLane(self, laneIndex):
        # Get a handle to each operator
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opClassify = self.pcApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)
        
        # Input Image -> Feature Op
        #         and -> Classification Op (for display)
        opTrainingFeatures.InputImage.connect( opData.Image )
        opClassify.InputImages.connect( opData.Image )
        
        # Feature Images -> Classification Op (for training, prediction)
        opClassify.FeatureImages.connect( opTrainingFeatures.OutputImage )
        opClassify.CachedFeatureImages.connect( opTrainingFeatures.CachedOutputImage )
        
        # Training flags -> Classification Op (for GUI restrictions)
        opClassify.LabelsAllowedFlags.connect( opData.AllowLabels )

        # Data Export connections
        opDataExport.RawData.connect( opData.ImageGroup[0] )
        opDataExport.Input.connect( opClassify.HeadlessPredictionProbabilities )
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )
        opDataExport.ConstraintDataset.connect( opData.ImageGroup[0] )

    def _initBatchWorkflow(self):
        """
        Connect the batch-mode top-level operators to the training workflow and to each other.
        """
        # Access applet operators from the training workflow
        opTrainingDataSelection = self.dataSelectionApplet.topLevelOperator
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator
        opClassify = self.pcApplet.topLevelOperator
        
        # Access the batch operators
        opBatchInputs = self.batchInputApplet.topLevelOperator
        opBatchResults = self.batchResultsApplet.topLevelOperator
        
        opBatchInputs.DatasetRoles.connect( opTrainingDataSelection.DatasetRoles )
        
        opSelectFirstLane = OperatorWrapper( OpSelectSubslot, parent=self )
        opSelectFirstLane.Inputs.connect( opTrainingDataSelection.ImageGroup )
        opSelectFirstLane.SubslotIndex.setValue(0)
        
        opSelectFirstRole = OpSelectSubslot( parent=self )
        opSelectFirstRole.Inputs.connect( opSelectFirstLane.Output )
        opSelectFirstRole.SubslotIndex.setValue(0)
        
        opBatchResults.ConstraintDataset.connect( opSelectFirstRole.Output )
        
        ## Create additional batch workflow operators
        opBatchFeatures = OperatorWrapper( OpFeatureSelectionNoCache, operator_kwargs={'filter_implementation': self.filter_implementation}, parent=self, promotedSlotNames=['InputImage'] )
        opBatchPredictionPipeline = OperatorWrapper( OpPredictionPipelineNoCache, parent=self )
        
        ## Connect Operators ##
        opTranspose = OpTransposeSlots( parent=self )
        opTranspose.OutputLength.setValue(1)
        opTranspose.Inputs.connect( opBatchInputs.DatasetGroup )
        
        # Provide dataset paths from data selection applet to the batch export applet
        opBatchResults.RawDatasetInfo.connect( opTranspose.Outputs[0] )
        opBatchResults.WorkingDirectory.connect( opBatchInputs.WorkingDirectory )
        
        # Connect (clone) the feature operator inputs from 
        #  the interactive workflow's features operator (which gets them from the GUI)
        opBatchFeatures.Scales.connect( opTrainingFeatures.Scales )
        opBatchFeatures.FeatureIds.connect( opTrainingFeatures.FeatureIds )
        opBatchFeatures.SelectionMatrix.connect( opTrainingFeatures.SelectionMatrix )
        
        # Classifier and NumClasses are provided by the interactive workflow
        opBatchPredictionPipeline.Classifier.connect( opClassify.Classifier )
        opBatchPredictionPipeline.FreezePredictions.setValue( False )
        opBatchPredictionPipeline.NumClasses.connect( opClassify.NumClasses )
        
        # Provide these for the gui
        opBatchResults.RawData.connect( opBatchInputs.Image )
        opBatchResults.PmapColors.connect( opClassify.PmapColors )
        opBatchResults.LabelNames.connect( opClassify.LabelNames )
        
        # Connect Image pathway:
        # Input Image -> Features Op -> Prediction Op -> Export
        opBatchFeatures.InputImage.connect( opBatchInputs.Image )
        opBatchPredictionPipeline.FeatureImages.connect( opBatchFeatures.OutputImage )
        opBatchResults.Input.connect( opBatchPredictionPipeline.HeadlessPredictionProbabilities )

        # We don't actually need the cached path in the batch pipeline.
        # Just connect the uncached features here to satisfy the operator.
        #opBatchPredictionPipeline.CachedFeatureImages.connect( opBatchFeatures.OutputImage )

        self.opBatchPredictionPipeline = opBatchPredictionPipeline

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        # If no data, nothing else is ready.
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = len(opDataSelection.ImageGroup) > 0 and not self.dataSelectionApplet.busy

        opFeatureSelection = self.featureSelectionApplet.topLevelOperator
        featureOutput = opFeatureSelection.OutputImage
        features_ready = input_ready and \
                         len(featureOutput) > 0 and  \
                         featureOutput[0].ready() and \
                         (TinyVector(featureOutput[0].meta.shape) > 0).all()

        opDataExport = self.dataExportApplet.topLevelOperator
        predictions_ready = features_ready and \
                            len(opDataExport.Input) > 0 and \
                            opDataExport.Input[0].ready() and \
                            (TinyVector(opDataExport.Input[0].meta.shape) > 0).all()

        # Problems can occur if the features or input data are changed during live update mode.
        # Don't let the user do that.
        opPixelClassification = self.pcApplet.topLevelOperator
        live_update_active = not opPixelClassification.FreezePredictions.value

        self._shell.setAppletEnabled(self.dataSelectionApplet, not live_update_active)
        self._shell.setAppletEnabled(self.featureSelectionApplet, input_ready and not live_update_active)
        self._shell.setAppletEnabled(self.pcApplet, features_ready)
        self._shell.setAppletEnabled(self.dataExportApplet, predictions_ready)

        if self.batchInputApplet is not None:
            # Training workflow must be fully configured before batch can be used
            self._shell.setAppletEnabled(self.batchInputApplet, predictions_ready)
    
            opBatchDataSelection = self.batchInputApplet.topLevelOperator
            batch_input_ready = predictions_ready and \
                                len(opBatchDataSelection.ImageGroup) > 0
            self._shell.setAppletEnabled(self.batchResultsApplet, batch_input_ready)
            
        # Lastly, check for certain "busy" conditions, during which we 
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.featureSelectionApplet.busy
        busy |= self.dataExportApplet.busy
        self._shell.enableProjectChanges( not busy )

    def getHeadlessOutputSlot(self, slotId):
        # "Regular" (i.e. with the images that the user selected as input data)
        if slotId == "Predictions":
            return self.pcApplet.topLevelOperator.HeadlessPredictionProbabilities
        elif slotId == "PredictionsUint8":
            return self.pcApplet.topLevelOperator.HeadlessUint8PredictionProbabilities
        # "Batch" (i.e. with the images that the user selected as batch inputs).
        elif slotId == "BatchPredictions":
            return self.opBatchPredictionPipeline.HeadlessPredictionProbabilities
        if slotId == "BatchPredictionsUint8":
            return self.opBatchPredictionPipeline.HeadlessUint8PredictionProbabilities
        
        raise Exception("Unknown headless output slot")
    
    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.
        
        If the user provided command-line arguments, use them to configure 
        the workflow for batch mode and export all results.
        (This workflow's headless mode supports only batch mode for now.)
        """
        # Configure the batch data selection operator.
        if self._batch_input_args and self._batch_input_args.input_files: 
            self.batchInputApplet.configure_operator_with_parsed_args( self._batch_input_args )
        
        # Configure the data export operator.
        if self._batch_export_args:
            self.batchResultsApplet.configure_operator_with_parsed_args( self._batch_export_args )

        if self._headless and self._batch_input_args and self._batch_export_args:
            
            # Make sure we're using the up-to-date classifier.
            self.pcApplet.topLevelOperator.FreezePredictions.setValue(False)
        
            # Now run the batch export and report progress....
            opBatchDataExport = self.batchResultsApplet.topLevelOperator
            for i, opExportDataLaneView in enumerate(opBatchDataExport):
                logger.info( "Exporting result {} to {}".format(i, opExportDataLaneView.ExportPath.value) )
    
                sys.stdout.write( "Result {}/{} Progress: ".format( i, len( opBatchDataExport ) ) )
                sys.stdout.flush()
                def print_progress( progress ):
                    sys.stdout.write( "{} ".format( progress ) )
                    sys.stdout.flush()
    
                # If the operator provides a progress signal, use it.
                slotProgressSignal = opExportDataLaneView.progressSignal
                slotProgressSignal.subscribe( print_progress )
                opExportDataLaneView.run_export()
                
                # Finished.
                sys.stdout.write("\n")

