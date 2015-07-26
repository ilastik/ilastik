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
import sys
import argparse
from lazyflow.graph import Graph, Operator, OperatorWrapper

from ilastik.workflow import Workflow

from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet

from ilastik.applets.counting import CountingApplet, CountingDataExportApplet
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.applets.counting.opCounting import OpPredictionPipeline

from lazyflow.roi import TinyVector
from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.generic import OpTransposeSlots, OpSelectSubslot

import logging
logger = logging.getLogger(__name__)

class CountingWorkflow(Workflow):
    workflowName = "Cell Density Counting"
    workflowDescription = "This is obviously self-explanatory."
    defaultAppletIndex = 1 # show DataSelection by default

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, appendBatchOperators=True, *args, **kwargs):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super( CountingWorkflow, self ).__init__( shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs )

        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument("--csv-export-file", help="Instead of exporting prediction density images, export total counts to the given csv path.")
        self.parsed_counting_workflow_args, unused_args = parser.parse_known_args(workflow_cmdline_args)

        ######################
        # Interactive workflow
        ######################

        self.projectMetadataApplet = ProjectMetadataApplet()

        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Input Data",
                                                       "Input Data",
                                                       batchDataGui=False,
                                                       force5d=False
                                                      )
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        role_names = ['Raw Data']
        opDataSelection.DatasetRoles.setValue( role_names )

        self.featureSelectionApplet = FeatureSelectionApplet(self,
                                                             "Feature Selection",
                                                             "FeatureSelections")

        #self.pcApplet = PixelClassificationApplet(self, "PixelClassification")
        self.countingApplet = CountingApplet(workflow=self)
        opCounting = self.countingApplet.topLevelOperator

        self.dataExportApplet = CountingDataExportApplet(self, "Density Export", opCounting)
        
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.PmapColors.connect(opCounting.PmapColors)
        opDataExport.LabelNames.connect(opCounting.LabelNames)
        opDataExport.UpperBound.connect(opCounting.UpperBound)
        opDataExport.WorkingDirectory.connect(opDataSelection.WorkingDirectory)
        opDataExport.SelectionNames.setValue( ['Probabilities'] )        

        self._applets = []
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.countingApplet)
        self._applets.append(self.dataExportApplet)


        self._batch_input_args = None
        self._batch_export_args = None

        self.batchInputApplet = None
        self.batchResultsApplet = None

        if appendBatchOperators:
            # Connect batch workflow (NOT lane-based)
            self._initBatchWorkflow()
            if unused_args:
                # We parse the export setting args first.
                # All remaining args are considered input files by the input applet.
                self._batch_export_args, unused_args = self.batchResultsApplet.parse_known_cmdline_args( unused_args )
                self._batch_input_args, unused_args = self.batchInputApplet.parse_known_cmdline_args( unused_args, role_names )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def connectLane(self, laneIndex):
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opCounting = self.countingApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)


        #### connect input image
        opTrainingFeatures.InputImage.connect(opData.Image)

        opCounting.InputImages.connect(opData.Image)
        opCounting.FeatureImages.connect(opTrainingFeatures.OutputImage)
        opCounting.LabelsAllowedFlags.connect(opData.AllowLabels)
        opCounting.CachedFeatureImages.connect( opTrainingFeatures.CachedOutputImage )
        #opCounting.UserLabels.connect(opClassify.LabelImages)
        #opCounting.ForegroundLabels.connect(opObjExtraction.LabelImage)
        opDataExport.Inputs.resize(1)
        opDataExport.Inputs[0].connect( opCounting.HeadlessPredictionProbabilities )
        opDataExport.RawData.connect( opData.ImageGroup[0] )
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )
        opDataExport.ConstraintDataset.connect( opData.ImageGroup[0] )

    def _initBatchWorkflow(self):
        """
        Connect the batch-mode top-level operators to the training workflow and to eachother.
        """
        # Access applet operators from the training workflow
        opTrainingDataSelection = self.dataSelectionApplet.topLevelOperator
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator
        opClassify = self.countingApplet.topLevelOperator
                
        opSelectFirstLane = OperatorWrapper( OpSelectSubslot, parent=self )
        opSelectFirstLane.Inputs.connect( opTrainingDataSelection.ImageGroup )
        opSelectFirstLane.SubslotIndex.setValue(0)
        
        opSelectFirstRole = OpSelectSubslot( parent=self )
        opSelectFirstRole.Inputs.connect( opSelectFirstLane.Output )
        opSelectFirstRole.SubslotIndex.setValue(0)

        ## Create additional batch workflow operators
        opBatchFeatures = OperatorWrapper( OpFeatureSelection, operator_kwargs={'filter_implementation':'Original'}, parent=self, promotedSlotNames=['InputImage'] )
        opBatchPredictionPipeline = OperatorWrapper( OpPredictionPipeline, parent=self )
        
        # Create applets for batch workflow
        self.batchInputApplet = DataSelectionApplet(self, "Batch Prediction Input Selections", "BatchDataSelection", supportIlastik05Import=False, batchDataGui=True)
        self.batchResultsApplet = CountingDataExportApplet(self, "Batch Prediction Output Locations", opBatchPredictionPipeline, isBatch=True)

        # Expose in shell        
        self._applets.append(self.batchInputApplet)
        self._applets.append(self.batchResultsApplet)

        opBatchInputs = self.batchInputApplet.topLevelOperator
        opBatchResults = self.batchResultsApplet.topLevelOperator
        
        opBatchInputs.DatasetRoles.connect( opTrainingDataSelection.DatasetRoles )
        opBatchResults.ConstraintDataset.connect( opSelectFirstRole.Output )
        
        
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
        
        # Classifier and LabelsCount are provided by the interactive workflow
        opBatchPredictionPipeline.Classifier.connect( opClassify.Classifier )
        opBatchPredictionPipeline.MaxLabel.connect( opClassify.MaxLabelValue )
        opBatchPredictionPipeline.FreezePredictions.setValue( False )
        
        # Provide these for the gui
        opBatchResults.RawData.connect( opBatchInputs.Image )
        opBatchResults.PmapColors.connect( opClassify.PmapColors )
        opBatchResults.LabelNames.connect( opClassify.LabelNames )
        opBatchResults.UpperBound.connect( opClassify.UpperBound )
        
        # Connect Image pathway:
        # Input Image -> Features Op -> Prediction Op -> Export
        opBatchFeatures.InputImage.connect( opBatchInputs.Image )
        opBatchPredictionPipeline.FeatureImages.connect( opBatchFeatures.OutputImage )
        
        opBatchResults.SelectionNames.setValue( ['Probabilities'] )        
        # opBatchResults.Inputs is indexed by [lane][selection],
        # Use OpTranspose to allow connection.
        opTransposeBatchInputs = OpTransposeSlots( parent=self )
        opTransposeBatchInputs.OutputLength.setValue(0)
        opTransposeBatchInputs.Inputs.resize(1)
        opTransposeBatchInputs.Inputs[0].connect( opBatchPredictionPipeline.HeadlessPredictionProbabilities ) # selection 0
        
        # Now opTransposeBatchInputs.Outputs is level-2 indexed by [lane][selection]
        opBatchResults.Inputs.connect( opTransposeBatchInputs.Outputs )

        # We don't actually need the cached path in the batch pipeline.
        # Just connect the uncached features here to satisfy the operator.
        opBatchPredictionPipeline.CachedFeatureImages.connect( opBatchFeatures.OutputImage )

        self.opBatchPredictionPipeline = opBatchPredictionPipeline

    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.
        
        If the user provided command-line arguments, use them to configure 
        the workflow for batch mode and export all results.
        (This workflow's headless mode supports only batch mode for now.)
        """
        # Configure the batch data selection operator.
        if self._batch_input_args and (self._batch_input_args.input_files or self._batch_input_args.raw_data):
            self.batchInputApplet.configure_operator_with_parsed_args( self._batch_input_args )
        
        # Configure the data export operator.
        if self._batch_export_args:
            self.batchResultsApplet.configure_operator_with_parsed_args( self._batch_export_args )

        if self._batch_input_args and self.countingApplet.topLevelOperator.classifier_cache._dirty:
            logger.warn("Your project file has no classifier.  "
                        "A new classifier will be trained for this run.")

        if self._headless:
            # In headless mode, let's see the messages from the training operator.
            logging.getLogger("lazyflow.operators.classifierOperators").setLevel(logging.DEBUG)
        
        if self._headless and self._batch_input_args and self._batch_export_args:
            # Make sure we're using the up-to-date classifier.
            self.countingApplet.topLevelOperator.FreezePredictions.setValue(False)

            csv_path = self.parsed_counting_workflow_args.csv_export_file
            if csv_path:
                logger.info( "Exporting Object Counts to {}".format(csv_path) )
                sys.stdout.write("Progress: ")
                sys.stdout.flush()
                def print_progress( progress ):
                    sys.stdout.write( "{:.1f} ".format( progress ) )
                    sys.stdout.flush()

                self.batchResultsApplet.progressSignal.connect(print_progress)
                req = self.batchResultsApplet.prepareExportObjectCountsToCsv( csv_path )
                req.wait()

                # Finished.
                sys.stdout.write("\n")
                sys.stdout.flush()
            else:
                # Now run the batch export and report progress....
                opBatchDataExport = self.batchResultsApplet.topLevelOperator
                for i, opExportDataLaneView in enumerate(opBatchDataExport):
                    logger.info( "Exporting object density image {} to {}".format(i, opExportDataLaneView.ExportPath.value) )
        
                    sys.stdout.write( "Result {}/{} Progress: ".format( i, len( opBatchDataExport ) ) )
                    sys.stdout.flush()
                    def print_progress( progress ):
                        sys.stdout.write( "{:.1f} ".format( progress ) )
                        sys.stdout.flush()
        
                    # If the operator provides a progress signal, use it.
                    slotProgressSignal = opExportDataLaneView.progressSignal
                    slotProgressSignal.subscribe( print_progress )
                    opExportDataLaneView.run_export()
                    
                    # Finished.
                    sys.stdout.write("\n")

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.statusUpdateSignal`
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
                            len(opDataExport.Inputs) > 0 and \
                            opDataExport.Inputs[0][0].ready() and \
                            (TinyVector(opDataExport.Inputs[0][0].meta.shape) > 0).all()

        self._shell.setAppletEnabled(self.featureSelectionApplet, input_ready)
        self._shell.setAppletEnabled(self.countingApplet, features_ready)
        self._shell.setAppletEnabled(self.dataExportApplet, predictions_ready and not self.dataExportApplet.busy)
        
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
