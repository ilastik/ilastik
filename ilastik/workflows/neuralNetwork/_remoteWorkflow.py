import argparse
import logging

from ._nnWorkflowBase import _NNWorkflowBase
from ilastik.applets.serverConfiguration import ServerConfigApplet
from ilastik.applets.neuralNetwork import NNClassApplet, NNClassificationDataExportApplet

from lazyflow.operators import tiktorch

from lazyflow.graph import Graph


logger = logging.getLogger(__name__)


class RemoteWorkflow(_NNWorkflowBase):
    """
    This class provides workflow for a remote tiktorch server
    It has special server configuration applets allowing user to
    connect to remotely running tiktorch server managed by user
    """

    auto_register = True
    workflowName = "Neural Network Classification (Remote)"
    workflowDescription = "Allows to apply bioimage.io models on your data using remotely running tiktorch server"

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        super().__init__(shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs)

    def createClassifierApplet(self):
        self.nnClassificationApplet = NNClassApplet(
            self, "NNClassApplet", connectionFactory=self.serverConfigApplet.connectionFactory
        )
        self._applets.append(self.nnClassificationApplet)

    def createInputAndConfigApplets(self):
        connFactory = tiktorch.TiktorchConnectionFactory()
        self.serverConfigApplet = ServerConfigApplet(self, connectionFactory=connFactory)
        self._applets.append(self.serverConfigApplet)
        super().createInputAndConfigApplets()

    def connectLane(self, laneIndex):
        """
        connects the operators for different lanes, each lane has a laneIndex starting at 0
        """
        super().connectLane(laneIndex)
        opServerConfig = self.serverConfigApplet.topLevelOperator.getLane(laneIndex)
        opNNclassify = self.nnClassificationApplet.topLevelOperator.getLane(laneIndex)
        opNNclassify.ServerConfig.connect(opServerConfig.ServerConfig)

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        # If no data, nothing else is ready.
        serverConfig_finished = self.serverConfigApplet.topLevelOperator.ServerConfig.ready()
        super().handleAppletStateUpdateRequested(upstream_ready=serverConfig_finished)
