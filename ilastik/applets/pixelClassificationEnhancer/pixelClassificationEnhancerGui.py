from ilastik.applets.pixelClassification.pixelClassificationGui import PixelClassificationGui
from ..pixelClassification.FeatureSelectionDialog import FeatureSelectionDialog

from functools import partial

import sip
from PyQt5.QtWidgets import QComboBox, QLabel, QHBoxLayout, QPushButton, QMenu, QAction


class PixelClassificationEnhancerGui(PixelClassificationGui):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__cleanup_fns = []
        drawer = self._labelControlUi

        channel_selector = QPushButton()
        self.channel_menu = QMenu(self)  # Must retain menus (in self) or else they get deleted.
        channel_selector.setMenu(self.channel_menu)
        channel_selector.clicked.connect(channel_selector.showMenu)

        def populate_channel_menu(*args):
            if sip.isdeleted(channel_selector):
                return
            self.channel_menu.clear()
            self.channel_actions = []
            label_names = self.topLevelOperatorView.LabelNames.value
            for i, label_name in enumerate(label_names):
                action = QAction(label_name, self.channel_menu)
                action.setCheckable(True)
                self.channel_menu.addAction(action)
                self.channel_actions.append(action)
                action.toggled.connect(self.onChannelSelectionClicked)

        populate_channel_menu()
        self.__cleanup_fns.append(self.topLevelOperatorView.LabelNames.notifyDirty(populate_channel_menu))

        channel_selector.setToolTip("Select Channels for NN input")
        channel_selection_layout = QHBoxLayout()
        channel_selection_layout.addWidget(QLabel("Select Channels"))
        channel_selection_layout.addWidget(channel_selector)
        drawer.verticalLayout.addLayout(channel_selection_layout)
        self._channel_selector = channel_selector

    def onChannelSelectionClicked(self, *args):
        channel_selections = []
        for ch in range(len(self.channel_actions)):
            if self.channel_actions[ch].isChecked():
                channel_selections.append(ch)

        self.topLevelOperatorView.SelectedChannels.setValue(channel_selections)

    def stopAndCleanUp(self):
        for fn in self.__cleanup_fns:
            fn()

        # Base class
        super().stopAndCleanUp()

    def setupLayers(self):

        layers = []
        # EnhancerInput
        enhancer_slot = self.topLevelOperatorView.EnhancerInput
        if enhancer_slot is not None and enhancer_slot.ready():
            layer = self.createStandardLayerFromSlot(enhancer_slot, name="EnhancerInput")
            layers.append(layer)

        layers.extend(super().setupLayers())
        return layers

    def initFeatSelDlg(self):
        thisOpFeatureSelection = (
            self.topLevelOperatorView.parent.featureSelectionApplet.topLevelOperator.innerOperators[0]
        )

        self.featSelDlg = FeatureSelectionDialog(thisOpFeatureSelection, self, self.labelListData)
