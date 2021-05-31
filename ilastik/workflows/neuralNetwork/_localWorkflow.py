import logging

from ilastik.config import runtime_cfg
from ilastik.applets.serverConfiguration.types import ServerConfig, Device
from ._nnWorkflowBase import _NNWorkflowBase
from ._localLauncher import LocalServerLauncher
from ilastik.applets.neuralNetwork import NNClassApplet
from lazyflow.operators import tiktorch


logger = logging.getLogger(__name__)


class LocalWorkflow(_NNWorkflowBase):
    """
    This class provides workflow for a local tiktorch executable.
    It can be specified via "--tiktorch_executable" command line parameter.
    Furthermore, the ilastik app will try to find a tiktorch version
    (usually the case when bundled for distribution) if the parameter is not
    supplied. If it cannot be found, workflow is not available.
    """

    auto_register = False
    workflowName = "Neural Network Classification (Local)"
    workflowDescription = "Allows to apply bioimage.io models on your data using bundled tiktorch"

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        tiktorch_exe_path = runtime_cfg.tiktorch_executable
        if not tiktorch_exe_path:
            raise RuntimeError("No tiktorch-executable specified")

        self._launcher = LocalServerLauncher(tiktorch_exe_path)
        super().__init__(shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs)

    def createClassifierApplet(self):
        conn_str = self._launcher.start()
        srv_config = ServerConfig(id="auto", address=conn_str, devices=[Device(id="cpu", name="cpu", enabled=True)])
        connFactory = tiktorch.TiktorchConnectionFactory()
        self.nnClassificationApplet = NNClassApplet(self, "NNClassApplet", connectionFactory=connFactory)
        opClassify = self.nnClassificationApplet.topLevelOperator
        opClassify.ServerConfig.setValue(srv_config)
        self._applets.append(self.nnClassificationApplet)
