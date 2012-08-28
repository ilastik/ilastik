import os
#import tempfile
import vigra
import h5py
from ilastik.applets.base.appletSerializer import AppletSerializer
from ilastik.utility import bind
from lazyflow.operators import OpH5WriterBigDataset
import threading

import tempfile

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

from lazyflow.tracer import Tracer

class Section():
    Labels = 0
    Classifier = 1
    Predictions = 2

class PixelClassificationSerializer(AppletSerializer):
    """
    Encapsulate the serialization scheme for pixel classification workflow parameters and datasets.
    """
    SerializerVersion = 0.1
    
    def __init__(self, mainOperator, projectFileGroupName):
        with Tracer(traceLogger):
            super( PixelClassificationSerializer, self ).__init__( projectFileGroupName, self.SerializerVersion )
            self.mainOperator = mainOperator
            self._initDirtyFlags()
   
            # Set up handlers for dirty detection
            def handleDirty(section):
                self._dirtyFlags[section] = True
    
            self.mainOperator.Classifier.notifyDirty( bind(handleDirty, Section.Classifier) )
    
            def handleNewImage(section, slot, index):
                slot[index].notifyDirty( bind(handleDirty, section) )
    
            # These are multi-slots, so subscribe to dirty callbacks on each of their subslots as they are created
            self.mainOperator.LabelImages.notifyInserted( bind(handleNewImage, Section.Labels) )
            self.mainOperator.PredictionProbabilities.notifyInserted( bind(handleNewImage, Section.Predictions) )

            self._predictionStorageEnabled = False
            self._predictionStorageRequest = None
            self._predictionsPresent = False
                
    @property
    def predictionStorageEnabled(self):
        return self._predictionStorageEnabled
    
    @predictionStorageEnabled.setter
    def predictionStorageEnabled(self, enabled):
        self._predictionStorageEnabled = enabled
        if not self._predictionsPresent:
            self._dirtyFlags[Section.Predictions] = True
        
    def _initDirtyFlags(self):
        self._dirtyFlags = { Section.Labels      : False,
                             Section.Classifier  : False,
                             Section.Predictions : False }

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        with Tracer(traceLogger):

            numSteps = sum( self._dirtyFlags.values() )
            progress = 0
            if numSteps > 0:
                increment = 100/numSteps

            if self._dirtyFlags[Section.Labels]:
                self._serializeLabels( topGroup )            
                progress += increment
                self.progressSignal.emit( progress )
    
            if self._dirtyFlags[Section.Classifier]:
                self._serializeClassifier( topGroup )
                progress += increment
                self.progressSignal.emit( progress )

            # Need to call serialize predictions even if it isn't dirty
            # (Since it isn't always stored.)    
            self._serializePredictions( topGroup, progress, progress + increment )
            if self._dirtyFlags[Section.Predictions]:
                progress += increment
                self.progressSignal.emit( progress )

    def _serializeLabels(self, topGroup):
        with Tracer(traceLogger):
            # Delete all labels from the file
            self.deleteIfPresent(topGroup, 'LabelSets')
            labelSetDir = topGroup.create_group('LabelSets')
    
            numImages = len(self.mainOperator.NonzeroLabelBlocks)
            for imageIndex in range(numImages):
                # Create a group for this image
                labelGroupName = 'labels{:03d}'.format(imageIndex)
                labelGroup = labelSetDir.create_group(labelGroupName)
                
                # Get a list of slicings that contain labels
                nonZeroBlocks = self.mainOperator.NonzeroLabelBlocks[imageIndex].value
                for blockIndex, slicing in enumerate(nonZeroBlocks):
                    # Read the block from the label output
                    block = self.mainOperator.LabelImages[imageIndex][slicing].wait()
                    
                    # Store the block as a new dataset
                    blockName = 'block{:04d}'.format(blockIndex)
                    labelGroup.create_dataset(blockName, data=block)
                    
                    # Add the slice this block came from as an attribute of the dataset
                    labelGroup[blockName].attrs['blockSlice'] = self.slicingToString(slicing)
    
            self._dirtyFlags[Section.Labels] = False

    def _serializeClassifier(self, topGroup):
        with Tracer(traceLogger):
            self.deleteIfPresent(topGroup, 'Classifier')
            self._dirtyFlags[Section.Classifier] = False
    
            if not self.mainOperator.Classifier.ready():
                return

            classifier = self.mainOperator.Classifier.value

            # Classifier can be None if there isn't any training data yet.
            if classifier is None:
                return

            # Due to non-shared hdf5 dlls, vigra can't write directly to our open hdf5 group.
            # Instead, we'll use vigra to write the classifier to a temporary file.
            tmpDir = tempfile.mkdtemp()
            cachePath = os.path.join(tmpDir, 'classifier_cache.h5')
            classifier.writeHDF5(cachePath, 'Classifier')
            
            # Open the temp file and copy to our project group
            cacheFile = h5py.File(cachePath, 'r')
            topGroup.copy(cacheFile['Classifier'], 'Classifier')
            
            cacheFile.close()
            os.remove(cachePath)
            os.removedirs(tmpDir)

    def _serializePredictions(self, topGroup, startProgress, endProgress):
        """
        Called when the currently stored predictions are dirty.
        If prediction storage is currently enabled, store them to the file.
        Otherwise, just delete them/
        (Avoid inconsistent project states, e.g. don't allow old predictions to be stored with a new classifier.)
        """
        with Tracer(traceLogger):
            # If the predictions are missing, then maybe the user wants them stored (even if they aren't dirty)
            if self._dirtyFlags[Section.Predictions] or 'Predictions' not in topGroup.keys():

                self.deleteIfPresent(topGroup, 'Predictions')

                if self.predictionStorageEnabled:
                    predictionDir = topGroup.create_group('Predictions')
                    numImages = len(self.mainOperator.PredictionProbabilities)
    
                    if numImages > 0:
                        increment = (endProgress - startProgress) / float(numImages)
    
                    for imageIndex in range(numImages):
                        # Have we been cancelled?
                        if not self.predictionStorageEnabled:
                            break
    
                        datasetName = 'predictions{:04d}'.format(imageIndex)
    
                        progress = [startProgress]
    
                        # Use a big dataset writer to do this in chunks
                        opWriter = OpH5WriterBigDataset(self.mainOperator.graph)
                        opWriter.hdf5File.setValue( predictionDir )
                        opWriter.hdf5Path.setValue( datasetName )
                        opWriter.Image.connect( self.mainOperator.PredictionProbabilities[imageIndex] )
                        
                        # Create the request
                        self._predictionStorageRequest = opWriter.WriteImage[...]
    
                        def handleProgress(percent):
                            # Stop sending progress if we were cancelled
                            if self.predictionStorageEnabled:
                                progress[0] = startProgress + percent * (increment / 100.0)
                                self.progressSignal.emit( progress[0] )
                        opWriter.progressSignal.subscribe( handleProgress )
    
                        finishedEvent = threading.Event()
                        def handleFinish(request):
                            finishedEvent.set()
    
                        def handleCancel(request):
                            self._predictionStorageRequest = None
                            finishedEvent.set()
    
                        # Trigger the write and wait for it to complete or cancel.
                        self._predictionStorageRequest.notify(handleFinish)
                        self._predictionStorageRequest.onCancel(handleCancel)
                        finishedEvent.wait()
                        
                    # If we were cancelled, delete the predictions we just started
                    if not self.predictionStorageEnabled:
                        self.deleteIfPresent(predictionDir, datasetName)
                        self._predictionsPresent = False
                        startProgress = progress[0]
                    else:
                        self._dirtyFlags[Section.Predictions] = False
                        self._predictionsPresent = True

    def cancel(self):
        """Currently, this only cancels prediction storage."""
        if self._predictionStorageRequest is not None:
            self.predictionStorageEnabled = False
            self._predictionStorageRequest.cancel()

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        with Tracer(traceLogger):
            self.progressSignal.emit(0)            
            self._deserializeLabels( topGroup )
            self.progressSignal.emit(50)            
            self._deserializeClassifier( topGroup )
            
            self._predictionsPresent = 'Predictions' in topGroup.keys()
            
            self.progressSignal.emit(100)

    def _deserializeLabels(self, topGroup):
        with Tracer(traceLogger):
            try:
                labelSetGroup = topGroup['LabelSets']
            except KeyError:
                pass
            else:
                numImages = len(labelSetGroup)
                self.mainOperator.LabelInputs.resize(numImages)
        
                # For each image in the file
                for index, (groupName, labelGroup) in enumerate( sorted(labelSetGroup.items()) ):
                    # For each block of label data in the file
                    for blockData in labelGroup.values():
                        # The location of this label data block within the image is stored as an hdf5 attribute
                        slicing = self.stringToSlicing( blockData.attrs['blockSlice'] )
                        # Slice in this data to the label input
                        self.mainOperator.LabelInputs[index][slicing] = blockData[...]
            finally:
                self._dirtyFlags[Section.Labels] = False

    def _deserializeClassifier(self, topGroup):
        with Tracer(traceLogger):
            try:
                classifierGroup = topGroup['Classifier']
            except KeyError:
                pass
            else:
                # Due to non-shared hdf5 dlls, vigra can't read directly from our open hdf5 group.
                # Instead, we'll copy the classfier data to a temporary file and give it to vigra.
                tmpDir = tempfile.mkdtemp()
                cachePath = os.path.join(tmpDir, 'classifier_cache.h5')
                cacheFile = h5py.File(cachePath, 'w')
                cacheFile.copy(classifierGroup, 'Classifier')
                cacheFile.close()
        
                classifier = vigra.learning.RandomForest(cachePath, 'Classifier')
                os.remove(cachePath)
                os.removedirs(tmpDir)
                
                # Now force the classifier into our classifier cache.
                # The downstream operators (e.g. the prediction operator) can use the classifier without inducing it to be re-trained.
                # (This assumes that the classifier we are loading is consistent with the images and labels that we just loaded.
                #  As soon as training input changes, it will be retrained.)
                self.mainOperator.classifier_cache.forceValue( classifier )
            finally:
                self._dirtyFlags[Section.Classifier] = False

    def slicingToString(self, slicing):
        """
        Convert the given slicing into a string of the form '[0:1,2:3,4:5]'
        """
        strSlicing = '['
        for s in slicing:
            strSlicing += str(s.start)
            strSlicing += ':'
            strSlicing += str(s.stop)
            strSlicing += ','
        
        # Drop the last comma
        strSlicing = strSlicing[:-1]
        strSlicing += ']'
        return strSlicing
        
    def stringToSlicing(self, strSlicing):
        """
        Parse a string of the form '[0:1,2:3,4:5]' into a slicing (i.e. list of slices)
        """
        slicing = []
        # Drop brackets
        strSlicing = strSlicing[1:-1]
        sliceStrings = strSlicing.split(',')
        for s in sliceStrings:
            ends = s.split(':')
            start = int(ends[0])
            stop = int(ends[1])
            slicing.append(slice(start, stop))
        
        return slicing

    def isDirty(self):
        """
        Return true if the current state of this item 
        (in memory) does not match the state of the HDF5 group on disk.
        """
        flags = dict(self._dirtyFlags)
        flags[Section.Predictions] = False
        dirty = any(flags.values())
        dirty |= self._dirtyFlags[Section.Predictions] and self.predictionStorageEnabled
        
        return dirty

    def unload(self):
        """
        Called if either
        (1) the user closed the project or
        (2) the project opening process needs to be aborted for some reason
            (e.g. not all items could be deserialized properly due to a corrupted ilp)
        This way we can avoid invalid state due to a partially loaded project. """ 
        self.mainOperator.LabelInputs.resize(0)
        self.mainOperator.classifier_cache.Input.setDirty(slice(None))

class Ilastik05ImportDeserializer(AppletSerializer):
    """
    Special (de)serializer for importing ilastik 0.5 projects.
    For now, this class is import-only.  Only the deserialize function is implemented.
    If the project is not an ilastik0.5 project, this serializer does nothing.
    """
    SerializerVersion = 0.1

    def __init__(self, topLevelOperator):
        super( Ilastik05ImportDeserializer, self ).__init__( '', self.SerializerVersion )
        self.mainOperator = topLevelOperator
    
    def serializeToHdf5(self, hdf5Group, projectFilePath):
        """Not implemented. (See above.)"""
        pass
    
    def deserializeFromHdf5(self, hdf5File, projectFilePath):
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

            for index, (datasetName, datasetGroup) in enumerate( sorted( hdf5File['DataSets'].items() ) ):
                try:
                    dataset = datasetGroup['labels/data']
                except KeyError:
                    # We'll get a KeyError if this project doesn't have labels for this dataset.
                    # That's allowed, so we simply continue.
                    pass
                else:
                    self.mainOperator.LabelInputs[index][...] = dataset.value[...]

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

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        # This deserializer is a special-case.
        # It doesn't make use of the serializer base class, which makes assumptions about the file structure.
        # Instead, if overrides the public serialize/deserialize functions directly
        assert False






