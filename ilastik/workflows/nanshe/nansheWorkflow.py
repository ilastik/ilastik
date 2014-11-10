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

__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Oct 16, 2014 16:04:03 EDT$"



from nanshe.read_config import read_parameters

from lazyflow.graph import Graph

from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.nanshe.preprocessing.nanshePreprocessingApplet import NanshePreprocessingApplet
from ilastik.applets.nanshe.dictionaryLearning.nansheDictionaryLearningApplet import NansheDictionaryLearningApplet
from ilastik.applets.nanshe.postprocessing.nanshePostprocessingApplet import NanshePostprocessingApplet


class NansheWorkflow(Workflow):
    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(NansheWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph)
        self._applets = []
        self._menus = None

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.nanshePreprocessingApplet = NanshePreprocessingApplet(self, "Preprocessing", "NanshePreprocessing")
        self.nansheDictionaryLearningApplet = NansheDictionaryLearningApplet(self, "DictionaryLearning", "NansheDictionaryLearning")
        self.nanshePostprocessingApplet = NanshePostprocessingApplet(self, "Postprocessing", "NanshePostprocessing")

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data'] )

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.nanshePreprocessingApplet )
        self._applets.append( self.nansheDictionaryLearningApplet )
        self._applets.append( self.nanshePostprocessingApplet )

    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)        
        opPreprocessing = self.nanshePreprocessingApplet.topLevelOperator.getLane(laneIndex)
        opDictionaryLearning = self.nansheDictionaryLearningApplet.topLevelOperator.getLane(laneIndex)
        opPostprocessing = self.nanshePostprocessingApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opPreprocessing.InputImage.connect( opDataSelection.Image )
        opDictionaryLearning.InputImage.connect( opPreprocessing.CacheOutput )
        opPostprocessing.InputImage.connect( opDictionaryLearning.Output )

    def menus(self):
        from PyQt4.QtGui import QMenu

        if self._menus is None:
            self._menus = []

            configuration_menu = QMenu("Configuration")

            configuration_menu.addAction("Import").triggered.connect(self._import_configuration)
            configuration_menu.addAction("Export").triggered.connect(self._export_configuration)

            self._menus.append(configuration_menu)

        return self._menus

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def _import_configuration(self):
        from PyQt4.QtGui import QFileDialog

        filename = QFileDialog.getOpenFileName(caption="Import Configuration", filter="*.json")
        filename = str(filename)

        config_all = read_parameters(filename)

        config = config_all


        if "generate_neurons_blocks" in config:
            config = config["generate_neurons_blocks"]

        config = config["generate_neurons"]


        preprocess_config = config["preprocess_data"]
        dictionary_config = config["generate_dictionary"]["spams.trainDL"]
        postprocess_config = config["postprocess_data"]

        if "remove_zeroed_lines" in preprocess_config:
            local_config = preprocess_config["remove_zeroed_lines"]

            erosion_shape = local_config["erosion_shape"]
            dilation_shape = local_config["dilation_shape"]

            self.nanshePreprocessingApplet.topLevelOperator.ToRemoveZeroedLines.setValue(True)
            self.nanshePreprocessingApplet.topLevelOperator.ErosionShape.setValue(erosion_shape)
            self.nanshePreprocessingApplet.topLevelOperator.DilationShape.setValue(dilation_shape)
        else:
            self.nanshePreprocessingApplet.topLevelOperator.ToRemoveZeroedLines.setValue(False)

        if "extract_f0" in preprocess_config:
            local_config = preprocess_config["extract_f0"]

            bias = local_config.get("bias")
            temporal_smoothing_gaussian_filter_stdev = local_config["temporal_smoothing_gaussian_filter_stdev"]
            half_window_size = local_config["half_window_size"]
            which_quantile = local_config["which_quantile"]
            spatial_smoothing_gaussian_filter_stdev = local_config["spatial_smoothing_gaussian_filter_stdev"]


            self.nanshePreprocessingApplet.topLevelOperator.ToExtractF0.setValue(True)

            if bias is not None:
                self.nanshePreprocessingApplet.topLevelOperator.BiasEnabled.setValue(True)
                self.nanshePreprocessingApplet.topLevelOperator.Bias.setValue(bias)
            else:
                self.nanshePreprocessingApplet.topLevelOperator.BiasEnabled.setValue(False)

            self.nanshePreprocessingApplet.topLevelOperator.TemporalSmoothingGaussianFilterStdev.setValue(temporal_smoothing_gaussian_filter_stdev)
            self.nanshePreprocessingApplet.topLevelOperator.HalfWindowSize.setValue(half_window_size)
            self.nanshePreprocessingApplet.topLevelOperator.WhichQuantile.setValue(which_quantile)
            self.nanshePreprocessingApplet.topLevelOperator.SpatialSmoothingGaussianFilterStdev.setValue(spatial_smoothing_gaussian_filter_stdev)
        else:
            self.nanshePreprocessingApplet.topLevelOperator.ToExtractF0.setValue(False)

        if "wavelet_transform" in preprocess_config:
            local_config = preprocess_config["wavelet_transform"]
            scale = local_config["scale"]

            self.nanshePreprocessingApplet.topLevelOperator.ToWaveletTransform.setValue(True)
            self.nanshePreprocessingApplet.topLevelOperator.Scale.setValue(local_config["scale"])
        else:
            self.nanshePreprocessingApplet.topLevelOperator.ToWaveletTransform.setValue(False)


        norm = preprocess_config["normalize_data"]["simple_image_processing.renormalized_images"].get("ord", 2)
        self.nansheDictionaryLearningApplet.topLevelOperator.Ord.setValue(norm)

        self.nansheDictionaryLearningApplet.topLevelOperator.K.setValue(dictionary_config["K"])
        self.nansheDictionaryLearningApplet.topLevelOperator.Gamma1.setValue(dictionary_config["gamma1"])
        self.nansheDictionaryLearningApplet.topLevelOperator.Gamma2.setValue(dictionary_config["gamma2"])
        self.nansheDictionaryLearningApplet.topLevelOperator.NumThreads.setValue(dictionary_config["numThreads"])
        self.nansheDictionaryLearningApplet.topLevelOperator.Batchsize.setValue(dictionary_config["batchsize"])
        self.nansheDictionaryLearningApplet.topLevelOperator.NumIter.setValue(dictionary_config["iter"])
        self.nansheDictionaryLearningApplet.topLevelOperator.Lambda1.setValue(dictionary_config["lambda1"])
        self.nansheDictionaryLearningApplet.topLevelOperator.Lambda2.setValue(dictionary_config["lambda2"])
        self.nansheDictionaryLearningApplet.topLevelOperator.PosAlpha.setValue(dictionary_config["posAlpha"])
        self.nansheDictionaryLearningApplet.topLevelOperator.PosD.setValue(dictionary_config["posD"])
        self.nansheDictionaryLearningApplet.topLevelOperator.Clean.setValue(dictionary_config["clean"])
        self.nansheDictionaryLearningApplet.topLevelOperator.Mode.setValue(dictionary_config["mode"])
        self.nansheDictionaryLearningApplet.topLevelOperator.ModeD.setValue(dictionary_config["modeD"])


        self.nanshePostprocessingApplet.topLevelOperator.SignificanceThreshold.setValue(
            postprocess_config["wavelet_denoising"]["denoising.estimate_noise"]["significance_threshold"]
        )
        self.nanshePostprocessingApplet.topLevelOperator.WaveletTransformScale.setValue(
            postprocess_config["wavelet_denoising"]["wavelet_transform.wavelet_transform"]["scale"]
        )
        self.nanshePostprocessingApplet.topLevelOperator.NoiseThreshold.setValue(
            postprocess_config["wavelet_denoising"]["denoising.significant_mask"]["noise_threshold"]
        )

        major_axis_length_config = postprocess_config["wavelet_denoising"]["accepted_region_shape_constraints"].get("major_axis_length")
        if major_axis_length_config is not None:
            min = major_axis_length_config.get("min")
            max = major_axis_length_config.get("max")

            if min is not None:
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled.setValue(True)
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedRegionShapeConstraints_MajorAxisLength_Min.setValue(min)
            else:
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled.setValue(False)

            if max is not None:
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled.setValue(True)
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedRegionShapeConstraints_MajorAxisLength_Max.setValue(max)
            else:
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled.setValue(False)

        self.nanshePostprocessingApplet.topLevelOperator.PercentagePixelsBelowMax.setValue(
            postprocess_config["wavelet_denoising"]["remove_low_intensity_local_maxima"]["percentage_pixels_below_max"]
        )
        self.nanshePostprocessingApplet.topLevelOperator.MinLocalMaxDistance.setValue(
            postprocess_config["wavelet_denoising"]["remove_too_close_local_maxima"]["min_local_max_distance"]
        )

        area_config = postprocess_config["wavelet_denoising"]["accepted_neuron_shape_constraints"].get("area")
        if area_config is not None:
            min = area_config.get("min")
            max = area_config.get("max")

            if min is not None:
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Area_Min_Enabled.setValue(True)
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Area_Min.setValue(min)
            else:
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Area_Min_Enabled.setValue(False)

            if max is not None:
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Area_Max_Enabled.setValue(True)
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Area_Max.setValue(max)
            else:
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Area_Max_Enabled.setValue(False)

        eccentricity_config = postprocess_config["wavelet_denoising"]["accepted_neuron_shape_constraints"].get("eccentricity")
        if eccentricity_config is not None:
            min = eccentricity_config.get("min")
            max = eccentricity_config.get("max")

            if min is not None:
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled.setValue(True)
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Eccentricity_Min.setValue(min)
            else:
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled.setValue(False)

            if max is not None:
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled.setValue(True)
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Eccentricity_Max.setValue(max)
            else:
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled.setValue(False)

        self.nanshePostprocessingApplet.topLevelOperator.AlignmentMinThreshold.setValue(
            postprocess_config["merge_neuron_sets"]["alignment_min_threshold"]
        )
        self.nanshePostprocessingApplet.topLevelOperator.OverlapMinThreshold.setValue(
            postprocess_config["merge_neuron_sets"]["overlap_min_threshold"]
        )
        self.nanshePostprocessingApplet.topLevelOperator.Fuse_FractionMeanNeuronMaxThreshold.setValue(
            postprocess_config["merge_neuron_sets"]["fuse_neurons"]["fraction_mean_neuron_max_threshold"]
        )

    def _export_configuration(self):
        from PyQt4.QtGui import QFileDialog
        import json
        from collections import OrderedDict


        filename = QFileDialog.getSaveFileName(caption="Export Configuration", filter="*.json")
        filename = str(filename)


        with open(filename, "w") as file_handle:
            config = OrderedDict()
            config["generate_neurons_blocks"] = OrderedDict()
            generate_neurons_blocks_config = config["generate_neurons_blocks"]


            generate_neurons_blocks_config["__comment__use_drmaa"] = "Whether to use DRMAA for job submission, false by default."
            generate_neurons_blocks_config["use_drmaa"] = True

            generate_neurons_blocks_config["__comment__num_drmaa_cores"] = "Number of cores per job."
            generate_neurons_blocks_config["num_drmaa_cores"] = 1

            generate_neurons_blocks_config["__comment__block_shape"] = "The shape of the blocks. -1 represents an unspecified length, which must be specified in num_blocks."
            generate_neurons_blocks_config["block_shape"] = [10000, -1, -1]

            generate_neurons_blocks_config["__comment__num_blocks"] = "The number of the blocks per dimension. -1 represents an unspecified length, which must be specified in block_shape."
            generate_neurons_blocks_config["num_blocks"] = [-1, 8, 8]

            generate_neurons_blocks_config["__comment__half_border_shape"] = "The shape of the border to remove. Trims on both sides of each axis."
            generate_neurons_blocks_config["half_border_shape"] = [0, 16, 16]

            generate_neurons_blocks_config["__comment__half_window_shape"] = "The shape of the overlap in each direction. The time portion must be bigger or equal to the half_window_size."
            generate_neurons_blocks_config["half_window_shape"] = [400, 20, 20]

            generate_neurons_blocks_config["__comment__debug"] = "Whether to include debug information. False by default."
            generate_neurons_blocks_config["debug"] = False

            generate_neurons_blocks_config["generate_neurons"] = OrderedDict()
            generate_neurons_config = generate_neurons_blocks_config["generate_neurons"]


            generate_neurons_config["__comment__run_stage"] = "Where to run until either preprocessing, dictionary, or postprocessing. If resume, is true then it will delete the previous results at this stage. By default (all can be set explicitly to null string) runs all the way through."
            generate_neurons_config["run_stage"] = ""


            generate_neurons_config["__comment__preprocess_data"] = "Performs all processing before dictionary learning."
            generate_neurons_config["preprocess_data"] = OrderedDict()
            preprocess_data_config = generate_neurons_config["preprocess_data"]


            if self.nanshePreprocessingApplet.topLevelOperator.ToRemoveZeroedLines.value:
                preprocess_data_config["__comment__remove_zeroed_lines"] = "Optional. Interpolates over missing lines that could not be registered. This is done by finding an outline around all missing points to use for calculating the interpolation."
                preprocess_data_config["remove_zeroed_lines"] = OrderedDict()
                remove_zeroed_lines_config = preprocess_data_config["remove_zeroed_lines"]

                remove_zeroed_lines_config["__comment__erosion_shape"] = "Kernel shape for performing erosion. Axis order is [y, x] or [z, y, x]."
                remove_zeroed_lines_config["__comment__dilation_shape"] = "Kernel shape for performing dilation. Axis order is [y, x] or [z, y, x]."

                remove_zeroed_lines_config["erosion_shape"] = self.nanshePreprocessingApplet.topLevelOperator.ErosionShape.value
                remove_zeroed_lines_config["dilation_shape"] = self.nanshePreprocessingApplet.topLevelOperator.DilationShape.value


            if self.nanshePreprocessingApplet.topLevelOperator.ToExtractF0.value:
                preprocess_data_config["__comment__extract_f0"] = "Optional. Estimates and removes f0 from the data using a percentile (rank order) filter."
                preprocess_data_config["extract_f0"] = OrderedDict()
                extract_f0_config = preprocess_data_config["extract_f0"]

                if self.nanshePreprocessingApplet.topLevelOperator.BiasEnabled.value:
                    extract_f0_config["__comment__bias"] = "To avoid division by zero, this constant is added to the data. If unspecified, a bias will be found so that the smallest value is 1."
                    extract_f0_config["bias"] = self.nanshePreprocessingApplet.topLevelOperator.Bias.value

                extract_f0_config["__comment__temporal_smoothing_gaussian_filter_stdev"] = "What standard deviation to use for the smoothing gaussian applied along time."
                extract_f0_config["temporal_smoothing_gaussian_filter_stdev"] = self.nanshePreprocessingApplet.topLevelOperator.TemporalSmoothingGaussianFilterStdev.value

                extract_f0_config["__comment__half_window_size"] = "How many frames to include in half of the window. All windows are odd. So, the total window size will be 2 * half_window_size + 1."
                extract_f0_config["half_window_size"] = self.nanshePreprocessingApplet.topLevelOperator.HalfWindowSize.value

                extract_f0_config["__comment__which_quantile"] = "The quantile to be used for filtering. Must be a single float from [0.0, 1.0]. If set to 0.5, this is a median filter."
                extract_f0_config["which_quantile"] = self.nanshePreprocessingApplet.topLevelOperator.WhichQuantile.value

                extract_f0_config["__comment__spatial_smoothing_gaussian_filter_stdev"] = "What standard deviation to use for the smoothing gaussian applied along each spatial dimension, independently."
                extract_f0_config["spatial_smoothing_gaussian_filter_stdev"] = self.nanshePreprocessingApplet.topLevelOperator.SpatialSmoothingGaussianFilterStdev.value


            if self.nanshePreprocessingApplet.topLevelOperator.ToWaveletTransform.value:
                preprocess_data_config["__comment__wavelet_transform"] = "Optional. Runs a wavelet transform on the data."
                preprocess_data_config["wavelet_transform"] = OrderedDict()
                wavelet_transform_config = preprocess_data_config["wavelet_transform"]

                wavelet_transform_config["__comment__scale"] = "This can be a single value, which is then applied on all axes or it can be an array. For the array, the axis order is [t, y, x] for 2D and [t, z, y, x] for 3D."
                wavelet_transform_config["scale"] = self.nanshePreprocessingApplet.topLevelOperator.Scale.value


            preprocess_data_config["__comment__normalize_data"] = "How to normalize data. L_2 norm recommended."
            preprocess_data_config["normalize_data"] = OrderedDict()
            preprocess_data_config["normalize_data"]["simple_image_processing.renormalized_images"] = OrderedDict()
            preprocess_data_config["normalize_data"]["simple_image_processing.renormalized_images"]["ord"] = 2



            generate_neurons_config["__comment__generate_dictionary"] = "Wrapper function that calls spams.trainDL. Comments borrowed from SPAMS documentation ( http://spams-devel.gforge.inria.fr/doc-python/html/doc_spams004.html#sec5 ). Only relevant parameters have comments included here."
            generate_neurons_config["generate_dictionary"] = OrderedDict()
            generate_dictionary_config = generate_neurons_config["generate_dictionary"]

            generate_dictionary_config["__comment__spams.trainDL"] = "spams.trainDL is an efficient implementation of the dictionary learning technique presented in 'Online Learning for Matrix Factorization and Sparse Coding' by Julien Mairal, Francis Bach, Jean Ponce and Guillermo Sapiro arXiv:0908.0050"
            generate_dictionary_config["spams.trainDL"] = OrderedDict()

            generate_dictionary_config["spams.trainDL"]["K"] = self.nansheDictionaryLearningApplet.topLevelOperator.K.value
            generate_dictionary_config["spams.trainDL"]["gamma1"] = self.nansheDictionaryLearningApplet.topLevelOperator.Gamma1.value
            generate_dictionary_config["spams.trainDL"]["gamma2"] = self.nansheDictionaryLearningApplet.topLevelOperator.Gamma2.value
            generate_dictionary_config["spams.trainDL"]["numThreads"] = self.nansheDictionaryLearningApplet.topLevelOperator.NumThreads.value
            generate_dictionary_config["spams.trainDL"]["batchsize"] = self.nansheDictionaryLearningApplet.topLevelOperator.Batchsize.value
            generate_dictionary_config["spams.trainDL"]["iter"] = self.nansheDictionaryLearningApplet.topLevelOperator.NumIter.value
            generate_dictionary_config["spams.trainDL"]["lambda1"] = self.nansheDictionaryLearningApplet.topLevelOperator.Lambda1.value
            generate_dictionary_config["spams.trainDL"]["lambda2"] = self.nansheDictionaryLearningApplet.topLevelOperator.Lambda2.value
            generate_dictionary_config["spams.trainDL"]["posAlpha"] = True
            generate_dictionary_config["spams.trainDL"]["posD"] = True
            generate_dictionary_config["spams.trainDL"]["clean"] = True
            generate_dictionary_config["spams.trainDL"]["mode"] = 2
            generate_dictionary_config["spams.trainDL"]["modeD"] = 0



            generate_neurons_config["postprocess_data"] = OrderedDict()
            postprocess_data_config = generate_neurons_config["postprocess_data"]


            postprocess_data_config["__comment__wavelet_denoising"] = "Performs segmentation on each basis image to extract neurons."
            postprocess_data_config["wavelet_denoising"] = OrderedDict()
            wavelet_denoising_config = postprocess_data_config["wavelet_denoising"]

            wavelet_denoising_config["__comment__denoising.estimate_noise"] = "Estimates the upper bound on the noise by finding the standard deviation on a subset of the data. The subset is determined by finding the standard deviation ( std_all ) for all of the data and determining what is within that std_all*significance_threshold. It is recommended that significance_threshold is left at 3.0."
            wavelet_denoising_config["denoising.estimate_noise"] = OrderedDict()
            wavelet_denoising_config["denoising.estimate_noise"]["significance_threshold"] = self.nanshePostprocessingApplet.topLevelOperator.SignificanceThreshold.value

            wavelet_denoising_config["__comment__wavelet_transform.wavelet_transform"] = "Performed on the basis image."
            wavelet_denoising_config["wavelet_transform.wavelet_transform"] = OrderedDict()
            wavelet_denoising_config["wavelet_transform.wavelet_transform"]["__comment__scale"] = "Scalars are applied to all dimensions. It is recommended that this be symmetric."
            wavelet_denoising_config["wavelet_transform.wavelet_transform"]["scale"] = self.nanshePostprocessingApplet.topLevelOperator.WaveletTransformScale.value

            wavelet_denoising_config["__comment__denoising.significant_mask"] = "Using the noise estimate from denoising.estimate_noise and the wavelet transformed image from wavelet_transform.wavelet_transform, anything within the noise range from before scaled up by the noise_threshold. Typical values are 2.0-4.0."
            wavelet_denoising_config["denoising.significant_mask"] = OrderedDict()
            wavelet_denoising_config["denoising.significant_mask"]["noise_threshold"] = self.nanshePostprocessingApplet.topLevelOperator.NoiseThreshold.value


            wavelet_denoising_config["__comment__accepted_region_shape_constraints"] = "Set of region constraints to determine if the wavelet transform is too high for that region. If so, the next lowest transform replaces it."
            wavelet_denoising_config["accepted_region_shape_constraints"] = OrderedDict()
            wavelet_denoising_config["accepted_region_shape_constraints"]["__comment__major_axis_length"] = "Acceptable range or single bound for the major axis length."

            if self.nanshePostprocessingApplet.topLevelOperator.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled.value or\
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled.value:
                wavelet_denoising_config["accepted_region_shape_constraints"]["major_axis_length"] = OrderedDict()

                if self.nanshePostprocessingApplet.topLevelOperator.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled.value:
                    wavelet_denoising_config["accepted_region_shape_constraints"]["major_axis_length"]["min"] =\
                        self.nanshePostprocessingApplet.topLevelOperator.AcceptedRegionShapeConstraints_MajorAxisLength_Min.value
                if self.nanshePostprocessingApplet.topLevelOperator.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled.value:
                    wavelet_denoising_config["accepted_region_shape_constraints"]["major_axis_length"]["max"] =\
                        self.nanshePostprocessingApplet.topLevelOperator.AcceptedRegionShapeConstraints_MajorAxisLength_Max.value


            wavelet_denoising_config["__comment__remove_low_intensity_local_maxima"] = "Removes regions that don't have enough pixels below their max."
            wavelet_denoising_config["remove_low_intensity_local_maxima"] = OrderedDict()
            wavelet_denoising_config["remove_low_intensity_local_maxima"]["__comment__percentage_pixels_below_max"] = "Ratio of pixels below their max to number of pixels in the region. This sets the upper bound."
            wavelet_denoising_config["remove_low_intensity_local_maxima"]["percentage_pixels_below_max"] =\
                self.nanshePostprocessingApplet.topLevelOperator.PercentagePixelsBelowMax.value


            wavelet_denoising_config["__comment__remove_too_close_local_maxima"] = "Removes regions that are too close to each other. Keeps the one with the highest intensity. No other tie breakers."
            wavelet_denoising_config["remove_too_close_local_maxima"] = OrderedDict()
            wavelet_denoising_config["remove_too_close_local_maxima"]["__comment__min_local_max_distance"] = "Constraint on how close they can be."
            wavelet_denoising_config["remove_too_close_local_maxima"]["min_local_max_distance"] =\
                self.nanshePostprocessingApplet.topLevelOperator.MinLocalMaxDistance.value


            wavelet_denoising_config["__comment__accepted_neuron_shape_constraints"] = "Constraints required for a region to be extracted and used as a neuron."
            wavelet_denoising_config["accepted_neuron_shape_constraints"] = OrderedDict()

            if self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Area_Min_Enabled.value or\
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Area_Max_Enabled.value:
                wavelet_denoising_config["accepted_neuron_shape_constraints"]["area"] = OrderedDict()

                if self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Area_Min_Enabled.value:
                    wavelet_denoising_config["accepted_neuron_shape_constraints"]["area"]["min"] =\
                        self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Area_Min.value
                if self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Area_Max_Enabled.value:
                    wavelet_denoising_config["accepted_neuron_shape_constraints"]["area"]["max"] =\
                        self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Area_Max.value

            if self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled.value or\
                self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled.value:
                wavelet_denoising_config["accepted_neuron_shape_constraints"]["eccentricity"] = OrderedDict()

                if self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled.value:
                    wavelet_denoising_config["accepted_neuron_shape_constraints"]["eccentricity"]["min"] =\
                        self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Eccentricity_Min.value
                if self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled.value:
                    wavelet_denoising_config["accepted_neuron_shape_constraints"]["eccentricity"]["max"] =\
                        self.nanshePostprocessingApplet.topLevelOperator.AcceptedNeuronShapeConstraints_Eccentricity_Max.value



            postprocess_data_config["__comment__merge_neuron_sets"] = "Merges sets of neurons that may be duplicated in the dictionary (i.e. if one neuron is active with two different sets of neurons, it may show up in two frames)."
            postprocess_data_config["merge_neuron_sets"] = OrderedDict()
            merge_neuron_sets_config = postprocess_data_config["merge_neuron_sets"]

            merge_neuron_sets_config["__comment__alignment_min_threshold"] = "If the images associated with two neurons, are arranged as vectors. It would be possible to find the cosine of the angle between them. Then, this represents the lower bound for them to merge."
            merge_neuron_sets_config["alignment_min_threshold"] =\
                self.nanshePostprocessingApplet.topLevelOperator.AlignmentMinThreshold.value

            merge_neuron_sets_config["__comment__overlap_min_threshold"] = "If the masks associated with two neurons, are arranged as vectors. It would be possible to find the L_1 norm between them. This could then be turned into a ratio by dividing by the area of either neuron. Then, this represents the lower bound for them to merge."
            merge_neuron_sets_config["overlap_min_threshold"] =\
                self.nanshePostprocessingApplet.topLevelOperator.OverlapMinThreshold.value

            merge_neuron_sets_config["__comment__fuse_neurons"] = "Fuses two neurons into one."
            merge_neuron_sets_config["fuse_neurons"] = OrderedDict()
            merge_neuron_sets_config["fuse_neurons"]["__comment__fraction_mean_neuron_max_threshold"] = "When determining the mask of the fused neuron, it must not include any values less that max of the fused image times this threshold."
            merge_neuron_sets_config["fuse_neurons"]["fraction_mean_neuron_max_threshold"] =\
                self.nanshePostprocessingApplet.topLevelOperator.Fuse_FractionMeanNeuronMaxThreshold.value


            json.dump(config, file_handle, indent=4, separators=(",", " : "))

            file_handle.write("\n")
