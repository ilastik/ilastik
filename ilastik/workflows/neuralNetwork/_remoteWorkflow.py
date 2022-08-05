###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2021, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
import logging

from ilastik.applets.neuralNetwork import NNClassApplet
from ilastik.applets.serverConfiguration import ServerConfigApplet
from ilastik.applets.serverConfiguration.types import Device, ServerConfig
from lazyflow.operators import tiktorch

from ._nnWorkflowBase import _NNWorkflowBase

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

    def _createClassifierApplet(self, headless=False, conn_str=None):
        # "Normal operation" - see also `connectLane`. Server applet is connected.
        self.nnClassificationApplet = NNClassApplet(
            self, "NNClassApplet", connectionFactory=self.serverConfigApplet.connectionFactory
        )

        self._applets.append(self.nnClassificationApplet)

    def _createInputAndConfigApplets(self):
        connFactory = tiktorch.TiktorchConnectionFactory()
        self.serverConfigApplet = ServerConfigApplet(self, connectionFactory=connFactory)
        self._applets.append(self.serverConfigApplet)
        super()._createInputAndConfigApplets()

    def connectLane(self, laneIndex):
        """
        connects the operators for different lanes, each lane has a laneIndex starting at 0
        """
        super().connectLane(laneIndex)

        if not self._headless:
            # "Normal operation", connect server applet.
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

    def _setup_classifier_op_for_batch(self):
        # relevant cmd args
        conn_str = self.parsed_args.connection_string

        # gather data from ServerConfig Op:
        saved_server_config = self.serverConfigApplet.topLevelOperator.ServerConfig.value

        device = None
        if not conn_str:
            conn_str = saved_server_config.address
            _devices = [d for d in saved_server_config.devices if d.enabled]
            assert len(_devices) == 1, "For now there is no support for mutlti-GPU anything from our side."
            device = _devices[0].id

        srv_config = ServerConfig(id="auto", address=conn_str, devices=[Device(id="cpu", name="cpu", enabled=True)])
        connFactory = tiktorch.TiktorchConnectionFactory()
        conn = connFactory.ensure_connection(srv_config)
        preferred_cuda_device_id, device_name = super()._configure_device(conn, saved_device=device)
        srv_config = srv_config.evolve(devices=[Device(id=preferred_cuda_device_id, name=device_name, enabled=True)])
        opClassify = self.nnClassificationApplet.topLevelOperator
        opClassify.ServerConfig.setValue(srv_config)

    def cleanUp(self):
        self.nnClassificationApplet.tiktorchController.closeSession()
        super().cleanUp()
