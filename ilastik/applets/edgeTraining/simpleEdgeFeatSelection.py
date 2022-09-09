###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2022, the ilastik developers
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
#           http://ilastik.org/license.html
###############################################################################
import enum
from functools import partial
from typing import Dict, List, Set

from ilastikrag.gui import FeatureSelectionDialog
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ilastik.utility.gui.widgets import silent_qobject
from ilastik.widgets.collapsibleWidget import CollapsibleWidget


class SimpleEdgeFeatureSelection(QDialog):
    """Simplified Edge feature selection dialog

    The feature set behind the simplified feature groups are hard-coded in
    `_defaultFeaturesStateDict`. These must be a subset of `supported_features`,
    otherwise the dialog errors out.

    `self._current_selection` is kept up to date via updateState callback from
    checkmarks of this dialog. After accepting the advanced dialog, it is updated
    via `_setFeatures`.

    Args:
      raw_channels: names of the raw channels that should be included in the selection
      boundary_channels: names of the channels that were considered when calculating the superpixels
      probability_channels names of the probability channels
      selection: dictionary of (initially) selected features per channel.
        {"channel_name": ["selected_feature1", "selected_feature2", ...]}
      supported_feaures: list of feature names -> passed to ilastikrag.gui.FeatureSelectionDialog
      data_is_3d: default feature set depends on dimensionality (2d vs 3d data)
      parent: parent widget - dialog is modal and will block the parent
    """

    @enum.unique
    class FeatureGroup(enum.Enum):
        shape = "shape"
        boundary_edge = "boundary channel along edges"
        boundary_sp = "boundary channel on superpixels"
        raw_edge = "raw data along edges"
        raw_sp = "raw data on superpixels"

    def __init__(
        self,
        raw_channels: List[str],
        boundary_channels: List[str],
        probability_channels: List[str],
        selection: Dict[str, List[str]],
        supported_features: List[str],
        data_is_3d: bool = False,
        parent: QWidget = None,
    ):
        super().__init__(parent)
        layout = QVBoxLayout()

        self.setWindowTitle("Edge Feature Selection")
        self.raw_channels = raw_channels
        self.boundary_channels = boundary_channels
        self.probability_channels = probability_channels
        self.data_is_3d = data_is_3d
        self.channel_names = raw_channels + boundary_channels + probability_channels
        # for the "big" feature selection dialog (ilastikrag)
        self.supported_features = supported_features

        self._internal_state = self._defaultFeaturesStateDict(raw_channels, boundary_channels, data_is_3d)

        def make_checkbox(name):
            checkbox = QCheckBox(name.value)
            details = self._internal_state[name]
            checkbox.stateChanged.connect(partial(self._updateState, name))
            checkbox.setToolTip(details["description"])
            return checkbox

        self.checkboxes = {}

        shapeGroupBox = QGroupBox("Shape")
        shapeLayout = QVBoxLayout()
        self.checkboxes[self.FeatureGroup.shape] = make_checkbox(self.FeatureGroup.shape)
        shapeLabel = QLabel(
            "Shape features take into account the shape of the superpixels. "
            "These include the length/area, as well as an estimate of radii of an "
            "ellipse/ellipsoid fitted to each edge."
        )
        shapeLabel.setWordWrap(True)

        shapeLayout.addWidget(self.checkboxes[self.FeatureGroup.shape])
        shapeLayout.addWidget(CollapsibleWidget(shapeLabel))
        shapeGroupBox.setLayout(shapeLayout)
        self.shapeGroupBox = shapeGroupBox

        layout.addWidget(shapeGroupBox)

        intensityGroupBox = QGroupBox("Intensity statistics")
        intensityLayout = QVBoxLayout()
        self.checkboxes[self.FeatureGroup.boundary_edge] = make_checkbox(self.FeatureGroup.boundary_edge)
        self.checkboxes[self.FeatureGroup.boundary_sp] = make_checkbox(self.FeatureGroup.boundary_sp)
        intensityLayout.addWidget(self.checkboxes[self.FeatureGroup.boundary_edge])
        intensityLayout.addWidget(self.checkboxes[self.FeatureGroup.boundary_sp])

        self.checkboxes[self.FeatureGroup.raw_edge] = make_checkbox(self.FeatureGroup.raw_edge)
        self.checkboxes[self.FeatureGroup.raw_sp] = make_checkbox(self.FeatureGroup.raw_sp)
        intensityLayout.addWidget(self.checkboxes[self.FeatureGroup.raw_edge])
        intensityLayout.addWidget(self.checkboxes[self.FeatureGroup.raw_sp])
        intensityLabel = QLabel(
            "Intensity statistics are computed along either edges or superpixel area/volume. "
            "Quantities computed include 10th and 90th quantile, and mean intensity. "
            "For raw data these quantities are computed per channel."
        )
        intensityLabel.setWordWrap(True)
        intensityLayout.addWidget(CollapsibleWidget(intensityLabel))
        intensityGroupBox.setLayout(intensityLayout)
        self.intensityGroupBox = intensityGroupBox
        layout.addWidget(intensityGroupBox)

        buttonbox = QDialogButtonBox(Qt.Horizontal)
        buttonbox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        advButton = QPushButton("Advanced")
        advButton.clicked.connect(self._openAdvancedDlg)
        self._advButton = advButton
        buttonbox.addButton(advButton, QDialogButtonBox.ActionRole)

        resetButton = QPushButton("Reset")
        resetButton.setToolTip("Reset selection to default.")
        resetButton.clicked.connect(self._resetToDefault)
        buttonbox.addButton(resetButton, QDialogButtonBox.ResetRole)
        layout.addWidget(buttonbox)

        self.setLayout(layout)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        self._setFeatures(selection)

    def _setFeatures(self, features: Dict[str, List[str]]):
        """update current feature set and synchronize GUI

        internal state is synchronized via callbacks on checkboxes.stateChanged

        Args:
          features: dictionary in the same format as used to set value in slots:
            {"channel_name": ["selected_feature1", "selected_feature2", ...]}
        """
        self._current_selection = features
        if not self._checkSelectionCompatible(self._current_selection):
            self._setEnabledState(False)
            for group, checkbox in self.checkboxes.items():
                with silent_qobject(checkbox) as w:
                    w.setChecked(Qt.Unchecked)
                    self._internal_state[group]["state"] = False
            return

        self._setEnabledState(True)

        # synchronize checkboxes
        if self._current_selection:
            checks = self._checkmarks(self._current_selection)
            for group, val in checks.items():
                with silent_qobject(self.checkboxes[group]) as w:
                    w.setCheckState(Qt.Checked if val else Qt.Unchecked)
                    self._internal_state[group]["state"] = val

    def _setEnabledState(self, state: bool):
        """User has selected something in the advanced dialog, disable all checkboxes."""
        self.intensityGroupBox.setEnabled(state)
        self.shapeGroupBox.setEnabled(state)

        if state:
            self._advButton.setText("Advanced")
            self._advButton.setToolTip("Open advanced Feature Selection Dialog for more fine-grained control.")
        else:
            self._advButton.setText("Advanced*")
            self._advButton.setToolTip(
                "Non-standard feature selection - reset or open advanced Feature Selection Dialog for more fine-grained control."
            )

    def _updateState(self, group, state):
        """update after checkbox change - always valid feature set"""
        self._internal_state[group]["state"] = bool(state)
        self._current_selection = SimpleEdgeFeatureSelection._to_feature_dict(self._internal_state)

    def _checkSelectionCompatible(self, selection) -> bool:
        for group, group_features in self._internal_state.items():
            # make sure that groups are not _partly_ selected
            for chan, features in group_features["features"].items():
                overlap_sum = sum(x in features for x in selection.get(chan, []))
                if overlap_sum not in [0, len(features)]:
                    return False
            # now check that there are no features not in the default_feauture_set
            feats_flat = SimpleEdgeFeatureSelection.default_features(
                self.raw_channels, self.boundary_channels, self.data_is_3d
            )
            for chan, feats in selection.items():
                if feats and (chan not in feats_flat):
                    return False
                if any(x not in feats_flat[chan] for x in feats):
                    return False
        return True

    def _resetToDefault(self):
        self._internal_state = self._defaultFeaturesStateDict(self.raw_channels, self.boundary_channels)
        self._setFeatures(SimpleEdgeFeatureSelection._to_feature_dict(self._internal_state))

    def _checkmarks(self, selection: Dict[str, List[str]]) -> Dict[str, bool]:
        if not self._checkSelectionCompatible(selection):
            # don't bother
            return {}

        checks = {}
        for group, group_features in self._internal_state.items():
            # make sure that groups are not _partly_ selected
            for chan, features in group_features["features"].items():
                overlap_sum = sum(x in features for x in selection.get(chan, []))
                if overlap_sum == len(features):
                    checks[group] = True
                else:
                    checks[group] = False

        return checks

    def _openAdvancedDlg(self):
        default_features = SimpleEdgeFeatureSelection._to_feature_dict(
            self._defaultFeaturesStateDict(self.raw_channels, self.boundary_channels)
        )

        dlg = FeatureSelectionDialog(
            self.channel_names, self.supported_features, self.selections(), default_features, parent=self
        )
        dlg_result = dlg.exec_()
        if dlg_result != dlg.Accepted:
            return

        selections = dlg.selections()
        self._setFeatures(selections)

    def selections(self) -> Dict[str, List[str]]:
        """
        feature selection compatible with operator/ilastikrag.gui.feature_selection_dialog

        returns:
          dict of currently selected features (values) per channel name (keys)
        """
        return self._current_selection

    @classmethod
    def _defaultFeaturesStateDict(cls, raw_channels, edge_channels, data_is_3d=False):
        default_sp_features = [
            "standard_sp_mean",
            "standard_sp_quantiles_10",
            "standard_sp_quantiles_90",
        ]
        default_boundary_features = [
            "standard_edge_mean",
            "standard_edge_quantiles_10",
            "standard_edge_quantiles_90",
        ]
        default_shape_feautures = [
            "edgeregion_edge_regionradii_0",
            "edgeregion_edge_regionradii_1",
        ]

        if data_is_3d:
            default_shape_feautures += ["edgeregion_edge_regionradii_2"]

        selected_features = {}

        for channel in raw_channels:
            selected_features[channel] = default_sp_features

        for channel in edge_channels:
            selected_features[channel] = default_boundary_features

        default_dialog_features = {
            cls.FeatureGroup.shape: {
                "features": {edge_channels[0]: default_shape_feautures},
                "state": True,
                "description": "Radii of the superpixel edges as estimated by eigenvalues of the PCA.",
            },
            cls.FeatureGroup.boundary_edge: {
                "description": "Intensity statistics (mean, Q10, Q90) computed on the boundary channel along the edges.",
                "features": {channel: default_boundary_features for channel in edge_channels},
                "state": True,
            },
            cls.FeatureGroup.raw_edge: {
                "description": "Intensity statistics (mean, Q10, Q90) computed on the raw data along the edges.",
                "features": {channel: default_boundary_features for channel in raw_channels},
                "state": False,
            },
            cls.FeatureGroup.boundary_sp: {
                "description": "Intensity statistics (mean, Q10, Q90) computed on the boundary channel on superpixels.",
                "features": {channel: default_sp_features for channel in edge_channels},
                "state": False,
            },
            cls.FeatureGroup.raw_sp: {
                "description": "Intensity statistics (mean, Q10, Q90) computed on the raw data on superpixels.",
                "features": {channel: default_sp_features for channel in raw_channels},
                "state": True,
            },
        }

        return default_dialog_features

    @staticmethod
    def _to_feature_dict(state_dict) -> Dict[str, List[str]]:
        selected_features: Dict[str, Set[str]] = {}

        for group_features in state_dict.values():
            if group_features["state"]:
                for channel, features in group_features["features"].items():
                    if channel not in selected_features:
                        selected_features[channel] = set()
                    selected_features[channel] |= set(features)

        return {k: list(v) for k, v in selected_features.items() if v}

    @classmethod
    def default_features(cls, raw_channels, boundary_channels, data_is_3d):
        return cls._to_feature_dict(cls._defaultFeaturesStateDict(raw_channels, boundary_channels, data_is_3d))


if __name__ == "__main__":
    import os
    import signal

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    os.environ["QT_MAC_WANTS_LAYER"] = "1"
    os.environ["VOLUMINA_SHOW_3D_WIDGET"] = "0"

    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    supported_features = [
        "edgeregion_edge_area",
        "edgeregion_edge_regionradii_0",
        "edgeregion_edge_regionradii_1",
        "standard_sp_mean",
        "standard_sp_quantiles_10",
        "standard_sp_quantiles_100",
        "standard_sp_quantiles_20",
        "standard_sp_quantiles_30",
        "standard_sp_quantiles_40",
        "standard_sp_quantiles_50",
        "standard_sp_quantiles_60",
        "standard_sp_quantiles_70",
        "standard_sp_quantiles_80",
        "standard_sp_quantiles_90",
        "standard_edge_mean",
        "standard_edge_quantiles_10",
        "standard_edge_quantiles_100",
        "standard_edge_quantiles_20",
        "standard_edge_quantiles_30",
        "standard_edge_quantiles_40",
        "standard_edge_quantiles_50",
        "standard_edge_quantiles_60",
        "standard_edge_quantiles_70",
        "standard_edge_quantiles_80",
        "standard_edge_quantiles_90",
    ]

    dlg = SimpleEdgeFeatureSelection(
        [
            "raw 0",
            "raw 1",
            "raw 2",
        ],
        ["boundary"],
        ["probs 1", "probs 2"],
        {
            "boundary": ["standard_sp_mean", "standard_sp_quantiles_10", "standard_sp_quantiles_90"],
            "raw 0": [
                "standard_edge_mean",
                "standard_edge_quantiles_10",
                "standard_edge_quantiles_90",
            ],
            "raw 51": [
                "standard_edge_mean",
                "standard_edge_quantiles_10",
                "standard_edge_quantiles_90",
            ],
            "raw 16": [
                "standard_edge_mean",
                "standard_edge_quantiles_10",
                "standard_edge_quantiles_90",
            ],
        },
        supported_features=supported_features,
    )
    dlg.exec_()

    if dlg.Accepted:
        from pprint import pprint

        pprint(dlg.selections())
