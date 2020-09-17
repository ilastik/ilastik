import numpy
import abc


class Classifier(abc.ABC):

    @abc.abstractmethod
    def predict(self, data: numpy.ndarray) -> numpy.ndarray:
        ...
