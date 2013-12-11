import os
import logging
from functools import partial

from PyQt4 import uic

from ilastik.utility import bind
from ilastik.utility.gui import threadRouted

# parent GUI
from ilastik.applets.thresholdTwoLevels.thresholdTwoLevelsGui import ThresholdTwoLevelsGui

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)


class GraphCutSegmentationGui(ThresholdTwoLevelsGui):

    def __init__(self, *args, **kwargs):
        self.__cleanup_fns = []  # this has to be here, but why??
        super(GraphCutSegmentationGui, self).__init__(*args, **kwargs)
        self._showDebug = False

    def initAppletDrawerUi(self):
        """
        Reimplemented from LayerViewerGui base class.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(os.path.join(localDir,"drawer.ui"))

        self._allWatchedWidgets = [
            self._drawer.inputChannelSpinBox,
            self._drawer.betaSpinBox]

        for widget in self._allWatchedWidgets:
            # If the user pressed enter inside a spinbox, auto-click "Apply"
            widget.installEventFilter(self)

        self._updateGuiFromOperator()
        self.topLevelOperatorView.InputImage.notifyReady(
            bind(self._updateGuiFromOperator))
        self.__cleanup_fns.append(
            partial(self.topLevelOperatorView.InputImage.unregisterUnready,
                    bind(self._updateGuiFromOperator)))

        self.topLevelOperatorView.InputImage.notifyMetaChanged(
            bind(self._updateGuiFromOperator))
        self.__cleanup_fns.append(
            partial(self.topLevelOperatorView.InputImage.unregisterMetaChanged,
                    bind(self._updateGuiFromOperator)))

    @threadRouted
    def _updateGuiFromOperator(self):
        op = self.topLevelOperatorView

        numChannels = 0
        if op.InputImage.ready():
            # Channel
            channelIndex = op.InputImage.meta.axistags.index('c')
            numChannels = op.InputImage.meta.shape[channelIndex]
        self._drawer.inputChannelSpinBox.setRange(0, numChannels-1)
        self._drawer.inputChannelSpinBox.setValue(op.Channel.value)

        # Beta
        self._drawer.betaSpinBox.setValue(op.Beta.value)

    def _updateOperatorFromGui(self):
        op = self.topLevelOperatorView

        # Read all gui settings before updating the operator
        # (The gui is still responding to operator changes, 
        #  and we don't want it to update until we've read all gui values.)

        # Read Channel
        channel = self._drawer.inputChannelSpinBox.value()
        
        # read beta
        beta = self._drawer.betaSpinBox.value()

        # Apply new settings to the operator
        op.Channel.setValue(channel)
        op.Beta.setValue(beta)
