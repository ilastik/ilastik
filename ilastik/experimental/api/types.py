import numpy
import abc


class PixelClassificationPipeline(abc.ABC):
    @abc.abstractmethod
    def get_probabilities(self, raw_data: numpy.ndarray) -> numpy.ndarray:
        ...
