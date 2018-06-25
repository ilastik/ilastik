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
#          http://ilastik.org/license.html
###############################################################################
import numpy

from ilastik.applets.base.appletSerializer import AppletSerializer, deleteIfPresent

from ilastik.utility import bind
from lazyflow.utility.timer import timeLogged

import logging
logger = logging.getLogger(__name__)


class FeatureSelectionSerializer(AppletSerializer):
    """
    Serializes the user's pixel feature selections to an ilastik v0.6 project file.
    """

    def __init__(self, topLevelOperator, projectFileGroupName):
        super(FeatureSelectionSerializer, self).__init__(projectFileGroupName)
        self.topLevelOperator = topLevelOperator
        self._dirty = False

        def handleDirty():
            if not self.ignoreDirty:
                self._dirty = True

        self.topLevelOperator.FeatureIds.notifyDirty(bind(handleDirty))
        self.topLevelOperator.Scales.notifyDirty(bind(handleDirty))
        self.topLevelOperator.ComputeIn2d.notifyDirty(bind(handleDirty))
        self.topLevelOperator.SelectionMatrix.notifyDirty(bind(handleDirty))
        self.topLevelOperator.FeatureListFilename.notifyDirty(bind(handleDirty))

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        # Can't store anything without both scales and features
        if not self.topLevelOperator.Scales.ready() \
                or not self.topLevelOperator.FeatureIds.ready():
            return

        # Delete previous entries if they exist
        deleteIfPresent(topGroup, 'Scales')
        deleteIfPresent(topGroup, 'FeatureIds')
        deleteIfPresent(topGroup, 'SelectionMatrix')
        deleteIfPresent(topGroup, 'FeatureListFilename')
        deleteIfPresent(topGroup, 'ComputeIn2d')

        # Store the new values (as numpy arrays)

        topGroup.create_dataset('Scales', data=self.topLevelOperator.Scales.value)

        feature_ids = list(map(lambda s: s.encode('utf-8'), self.topLevelOperator.FeatureIds.value))
        topGroup.create_dataset('FeatureIds', data=feature_ids)

        if self.topLevelOperator.SelectionMatrix.ready():
            topGroup.create_dataset('SelectionMatrix', data=self.topLevelOperator.SelectionMatrix.value)

        if self.topLevelOperator.FeatureListFilename.ready():
            fnames = []
            for slot in self.topLevelOperator.FeatureListFilename:
                fnames.append(slot.value)
            if fnames:
                fnames = map(lambda s: s.encode('utf-8'), fnames)
                topGroup.create_dataset('FeatureListFilename', data=fnames)

        if self.topLevelOperator.ComputeIn2d.ready():
            topGroup.create_dataset('ComputeIn2d', data=self.topLevelOperator.ComputeIn2d.value)

        self._dirty = False

    @timeLogged(logger, logging.DEBUG)
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath, headless=False):
        try:
            scales = topGroup['Scales'].value
            scales = list(map(float, scales))

            # Restoring 'feature computation in 2d' only makes sense, if scales were recovered...
            try:
                computeIn2d = topGroup['ComputeIn2d'].value
                computeIn2d = list(map(bool, computeIn2d))
                self.topLevelOperator.ComputeIn2d.setValue(computeIn2d)
            except KeyError:
                pass  # older ilastik versions did not support feature computation in 2d

            featureIds = list(map(lambda s: s.decode('utf-8'), topGroup['FeatureIds'].value))
        except KeyError:
            pass
        else:
            if 'FeatureListFilename' in topGroup:
                raise NotImplementedError('Not simplified yet!')
                filenames = topGroup['FeatureListFilename'][:]
                for slot, filename in zip(self.topLevelOperator.FeatureListFilename, filenames):
                    slot.setValue(filename.decode('utf-8'))

                # Create a dummy SelectionMatrix, just so the operator knows it is configured
                # This is a little hacky.  We should really make SelectionMatrix optional,
                # and then handle the choice correctly in setupOutputs, probably involving
                # the Output.meta.NOTREADY flag
                dummy_matrix = numpy.zeros((6, 7), dtype=bool)
                dummy_matrix[0, 0] = True
                self.topLevelOperator.SelectionMatrix.setValue(dummy_matrix)
            else:
                # If the matrix isn't there, just return
                try:
                    savedMatrix = topGroup['SelectionMatrix'].value
                    # Check matrix dimensions
                    assert savedMatrix.shape[0] == len(
                        featureIds), "Invalid project data: feature selection matrix dimensions don't make sense"
                    assert savedMatrix.shape[1] == len(
                        scales), "Invalid project data: feature selection matrix dimensions don't make sense"
                except KeyError:
                    pass
                else:
                    # Apply saved settings
                    # Disconnect an input (used like a transaction slot)
                    self.topLevelOperator.SelectionMatrix.disconnect()

                    self.topLevelOperator.Scales.setValue(scales)
                    self.topLevelOperator.FeatureIds.setValue(featureIds)
                    # set disconnected slot at last (used like a transaction slot)
                    self.topLevelOperator.SelectionMatrix.setValue(savedMatrix)

        self._dirty = False

    def isDirty(self):
        """ Return true if the current state of this item
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        return self._dirty

    def unload(self):
        self.topLevelOperator.SelectionMatrix.disconnect()


class Ilastik05FeatureSelectionDeserializer(AppletSerializer):
    """
    Deserializes the user's pixel feature selections from an ilastik v0.5 project file.
    """

    def __init__(self, topLevelOperator):
        super(Ilastik05FeatureSelectionDeserializer, self).__init__('')
        self.topLevelOperator = topLevelOperator

    def serializeToHdf5(self, hdf5File, filePath):
        # This class is only for DEserialization
        pass

    def deserializeFromHdf5(self, hdf5File, filePath, headless=False):
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # This is the v0.5 import deserializer.  Don't work with 0.6 projects (or anything else).
        if ilastikVersion != 0.5:
            return

        # Use the hard-coded ilastik v0.5 scales and feature ids
        ScalesList = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        FeatureIds = ['GaussianSmoothing',
                      'LaplacianOfGaussian',
                      'StructureTensorEigenvalues',
                      'HessianOfGaussianEigenvalues',
                      'GaussianGradientMagnitude',
                      'DifferenceOfGaussians']

        self.topLevelOperator.Scales.setValue(ScalesList)
        # If the main operator already has a feature ordering (provided by the GUI),
        # then don't overwrite it.  We'll re-order the matrix to match the existing ordering.
        if not self.topLevelOperator.FeatureIds.ready():
            self.topLevelOperator.FeatureIds.setValue(FeatureIds)

        # Create a feature selection matrix of the correct shape (all false by default)
        pipeLineSelectedFeatureMatrix = numpy.array(numpy.zeros((6, 7)), dtype=bool)

        try:
            # In ilastik 0.5, features were grouped into user-friendly selections.  We have to split these
            #  selections apart again into the actual features that must be computed.
            userFriendlyFeatureMatrix = hdf5File['Project']['FeatureSelection']['UserSelection'].value
        except KeyError:
            # If the project file doesn't specify feature selections,
            #  we'll just use the default (blank) selections as initialized above
            pass
        else:
            # Number of feature types must be correct or something is totally wrong
            assert userFriendlyFeatureMatrix.shape[0] == 4

            # Some older versions of ilastik had only 6 scales.
            # Add columns of zeros until we have 7 columns.
            while userFriendlyFeatureMatrix.shape[1] < 7:
                userFriendlyFeatureMatrix = numpy.append(
                    userFriendlyFeatureMatrix, numpy.zeros((4, 1), dtype=bool), axis=1)

            # Here's how features map to the old "feature groups"
            # (Note: Nothing maps to the orientation group.)
            featureToGroup = {'GaussianSmoothing': 0,  # Gaussian Smoothing -> Color
                              'LaplacianOfGaussian': 1,  # Laplacian of Gaussian -> Edge
                              'StructureTensorEigenvalues': 3,  # Structure Tensor Eigenvalues -> Texture
                              'HessianOfGaussianEigenvalues': 3,  # Eigenvalues of Hessian of Gaussian -> Texture
                              'GaussianGradientMagnitude': 1,  # Gradient Magnitude of Gaussian -> Edge
                              'DifferenceOfGaussians': 1}  # Difference of Gaussians -> Edge

            newFeatureIds = self.topLevelOperator.FeatureIds.value
            # For each feature, determine which group's settings to take
            for featureId, featureGroupIndex in list(featureToGroup.items()):
                newRow = newFeatureIds.index(featureId)
                # Copy the whole row of selections from the feature group
                pipeLineSelectedFeatureMatrix[newRow] = userFriendlyFeatureMatrix[featureGroupIndex]

        # Finally, update the pipeline with the feature selections
        self.topLevelOperator.SelectionMatrix.setValue(pipeLineSelectedFeatureMatrix)

    def isDirty(self):
        """ Return true if the current state of this item
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        return False

    def unload(self):
        self.topLevelOperator.SelectionMatrix.disconnect()

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        assert False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath, headless=False):
        # This deserializer is a special-case.
        # It doesn't make use of the serializer base class, which makes assumptions about the file structure.
        # Instead, if overrides the public serialize/deserialize functions directly
        assert False
