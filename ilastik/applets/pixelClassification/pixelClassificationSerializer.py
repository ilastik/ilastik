from ilastik.applets.base.appletSerializer import AppletSerializer, SerialClassifierSlot, SerialBlockSlot, SerialListSlot

class PixelClassificationSerializer(AppletSerializer):
    """Encapsulate the serialization scheme for pixel classification
    workflow parameters and datasets.

    """
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialListSlot(operator.LabelNames,
                                transform=str),
                 SerialListSlot(operator.LabelColors, transform=lambda x: tuple(x.flat)),
                 SerialListSlot(operator.PmapColors, transform=lambda x: tuple(x.flat)),
                 SerialBlockSlot(operator.LabelImages,
                                 operator.LabelInputs,
                                 operator.NonzeroLabelBlocks,
                                 name='LabelSets',
                                 subname='labels{:03d}',
                                 selfdepends=False,
                                 shrink_to_bb=True),
                 SerialClassifierSlot(operator.Classifier,
                                      operator.classifier_cache,
                                      name="ClassifierForests",
                                      subname="Forest{:04d}") ]

        super(PixelClassificationSerializer, self).__init__(projectFileGroupName,
                                                            slots=slots)

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

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        # This deserializer is a special-case.
        # It doesn't make use of the serializer base class, which makes assumptions about the file structure.
        # Instead, if overrides the public serialize/deserialize functions directly
        assert False
