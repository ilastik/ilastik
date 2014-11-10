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
