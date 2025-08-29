import os
import logging

from contextlib import contextmanager

from qtpy import uic
from qtpy.QtCore import QStateMachine, QState, QSignalTransition, Signal, Qt, QEvent
from qtpy.QtWidgets import QWidget, QLineEdit, QListWidget, QMessageBox, QListWidgetItem

from . import types


logger = logging.getLogger(__name__)


class ServerConfigForm(QWidget):
    nameEdit: QLineEdit
    addressEdit: QLineEdit
    deviceList: QListWidget
    gotDevices = Signal()

    UI_FILE = "serverConfigForm.ui"

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value
        self._updateFieldsFromConfig()

    def __init__(self, connectionFactory) -> None:
        super().__init__(None)
        self._config = types.ServerConfig.default()
        self._initUI()

        self._connectionFactory = connectionFactory
        self._updating = False

    @property
    def _ui_path(self):
        local_dir = os.path.dirname(__file__)
        return os.path.join(local_dir, self.UI_FILE)

    def _initUI(self):
        """
        Load the ui file for the central widget.
        """
        uic.loadUi(self._ui_path, self)
        # Trigger state updates
        self.nameEdit.textChanged.connect(self._updateConfigFromFields)
        self.addressEdit.textChanged.connect(self._updateConfigFromFields)
        self.deviceList.itemChanged.connect(self._updateConfigFromFields)

        # UI updates
        self.getDevicesBtn.clicked.connect(self._setDevices)
        self.deviceList.itemClicked.connect(self._deviceListSetCheckboxOnClick)

    def _deviceListSetCheckboxOnClick(self, item: "DeviceListWidgetItem") -> None:
        if not item:
            return
        item.setCheckState(not item.checkState())

    def _setDevicesFromConfig(self):
        self.deviceList.clear()
        for dev in self._config.devices:
            item = DeviceListWidgetItem(dev.id, dev.name, self.deviceList)
            item.setCheckState(dev.enabled)

    def _setDevices(self):
        current_devices = self._config.devices

        def get_device_state(id_):
            for dev in current_devices:
                if dev.id == id_:
                    return dev.enabled
            return False

        try:
            conn = self._connectionFactory.ensure_connection(self._config)
            devices = conn.get_devices()
        except Exception:
            logger.exception("Failed to connect to tiktoch server please check settings and try again")
            QMessageBox.critical(
                self, "Connection failed", "Failed to connect to tiktoch server please check settings and try again"
            )
            return

        new_devices = []

        for id_, name in devices:
            state = get_device_state(id_)
            new_devices.append(types.Device(id=id_, name=name, enabled=state))

        self._config = self._config.evolve(devices=new_devices)
        self._updateFieldsFromConfig()
        self.gotDevices.emit()

    def _getDevices(self):
        result = []
        for idx in range(self.deviceList.count()):
            item = self.deviceList.item(idx)
            result.append(types.Device(id=item.id, name=item.name, enabled=bool(item.checkState())))

        return result

    @contextmanager
    def _batch_update_fields(self):
        self._updating = True
        yield
        self._updating = False

    def _updateConfigFromFields(self):
        if self._updating:
            return

        self._config.name = self.nameEdit.text()
        self._config.address = self.addressEdit.text()
        self._config.devices = self._getDevices()

    def _updateFieldsFromConfig(self):
        with self._batch_update_fields():
            self.nameEdit.setText(self._config.name)
            self.addressEdit.setText(self._config.address)
            self._setDevicesFromConfig()

    def keyPressEvent(self, event):
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if self.saveBtn.isEnabled():
                    self.saveBtn.click()

        super().keyPressEvent(event)


class ServerFormWorkflow:
    class CheckedTranstion(QSignalTransition):
        def __init__(self, signal, *, target, testFn):
            super().__init__(signal)
            self.setTargetState(target)
            self._testFn = testFn

        def eventTest(self, event) -> bool:
            if not super().eventTest(event):
                return False

            return self._testFn()

    def __init__(self, form) -> None:
        self._form = form

        self._machine = machine = QStateMachine()

        init = self._make_initial_state(form)
        dev_fetched = self._make_dev_fetched_state(form)
        save = self._make_save_state(form)

        machine.addState(init)
        machine.addState(dev_fetched)
        machine.addState(save)
        machine.setInitialState(init)

        init.addTransition(form.gotDevices, dev_fetched)

        unselected_tr = self.CheckedTranstion(
            form.deviceList.itemChanged, target=dev_fetched, testFn=lambda: not self._hasSelectedItems()
        )
        save.addTransition(unselected_tr)
        save.addTransition(form.editBtn.clicked, init)

        selected_tr = self.CheckedTranstion(form.deviceList.itemChanged, target=save, testFn=self._hasSelectedItems)
        entered_dev_feched = self.CheckedTranstion(dev_fetched.entered, target=save, testFn=self._hasSelectedItems)

        dev_fetched.addTransition(selected_tr)
        dev_fetched.addTransition(entered_dev_feched)
        dev_fetched.addTransition(form.editBtn.clicked, init)

        machine.start()

    def _hasSelectedItems(self):
        for idx in range(self._form.deviceList.count()):
            if self._form.deviceList.item(idx).checkState():
                return True

        return False

    def restart(self):
        self._machine.stop()
        self._machine.stopped.connect(self._machine.start)

    def _make_initial_state(self, form) -> QState:
        s = QState()
        s.assignProperty(form.editBtn, "enabled", False)
        s.assignProperty(form.saveBtn, "enabled", False)
        s.assignProperty(form.deviceList, "enabled", False)
        s.assignProperty(form.addressEdit, "enabled", True)
        return s

    def _make_dev_fetched_state(self, form) -> QState:
        s = QState()
        s.assignProperty(form.editBtn, "enabled", True)
        s.assignProperty(form.deviceList, "enabled", True)
        s.assignProperty(form.saveBtn, "enabled", False)
        s.assignProperty(form.addressEdit, "enabled", False)

        return s

    def _make_save_state(self, form):
        s = QState()
        s.assignProperty(form.saveBtn, "enabled", True)
        return s


class DeviceListWidgetItem(QListWidgetItem):
    def __init__(self, id, name, parent):
        super().__init__(parent, type=QListWidgetItem.UserType)
        self.id = id
        self.name = name
        self.setText(f"{id} ({name})")
        self.setCheckState(Qt.Unchecked)
        # Negation of Qt.ItemIsUserCheckable so we would be able to toggle check state on line click
        # otherwise it will immediately uncheck
        self.setFlags(self.flags() & (~Qt.ItemIsUserCheckable))

    def __repr__(self) -> str:
        return f"DeviceListWidgetItem(id: {self.id})"
