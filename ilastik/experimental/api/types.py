import numpy
import abc


class Pipeline(abc.ABC):

    @abc.abstractmethod
    def predict(self, data: numpy.ndarray) -> numpy.ndarray:
        ...
