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
__date__ = "$Oct 23, 2014 09:45:39 EDT$"



from lazyflow.graph import Operator, InputSlot, OutputSlot

from lazyflow.operators import OpArrayCache

import vigra

import numpy

import nanshe
import nanshe.expanded_numpy
import nanshe.advanced_image_processing


class OpNanshePostprocessData(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNanshePostprocessData"
    category = "Pointwise"


    InputImage = InputSlot()

    SignificanceThreshold = InputSlot(value=3.0, stype="float")
    WaveletTransformScale = InputSlot(value=4, stype="int")
    NoiseThreshold = InputSlot(value=4.0, stype="float")
    AcceptedRegionShapeConstraints_MajorAxisLength_Min = InputSlot(value=0.0, stype="float")
    AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled = InputSlot(value=True, stype="bool")
    AcceptedRegionShapeConstraints_MajorAxisLength_Max = InputSlot(value=25.0, stype="float")
    AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled = InputSlot(value=True, stype="bool")

    PercentagePixelsBelowMax = InputSlot(value=0.8, stype="float")
    MinLocalMaxDistance = InputSlot(value=20.0, stype="float")

    AcceptedNeuronShapeConstraints_Area_Min = InputSlot(value=45, stype="int")
    AcceptedNeuronShapeConstraints_Area_Min_Enabled = InputSlot(value=True, stype="bool")
    AcceptedNeuronShapeConstraints_Area_Max = InputSlot(value=60, stype="int")
    AcceptedNeuronShapeConstraints_Area_Max_Enabled = InputSlot(value=True, stype="bool")

    AcceptedNeuronShapeConstraints_Eccentricity_Min = InputSlot(value=0.0, stype="float")
    AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled = InputSlot(value=True, stype="bool")
    AcceptedNeuronShapeConstraints_Eccentricity_Max = InputSlot(value=0.9, stype="float")
    AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled = InputSlot(value=True, stype="bool")

    AlignmentMinThreshold = InputSlot(value=0.6, stype="float")
    OverlapMinThreshold = InputSlot(value=0.6, stype="float")

    Fuse_FractionMeanNeuronMaxThreshold = InputSlot(value=0.01, stype="float")

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNanshePostprocessData, self ).__init__( *args, **kwargs )

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )
        self.Output.meta.shape = self.Output.meta.shape[1:] + (1,)
        self.Output.meta.dtype = numpy.uint64

        spatial_dims = [_ for _ in self.Output.meta.axistags if _.isSpatial()]

        self.Output.meta.axistags = vigra.AxisTags(*(spatial_dims + [vigra.AxisInfo.c]))
    
    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()

        key = list(key)
        key = key[:-1]
        key = [slice(None)] + key
        key = tuple(key)

        raw = self.InputImage[key].wait()


        accepted_region_shape_constraints = {}

        if self.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled.value or\
                self.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled.value:
            accepted_region_shape_constraints["major_axis_length"] = {}

            if self.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled.value:
                accepted_region_shape_constraints["major_axis_length"]["min"] =\
                    self.AcceptedRegionShapeConstraints_MajorAxisLength_Min.value
            if self.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled.value:
                accepted_region_shape_constraints["major_axis_length"]["max"] =\
                    self.AcceptedRegionShapeConstraints_MajorAxisLength_Max.value

        accepted_neuron_shape_constraints = {}

        if self.AcceptedNeuronShapeConstraints_Area_Min_Enabled.value or\
                self.AcceptedNeuronShapeConstraints_Area_Max_Enabled.value:
            accepted_neuron_shape_constraints["area"] = {}

            if self.AcceptedNeuronShapeConstraints_Area_Min_Enabled.value:
                accepted_neuron_shape_constraints["area"]["min"] =\
                    self.AcceptedNeuronShapeConstraints_Area_Min.value
            if self.AcceptedNeuronShapeConstraints_Area_Max_Enabled.value:
                accepted_neuron_shape_constraints["area"]["max"] =\
                    self.AcceptedNeuronShapeConstraints_Area_Max.value

        if self.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled.value or\
                self.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled.value:
            accepted_neuron_shape_constraints["eccentricity"] = {}

            if self.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled.value:
                accepted_neuron_shape_constraints["eccentricity"]["min"] =\
                    self.AcceptedNeuronShapeConstraints_Eccentricity_Min.value
            if self.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled.value:
                accepted_neuron_shape_constraints["eccentricity"]["max"] =\
                    self.AcceptedNeuronShapeConstraints_Eccentricity_Max.value


        parameters = {
            "wavelet_denoising" : {

                "denoising.estimate_noise" : {
                    "significance_threshold" : self.SignificanceThreshold.value
                },

                "wavelet_transform.wavelet_transform" : {
                    "scale" : self.WaveletTransformScale.value
                },

                "denoising.significant_mask" : {
                    "noise_threshold" : self.NoiseThreshold.value
                },

                "accepted_region_shape_constraints" : accepted_region_shape_constraints,

                "remove_low_intensity_local_maxima" : {
                    "percentage_pixels_below_max" : self.PercentagePixelsBelowMax.value
                },

                "remove_too_close_local_maxima" : {
                    "min_local_max_distance" : self.MinLocalMaxDistance.value
                },

                "accepted_neuron_shape_constraints" : accepted_neuron_shape_constraints
            },

            "merge_neuron_sets" : {
                "alignment_min_threshold" : self.AlignmentMinThreshold.value,

                "overlap_min_threshold" : self.OverlapMinThreshold.value,

                "fuse_neurons" : {
                    "fraction_mean_neuron_max_threshold" : self.Fuse_FractionMeanNeuronMaxThreshold.value
                }
            }
        }

        processed = nanshe.advanced_image_processing.postprocess_data(raw, **parameters)

        processed_label_image = nanshe.expanded_numpy.enumerate_masks_max(processed["mask"])

        processed_label_image = processed_label_image[0]
        processed_label_image = processed_label_image[..., None]

        if slot.name == 'Output':
            result[...] = processed_label_image

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        if (slot.name == "InputImage") or (slot.name == "SignificanceThreshold") or\
            (slot.name == "WaveletTransformScale") or (slot.name == "NoiseThreshold") or\
            (slot.name == "AcceptedRegionShapeConstraints_MajorAxisLength_Min") or\
            (slot.name == "AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled") or\
            (slot.name == "AcceptedRegionShapeConstraints_MajorAxisLength_Max") or\
            (slot.name == "AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled") or\
            (slot.name == "PercentagePixelsBelowMax") or (slot.name == "MinLocalMaxDistance") or\
            (slot.name == "AcceptedNeuronShapeConstraints_Area_Min") or\
            (slot.name == "AcceptedNeuronShapeConstraints_Area_Min_Enabled") or\
            (slot.name == "AcceptedNeuronShapeConstraints_Area_Max") or\
            (slot.name == "AcceptedNeuronShapeConstraints_Area_Max_Enabled") or\
            (slot.name == "AcceptedNeuronShapeConstraints_Eccentricity_Min") or\
            (slot.name == "AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled") or\
            (slot.name == "AcceptedNeuronShapeConstraints_Eccentricity_Max") or\
            (slot.name == "AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled") or\
            (slot.name == "AlignmentMinThreshold") or (slot.name == "OverlapMinThreshold") or\
            (slot.name == "Fuse_FractionMeanNeuronMaxThreshold"):
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"


class OpNanshePostprocessDataCached(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNanshePostprocessDataCached"
    category = "Pointwise"


    InputImage = InputSlot()
    CacheInput = InputSlot(optional=True)

    SignificanceThreshold = InputSlot(value=3.0, stype="float")
    WaveletTransformScale = InputSlot(value=4, stype="int")
    NoiseThreshold = InputSlot(value=4.0, stype="float")
    AcceptedRegionShapeConstraints_MajorAxisLength_Min = InputSlot(value=0.0, stype="float")
    AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled = InputSlot(value=True, stype="bool")
    AcceptedRegionShapeConstraints_MajorAxisLength_Max = InputSlot(value=25.0, stype="float")
    AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled = InputSlot(value=True, stype="bool")

    PercentagePixelsBelowMax = InputSlot(value=0.8, stype="float")
    MinLocalMaxDistance = InputSlot(value=20.0, stype="float")

    AcceptedNeuronShapeConstraints_Area_Min = InputSlot(value=45, stype="int")
    AcceptedNeuronShapeConstraints_Area_Min_Enabled = InputSlot(value=True, stype="bool")
    AcceptedNeuronShapeConstraints_Area_Max = InputSlot(value=60, stype="int")
    AcceptedNeuronShapeConstraints_Area_Max_Enabled = InputSlot(value=True, stype="bool")

    AcceptedNeuronShapeConstraints_Eccentricity_Min = InputSlot(value=0.0, stype="float")
    AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled = InputSlot(value=True, stype="bool")
    AcceptedNeuronShapeConstraints_Eccentricity_Max = InputSlot(value=0.9, stype="float")
    AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled = InputSlot(value=True, stype="bool")

    AlignmentMinThreshold = InputSlot(value=0.6, stype="float")
    OverlapMinThreshold = InputSlot(value=0.6, stype="float")

    Fuse_FractionMeanNeuronMaxThreshold = InputSlot(value=0.01, stype="float")

    CleanBlocks = OutputSlot()
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNanshePostprocessDataCached, self ).__init__( *args, **kwargs )

        self.opPostprocessing = OpNanshePostprocessData(parent=self)

        self.opPostprocessing.SignificanceThreshold.connect(self.SignificanceThreshold)
        self.opPostprocessing.WaveletTransformScale.connect(self.WaveletTransformScale)
        self.opPostprocessing.NoiseThreshold.connect(self.NoiseThreshold)
        self.opPostprocessing.AcceptedRegionShapeConstraints_MajorAxisLength_Min.connect(self.AcceptedRegionShapeConstraints_MajorAxisLength_Min)
        self.opPostprocessing.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled.connect(self.AcceptedRegionShapeConstraints_MajorAxisLength_Min_Enabled)
        self.opPostprocessing.AcceptedRegionShapeConstraints_MajorAxisLength_Max.connect(self.AcceptedRegionShapeConstraints_MajorAxisLength_Max)
        self.opPostprocessing.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled.connect(self.AcceptedRegionShapeConstraints_MajorAxisLength_Max_Enabled)
        self.opPostprocessing.PercentagePixelsBelowMax.connect(self.PercentagePixelsBelowMax)
        self.opPostprocessing.MinLocalMaxDistance.connect(self.MinLocalMaxDistance)
        self.opPostprocessing.AcceptedNeuronShapeConstraints_Area_Min.connect(self.AcceptedNeuronShapeConstraints_Area_Min)
        self.opPostprocessing.AcceptedNeuronShapeConstraints_Area_Min_Enabled.connect(self.AcceptedNeuronShapeConstraints_Area_Min_Enabled)
        self.opPostprocessing.AcceptedNeuronShapeConstraints_Area_Max.connect(self.AcceptedNeuronShapeConstraints_Area_Max)
        self.opPostprocessing.AcceptedNeuronShapeConstraints_Area_Max_Enabled.connect(self.AcceptedNeuronShapeConstraints_Area_Max_Enabled)
        self.opPostprocessing.AcceptedNeuronShapeConstraints_Eccentricity_Min.connect(self.AcceptedNeuronShapeConstraints_Eccentricity_Min)
        self.opPostprocessing.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled.connect(self.AcceptedNeuronShapeConstraints_Eccentricity_Min_Enabled)
        self.opPostprocessing.AcceptedNeuronShapeConstraints_Eccentricity_Max.connect(self.AcceptedNeuronShapeConstraints_Eccentricity_Max)
        self.opPostprocessing.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled.connect(self.AcceptedNeuronShapeConstraints_Eccentricity_Max_Enabled)
        self.opPostprocessing.AlignmentMinThreshold.connect(self.AlignmentMinThreshold)
        self.opPostprocessing.OverlapMinThreshold.connect(self.OverlapMinThreshold)
        self.opPostprocessing.Fuse_FractionMeanNeuronMaxThreshold.connect(self.Fuse_FractionMeanNeuronMaxThreshold)


        self.opCache = OpArrayCache(parent=self)
        self.opCache.fixAtCurrent.setValue(False)
        self.CleanBlocks.connect( self.opCache.CleanBlocks )

        self.opPostprocessing.InputImage.connect( self.InputImage )
        self.opCache.Input.connect( self.opPostprocessing.Output )
        self.Output.connect( self.opCache.Output )

    def setupOutputs(self):
        self.opCache.blockShape.setValue( self.opPostprocessing.Output.meta.shape )


        self.Output.meta.assignFrom( self.opCache.Output.meta )

    def setInSlot(self, slot, subindex, key, value):
        assert slot == self.CacheInput

        self.opCache.setInSlot(self.opCache.Input, subindex, key, value)

    def propagateDirty(self, slot, subindex, roi):
        pass
