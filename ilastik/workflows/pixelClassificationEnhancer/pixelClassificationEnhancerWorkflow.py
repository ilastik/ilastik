from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from ilastik.applets.pixelClassification import PixelClassificationDataExportApplet
from ilastik.applets.pixelClassificationEnhancer import PixelClassificationEnhancerApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet
from lazyflow.graph import Graph

from ilastik.config import runtime_cfg
from ilastik.applets.serverConfiguration.types import ServerConfig, Device

from ilastik.workflows.neuralNetwork._localLauncher import LocalServerLauncher
from lazyflow.operators import tiktorch as tiktorch_lf


import logging

logger = logging.getLogger(__name__)


class PixelClassificationEnhancerWorkflow(PixelClassificationWorkflow):
    workflowName = "Pixel Classification Enhancer"
    workflowDisplayName = "Pixel Classification Enhancer"
    workflowDescription = "Augment your predictions with Enhancer Neural Network."

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        # Applets for training (interactive) workflow
        graph = Graph()
        super(PixelClassificationWorkflow, self).__init__(
            shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs
        )
        self.stored_classifier = None
        self._applets = []
        self._workflow_cmdline_args = workflow_cmdline_args
        self.dataSelectionApplet = self.createDataSelectionApplet()
        opDataSelection = self.dataSelectionApplet.topLevelOperator

        data_instructions = (
            "Select your input data using the 'Raw Data' tab shown on the right.\n\n"
            "Power users: Optionally use the 'Prediction Mask' tab to supply a binary image that tells ilastik where it should avoid computations you don't need."
        )

        self.featureSelectionApplet = self.createFeatureSelectionApplet()

        tiktorch_exe_path = runtime_cfg.tiktorch_executable
        if not tiktorch_exe_path:
            raise RuntimeError("No tiktorch-executable specified")

        self._launcher = LocalServerLauncher(tiktorch_exe_path)

        self.pcApplet = self.createPixelClassificationEnhancerApplet()
        opClassify = self.pcApplet.topLevelOperator

        self.dataExportApplet = PixelClassificationDataExportApplet(self, "Prediction Export")
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.PmapColors.connect(opClassify.PmapColors)
        opDataExport.LabelNames.connect(opClassify.LabelNames)
        opDataExport.WorkingDirectory.connect(opDataSelection.WorkingDirectory)
        opDataExport.SelectionNames.setValue(self.ExportNames.asDisplayNameList())

        # Expose for shell
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.pcApplet)
        self._applets.append(self.dataExportApplet)

        self.dataExportApplet.prepare_for_entire_export = self.prepare_for_entire_export
        self.dataExportApplet.post_process_entire_export = self.post_process_entire_export

        self.batchProcessingApplet = BatchProcessingApplet(
            self, "Batch Processing", self.dataSelectionApplet, self.dataExportApplet
        )

        # meh:
        self.generate_random_labels = False
        self.print_labels_by_slice = False
        self.variable_importance_path = False
        self.tree_count = False
        self.label_proportion = False
        self.retrain = False

        # meh pt. 2
        self._batch_export_args = False
        self._batch_input_args = False

    def createPixelClassificationEnhancerApplet(self):

        server_config, connection_factory = self._start_local_server()

        pce_appplet = PixelClassificationEnhancerApplet(
            self, "PixelClassificationEnhancer", connectionFactory=connection_factory
        )
        opClassify = pce_appplet.topLevelOperator
        opClassify.ServerConfig.setValue(server_config)
        return pce_appplet

    def _start_local_server(self):
        conn_str = self._launcher.start()
        srv_config = ServerConfig(id="auto", address=conn_str, devices=[Device(id="cpu", name="cpu", enabled=True)])
        connFactory = tiktorch_lf.TiktorchConnectionFactory()
        conn = connFactory.ensure_connection(srv_config)

        devices = conn.get_devices()
        preferred_cuda_device_id = runtime_cfg.preferred_cuda_device_id
        device_ids = [dev[0] for dev in devices]
        cuda_devices = tuple(d for d in device_ids if d.startswith("cuda"))

        if preferred_cuda_device_id not in device_ids:
            if preferred_cuda_device_id:
                logger.warning(f"Could nor find preferred cuda device {preferred_cuda_device_id}")
            try:
                preferred_cuda_device_id = cuda_devices[0]
            except IndexError:
                preferred_cuda_device_id = "cpu"

            logger.info(f"Using default device for Neural Network Workflow {preferred_cuda_device_id}")
        else:
            logger.info(f"Using specified device for Neural Netowrk Workflow {preferred_cuda_device_id}")

        device_name = devices[device_ids.index(preferred_cuda_device_id)][1]

        srv_config = srv_config.evolve(devices=[Device(id=preferred_cuda_device_id, name=device_name, enabled=True)])

        return srv_config, connFactory
