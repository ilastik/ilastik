from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.pixelClassificationEnhancer.opPixelClassificationEnhancer import OpPixelClassificationEnhancer
from ilastik.applets.pixelClassificationEnhancer.pixelClassificationEnhancerSerializer import (
    PixelClassificationEnhancerSerializer,
)
from ilastik.applets.neuralNetwork.tiktorchController import TiktorchController, TiktorchOperatorModel


class TiktorchOperatorModelHack(TiktorchOperatorModel):
    def clear(self):
        self._state = self.State.Empty
        self._operator.ModelBinary.setValue(None)
        self._operator.ModelSession.setValue(None)
        self._operator.ModelInfo.setValue(None)
        self._operator.NumNNClasses.setValue(None)

    def setState(self, content, info, session):
        self._operator.ModelBinary.setValue(content)
        self._operator.ModelSession.setValue(session)
        self._operator.ModelInfo.setValue(info)
        self._operator.NumNNClasses.setValue(info.numClasses)


class PixelClassificationEnhancerApplet(PixelClassificationApplet):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """

    def __init__(self, workflow, projectFileGroupName, connectionFactory):
        self._topLevelOperator = OpPixelClassificationEnhancer(parent=workflow, connectionFactory=connectionFactory)

        def on_classifier_changed(slot, roi):
            if (
                self._topLevelOperator.classifier_cache.Output.ready()
                and self._topLevelOperator.classifier_cache.fixAtCurrent.value is True
                and self._topLevelOperator.classifier_cache.Output.value is None
            ):
                # When the classifier is deleted (e.g. because the number of features has changed,
                #  then notify the workflow. (Export applet should be disabled.)
                self.appletStateUpdateRequested()

        self._topLevelOperator.classifier_cache.Output.notifyDirty(on_classifier_changed)

        super(PixelClassificationApplet, self).__init__("Training")

        # We provide two independent serializing objects:
        #  one for the current scheme and one for importing old projects.
        self._serializableItems = [
            PixelClassificationEnhancerSerializer(
                self._topLevelOperator, projectFileGroupName
            ),  # Default serializer for new projects
        ]

        self._gui = None

        # GUI needs access to the serializer to enable/disable prediction storage
        self.predictionSerializer = self._serializableItems[0]

        # FIXME: For now, we can directly connect the progress signal from the classifier training operator
        #  directly to the applet's overall progress signal, because it's the only thing we report progress for at the moment.
        # If we start reporting progress for multiple tasks that might occur simulatneously,
        #  we'll need to aggregate the progress updates.
        self._topLevelOperator.opTrain.progressSignal.subscribe(self.progressSignal)

        self.tiktorchOpModel = TiktorchOperatorModelHack(self.topLevelOperator)
        self.tiktorchController = TiktorchController(self.tiktorchOpModel, connectionFactory)

    @property
    def singleLaneGuiClass(self):
        from .pixelClassificationEnhancerGui import (
            PixelClassificationEnhancerGui,
        )  # prevent imports of QT classes in headless mode

        return PixelClassificationEnhancerGui
