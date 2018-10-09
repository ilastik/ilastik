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
from __future__ import division
from builtins import range
from ilastik.applets.base.appletSerializer import \
    AppletSerializer, deleteIfPresent, SerialSlot, SerialCountingSlot, \
    SerialBlockSlot, SerialListSlot
from lazyflow.operators.ioOperators import OpStreamingHdf5Reader, OpH5WriterBigDataset
from lazyflow.utility.orderedSignal import OrderedSignal
import threading

import logging
logger = logging.getLogger(__name__)


class SerialPredictionSlot(SerialSlot):

    def __init__(self, slot, operator, inslot=None, name=None,
                 subname=None, default=None, depends=None,
                 selfdepends=True):
        super(SerialPredictionSlot, self).__init__(
            slot, inslot, name, subname, default, depends, selfdepends
        )
        self.operator = operator
        self.progressSignal = OrderedSignal()

        self._predictionStorageEnabled = False
        self._predictionStorageRequest = None
        self._predictionsPresent = False

    def setDirty(self, *args, **kwargs):
        self.dirty = True
        self._predictionsPresent = False

    @property
    def predictionStorageEnabled(self):
        return self._predictionStorageEnabled

    @predictionStorageEnabled.setter
    def predictionStorageEnabled(self, value):
        self._predictionStorageEnabled = value
        if not self._predictionsPresent:
            self.dirty = True

    def cancel(self):
        if self._predictionStorageRequest is not None:
            self.predictionStorageEnabled = False
            self._predictionStorageRequest.cancel()

    def shouldSerialize(self, group):
        result = super(SerialPredictionSlot,self).shouldSerialize(group)
        result &= self.predictionStorageEnabled
        return result

    def _disconnect(self):
        for i,slot in enumerate(self.operator.PredictionsFromDisk):
            slot.disconnect()

    def serialize(self, group):
        if not self.shouldSerialize(group):
            return

        self._disconnect()
        super(SerialPredictionSlot, self).serialize(group)
        self.deserialize(group)

    def _serialize(self, group, name, slot):
        """Called when the currently stored predictions are dirty. If
        prediction storage is currently enabled, store them to the
        file. Otherwise, just delete them/

        (Avoid inconsistent project states, e.g. don't allow old
        predictions to be stored with a new classifier.)

        """
        predictionDir = group.create_group(self.name)

        # Disconnect the operators that might be using the old data.
        self.deserialize(group)
        
        failedToSave = False
        opWriter = None
        try:
            num = len(slot)
            if num > 0:
                increment = 100 / float(num)

            progress = 0
            for imageIndex in range(num):
                # Have we been cancelled?
                if not self.predictionStorageEnabled:
                    break

                datasetName = self.subname.format(imageIndex)

                # Use a big dataset writer to do this in chunks
                opWriter = OpH5WriterBigDataset(graph=self.operator.graph, parent = self.operator.parent)
                opWriter.hdf5File.setValue(predictionDir)
                opWriter.hdf5Path.setValue(datasetName)
                opWriter.Image.connect(slot[imageIndex])

                def handleProgress(percent):
                    # Stop sending progress if we were cancelled
                    if self.predictionStorageEnabled:
                        curprogress = progress + percent * (increment / 100.0)
                        self.progressSignal(curprogress)
                opWriter.progressSignal.subscribe(handleProgress)

                # Create the request
                self._predictionStorageRequest = opWriter.WriteImage[...]

                # Must use a threading event here because if we wait on the 
                # request from within a "real" thread, it refuses to be cancelled.
                finishedEvent = threading.Event()
                def handleFinish(result):
                    finishedEvent.set()

                def handleCancel():
                    logger.info("Full volume prediction save CANCELLED.")
                    self._predictionStorageRequest = None
                    finishedEvent.set()

                # Trigger the write and wait for it to complete or cancel.
                self._predictionStorageRequest.notify_finished(handleFinish)
                self._predictionStorageRequest.notify_cancelled(handleCancel)
                self._predictionStorageRequest.submit() # Can't call wait().  See note above.
                finishedEvent.wait()
                progress += increment
                opWriter.cleanUp()
                opWriter = None
        except:
            failedToSave = True
            raise
        finally:
            if opWriter is not None:
                opWriter.cleanUp()

            # If we were cancelled, delete the predictions we just started
            if not self.predictionStorageEnabled or failedToSave:
                deleteIfPresent(group, name)

    def deserialize(self, group):
        # override because we need to set self._predictionsPresent
        self._predictionsPresent = self.name in list(group.keys())
        super(SerialPredictionSlot, self).deserialize(group)

    def _deserialize(self, group, slot):
        # Flush the GUI cache of any saved up dirty rois
        if self.operator.FreezePredictions.value == True:
            self.operator.FreezePredictions.setValue(False)
            self.operator.FreezePredictions.setValue(True)

        #self.operator.PredictionsFromDisk.resize(len(group))
        if len(list(group.keys())) > 0:
            assert len(list(group.keys())) == len(self.operator.PredictionsFromDisk), "Expected to find the same number of on-disk predications as there are images loaded."
        else:
            for slot in self.operator.PredictionsFromDisk:
                slot.disconnect()
        for imageIndex, datasetName in enumerate(group.keys()):
            opStreamer = OpStreamingHdf5Reader(graph=self.operator.graph, parent=self.operator.parent)
            opStreamer.Hdf5File.setValue(group)
            opStreamer.InternalPath.setValue(datasetName)
            self.operator.PredictionsFromDisk[imageIndex].connect(opStreamer.OutputImage)

class SerialBoxSlot(SerialSlot):
    def __init__(self, slot, operator, inslot=None, name=None,
                 subname=None, default=None, depends=None,
                 selfdepends=True):
        super(SerialBoxSlot, self).__init__(
            slot, inslot, name, subname, default, depends, selfdepends
        )
        self.operator = operator
        self.progressSignal = OrderedSignal()  # Signature: __call__(percentComplete)

    def _serialize(self, group, name, multislot):
        #create subgroups, one for every imagelane
        BoxDir = group.create_group(self.name)
        self.deserialize(group)
        for i, slot in enumerate(multislot):
            g = BoxDir.create_group(self.subname.format(i))

            s = SerialListSlot(slot)
            s.serialize(g)

    def _deserialize(self, group, slot):
        for imageIndex, datasetName in enumerate(group.keys()):
            subgroup = group[datasetName]
            subslot = subgroup[slot.name]
            if "isEmpty" in subslot.attrs and not subslot.attrs["isEmpty"]:
                slot[imageIndex].setValue(group[datasetName][slot.name].value.tolist())
        #self.op.opTrain.BoxConstraints[i].setValue(res[i])


class CountingSerializer(AppletSerializer):
    """Encapsulate the serialization scheme for pixel classification
    workflow parameters and datasets.
    """

    def __init__(self, operator, projectFileGroupName):
        self.predictionSlot = SerialPredictionSlot(
            operator.PredictionProbabilities,
            operator,
            name='Predictions',
            subname='predictions{:04d}',
        )

        slots = [
            SerialListSlot(
                operator.LabelNames,
            ),
            SerialListSlot(
                operator.LabelColors,
                transform=lambda x: tuple(x.flat),
            ),
            SerialListSlot(
                operator.PmapColors,
                transform=lambda x: tuple(x.flat),
            ),
            SerialBlockSlot(
                operator.LabelImages,
                operator.LabelInputs,
                operator.NonzeroLabelBlocks,
                name='LabelSets',
                subname='labels{:0}',
                selfdepends=False,
            ),
            self.predictionSlot,
            SerialBoxSlot(
                operator.opTrain.BoxConstraintRois,
                operator.opTrain,
                name='Rois',
                subname='rois{:04d}',
            ),
            SerialBoxSlot(
                operator.opTrain.BoxConstraintValues,
                operator.opTrain,
                name='Values',
                subname='values{:04d}',
            ),
            SerialSlot(
                operator.opTrain.Sigma,
                name='Sigma',
            ),
            SerialBoxSlot(
                operator.boxViewer.rois,
                operator.boxViewer,
                name='ViewRois',
                subname='viewrois{:04d}',
            ),
            SerialCountingSlot(
                operator.Classifier,
                operator.classifier_cache,
                name='CountingWrappers',
            ),
        ]

        super(CountingSerializer, self).__init__(projectFileGroupName, slots=slots)
        self.predictionSlot.progressSignal.subscribe(self.progressSignal)

    @property
    def predictionStorageEnabled(self):
        return self.predictionSlot.predictionStorageEnabled

    @predictionStorageEnabled.setter
    def predictionStorageEnabled(self, value):
        self.predictionSlot.predictionStorageEnabled = value

    def cancel(self):
        self.predictionSlot.cancel()

    def isDirty(self):
        for slot in self.serialSlots:
            if slot == self.predictionSlot:
                continue
            if slot.dirty:
                return True
        if self.predictionSlot.predictionStorageEnabled:
            return self.predictionSlot.dirty
        return False


class Ilastik05ImportDeserializer(AppletSerializer):
    """
    Special (de)serializer for importing ilastik 0.5 projects.
    For now, this class is import-only.  Only the deserialize function is implemented.
    If the project is not an ilastik0.5 project, this serializer does nothing.
    """

    def __init__(self, topLevelOperator):
        super(Ilastik05ImportDeserializer, self).__init__('')
        self.mainOperator = topLevelOperator

    def serializeToHdf5(self, hdf5Group, projectFilePath):
        """Not implemented. (See above.)"""
        pass

    def deserializeFromHdf5(self, hdf5File, projectFilePath, headless=False):
        """If (and only if) the given hdf5Group is the root-level group of an
           ilastik 0.5 project, then the project is imported.  The pipeline is updated
           with the saved parameters and datasets."""
        # The group we were given is the root (file).
        # Check the version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # The pixel classification workflow supports importing projects in the old 0.5 format
        if ilastikVersion == 0.5:
            numImages = len(hdf5File['DataSets'])
            self.mainOperator.LabelInputs.resize(numImages)

            for index, (datasetName, datasetGroup) in enumerate(sorted(hdf5File['DataSets'].items())):
                try:
                    dataset = datasetGroup['labels/data']
                except KeyError:
                    # We'll get a KeyError if this project doesn't have labels for this dataset.
                    # That's allowed, so we simply continue.
                    pass
                else:
                    slicing = [slice(0,s) for s in dataset.shape]
                    self.mainOperator.LabelInputs[index][slicing] = dataset[...]

    def importClassifier(self, hdf5File):
        """
        Import the random forest classifier (if any) from the v0.5 project file.
        """
        # Not yet implemented.
        # The old version of ilastik didn't actually deserialize the
        #  classifier, but it did determine how many trees were used.
        pass

    def isDirty(self):
        """Always returns False because we don't support saving to ilastik0.5 projects"""
        return False

    def unload(self):
        # This is a special-case import deserializer.  Let the real deserializer handle unloading.
        pass

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        assert False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath, headless=False):
        # This deserializer is a special-case.
        # It doesn't make use of the serializer base class, which makes assumptions about the file structure.
        # Instead, if overrides the public serialize/deserialize functions directly
        assert False
