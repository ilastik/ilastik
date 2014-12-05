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
import os
import warnings
import argparse
import csv

import numpy
import h5py

from ilastik.workflow import Workflow
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.applets.pixelClassification.opPixelClassification import OpPredictionPipeline
from ilastik.applets.thresholdTwoLevels import ThresholdTwoLevelsApplet, OpThresholdTwoLevels
from ilastik.applets.objectExtraction import ObjectExtractionApplet
from ilastik.applets.objectClassification import ObjectClassificationApplet, ObjectClassificationDataExportApplet
from ilastik.applets.fillMissingSlices import FillMissingSlicesApplet
from ilastik.applets.fillMissingSlices.opFillMissingSlices import OpFillMissingSlicesNoCache
from ilastik.applets.blockwiseObjectClassification import BlockwiseObjectClassificationApplet, OpBlockwiseObjectClassification

from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.generic import OpTransposeSlots, OpSelectSubslot
from lazyflow.operators.valueProviders import OpAttributeSelector
from lazyflow.roi import TinyVector
from lazyflow.utility import PathComponents

import logging
logger = logging.getLogger(__name__)

EXPORT_SELECTION_PREDICTIONS = 0
EXPORT_SELECTION_PROBABILITIES = 1
EXPORT_SELECTION_PIXEL_PROBABILITIES = 2

# Constants for pointcloud generation on cluster
CSV_FORMAT = { 'delimiter' : '\t', 'lineterminator' : '\n' }
OUTPUT_COLUMNS = ["x_px", "y_px", "z_px", 
                  "size_px", 
                  "min_x_px", "min_y_px", "min_z_px", 
                  "max_x_px", "max_y_px", "max_z_px"]


class ObjectClassificationWorkflow(Workflow):
    workflowName = "Object Classification Workflow Base"
    defaultAppletIndex = 1 # show DataSelection by default

    def __init__(self, shell, headless,
                 workflow_cmdline_args,
                 project_creation_args,
                 *args, **kwargs):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs:
            del kwargs['graph']
        super(ObjectClassificationWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)

        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument('--fillmissing', help="use 'fill missing' applet with chosen detection method", choices=['classic', 'svm', 'none'], default='none')
        parser.add_argument('--filter', help="pixel feature filter implementation.", choices=['Original', 'Refactored', 'Interpolated'], default='Original')
        parser.add_argument('--nobatch', help="do not append batch applets", action='store_true', default=False)
        
        parsed_creation_args, unused_args = parser.parse_known_args(project_creation_args)

        self.fillMissing = parsed_creation_args.fillmissing
        self.filter_implementation = parsed_creation_args.filter

        parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)
        if parsed_args.fillmissing != 'none' and parsed_creation_args.fillmissing != parsed_args.fillmissing:
            logger.error( "Ignoring --fillmissing cmdline arg.  Can't specify a different fillmissing setting after the project has already been created." )
        
        if parsed_args.filter != 'Original' and parsed_creation_args.filter != parsed_args.filter:
            logger.error( "Ignoring --filter cmdline arg.  Can't specify a different filter setting after the project has already been created." )

        self.batch = not parsed_args.nobatch

        self._applets = []

        self.projectMetadataApplet = ProjectMetadataApplet()
        self._applets.append(self.projectMetadataApplet)

        self.setupInputs()
        
        if self.fillMissing != 'none':
            self.fillMissingSlicesApplet = FillMissingSlicesApplet(
                self, "Fill Missing Slices", "Fill Missing Slices", self.fillMissing)
            self._applets.append(self.fillMissingSlicesApplet)

        if isinstance(self, ObjectClassificationWorkflowPixel):
            self.input_types = 'raw'
        elif isinstance(self, ObjectClassificationWorkflowBinary):
            self.input_types = 'raw+binary'
        elif isinstance( self, ObjectClassificationWorkflowPrediction ):
            self.input_types = 'raw+pmaps'
        
        # our main applets
        self.objectExtractionApplet = ObjectExtractionApplet(workflow=self, name = "Object Feature Selection")
        self.objectClassificationApplet = ObjectClassificationApplet(workflow=self)
        self.dataExportApplet = ObjectClassificationDataExportApplet(self, "Object Prediction Export")
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect( self.dataSelectionApplet.topLevelOperator.WorkingDirectory )
        
        # See EXPORT_SELECTION_PREDICTIONS and EXPORT_SELECTION_PROBABILITIES, above
        opDataExport.SelectionNames.setValue( ['Object Predictions', 'Object Probabilities'] )        
        if self.input_types == 'raw':
            # Re-configure to add the pixel probabilities option
            # See EXPORT_SELECTION_PIXEL_PROBABILITIES, above
            opDataExport.SelectionNames.setValue( ['Object Predictions', 'Object Probabilities', 'Pixel Probabilities'] )

        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.objectClassificationApplet)
        self._applets.append(self.dataExportApplet)

        if self.batch:
            self.dataSelectionAppletBatch = DataSelectionApplet(
                    self, "Batch Inputs", "Batch Inputs", batchDataGui=True)
            self.opDataSelectionBatch = self.dataSelectionAppletBatch.topLevelOperator
            
            if self.input_types == 'raw':
                self.opDataSelectionBatch.DatasetRoles.setValue(['Raw Data'])
            elif self.input_types == 'raw+binary':
                self.opDataSelectionBatch.DatasetRoles.setValue(['Raw Data', 'Binary Data'])
            elif self.input_types == 'raw+pmaps':
                self.opDataSelectionBatch.DatasetRoles.setValue(['Raw Data', 'Prediction Maps'])
            else:
                assert False, "Unknown object classification subclass type."
    
            self.blockwiseObjectClassificationApplet = BlockwiseObjectClassificationApplet(
                self, "Blockwise Object Classification", "Blockwise Object Classification")
            self._applets.append(self.blockwiseObjectClassificationApplet)

            self.batchExportApplet = ObjectClassificationDataExportApplet(
                self, "Batch Object Prediction Export", isBatch=True)
        
            opBatchDataExport = self.batchExportApplet.topLevelOperator
            opBatchDataExport.WorkingDirectory.connect( self.dataSelectionApplet.topLevelOperator.WorkingDirectory )

            self._applets.append(self.dataSelectionAppletBatch)
            self._applets.append(self.batchExportApplet)

            self._initBatchWorkflow()

            self._batch_export_args = None
            self._batch_input_args = None
            if unused_args:
                # Additional export args (specific to the object classification workflow)
                export_arg_parser = argparse.ArgumentParser()
                export_arg_parser.add_argument( "--table_filename", help="The location to export the object feature/prediction CSV file.", required=False )
                export_arg_parser.add_argument( "--export_object_prediction_img", action="store_true" )
                export_arg_parser.add_argument( "--export_object_probability_img", action="store_true" )

                # TODO: Support this, too, someday?
                #export_arg_parser.add_argument( "--export_object_label_img", action="store_true" )
                
                if self.input_types == 'raw':
                    export_arg_parser.add_argument( "--export_pixel_probability_img", action="store_true" )
                self._export_args, unused_args = export_arg_parser.parse_known_args(unused_args)

                # We parse the export setting args first.  All remaining args are considered input files by the input applet.
                self._batch_export_args, unused_args = self.batchExportApplet.parse_known_cmdline_args( unused_args )
                self._batch_input_args, unused_args = self.dataSelectionAppletBatch.parse_known_cmdline_args( unused_args )

        if unused_args:
            warnings.warn("Unused command-line args: {}".format( unused_args ))

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def connectLane(self, laneIndex):
        rawslot, binaryslot = self.connectInputs(laneIndex)

        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)

        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        opObjExtraction.RawImage.connect(rawslot)
        opObjExtraction.BinaryImage.connect(binaryslot)

        opObjClassification.RawImages.connect(rawslot)
        opObjClassification.LabelsAllowedFlags.connect(opData.AllowLabels)
        opObjClassification.BinaryImages.connect(binaryslot)

        opObjClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opObjClassification.ObjectFeatures.connect(opObjExtraction.RegionFeatures)
        opObjClassification.ComputedFeatureNames.connect(opObjExtraction.ComputedFeatureNames)

        # Data Export connections
        opDataExport.RawData.connect( opData.ImageGroup[0] )
        opDataExport.RawDatasetInfo.connect( opData.DatasetGroup[0] )
        opDataExport.Inputs.resize(2)
        opDataExport.Inputs[EXPORT_SELECTION_PREDICTIONS].connect( opObjClassification.UncachedPredictionImages )
        opDataExport.Inputs[EXPORT_SELECTION_PROBABILITIES].connect( opObjClassification.ProbabilityChannelImage )
        if self.input_types == 'raw':
            # Append the prediction probabilities to the list of slots that can be exported.
            opDataExport.Inputs.resize(3)
            # Pull from this slot since the data has already been through the Op5 operator
            # (All data in the export operator must have matching spatial dimensions.)
            opThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)
            opDataExport.Inputs[EXPORT_SELECTION_PIXEL_PROBABILITIES].connect( opThreshold.InputImage )

        if self.batch:
            opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)
            opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator.getLane(laneIndex)

            opBlockwiseObjectClassification.RawImage.connect(opObjClassification.RawImages)
            opBlockwiseObjectClassification.BinaryImage.connect(opObjClassification.BinaryImages)
            opBlockwiseObjectClassification.Classifier.connect(opObjClassification.Classifier)
            opBlockwiseObjectClassification.LabelsCount.connect(opObjClassification.NumLabels)
            opBlockwiseObjectClassification.SelectedFeatures.connect(opObjClassification.SelectedFeatures)

    def _initBatchWorkflow(self):
        # Access applet operators from the training workflow
        opObjectTrainingTopLevel = self.objectClassificationApplet.topLevelOperator
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator

        # If we are not in the binary workflow, connect the thresholding operator.
        # Parameter inputs are cloned from the interactive workflow,
        if isinstance(self, ObjectClassificationWorkflowBinary):
            #FIXME
            pass
        else:
            opInteractiveThreshold = self.thresholdingApplet.topLevelOperator
            opBatchThreshold = OperatorWrapper(OpThresholdTwoLevels, parent=self)
            opBatchThreshold.MinSize.connect(opInteractiveThreshold.MinSize)
            opBatchThreshold.MaxSize.connect(opInteractiveThreshold.MaxSize)
            opBatchThreshold.HighThreshold.connect(opInteractiveThreshold.HighThreshold)
            opBatchThreshold.LowThreshold.connect(opInteractiveThreshold.LowThreshold)
            opBatchThreshold.SingleThreshold.connect(opInteractiveThreshold.SingleThreshold)
            opBatchThreshold.SmootherSigma.connect(opInteractiveThreshold.SmootherSigma)
            opBatchThreshold.Channel.connect(opInteractiveThreshold.Channel)
            opBatchThreshold.CurOperator.connect(opInteractiveThreshold.CurOperator)

        # OpDataSelectionGroup.ImageGroup is indexed by [laneIndex][roleIndex],
        # but we need a slot that is indexed by [roleIndex][laneIndex]
        # so we can pass each role to the appropriate slots.
        # We use OpTransposeSlots to do this.
        opBatchInputByRole = OpTransposeSlots( parent=self )
        opBatchInputByRole.Inputs.connect( self.opDataSelectionBatch.ImageGroup )
        opBatchInputByRole.OutputLength.setValue(2)
        
        # Lane-indexed multislot for raw data
        batchInputsRaw = opBatchInputByRole.Outputs[0]
        # Lane-indexed multislot for binary/prediction-map data
        batchInputsOther = opBatchInputByRole.Outputs[1]

        # Connect the blockwise classification operator
        # Parameter inputs are cloned from the interactive workflow,
        opBatchClassify = OperatorWrapper(OpBlockwiseObjectClassification, parent=self,
                                          promotedSlotNames=['RawImage', 'BinaryImage'])
        opBatchClassify.Classifier.connect(opObjectTrainingTopLevel.Classifier)
        opBatchClassify.LabelsCount.connect(opObjectTrainingTopLevel.NumLabels)
        opBatchClassify.SelectedFeatures.connect(opObjectTrainingTopLevel.SelectedFeatures)
        opBatchClassify.BlockShape3dDict.connect(opBlockwiseObjectClassification.BlockShape3dDict)
        opBatchClassify.HaloPadding3dDict.connect(opBlockwiseObjectClassification.HaloPadding3dDict)

        #  but image pathway is from the batch pipeline
        op5Raw = OperatorWrapper(OpReorderAxes, parent=self)
        
        if self.fillMissing != 'none':
            opBatchFillMissingSlices = OperatorWrapper(OpFillMissingSlicesNoCache, parent=self)
            opBatchFillMissingSlices.Input.connect(batchInputsRaw)
            op5Raw.Input.connect(opBatchFillMissingSlices.Output)
        else:
            op5Raw.Input.connect(batchInputsRaw)
        
        
        op5Binary = OperatorWrapper(OpReorderAxes, parent=self)
        if self.input_types != 'raw+binary':
            op5Pred = OperatorWrapper(OpReorderAxes, parent=self)
            op5Pred.Input.connect(batchInputsOther)
            opBatchThreshold.RawInput.connect(op5Raw.Output)
            opBatchThreshold.InputImage.connect(op5Pred.Output)
            op5Binary.Input.connect(opBatchThreshold.Output)
        else:
            op5Binary.Input.connect(batchInputsOther)

        opBatchClassify.RawImage.connect(op5Raw.Output)
        opBatchClassify.BinaryImage.connect(op5Binary.Output)

        self.opBatchClassify = opBatchClassify

        # We need to transpose the dataset group, because it is indexed by [image_index][group_index]
        # But we want it to be indexed by [group_index][image_index] for the RawDatasetInfo connection, below.
        opTransposeDatasetGroup = OpTransposeSlots( parent=self )
        opTransposeDatasetGroup.OutputLength.setValue(1)
        opTransposeDatasetGroup.Inputs.connect( self.opDataSelectionBatch.DatasetGroup )

        # Connect the batch OUTPUT applet
        opBatchExport = self.batchExportApplet.topLevelOperator
        opBatchExport.RawData.connect( batchInputsRaw )
        opBatchExport.RawDatasetInfo.connect( opTransposeDatasetGroup.Outputs[0] )
        
        # See EXPORT_SELECTION_PREDICTIONS and EXPORT_SELECTION_PROBABILITIES, above
        opBatchExport.SelectionNames.setValue( ['Object Predictions', 'Object Probabilities'] )        
        # opBatchResults.Inputs is indexed by [lane][selection],
        # Use OpTranspose to allow connection.
        opTransposeBatchInputs = OpTransposeSlots( parent=self )
        opTransposeBatchInputs.OutputLength.setValue(0)
        opTransposeBatchInputs.Inputs.resize(2)
        opTransposeBatchInputs.Inputs[EXPORT_SELECTION_PREDICTIONS].connect( opBatchClassify.PredictionImage ) # selection 0
        opTransposeBatchInputs.Inputs[EXPORT_SELECTION_PROBABILITIES].connect( opBatchClassify.ProbabilityChannelImage ) # selection 1
        
        # Now opTransposeBatchInputs.Outputs is level-2 indexed by [lane][selection]
        opBatchExport.Inputs.connect( opTransposeBatchInputs.Outputs )

    def onProjectLoaded(self, projectManager):
        if self._headless and self._batch_input_args and self._batch_export_args:
            
            # Check for problems: Is the project file ready to use?
            opObjClassification = self.objectClassificationApplet.topLevelOperator
            if not opObjClassification.Classifier.ready():
                logger.error( "Can't run batch prediction.\n"
                              "Couldn't obtain a classifier from your project file: {}.\n"
                              "Please make sure your project is fully configured with a trained classifier."
                              .format(projectManager.currentProjectPath) )
                return

            # Configure the batch data selection operator.
            if self._batch_input_args and self._batch_input_args.raw_data:
                self.dataSelectionAppletBatch.configure_operator_with_parsed_args( self._batch_input_args )
            
            # Configure the data export operator.
            if self._batch_export_args:
                self.batchExportApplet.configure_operator_with_parsed_args( self._batch_export_args )

            self.opBatchClassify.BlockShape3dDict.disconnect()

            # For each BATCH lane...
            for lane_index, opBatchClassifyView in enumerate(self.opBatchClassify):
                # Force the block size to be the same as image size (1 big block)
                tagged_shape = opBatchClassifyView.RawImage.meta.getTaggedShape()
                try:
                    tagged_shape.pop('t')
                except KeyError:
                    pass
                try:
                    tagged_shape.pop('c')
                except KeyError:
                    pass
                opBatchClassifyView.BlockShape3dDict.setValue( tagged_shape )

                # For now, we force the entire result to be computed as one big block.
                # Force the batch classify op to create an internal pipeline for our block.
                opBatchClassifyView._ensurePipelineExists( (0,0,0,0,0) )
                opSingleBlockClassify = opBatchClassifyView._blockPipelines[(0,0,0,0,0)]

                # Export the images (if any)
                if self.input_types == 'raw':
                    # If pixel probabilities need export, do that first.
                    # (They are needed by the other outputs, anyway)
                    if self._export_args.export_pixel_probability_img:
                        self._export_batch_image( lane_index, EXPORT_SELECTION_PIXEL_PROBABILITIES, 'pixel-probability-img' )
                if self._export_args.export_object_prediction_img:
                    self._export_batch_image( lane_index, EXPORT_SELECTION_PREDICTIONS, 'object-prediction-img' )
                if self._export_args.export_object_probability_img:
                    self._export_batch_image( lane_index, EXPORT_SELECTION_PROBABILITIES, 'object-probability-img' )

                # Export the CSV
                csv_filename = self._export_args.table_filename
                if csv_filename:
                    feature_table = opSingleBlockClassify._opPredict.createExportTable([])
                    if len(self.opBatchClassify) > 1:
                        base, ext = os.path.splitext( csv_filename )
                        csv_filename = base + '-' + str(lane_index) + ext
                    print "Exporting object table for image #{}:\n{}".format( lane_index, csv_filename )
                    self.record_array_to_csv(feature_table, csv_filename)
                
                print "FINISHED."

    def _export_batch_image(self, lane_index, selection_index, selection_name):
        opBatchExport = self.batchExportApplet.topLevelOperator
        opBatchExport.InputSelection.setValue(selection_index)
        opBatchExportView = opBatchExport.getLane(lane_index)

        # Remember this so we can restore it later
        default_output_path = opBatchExport.OutputFilenameFormat.value
        export_path = opBatchExportView.ExportPath.value

        path_comp = PathComponents( export_path, os.getcwd() )
        path_comp.filenameBase += '-' + selection_name
        opBatchExport.OutputFilenameFormat.setValue( path_comp.externalPath )
        
        logger.info( "Exporting {} for image #{} to {}"
                     .format(selection_name, lane_index+1, opBatchExportView.ExportPath.value) )

        sys.stdout.write( "Result {}/{} Progress: "
                          .format( lane_index+1, len( self.opBatchClassify ) ) )
        sys.stdout.flush()
        def print_progress( progress ):
            sys.stdout.write( "{} ".format( progress ) )
            sys.stdout.flush()

        # If the operator provides a progress signal, use it.
        slotProgressSignal = opBatchExportView.progressSignal
        slotProgressSignal.subscribe( print_progress )
        opBatchExportView.run_export()
        
        # Finished.
        sys.stdout.write("\n")
        
        # Restore original format
        opBatchExport.OutputFilenameFormat.setValue( default_output_path )

    def record_array_to_csv(self, record_array, filename):
        """
        Save the given record array to a CSV file.
        """
        # Sort by offset
        with open(filename, 'w') as csv_file:
            sorted_fields = sorted( record_array.dtype.fields.items(), key=lambda (k,v): v[1] )
            field_names = map( lambda (k,v): k, sorted_fields )
            for name in field_names:
                # Remove any commas in the header (this is csv, after all)
                name = name.replace(',', '/')
                csv_file.write(name + ',')
            csv_file.write('\n')
            for row in record_array:
                for name in field_names:
                    csv_file.write(str(row[name]) + ',')
                csv_file.write('\n')

    def getHeadlessOutputSlot(self, slotId):
        if slotId == "BatchPredictionImage":
            return self.opBatchClassify.PredictionImage
        raise Exception("Unknown headless output slot")

    def postprocessClusterSubResult(self, roi, result, blockwise_fileset):
        """
        """
        # TODO: Here, we hard-code to select from the first lane only.
        opBatchClassify = self.opBatchClassify[0]
        
        from lazyflow.utility.io.blockwiseFileset import vectorized_pickle_dumps
        # Assume that roi always starts as a multiple of the blockshape
        block_shape = opBatchClassify.get_blockshape()
        assert all(block_shape == blockwise_fileset.description.sub_block_shape), "block shapes don't match"
        assert all((roi[0] % block_shape) == 0), "Sub-blocks must exactly correspond to the blockwise object classification blockshape"
        sub_block_index = roi[0] / blockwise_fileset.description.sub_block_shape

        sub_block_start = sub_block_index
        sub_block_stop = sub_block_start + 1
        sub_block_roi = (sub_block_start, sub_block_stop)
        
        # FIRST, remove all objects that lie outside the block (i.e. remove the ones in the halo)
        region_features = opBatchClassify.BlockwiseRegionFeatures( *sub_block_roi ).wait()
        region_features_dict = region_features.flat[0]
        region_centers = region_features_dict['Default features']['RegionCenter']

        opBlockPipeline = opBatchClassify._blockPipelines[ tuple(roi[0]) ]

        # Compute the block offset within the image coordinates
        halo_roi = opBlockPipeline._halo_roi

        translated_region_centers = region_centers + halo_roi[0][1:-1]

        # TODO: If this is too slow, vectorize this
        mask = numpy.zeros( region_centers.shape[0], dtype=numpy.bool_ )
        for index, translated_region_center in enumerate(translated_region_centers):
            # FIXME: Here we assume t=0 and c=0
            mask[index] = opBatchClassify.is_in_block( roi[0], (0,) + tuple(translated_region_center) + (0,) )
        
        # Always exclude the first object (it's the background??)
        mask[0] = False
        
        # Remove all 'negative' predictions, emit only 'positive' predictions
        # FIXME: Don't hardcode this?
        POSITIVE_LABEL = 2
        objectwise_predictions = opBlockPipeline.ObjectwisePredictions([]).wait()[0]
        assert objectwise_predictions.shape == mask.shape
        mask[objectwise_predictions != POSITIVE_LABEL] = False

        filtered_features = {}
        for feature_group, feature_dict in region_features_dict.items():
            filtered_group = filtered_features[feature_group] = {}
            for feature_name, feature_array in feature_dict.items():
                filtered_group[feature_name] = feature_array[mask]

        # SECOND, translate from block-local coordinates to global (file) coordinates.
        # Unfortunately, we've got multiple translations to perform here:
        # Coordinates in the region features are relative to their own block INCLUDING HALO,
        #  so we need to add the start of the block-with-halo as an offset.
        # BUT the image itself may be offset relative to the BlockwiseFileset coordinates
        #  (due to the view_origin setting), so we also need to add an offset for that, too

        # Get the image offset relative to the file coordinates
        image_offset = blockwise_fileset.description.view_origin
        
        total_offset_5d = halo_roi[0] + image_offset
        total_offset_3d = total_offset_5d[1:-1]

        filtered_features["Default features"]["RegionCenter"] += total_offset_3d
        filtered_features["Default features"]["Coord<Minimum>"] += total_offset_3d
        filtered_features["Default features"]["Coord<Maximum>"] += total_offset_3d

        # Finally, write the features to hdf5
        h5File = blockwise_fileset.getOpenHdf5FileForBlock( roi[0] )
        if 'pickled_region_features' in h5File:
            del h5File['pickled_region_features']

        # Must use str dtype
        dtype = h5py.new_vlen(str)
        dataset = h5File.create_dataset( 'pickled_region_features', shape=(1,), dtype=dtype )
        pickled_features = vectorized_pickle_dumps(numpy.array((filtered_features,)))
        dataset[0] = pickled_features

        object_centers_xyz = filtered_features["Default features"]["RegionCenter"].astype(int)
        object_min_coords_xyz = filtered_features["Default features"]["Coord<Minimum>"].astype(int)
        object_max_coords_xyz = filtered_features["Default features"]["Coord<Maximum>"].astype(int)
        object_sizes = filtered_features["Default features"]["Count"][:,0].astype(int)

        # Also, write out selected features as a 'point cloud' csv file.
        # (Store the csv file next to this block's h5 file.)
        dataset_directory = blockwise_fileset.getDatasetDirectory(roi[0])
        pointcloud_path = os.path.join( dataset_directory, "block-pointcloud.csv" )
        
        logger.info("Writing to csv: {}".format( pointcloud_path ))
        with open(pointcloud_path, "w") as fout:
            csv_writer = csv.DictWriter(fout, OUTPUT_COLUMNS, **CSV_FORMAT)
            csv_writer.writeheader()
        
            for obj_id in range(len(object_sizes)):
                fields = {}
                fields["x_px"], fields["y_px"], fields["z_px"], = object_centers_xyz[obj_id]
                fields["min_x_px"], fields["min_y_px"], fields["min_z_px"], = object_min_coords_xyz[obj_id]
                fields["max_x_px"], fields["max_y_px"], fields["max_z_px"], = object_max_coords_xyz[obj_id]
                fields["size_px"] = object_sizes[obj_id]

                csv_writer.writerow( fields )
                #fout.flush()
        
        logger.info("FINISHED csv export")

    def handleAppletStateUpdateRequested(self, upstream_ready=False):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        
        This method will be called by the child classes with the result of their
        own applet readyness findings as keyword argument.
        """

        # all workflows have these applets in common:

        # object feature selection
        # object classification
        # object prediction export
        # blockwise classification
        # batch input
        # batch prediction export

        cumulated_readyness = upstream_ready
        self._shell.setAppletEnabled(self.objectExtractionApplet, cumulated_readyness)

        if len(self.objectExtractionApplet.topLevelOperator.ComputedFeatureNames) == 0:
            object_features_ready = False
        else:
            object_features_ready = True
            for slot in self.objectExtractionApplet.topLevelOperator.ComputedFeatureNames:
                object_features_ready = object_features_ready and len(slot.value) > 0
        #object_features_ready = self.objectExtractionApplet.topLevelOperator.RegionFeatures.ready()

        cumulated_readyness = cumulated_readyness and object_features_ready
        self._shell.setAppletEnabled(self.objectClassificationApplet, cumulated_readyness)

        object_classification_ready = \
            self.objectClassificationApplet.predict_enabled

        cumulated_readyness = cumulated_readyness and object_classification_ready
        self._shell.setAppletEnabled(self.dataExportApplet, cumulated_readyness)

        if self.batch:
            object_prediction_ready = True  # TODO is that so?
            cumulated_readyness = cumulated_readyness and object_prediction_ready

            self._shell.setAppletEnabled(self.blockwiseObjectClassificationApplet, cumulated_readyness)
            self._shell.setAppletEnabled(self.dataSelectionAppletBatch, cumulated_readyness)
            self._shell.setAppletEnabled(self.batchExportApplet, cumulated_readyness)

        # Lastly, check for certain "busy" conditions, during which we 
        # should prevent the shell from closing the project.
        #TODO implement
        busy = False
        self._shell.enableProjectChanges( not busy )

    def _inputReady(self, nRoles):
        slot = self.dataSelectionApplet.topLevelOperator.ImageGroup
        if len(slot) > 0:
            input_ready = True
            for sub in slot:
                input_ready = input_ready and \
                    all([sub[i].ready() for i in range(nRoles)])
        else:
            input_ready = False

        return input_ready


class ObjectClassificationWorkflowPixel(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from pixel classification)"
    workflowDisplayName = "Pixel Classification + Object Classification"

    def setupInputs(self):
        data_instructions = 'Use the "Raw Data" tab on the right to load your intensity image(s).'
        
        self.dataSelectionApplet = DataSelectionApplet( self, 
                                                        "Input Data", 
                                                        "Input Data", 
                                                        batchDataGui=False,
                                                        force5d=False, 
                                                        instructionText=data_instructions )
        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(['Raw Data'])

        self.featureSelectionApplet = FeatureSelectionApplet(
            self,
            "Feature Selection",
            "FeatureSelections",
            filter_implementation=self.filter_implementation
        )

        self.pcApplet = PixelClassificationApplet(
            self, "PixelClassification")
        self.thresholdingApplet = ThresholdTwoLevelsApplet(
            self, "Thresholding", "ThresholdTwoLevels")

        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        self._applets.append(self.thresholdingApplet)


    def connectInputs(self, laneIndex):
               
        op5raw = OpReorderAxes(parent=self)
        op5raw.AxisOrder.setValue("txyzc")
        op5pred = OpReorderAxes(parent=self)
        op5pred.AxisOrder.setValue("txyzc")
        op5threshold = OpReorderAxes(parent=self)
        op5threshold.AxisOrder.setValue("txyzc")
        
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opClassify = self.pcApplet.topLevelOperator.getLane(laneIndex)
        opThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)

        if self.fillMissing !='none':
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(opData.Image)
            rawslot = opFillMissingSlices.Output
        else:
            rawslot = opData.Image

        opTrainingFeatures.InputImage.connect(rawslot)

        opClassify.InputImages.connect(rawslot)
        opClassify.LabelsAllowedFlags.connect(opData.AllowLabels)
        opClassify.FeatureImages.connect(opTrainingFeatures.OutputImage)
        opClassify.CachedFeatureImages.connect(opTrainingFeatures.CachedOutputImage)

        op5raw.Input.connect(rawslot)
        op5pred.Input.connect(opClassify.PredictionProbabilities)

        opThreshold.RawInput.connect(op5raw.Output)
        opThreshold.InputImage.connect(op5pred.Output)

        op5threshold.Input.connect(opThreshold.CachedOutput)

        return op5raw.Output, op5threshold.Output

    def _initBatchWorkflow(self):
        
        # If we are in pixel workflow, start from raw data
        # The part below is simply copied from the pixel classification
        
        # Access applet operators from the training workflow
        opPixelTrainingDataSelection = self.dataSelectionApplet.topLevelOperator
        opPixelTrainingFeatures = self.featureSelectionApplet.topLevelOperator
        opPixelClassify = self.pcApplet.topLevelOperator
        
        # Access the batch operators
        opBatchInputs = self.dataSelectionAppletBatch.topLevelOperator
        opBatchExport = self.batchExportApplet.topLevelOperator
        
        opBatchInputs.DatasetRoles.connect( opPixelTrainingDataSelection.DatasetRoles )
        
        opSelectFirstLane = OperatorWrapper( OpSelectSubslot, parent=self )
        opSelectFirstLane.Inputs.connect( opPixelTrainingDataSelection.ImageGroup )
        opSelectFirstLane.SubslotIndex.setValue(0)
        
        opSelectFirstRole = OpSelectSubslot( parent=self )
        opSelectFirstRole.Inputs.connect( opSelectFirstLane.Output )
        opSelectFirstRole.SubslotIndex.setValue(0)
        
        ## Create additional batch workflow operators
        # FIXME: this should take the same filter_implementation as the pixel operator!!!
        opBatchPixelFeatures = OperatorWrapper( OpFeatureSelection, operator_kwargs={'filter_implementation':'Original'}, parent=self, promotedSlotNames=['InputImage'] )
        opBatchPixelPredictionPipeline = OperatorWrapper( OpPredictionPipeline, parent=self )
        
        # Connect (clone) the feature operator inputs from 
        #  the interactive workflow's features operator (which gets them from the GUI)
        opBatchPixelFeatures.Scales.connect( opPixelTrainingFeatures.Scales )
        opBatchPixelFeatures.FeatureIds.connect( opPixelTrainingFeatures.FeatureIds )
        opBatchPixelFeatures.SelectionMatrix.connect( opPixelTrainingFeatures.SelectionMatrix )
        
        # Classifier and LabelsCount are provided by the interactive workflow
        opBatchPixelPredictionPipeline.Classifier.connect( opPixelClassify.Classifier )
        opBatchPixelPredictionPipeline.NumClasses.connect( opPixelClassify.NumClasses )
        opBatchPixelPredictionPipeline.FreezePredictions.setValue( False )
                
        # Connect Image pathway:
        # Input Image -> Features Op -> Prediction Op -> Thresholding
        opBatchPixelFeatures.InputImage.connect( opBatchInputs.Image )
        opBatchPixelPredictionPipeline.FeatureImages.connect( opBatchPixelFeatures.OutputImage )

        # We don't actually need the cached path in the batch pipeline.
        # Just connect the uncached features here to satisfy the operator.
        opBatchPixelPredictionPipeline.CachedFeatureImages.connect( opBatchPixelFeatures.OutputImage ) 
        
        # Now connect the object part
        opObjectTrainingTopLevel = self.objectClassificationApplet.topLevelOperator
        
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator

        op5Raw = OperatorWrapper(OpReorderAxes, parent=self)

        if self.fillMissing != 'none':
            opBatchFillMissingSlices = OperatorWrapper(OpFillMissingSlicesNoCache, parent=self)
            opBatchFillMissingSlices.Input.connect(opBatchInputs.Image)
            op5Raw.Input.connect(opBatchFillMissingSlices.Output)
        else:
            op5Raw.Input.connect(opBatchInputs.Image)
        
        opInteractiveThreshold = self.thresholdingApplet.topLevelOperator
        opBatchThreshold = OperatorWrapper(OpThresholdTwoLevels, parent=self)
        opBatchThreshold.MinSize.connect(opInteractiveThreshold.MinSize)
        opBatchThreshold.MaxSize.connect(opInteractiveThreshold.MaxSize)
        opBatchThreshold.HighThreshold.connect(opInteractiveThreshold.HighThreshold)
        opBatchThreshold.LowThreshold.connect(opInteractiveThreshold.LowThreshold)
        opBatchThreshold.SingleThreshold.connect(opInteractiveThreshold.SingleThreshold)
        opBatchThreshold.SmootherSigma.connect(opInteractiveThreshold.SmootherSigma)
        opBatchThreshold.Channel.connect(opInteractiveThreshold.Channel)
        opBatchThreshold.CurOperator.connect(opInteractiveThreshold.CurOperator)
        
        #  Image pathway is from the batch pipeline
        op5Pred = OperatorWrapper(OpReorderAxes, parent=self)
        op5Pred.Input.connect(opBatchPixelPredictionPipeline.HeadlessPredictionProbabilities)
        op5Binary = OperatorWrapper(OpReorderAxes, parent=self)
        opBatchThreshold.RawInput.connect(op5Raw.Output)
        opBatchThreshold.InputImage.connect(op5Pred.Output)
        op5Binary.Input.connect(opBatchThreshold.Output)
        
        # BATCH outputs are computed BLOCKWISE.
        # Connect the blockwise classification operator
        # Parameter inputs are cloned from the interactive workflow,
        opBatchObjectClassify = OperatorWrapper(OpBlockwiseObjectClassification, parent=self,
                                          promotedSlotNames=['RawImage', 'BinaryImage'])
        opBatchObjectClassify.Classifier.connect(opObjectTrainingTopLevel.Classifier)
        opBatchObjectClassify.LabelsCount.connect(opObjectTrainingTopLevel.NumLabels)
        opBatchObjectClassify.SelectedFeatures.connect(opObjectTrainingTopLevel.SelectedFeatures)
        opBatchObjectClassify.BlockShape3dDict.connect(opBlockwiseObjectClassification.BlockShape3dDict)
        opBatchObjectClassify.HaloPadding3dDict.connect(opBlockwiseObjectClassification.HaloPadding3dDict)        
        
        opBatchObjectClassify.RawImage.connect(op5Raw.Output)
        opBatchObjectClassify.BinaryImage.connect(op5Binary.Output)

        self.opBatchClassify = opBatchObjectClassify

        # We need to transpose the dataset group, because it is indexed by [image_index][group_index]
        # But we want it to be indexed by [group_index][image_index] for the RawDatasetInfo connection, below.
        opTransposeDatasetGroup = OpTransposeSlots( parent=self )
        opTransposeDatasetGroup.OutputLength.setValue(1)
        opTransposeDatasetGroup.Inputs.connect( opBatchInputs.DatasetGroup )

        # Connect the batch OUTPUT applet
        opBatchExport.RawData.connect( opBatchInputs.Image )
        opBatchExport.RawDatasetInfo.connect( opTransposeDatasetGroup.Outputs[0] )

        # See EXPORT_SELECTION_PREDICTIONS, EXPORT_SELECTION_PROBABILITIES, and EXPORT_SELECTION_PIXEL_PROBABILITIES, above
        opBatchExport.SelectionNames.setValue( ['Object Predictions', 'Object Probabilities', 'Pixel Probabilities'] )        
        # opBatchResults.Inputs is indexed by [lane][selection],
        # Use OpTranspose to allow connection.
        opTransposeBatchInputs = OpTransposeSlots( parent=self )
        opTransposeBatchInputs.OutputLength.setValue(0)
        opTransposeBatchInputs.Inputs.resize(3)
        opTransposeBatchInputs.Inputs[EXPORT_SELECTION_PREDICTIONS].connect( opBatchObjectClassify.PredictionImage ) # selection 0
        opTransposeBatchInputs.Inputs[EXPORT_SELECTION_PROBABILITIES].connect( opBatchObjectClassify.ProbabilityChannelImage ) # selection 1
        opTransposeBatchInputs.Inputs[EXPORT_SELECTION_PIXEL_PROBABILITIES].connect( opBatchThreshold.InputImage ) # selection 2 (must use op5'd version)
        
        # Now opTransposeBatchInputs.Outputs is level-2 indexed by [lane][selection]
        opBatchExport.Inputs.connect( opTransposeBatchInputs.Outputs )

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        input_ready = self._inputReady(1)
        cumulated_readyness = input_ready

        opFeatureSelection = self.featureSelectionApplet.topLevelOperator
        featureOutput = opFeatureSelection.OutputImage
        features_ready = len(featureOutput) > 0 and  \
            featureOutput[0].ready() and \
            (TinyVector(featureOutput[0].meta.shape) > 0).all()
        cumulated_readyness = cumulated_readyness and features_ready
        self._shell.setAppletEnabled(self.pcApplet, cumulated_readyness)

        slot = self.pcApplet.topLevelOperator.PredictionProbabilities
        predictions_ready = len(slot) > 0 and \
            slot[0].ready() and \
            (TinyVector(slot[0].meta.shape) > 0).all()

        cumulated_readyness = cumulated_readyness and predictions_ready
        self._shell.setAppletEnabled(self.thresholdingApplet, cumulated_readyness)

        # Problems can occur if the features or input data are changed during live update mode.
        # Don't let the user do that.
        opPixelClassification = self.pcApplet.topLevelOperator
        live_update_active = not opPixelClassification.FreezePredictions.value

        self._shell.setAppletEnabled(self.dataSelectionApplet, not live_update_active)
        self._shell.setAppletEnabled(self.featureSelectionApplet, input_ready and not live_update_active)

        super(ObjectClassificationWorkflowPixel, self).handleAppletStateUpdateRequested(upstream_ready=cumulated_readyness)


class ObjectClassificationWorkflowBinary(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from binary image)"
    workflowDisplayName = "Object Classification [Inputs: Raw Data, Segmentation]"

    def setupInputs(self):
        data_instructions = 'Use the "Raw Data" tab to load your intensity image(s).\n\n'\
                            'Use the "Segmentation Image" tab to load your binary mask image(s).'

        self.dataSelectionApplet = DataSelectionApplet( self,
                                                        "Input Data",
                                                        "Input Data",
                                                        batchDataGui=False,
                                                        force5d=True,
                                                        instructionText=data_instructions )

        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(['Raw Data', 'Segmentation Image'])
        self._applets.append(self.dataSelectionApplet)

    def connectInputs(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        if self.fillMissing != 'none':
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(opData.ImageGroup[0])
            rawslot = opFillMissingSlices.Output
        else:
            rawslot = opData.ImageGroup[0]

        return rawslot, opData.ImageGroup[1]

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        input_ready = self._inputReady(2)

        super(ObjectClassificationWorkflowBinary, self).handleAppletStateUpdateRequested(upstream_ready=input_ready)


class ObjectClassificationWorkflowPrediction(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from prediction image)"
    workflowDisplayName = "Object Classification [Inputs: Raw Data, Pixel Prediction Map]"

    def setupInputs(self):
        data_instructions = 'Use the "Raw Data" tab to load your intensity image(s).\n\n'\
                            'Use the "Prediction Maps" tab to load your pixel-wise probability image(s).'
        
        self.dataSelectionApplet = DataSelectionApplet( self,
                                                        "Input Data",
                                                        "Input Data",
                                                        batchDataGui=False,
                                                        force5d=True,
                                                        instructionText=data_instructions )

        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(['Raw Data', 'Prediction Maps'])
        self._applets.append(self.dataSelectionApplet)

        self.thresholdingApplet = ThresholdTwoLevelsApplet(self, "Threshold and Size Filter", "ThresholdTwoLevels")
        self._applets.append(self.thresholdingApplet)

    def connectInputs(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTwoLevelThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)

        op5raw = OpReorderAxes(parent=self)
        op5raw.AxisOrder.setValue("txyzc")
        op5predictions = OpReorderAxes(parent=self)
        op5predictions.AxisOrder.setValue("txyzc")

        if self.fillMissing != 'none':
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(opData.ImageGroup[0])
            rawslot = opFillMissingSlices.Output
        else:
            rawslot = opData.ImageGroup[0]

        op5raw.Input.connect(rawslot)
        op5predictions.Input.connect(opData.ImageGroup[1])

        opTwoLevelThreshold.RawInput.connect(op5raw.Output)
        opTwoLevelThreshold.InputImage.connect(op5predictions.Output)

        op5Binary = OpReorderAxes(parent=self)
        op5Binary.AxisOrder.setValue("txyzc")
        op5Binary.Input.connect(opTwoLevelThreshold.CachedOutput)

        return op5raw.Output, op5Binary.Output

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        input_ready = self._inputReady(2)
        cumulated_readyness = input_ready
        self._shell.setAppletEnabled(self.thresholdingApplet, cumulated_readyness)

        thresholding_ready = True  # is that so?
        cumulated_readyness = cumulated_readyness and thresholding_ready
        super(ObjectClassificationWorkflowPrediction, self).handleAppletStateUpdateRequested(upstream_ready=cumulated_readyness)


if __name__ == "__main__":
    from sys import argv
    w = ObjectClassificationWorkflow(True, argv)
