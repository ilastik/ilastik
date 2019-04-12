from abc import ABC, abstractmethod
from typing import List, Iterator

import vigra.filters
import numpy

from ilastik.array5d import Slice5D, Point5D, Shape5D
from ilastik.array5d import Array5D, Image, ScalarImage
from ilastik.labels.sampler import Sampler
from ilastik.features.feature_extractor import FeatureExtractor

class ScribblingsOutOfBounds(Exception):
    def __init__(self, scribblings:Array5D, image:Array5D, offset:Array5D):
        super().__init__(f"Class map {scribblings} offset by {offset} exceeds bounds of image {image}")

class Annotation:
    "Represents a list of pixels belonging to a classification class"
    def __init__(self, scribblings:Sampler, image:Array5D, offset:Point5D=Point5D.zero()):
        """
        scribblings: bounding box of some scribblings. 0-valued pixels are considered not annotated
        image: The image onto which these annotations were made
        offset: position of the top-left corner of class-map inside the image shape
        """
        if scribblings.shape + offset > image.shape:
            raise ScribblingsOutOfBounds(scribblings=scribblings, image=image, offset=offset)
        self.scribblings = scribblings
        self.image = image
        self.offset = offset
        self._samples = None

    def get_samples(self, feature_extractor:FeatureExtractor):
        if self._samples is not None:
            return self._samples
        roi = self.scribblings.shape.to_slice_5d().offset(self.offset)
        roi = roi.with_coord(c=slice(0, self.image.shape.c))
        features = feature_extractor.compute(self.image.cut(roi))
        return self.scribblings.sample(features)

    def __repr__(self):
        return f"<labels for image: {self.image}>"
