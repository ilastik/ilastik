from enum import Enum
import logging
import os
from pathlib import Path
import traceback
from functools import wraps
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QPushButton,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QGroupBox,
    QApplication,
)
import yaml

from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.utility.gui import threadRouted
from lazyflow.operators.tiktorch.classifier import UnetConfig

from .tiktorchController import TiktorchUnetController, TiktorchUnetOperatorModel

logger = logging.getLogger(__file__)


def busy_cursor(func):
    """
    A decorator to set the cursor to 'busy' (wait cursor) while a function is running,
    and reset it back to normal after the function completes.

    todo: move this to utils
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        app = QApplication.instance()
        if app:
            app.setOverrideCursor(Qt.WaitCursor)
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            if app:
                app.restoreOverrideCursor()

    return wrapper


class ModelDim(Enum):
    TWO = 2
    THREE = 3


def expand_loaders_path(yaml_str) -> str:
    yaml_config = yaml.safe_load(yaml_str)
    train_files_path = yaml_config["loaders"]["train"]["file_paths"]
    assert len(train_files_path) == 1, "we assume that it is a directory with all the training subdirectories"
    val_files_path = yaml_config["loaders"]["val"]["file_paths"]
    assert len(val_files_path) == 1, "we assume that it is a directory with all the training subdirectories"
    train_file_path = train_files_path[0]
    val_file_path = val_files_path[0]

    train_files = os.listdir(train_file_path)
    val_files = os.listdir(val_file_path)
    train_files = [os.path.join(train_file_path, f) for f in train_files]
    val_files = [os.path.join(val_file_path, f) for f in val_files]
    yaml_config["loaders"]["train"]["file_paths"] = train_files
    yaml_config["loaders"]["val"]["file_paths"] = val_files

    # convert yaml_config to string
    config = yaml.dump(yaml_config)
    return config


def _sample_unet2d_config(
    *,
    checkpoint_dir: Path,
    train_data_dir: Path,
    val_data_path: Path,
    epochs: int,
    batch_size: int,
    in_channels: int,
    out_channels: int,
    resume: Optional[str] = None,
    device: str = "cpu",
    model_dim: ModelDim = ModelDim.TWO,
):
    # todo: upsampling makes model torchscript incompatible
    model_name = "UNet2D" if model_dim == ModelDim.TWO else "UNet3D"
    base = f"""
device: {device}  # Use CPU for faster test execution, change to 'cuda' if GPU is available and necessary
# Trained on data from the 2018 Kaggle Data Science Bowl: https://www.kaggle.com/c/data-science-bowl-2018/data
model:
  name: {model_name}
  in_channels: {in_channels}
  out_channels: {out_channels}
  layer_order: cr
  num_groups: 8
  f_maps: [32, 64, 128]
  final_sigmoid: true
  is_segmentation: true
trainer:
  checkpoint_dir: {checkpoint_dir}
  resume: null
  pre_trained: null
  validate_after_iters: 10
  log_after_iters: 1
  max_num_epochs: {epochs}
  max_num_iterations: 150000
  eval_score_higher_is_better: True
optimizer:
  learning_rate: 0.0002
  weight_decay: 0.00001
loss:
  name: BCEDiceLoss
  skip_last_target: true
eval_metric:
  name: BlobsAveragePrecision
  use_last_target: true
  metric: 'ap'
lr_scheduler:
  name: ReduceLROnPlateau
  mode: max
  factor: 0.2
  patience: 30
loaders:
  dataset: DSB2018Dataset
  batch_size: {batch_size}
  num_workers: 1
  train:
    file_paths:
      - {train_data_dir}

    transformer:
      raw:
        - name: CropToFixed
          size: [256, 256]
        - name: Standardize
        - name: RandomFlip
        - name: RandomRotate90
        - name: RandomRotate
          axes: [[2, 1]]
          angle_spectrum: 45
          mode: reflect
        - name: ElasticDeformation
          spline_order: 3
          execution_probability: 0.2
        - name: GaussianBlur3D
          execution_probability: 0.5
        - name: AdditiveGaussianNoise
          execution_probability: 0.2
        - name: AdditivePoissonNoise
          execution_probability: 0.2
        - name: ToTensor
          expand_dims: true
      label:
        - name: CropToFixed
          size: [256, 256]
        - name: RandomFlip
        - name: RandomRotate90
        - name: RandomRotate
          axes: [[2, 1]]
          angle_spectrum: 45
          mode: reflect
        - name: ElasticDeformation
          spline_order: 0
          execution_probability: 0.2
        - name: Relabel
        - name: BlobsToMask
          append_label: true
        - name: ToTensor
          expand_dims: true
  val:
    file_paths:
      - {val_data_path}

    transformer:
      raw:
        - name: CropToFixed
          size: [256, 256]
          centered: true
        - name: Standardize
        - name: ToTensor
          expand_dims: true
      label:
        - name: CropToFixed
          size: [256, 256]
          # always get the same crop for validation
          centered: true
        - name: Relabel
        - name: BlobsToMask
          append_label: true
        - name: ToTensor
          expand_dims: true
"""
    if resume:
        config = f"resume: {resume}{base}"
    else:
        config = base
    return expand_loaders_path(config)


class FileWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.path_line_edit = QLineEdit(self)
        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.open_file_dialog)

        # Ensure path input is stretchable, but button is compact
        self.path_line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.browse_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        file_layout = QHBoxLayout()
        file_layout.addWidget(self.path_line_edit)
        file_layout.addWidget(self.browse_button)
        file_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        self.setLayout(file_layout)

    def open_file_dialog(self):
        """
        Opens a file dialog to select a directory and sets the selected path in the QLineEdit.
        """
        directory_path = QFileDialog.getExistingDirectory(self, "Select Directory", "")
        if directory_path:
            self.path_line_edit.setText(directory_path)

    @property
    def file(self) -> Path:
        file_path = Path(self.path_line_edit.text())
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path


class UnetForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.group_box = QGroupBox("U-Net Training Configuration", self)
        group_box_layout = QVBoxLayout(self.group_box)

        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.checkpoint_widget = FileWidget(self)
        self.form_layout.addRow("Checkpoint path:", self.checkpoint_widget)

        self.train_dir_widget = FileWidget(self)
        self.form_layout.addRow("Dataset Train path:", self.train_dir_widget)

        self.val_dir_widget = FileWidget(self)
        self.form_layout.addRow("Dataset Validation path:", self.val_dir_widget)

        self.optimizer_combo_box = QComboBox(self)
        self.optimizer_combo_box.addItems(["Adam", "SGD", "RMSprop", "Adagrad", "Adadelta"])
        self.form_layout.addRow("Optimizer:", self.optimizer_combo_box)

        self.batch_size_combo_box = QComboBox(self)
        batch_sizes = [str(2**i) for i in range(5, 11)]
        self.batch_size_combo_box.addItems(batch_sizes)
        self.form_layout.addRow("Batch size:", self.batch_size_combo_box)

        self.num_epochs = QSpinBox(self)
        self.num_epochs.setRange(1, 10000)
        self.num_epochs.setValue(1000)
        self.form_layout.addRow("Epochs:", self.num_epochs)

        self.in_channels = QSpinBox(self)
        self.in_channels.setRange(1, 10)
        self.in_channels.setValue(1)
        self.form_layout.addRow("In channels:", self.in_channels)

        self.out_channels = QSpinBox(self)
        self.out_channels.setRange(1, 10)
        self.out_channels.setValue(1)
        self.form_layout.addRow("Out channels:", self.out_channels)

        self.model_dims_combobox = QComboBox(self)
        self.model_dims_combobox.addItems(["2D", "3D"])
        self.form_layout.addRow("Model dims:", self.model_dims_combobox)

        group_box_layout.addLayout(self.form_layout)
        self.main_layout.addWidget(self.group_box)
        self.setLayout(self.main_layout)

    def get_config(self) -> UnetConfig:
        checkpoint_dir = self.checkpoint_widget.file
        train_dir = self.train_dir_widget.file
        val_dir = self.val_dir_widget.file

        # todo: optimizer
        optimizer = self.optimizer_combo_box.currentText()
        epochs = self.num_epochs.value()
        batch_size = int(self.batch_size_combo_box.currentText())

        # these attributes should be deduced by the input data
        model_dims = ModelDim.TWO if self.model_dims_combobox.currentText() == "2D" else ModelDim.THREE
        in_channels = self.in_channels.value()
        out_channels = self.out_channels.value()

        yaml_config_str = _sample_unet2d_config(
            checkpoint_dir=checkpoint_dir,
            train_data_dir=train_dir,
            val_data_path=val_dir,
            epochs=epochs,
            batch_size=batch_size,
            model_dim=model_dims,
            in_channels=in_channels,
            out_channels=out_channels,
        )
        unet_config = UnetConfig(yaml_config_str=yaml_config_str)
        return unet_config


class UnetStateControl(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.unet_form = UnetForm(self)

        button_layout = QHBoxLayout()
        self.start_stop_button = QToolButton(self)
        self.start_stop_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.start_stop_button.setCheckable(True)
        self.start_stop_button.toggled.connect(self.set_start_stop_training_icon)
        self.start_stop_button.toggled.connect(self._on_start_stop_toggled)

        self.liveTraining = QToolButton()
        self.liveTraining.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.liveTraining.setCheckable(True)
        self.liveTraining.toggled.connect(self.set_live_training_icon)

        self.livePrediction = QToolButton()
        self.livePrediction.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.livePrediction.setCheckable(True)
        self.livePrediction.toggled.connect(self.set_live_predict_icon)

        self.export = QPushButton()
        self.export.setText("Export as bioimageio zoo model")
        self.export.clicked.connect(self._on_export)

        button_layout.addWidget(self.start_stop_button)
        button_layout.addWidget(self.liveTraining)
        button_layout.addWidget(self.livePrediction)
        button_layout.addWidget(self.export)
        button_layout.addStretch()

        self.set_start_stop_training_icon(False)
        self.set_live_predict_icon(False)
        self.set_live_training_icon(False)

        layout.addWidget(self.unet_form)
        layout.addLayout(button_layout)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def set_live_training_icon(self, active: bool):
        if active:
            self.liveTraining.setIcon(QIcon(ilastikIcons.Pause))
            self.liveTraining.setText("Live Training")
            self.liveTraining.setToolTip("Pause training")
        else:
            self.liveTraining.setText("Live Training")
            self.liveTraining.setToolTip("Resume training")
            self.liveTraining.setIcon(QIcon(ilastikIcons.Play))

    def set_live_predict_icon(self, active: bool):
        if active:
            self.livePrediction.setText("Live Prediction")
            self.livePrediction.setIcon(QIcon(ilastikIcons.Pause))
        else:
            self.livePrediction.setText("Live Prediction")
            self.livePrediction.setIcon(QIcon(ilastikIcons.Play))

    def set_start_stop_training_icon(self, active: bool):
        if active:
            self.unet_form.group_box.setEnabled(False)
            self.start_stop_button.setIcon(QIcon(ilastikIcons.Stop))
            self.start_stop_button.setText("Abort Training")
            self.start_stop_button.setToolTip("Abort training")
        else:
            self.unet_form.group_box.setEnabled(True)
            self.start_stop_button.setText("Start Training")
            self.start_stop_button.setToolTip("Start training")
            self.start_stop_button.setIcon(QIcon(ilastikIcons.Upload))

    def _on_export(self, clicked: bool):
        directory_path = self.open_file_dialog()
        if not directory_path:
            return
        file_path = Path(directory_path) / "bioimageio.zip"  # todo: make it more generic, what if file exists?
        self._tiktorchModel.session.export(file_path=file_path)

    def open_file_dialog(self):
        """
        Opens a file dialog to select a directory and sets the selected path in the QLineEdit.
        """
        directory_path = QFileDialog.getExistingDirectory(self, "Select Directory", "")
        return directory_path

    def setTiktorchController(self, tiktorchController: TiktorchUnetController):
        self._tiktorchController = tiktorchController

    def setTiktorchModel(self, tiktorchModel: TiktorchUnetOperatorModel):
        self._tiktorchModel = tiktorchModel

    @busy_cursor
    def _initTraining(self):
        unet_config: UnetConfig = self.unet_form.get_config()
        self._tiktorchController.initTraining(unet_config=unet_config)
        self._tiktorchModel.session.start_training()

    @busy_cursor
    def _stopTraining(self):
        self._tiktorchController.closeSession()

    def _on_start_stop_toggled(self, checked: bool):
        try:
            self._initTraining() if checked else self._stopTraining()
        except Exception as e:
            self._showErrorMessage(e)

    @threadRouted
    def _showErrorMessage(self, exc):
        logger.error("".join(traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)))
        QMessageBox.critical(
            self, "ilastik detected a problem with your model", f"Failed to initialize model:\n {type(exc)} {exc}"
        )
