from ilastik.applets.neuralNetwork.tiktorchController import TiktorchController
from ilastik.applets.pixelClassification import PixelClassificationApplet, PixelClassificationSerializer

from .opTrainableDomainAdaptation import OpTrainableDomainAdaptation
from .tiktorchController import TrainableDomaninAdaptationTiktorchOperatorModel
from .trainableDomainAdaptationSerializer import TrainableDomainAdaptationSerializer


class TrainableDomainAdaptationApplet(PixelClassificationApplet):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """

    def __init__(self, workflow, projectFileGroupName, connectionFactory):
        self._topLevelOperator = OpTrainableDomainAdaptation(parent=workflow, connectionFactory=connectionFactory)

        def on_classifier_changed(slot, roi):
            if (
                self._topLevelOperator.classifier_cache.Output.ready()
                and self._topLevelOperator.classifier_cache.fixAtCurrent.value is True
                and not self._topLevelOperator.classifier_cache.hasCacheValue()
            ):
                # When the classifier is deleted (e.g. because the number of features has changed,
                #  then notify the workflow. (Export applet should be disabled.)
                self.appletStateUpdateRequested()

        self._topLevelOperator.classifier_cache.Output.notifyDirty(on_classifier_changed)

        super(PixelClassificationApplet, self).__init__("Training")

        # We provide two independent serializing objects:
        #  one for the current scheme and one for importing old projects.
        self._serializableItems = [
            PixelClassificationSerializer(self._topLevelOperator, projectFileGroupName),
            TrainableDomainAdaptationSerializer(self._topLevelOperator, projectFileGroupName),
        ]

        self._gui = None

        # GUI needs access to the serializer to enable/disable prediction storage
        self.predictionSerializer = self._serializableItems[0]

        # FIXME: For now, we can directly connect the progress signal from the classifier training operator
        #  directly to the applet's overall progress signal, because it's the only thing we report progress for at the moment.
        # If we start reporting progress for multiple tasks that might occur simulatneously,
        #  we'll need to aggregate the progress updates.
        self._topLevelOperator.opTrain.progressSignal.subscribe(self.progressSignal)

        self.tiktorchOpModel = TrainableDomaninAdaptationTiktorchOperatorModel(self.topLevelOperator)
        self.tiktorchController = TiktorchController(self.tiktorchOpModel, connectionFactory)

    @property
    def singleLaneGuiClass(self):
        # prevent imports of QT classes in headless mode
        from .trainableDomainAdaptationGui import TrainableDomainAdaptationGui

        return TrainableDomainAdaptationGui
