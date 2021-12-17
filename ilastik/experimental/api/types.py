import numpy
import abc


class PixelClassificationPipeline(abc.ABC):
    @abc.abstractmethod
    def get_probabilities(self, raw_data: numpy.ndarray) -> numpy.ndarray:
        ...


class ObjectClassificationFromSegmentationPipeline(abc.ABC):
    @abc.abstractmethod
    def get_object_probabilities(self, raw_data: numpy.ndarray, segmentation_image: numpy.ndarray) -> numpy.ndarray:
        ...


class ObjectClassificationFromPredictionPipeline(abc.ABC):
    @abc.abstractmethod
    def get_object_probabilities(self, raw_data: numpy.ndarray, prediction_maps: numpy.ndarray) -> numpy.ndarray:
        ...
