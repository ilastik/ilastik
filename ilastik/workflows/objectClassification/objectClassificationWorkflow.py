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
# 		   http://ilastik.org/license.html
###############################################################################
from abc import abstractmethod
import sys
import os
import enum
import warnings
import argparse
import csv

import numpy
import h5py

from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet, DatasetInfo
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from ilastik.applets.pixelClassification.opPixelClassification import OpPredictionPipeline
from ilastik.applets.thresholdTwoLevels import ThresholdTwoLevelsApplet, OpThresholdTwoLevels
from ilastik.applets.objectExtraction import ObjectExtractionApplet
from ilastik.applets.objectClassification import ObjectClassificationApplet, ObjectClassificationDataExportApplet
from ilastik.applets.objectClassification.opObjectClassification import TableExportingOperator
from ilastik.applets.fillMissingSlices import FillMissingSlicesApplet
from ilastik.applets.fillMissingSlices.opFillMissingSlices import OpFillMissingSlicesNoCache
from ilastik.applets.blockwiseObjectClassification import (
    BlockwiseObjectClassificationApplet,
    OpBlockwiseObjectClassification,
)
from ilastik.applets.batchProcessing import BatchProcessingApplet

from lazyflow.graph import Graph, OperatorWrapper, OutputSlot
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.generic import OpTransposeSlots, OpSelectSubslot
from lazyflow.operators.valueProviders import OpAttributeSelector
from lazyflow.roi import TinyVector
from lazyflow.utility import PathComponents
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key
from ilastik.utility import SlotNameEnum

import logging

logger = logging.getLogger(__name__)

# Constants for pointcloud generation on cluster
CSV_FORMAT = {"delimiter": "\t", "lineterminator": "\n"}
OUTPUT_COLUMNS = [
    "x_px",
    "y_px",
    "z_px",
    "size_px",
    "min_x_px",
    "min_y_px",
    "min_z_px",
    "max_x_px",
    "max_y_px",
    "max_z_px",
]


class ObjectClassificationWorkflow(Workflow):
    workflowName = "Object Classification Workflow Base"
    defaultAppletIndex = 0  # show DataSelection by default

    @property
    def ExportNames(self):
        @enum.unique
        class ExportNames(SlotNameEnum):
            OBJECT_PREDICTIONS = enum.auto()
            OBJECT_PROBABILITIES = enum.auto()
            BLOCKWISE_OBJECT_PREDICTIONS = enum.auto()
            BLOCKWISE_OBJECT_PROBABILITIES = enum.auto()

        return ExportNames

    class InputImageRoles(SlotNameEnum):
        RAW_DATA = enum.auto()
        ATLAS = enum.auto()

    @property
    def data_instructions(self):
        return (
            f'Use the "{self.InputImageRoles.RAW_DATA.displayName}" tab to load your intensity image(s).\n\n'
            f'Use the (optional) "{self.InputImageRoles.ATLAS.displayName}" tab if you want to map your objects to colors in an Atlas image.\n\n'
        )

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        graph = kwargs.pop("graph") if "graph" in kwargs else Graph()
        super().__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)
        self.stored_object_classifier = None

        # Parse workflow-specific command-line args
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--fillmissing",
            help="use 'fill missing' applet with chosen detection method",
            choices=["classic", "svm", "none"],
            default="none",
        )
        parser.add_argument("--nobatch", help="do not append batch applets", action="store_true", default=False)

        parsed_creation_args, unused_args = parser.parse_known_args(project_creation_args)

        self.fillMissing = parsed_creation_args.fillmissing

        parsed_args, unused_args = parser.parse_known_args(workflow_cmdline_args)
        if parsed_args.fillmissing != "none" and parsed_creation_args.fillmissing != parsed_args.fillmissing:
            logger.error(
                "Ignoring --fillmissing cmdline arg.  Can't specify a different fillmissing setting after the project has already been created."
            )

        self.batch = not parsed_args.nobatch

        self._applets = []

        self.createInputApplets()

        if self.fillMissing != "none":
            self.fillMissingSlicesApplet = FillMissingSlicesApplet(
                self, "Fill Missing Slices", "Fill Missing Slices", self.fillMissing
            )
            self._applets.append(self.fillMissingSlicesApplet)

        # our main applets
        self.objectExtractionApplet = ObjectExtractionApplet(workflow=self, name="Object Feature Selection")
        self.objectClassificationApplet = ObjectClassificationApplet(workflow=self)
        self._tableExportingOp = TableExportingOperator(self.objectClassificationApplet.topLevelOperator)
        self.dataExportApplet = ObjectClassificationDataExportApplet(self, "Object Information Export")
        self.dataExportApplet.set_exporting_operator(self._tableExportingOp)

        # Customization hooks
        self.dataExportApplet.prepare_for_entire_export = self.prepare_for_entire_export
        # self.dataExportApplet.prepare_lane_for_export = self.prepare_lane_for_export
        self.dataExportApplet.post_process_lane_export = self.post_process_lane_export
        self.dataExportApplet.post_process_entire_export = self.post_process_entire_export

        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect(self.dataSelectionApplet.topLevelOperator.WorkingDirectory)

        opDataExport.SelectionNames.setValue(self.ExportNames.asDisplayNameList())

        self._batch_export_args = None
        self._batch_input_args = None
        self._export_args = None
        self.batchProcessingApplet = None

        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.objectClassificationApplet)
        self._applets.append(self.dataExportApplet)

        if self.batch:
            self.batchProcessingApplet = BatchProcessingApplet(
                self, "Batch Processing", self.dataSelectionApplet, self.dataExportApplet
            )
            self._applets.append(self.batchProcessingApplet)

            if unused_args:
                exportsArgParser, _ = self.exportsArgParser
                self._export_args, unused_args = exportsArgParser.parse_known_args(unused_args)

                # We parse the export setting args first.  All remaining args are considered input files by the input applet.
                self._batch_export_args, unused_args = self.dataExportApplet.parse_known_cmdline_args(unused_args)
                self._batch_input_args, unused_args = self.batchProcessingApplet.parse_known_cmdline_args(unused_args)

                # For backwards compatibility, translate these special args into the standard syntax
                self._batch_input_args.export_source = self._export_args.export_source

        self.blockwiseObjectClassificationApplet = BlockwiseObjectClassificationApplet(
            self, "Blockwise Object Classification", "Blockwise Object Classification"
        )
        self._applets.append(self.blockwiseObjectClassificationApplet)

        if unused_args:
            logger.warning("Unused command-line args: {}".format(unused_args))

    def createInputApplets(self):
        self.dataSelectionApplet = DataSelectionApplet(
            self,
            "Input Data",
            "Input Data",
            batchDataGui=False,
            forceAxisOrder=["txyzc"],
            instructionText=self.data_instructions,
        )

        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(self.InputImageRoles.asDisplayNameList())
        self._applets.append(self.dataSelectionApplet)

    @property
    def exportsArgParser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--table_filename", help="The location to export the object feature/prediction CSV file.")
        exportImageArgGroup = parser.add_mutually_exclusive_group()
        exportImageArgGroup.add_argument(
            "--export_object_prediction_img",
            dest="export_source",
            action="store_const",
            const=self.ExportNames.OBJECT_PREDICTIONS.displayName,
        )
        exportImageArgGroup.add_argument(
            "--export_object_probability_img",
            dest="export_source",
            action="store_const",
            const=self.ExportNames.OBJECT_PROBABILITIES.displayName,
        )
        return parser, exportImageArgGroup

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def prepareForNewLane(self, laneIndex):
        opObjectClassification = self.objectClassificationApplet.topLevelOperator
        if (
            opObjectClassification.classifier_cache.Output.ready()
            and not opObjectClassification.classifier_cache._dirty
        ):
            self.stored_object_classifier = opObjectClassification.classifier_cache.Output.value
        else:
            self.stored_object_classifier = None

    def handleNewLanesAdded(self):
        """
        If new lanes were added, then we invalidated our classifiers unecessarily.
        Here, we can restore the classifier so it doesn't need to be retrained.
        """
        if self.stored_object_classifier:
            opObjectClassification = self.objectClassificationApplet.topLevelOperator
            opObjectClassification.classifier_cache.forceValue(self.stored_object_classifier)
            # Release reference
            self.stored_object_classifier = None

    def getImageSlot(self, input_role, laneIndex) -> OutputSlot:
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        return opData.ImageGroup[input_role]

    def toDefaultAxisOrder(self, slot):
        return OpReorderAxes(parent=self, AxisOrder="txyzc", Input=slot).Output

    def createRawDataSourceSlot(self, laneIndex, canonicalOrder=True):
        rawslot = self.getImageSlot(self.InputImageRoles.RAW_DATA, laneIndex)
        if self.fillMissing != "none":
            opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
            opFillMissingSlices.Input.connect(rawslot)
            rawslot = opFillMissingSlices.Output

        if canonicalOrder:
            rawslot = self.toDefaultAxisOrder(rawslot)

        return rawslot

    def createAtlasSourceSlot(self, laneIndex):
        rawAtlasSlot = self.getImageSlot(self.InputImageRoles.ATLAS, laneIndex)
        return self.toDefaultAxisOrder(rawAtlasSlot)

    @abstractmethod
    def connectInputs(self, laneIndex):
        pass

    def connectLane(self, laneIndex):
        rawslot, binaryslot = self.connectInputs(laneIndex)
        atlas_slot = self.createAtlasSourceSlot(laneIndex)

        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)

        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator.getLane(laneIndex)

        opObjExtraction.RawImage.connect(rawslot)
        opObjExtraction.BinaryImage.connect(binaryslot)
        opObjExtraction.Atlas.connect(atlas_slot)

        opObjClassification.RawImages.connect(rawslot)
        opObjClassification.BinaryImages.connect(binaryslot)
        opObjClassification.Atlas.connect(atlas_slot)

        opObjClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opObjClassification.ObjectFeatures.connect(opObjExtraction.RegionFeatures)
        opObjClassification.ComputedFeatureNames.connect(opObjExtraction.Features)

        # Data Export connections
        opDataExport.RawData.connect(opData.ImageGroup[self.InputImageRoles.RAW_DATA])
        opDataExport.RawDatasetInfo.connect(opData.DatasetGroup[self.InputImageRoles.RAW_DATA])
        opDataExport.Inputs.resize(len(self.ExportNames))
        opDataExport.Inputs[self.ExportNames.OBJECT_PREDICTIONS].connect(opObjClassification.UncachedPredictionImages)
        opDataExport.Inputs[self.ExportNames.OBJECT_PROBABILITIES].connect(opObjClassification.ProbabilityChannelImage)
        opDataExport.Inputs[self.ExportNames.BLOCKWISE_OBJECT_PREDICTIONS].connect(
            opBlockwiseObjectClassification.PredictionImage
        )
        opDataExport.Inputs[self.ExportNames.BLOCKWISE_OBJECT_PROBABILITIES].connect(
            opBlockwiseObjectClassification.ProbabilityChannelImage
        )

        opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)
        opBlockwiseObjectClassification = self.blockwiseObjectClassificationApplet.topLevelOperator.getLane(laneIndex)

        opBlockwiseObjectClassification.RawImage.connect(opObjClassification.RawImages)
        opBlockwiseObjectClassification.BinaryImage.connect(opObjClassification.BinaryImages)
        opBlockwiseObjectClassification.Classifier.connect(opObjClassification.Classifier)
        opBlockwiseObjectClassification.LabelsCount.connect(opObjClassification.NumLabels)
        opBlockwiseObjectClassification.SelectedFeatures.connect(opObjClassification.SelectedFeatures)

    def onProjectLoaded(self, projectManager):
        if not self._headless:
            return

        if not (self._batch_input_args and self._batch_export_args):
            logger.warning("Was not able to understand the batch mode command-line arguments.")

        # Check for problems: Is the project file ready to use?
        opObjClassification = self.objectClassificationApplet.topLevelOperator
        if not opObjClassification.Classifier.ready():
            logger.error(
                "Can't run batch prediction.\n"
                "Couldn't obtain a classifier from your project file: {}.\n"
                "Please make sure your project is fully configured with a trained classifier.".format(
                    projectManager.currentProjectPath
                )
            )
            return

        # Configure the data export operator.
        if self._batch_export_args:
            self.dataExportApplet.configure_operator_with_parsed_args(self._batch_export_args)

        if self._export_args:
            csv_filename = self._export_args.table_filename
            if csv_filename:
                # The user wants to override the csv export location via
                #  the command-line arguments. Apply the new setting to the operator.
                settings, selected_features = (
                    self.objectClassificationApplet.topLevelOperator.get_table_export_settings()
                )
                if settings is None:
                    raise RuntimeError(
                        "You can't export the CSV object table unless you configure it in the GUI first."
                    )
                assert (
                    "file path" in settings
                ), "Expected settings dict to contain a 'file path' key.  Did you rename that key?"
                settings["file path"] = csv_filename
                self.objectClassificationApplet.topLevelOperator.configure_table_export_settings(
                    settings, selected_features
                )

        # Configure the batch data selection operator.
        if self._batch_input_args and self._batch_input_args.raw_data:
            logger.info("Beginning Batch Processing")
            self.batchProcessingApplet.run_export_from_parsed_args(self._batch_input_args)
            logger.info("Completed Batch Processing")

    def prepare_for_entire_export(self):
        # Un-freeze the workflow so we don't just get a bunch of zeros from the caches when we ask for results
        self.oc_freeze_status = self.objectClassificationApplet.topLevelOperator.FreezePredictions.value
        self.objectClassificationApplet.topLevelOperator.FreezePredictions.setValue(False)

    def post_process_entire_export(self):
        # Unfreeze.
        self.objectClassificationApplet.topLevelOperator.FreezePredictions.setValue(self.oc_freeze_status)

    def post_process_lane_export(self, lane_index):
        # FIXME: This probably only works for the non-blockwise export slot.
        #        We should assert that the user isn't using the blockwise slot.
        settings, selected_features = self._tableExportingOp.get_table_export_settings()
        if settings:
            raw_dataset_info = self.dataSelectionApplet.topLevelOperator.DatasetGroup[lane_index][
                self.InputImageRoles.RAW_DATA
            ].value
            if raw_dataset_info.is_in_filesystem():
                filename_suffix = raw_dataset_info.nickname
            else:
                filename_suffix = str(lane_index)
            req = self._tableExportingOp.export_object_data(
                lane_index,
                # FIXME: Even in non-headless mode, we can't show the gui because we're running in a non-main thread.
                #        That's not a huge deal, because there's still a progress bar for the overall export.
                show_gui=False,
                filename_suffix=filename_suffix,
            )
            req.wait()

    def getHeadlessOutputSlot(self, slotId):
        if slotId == "BatchPredictionImage":
            return self.opBatchClassify.PredictionImage
        raise Exception("Unknown headless output slot")

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

        self._shell.setAppletEnabled(self.dataSelectionApplet, not self.batchProcessingApplet.busy)

        cumulated_readyness = upstream_ready
        cumulated_readyness &= (
            not self.batchProcessingApplet.busy
        )  # Nothing can be touched while batch mode is executing.

        self._shell.setAppletEnabled(self.objectExtractionApplet, cumulated_readyness)

        object_features_ready = (
            self.objectExtractionApplet.topLevelOperator.Features.ready()
            and len(self.objectExtractionApplet.topLevelOperator.Features.value) > 0
        )
        cumulated_readyness = cumulated_readyness and object_features_ready
        self._shell.setAppletEnabled(self.objectClassificationApplet, cumulated_readyness)

        opObjectClassification = self.objectClassificationApplet.topLevelOperator
        invalid_classifier = (
            opObjectClassification.classifier_cache.fixAtCurrent.value
            and opObjectClassification.classifier_cache.Output.ready()
            and opObjectClassification.classifier_cache.Output.value is None
        )

        invalid_classifier |= not opObjectClassification.NumLabels.ready() or opObjectClassification.NumLabels.value < 2

        object_classification_ready = object_features_ready and not invalid_classifier

        cumulated_readyness = cumulated_readyness and object_classification_ready
        self._shell.setAppletEnabled(self.dataExportApplet, cumulated_readyness)

        if self.batch:
            object_prediction_ready = True  # TODO is that so?
            cumulated_readyness = cumulated_readyness and object_prediction_ready

            self._shell.setAppletEnabled(self.blockwiseObjectClassificationApplet, cumulated_readyness)
            self._shell.setAppletEnabled(self.batchProcessingApplet, cumulated_readyness)

        # Lastly, check for certain "busy" conditions, during which we
        # should prevent the shell from closing the project.
        # TODO implement
        busy = False
        self._shell.enableProjectChanges(not busy)

    def _inputReady(self):
        image_group_slot = self.dataSelectionApplet.topLevelOperator.ImageGroup
        for input_lane_slot in image_group_slot:
            for role in self.InputImageRoles:
                if role == self.InputImageRoles.ATLAS:
                    continue
                if not input_lane_slot[role].ready():
                    return False
        return bool(len(image_group_slot))

    def postprocessClusterSubResult(self, roi, result, blockwise_fileset):
        """
        This function is only used by special cluster scripts.

        When the batch-processing mechanism was rewritten, this function broke.
        It could probably be fixed with minor changes.
        """
        assert sys.version_info.major == 2, (
            "Alert! This function has not been "
            "tested under python 3. Please remove this assertion, and be wary of any "
            "strange behavior you encounter"
        )

        # TODO: Here, we hard-code to select from the first lane only.
        opBatchClassify = self.opBatchClassify[0]

        from lazyflow.utility.io_uti.blockwiseFileset import vectorized_pickle_dumps

        # Assume that roi always starts as a multiple of the blockshape
        block_shape = opBatchClassify.get_blockshape()
        assert all(block_shape == blockwise_fileset.description.sub_block_shape), "block shapes don't match"
        assert all(
            (roi[0] % block_shape) == 0
        ), "Sub-blocks must exactly correspond to the blockwise object classification blockshape"
        sub_block_index = roi[0] // blockwise_fileset.description.sub_block_shape

        sub_block_start = sub_block_index
        sub_block_stop = sub_block_start + 1
        sub_block_roi = (sub_block_start, sub_block_stop)

        # FIRST, remove all objects that lie outside the block (i.e. remove the ones in the halo)
        region_features = opBatchClassify.BlockwiseRegionFeatures(*sub_block_roi).wait()
        region_features_dict = region_features.flat[0]
        region_centers = region_features_dict[default_features_key]["RegionCenter"]

        opBlockPipeline = opBatchClassify._blockPipelines[tuple(roi[0])]

        # Compute the block offset within the image coordinates
        halo_roi = opBlockPipeline._halo_roi

        translated_region_centers = region_centers + halo_roi[0][1:-1]

        # TODO: If this is too slow, vectorize this
        mask = numpy.zeros(region_centers.shape[0], dtype=numpy.bool_)
        for index, translated_region_center in enumerate(translated_region_centers):
            # FIXME: Here we assume t=0 and c=0
            mask[index] = opBatchClassify.is_in_block(roi[0], (0,) + tuple(translated_region_center) + (0,))

        # Always exclude the first object (it's the background??)
        mask[0] = False

        # Remove all 'negative' predictions, emit only 'positive' predictions
        # FIXME: Don't hardcode this?
        POSITIVE_LABEL = 2
        objectwise_predictions = opBlockPipeline.ObjectwisePredictions([]).wait()[0]
        assert objectwise_predictions.shape == mask.shape
        mask[objectwise_predictions != POSITIVE_LABEL] = False

        filtered_features = {}
        for feature_group, feature_dict in list(region_features_dict.items()):
            filtered_group = filtered_features[feature_group] = {}
            for feature_name, feature_array in list(feature_dict.items()):
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

        filtered_features[default_features_key]["RegionCenter"] += total_offset_3d
        filtered_features[default_features_key]["Coord<Minimum>"] += total_offset_3d
        filtered_features[default_features_key]["Coord<Maximum>"] += total_offset_3d

        # Finally, write the features to hdf5
        h5File = blockwise_fileset.getOpenHdf5FileForBlock(roi[0])
        if "pickled_region_features" in h5File:
            del h5File["pickled_region_features"]

        # Must use str dtype
        dtype = h5py.new_vlen(str)
        dataset = h5File.create_dataset("pickled_region_features", shape=(1,), dtype=dtype)
        pickled_features = vectorized_pickle_dumps(numpy.array((filtered_features,)))
        dataset[0] = pickled_features

        object_centers_xyz = filtered_features[default_features_key]["RegionCenter"].astype(int)
        object_min_coords_xyz = filtered_features[default_features_key]["Coord<Minimum>"].astype(int)
        object_max_coords_xyz = filtered_features[default_features_key]["Coord<Maximum>"].astype(int)
        object_sizes = filtered_features[default_features_key]["Count"][:, 0].astype(int)

        # Also, write out selected features as a 'point cloud' csv file.
        # (Store the csv file next to this block's h5 file.)
        dataset_directory = blockwise_fileset.getDatasetDirectory(roi[0])
        pointcloud_path = os.path.join(dataset_directory, "block-pointcloud.csv")

        logger.info("Writing to csv: {}".format(pointcloud_path))
        with open(pointcloud_path, "w") as fout:
            csv_writer = csv.DictWriter(fout, OUTPUT_COLUMNS, **CSV_FORMAT)
            csv_writer.writeheader()

            for obj_id in range(len(object_sizes)):
                fields = {}
                fields["x_px"], fields["y_px"], fields["z_px"], = object_centers_xyz[obj_id]
                fields["min_x_px"], fields["min_y_px"], fields["min_z_px"], = object_min_coords_xyz[obj_id]
                fields["max_x_px"], fields["max_y_px"], fields["max_z_px"], = object_max_coords_xyz[obj_id]
                fields["size_px"] = object_sizes[obj_id]

                csv_writer.writerow(fields)
                # fout.flush()

        logger.info("FINISHED csv export")


class ObjectClassificationWorkflowPixel(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from pixel classification)"
    workflowDisplayName = "Pixel Classification + Object Classification"

    @property
    def ExportNames(self):
        class ExtraExportNames(SlotNameEnum):
            PIXEL_PROBABILITIES = super(self.__class__, self).ExportNames.getNext()

        return super().ExportNames.extendedWithEnum(ExtraExportNames)

    def __init__(self, *args, **kwargs):
        self.stored_pixel_classifier = None
        super().__init__(*args, **kwargs)

    @property
    def exportsArgParser(self):
        parser, exportImageArgGroup = super().exportsArgParser
        exportImageArgGroup.add_argument(
            "--export_pixel_probability_img",
            dest="export_source",
            action="store_const",
            const=self.ExportNames.PIXEL_PROBABILITIES.displayName,
        )
        return parser, exportImageArgGroup

    def prepareForNewLane(self, laneIndex):
        opPixelClassification = self.pcApplet.topLevelOperator
        if opPixelClassification.classifier_cache.Output.ready() and not opPixelClassification.classifier_cache._dirty:
            self.stored_pixel_classifier = opPixelClassification.classifier_cache.Output.value
        else:
            self.stored_pixel_classifier = None
        super().prepareForNewLane(laneIndex)

    def handleNewLanesAdded(self):
        # If we have stored classifiers, restore them into the workflow now.
        if self.stored_pixel_classifier:
            opPixelClassification = self.pcApplet.topLevelOperator
            opPixelClassification.classifier_cache.forceValue(self.stored_pixel_classifier)
            # Release reference
            self.stored_pixel_classifier = None
        super().handleNewLanesAdded()

    def prepare_for_entire_export(self):
        self.pc_freeze_status = self.pcApplet.topLevelOperator.FreezePredictions.value
        self.pcApplet.topLevelOperator.FreezePredictions.setValue(False)
        super().prepare_for_entire_export()

    def post_process_entire_export(self):
        self.pcApplet.topLevelOperator.FreezePredictions.setValue(self.pc_freeze_status)
        super().post_process_entire_export()

    def connectLane(self, laneIndex):
        super().connectLane(laneIndex)
        # Append the prediction probabilities to the list of slots that can be exported.
        # Pull from this slot since the data has already been through the Op5 operator
        # (All data in the export operator must have matching spatial dimensions.)
        opThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)
        opDataExport.Inputs[self.ExportNames.PIXEL_PROBABILITIES].connect(opThreshold.InputImage)

    def createInputApplets(self):
        super().createInputApplets()

        self.featureSelectionApplet = FeatureSelectionApplet(self, "Feature Selection", "FeatureSelections")

        self.pcApplet = PixelClassificationApplet(self, "PixelClassification")
        self.thresholdingApplet = ThresholdTwoLevelsApplet(self, "Thresholding", "ThresholdTwoLevels")

        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        self._applets.append(self.thresholdingApplet)

        if not self._headless:
            self._shell.currentAppletChanged.connect(self.handle_applet_changed)

    def connectInputs(self, laneIndex):
        ## Access applet operators
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opClassify = self.pcApplet.topLevelOperator.getLane(laneIndex)
        opThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)

        rawslot = self.createRawDataSourceSlot(laneIndex, canonicalOrder=False)
        atlas_slot = self.createAtlasSourceSlot(laneIndex)

        opTrainingFeatures.InputImage.connect(rawslot)

        opClassify.InputImages.connect(rawslot)
        opClassify.PredictionMasks.connect(atlas_slot)
        opClassify.FeatureImages.connect(opTrainingFeatures.OutputImage)
        opClassify.CachedFeatureImages.connect(opTrainingFeatures.CachedOutputImage)

        op5raw = OpReorderAxes(parent=self, AxisOrder="txyzc", Input=rawslot)
        op5pred = OpReorderAxes(parent=self, AxisOrder="txyzc", Input=opClassify.CachedPredictionProbabilities)

        opThreshold.RawInput.connect(op5raw.Output)
        opThreshold.InputImage.connect(op5pred.Output)
        opThreshold.InputChannelColors.connect(opClassify.PmapColors)

        op5threshold = OpReorderAxes(parent=self, AxisOrder="txyzc", Input=opThreshold.CachedOutput)

        return op5raw.Output, op5threshold.Output

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        input_ready = self._inputReady()
        cumulated_readyness = input_ready

        cumulated_readyness &= (
            not self.batchProcessingApplet.busy
        )  # Nothing can be touched while batch mode is executing.

        opFeatureSelection = self.featureSelectionApplet.topLevelOperator
        featureOutput = opFeatureSelection.OutputImage
        features_ready = (
            len(featureOutput) > 0 and featureOutput[0].ready() and (TinyVector(featureOutput[0].meta.shape) > 0).all()
        )
        cumulated_readyness = cumulated_readyness and features_ready
        self._shell.setAppletEnabled(self.pcApplet, cumulated_readyness)

        slot = self.pcApplet.topLevelOperator.CachedPredictionProbabilities
        predictions_ready = len(slot) > 0 and slot[0].ready() and (TinyVector(slot[0].meta.shape) > 0).all()

        cumulated_readyness = cumulated_readyness and predictions_ready
        self._shell.setAppletEnabled(self.thresholdingApplet, cumulated_readyness)

        # Problems can occur if the features or input data are changed during live update mode.
        # Don't let the user do that.
        opPixelClassification = self.pcApplet.topLevelOperator
        live_update_active = not opPixelClassification.FreezePredictions.value

        self._shell.setAppletEnabled(self.dataSelectionApplet, not live_update_active)
        self._shell.setAppletEnabled(self.featureSelectionApplet, input_ready and not live_update_active)

        super(ObjectClassificationWorkflowPixel, self).handleAppletStateUpdateRequested(
            upstream_ready=cumulated_readyness
        )

    def handle_applet_changed(self, prev_index, current_index):
        if prev_index != current_index:
            # If the user is viewing an applet downstream of the pixel classification applet,
            # Make sure it's in 'live update' mode, since the rest of the workflow pulls from the *cached* predictions.
            opPixelClassification = self.pcApplet.topLevelOperator
            opPixelClassification.FreezePredictions.setValue(
                self._shell.currentAppletIndex <= self.applets.index(self.pcApplet)
            )


class ObjectClassificationWorkflowBinary(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from binary image)"
    workflowDisplayName = "Object Classification [Inputs: Raw Data, Segmentation]"

    class InputImageRoles(SlotNameEnum):
        RAW_DATA = enum.auto()
        SEGMENTATION_IMAGE = enum.auto()
        ATLAS = enum.auto()

    @property
    def data_instructions(self):
        return (
            super().data_instructions
            + f'Use the "{self.InputImageRoles.SEGMENTATION_IMAGE.displayName}" tab to load your binary mask image(s).'
        )

    def connectInputs(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        return self.createRawDataSourceSlot(laneIndex), opData.ImageGroup[self.InputImageRoles.SEGMENTATION_IMAGE]

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        input_ready = self._inputReady()

        super(ObjectClassificationWorkflowBinary, self).handleAppletStateUpdateRequested(upstream_ready=input_ready)


class ObjectClassificationWorkflowPrediction(ObjectClassificationWorkflow):
    workflowName = "Object Classification (from prediction image)"
    workflowDisplayName = "Object Classification [Inputs: Raw Data, Pixel Prediction Map]"

    class InputImageRoles(SlotNameEnum):
        RAW_DATA = enum.auto()
        PREDICTION_MAPS = enum.auto()
        ATLAS = enum.auto()

    @property
    def data_instructions(self):
        return (
            super().data_instructions
            + f'Use the "{self.InputImageRoles.PREDICTION_MAPS.displayName}" tab to load your pixel-wise probability image(s).'
        )

    def createInputApplets(self):
        super().createInputApplets()

        self.thresholdingApplet = ThresholdTwoLevelsApplet(self, "Threshold and Size Filter", "ThresholdTwoLevels")
        self._applets.append(self.thresholdingApplet)

    def connectInputs(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTwoLevelThreshold = self.thresholdingApplet.topLevelOperator.getLane(laneIndex)

        op5predictions = OpReorderAxes(parent=self)
        op5predictions.AxisOrder.setValue("txyzc")

        rawslot = self.createRawDataSourceSlot(laneIndex)

        op5predictions.Input.connect(opData.ImageGroup[self.InputImageRoles.PREDICTION_MAPS])

        opTwoLevelThreshold.RawInput.connect(rawslot)
        opTwoLevelThreshold.InputImage.connect(op5predictions.Output)

        op5Binary = OpReorderAxes(parent=self)
        op5Binary.AxisOrder.setValue("txyzc")
        op5Binary.Input.connect(opTwoLevelThreshold.CachedOutput)

        return rawslot, op5Binary.Output

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        input_ready = self._inputReady()
        cumulated_readyness = input_ready
        cumulated_readyness &= (
            not self.batchProcessingApplet.busy
        )  # Nothing can be touched while batch mode is executing.
        self._shell.setAppletEnabled(self.thresholdingApplet, cumulated_readyness)

        thresholding_ready = True  # is that so?
        cumulated_readyness = cumulated_readyness and thresholding_ready
        super(ObjectClassificationWorkflowPrediction, self).handleAppletStateUpdateRequested(
            upstream_ready=cumulated_readyness
        )


if __name__ == "__main__":
    from sys import argv

    w = ObjectClassificationWorkflow(True, argv)
