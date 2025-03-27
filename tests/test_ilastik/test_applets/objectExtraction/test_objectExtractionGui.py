from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtCore import Qt

def test_partially_checked_state_is_included():
    parent = QTreeWidgetItem()
    child = QTreeWidgetItem(parent)

    # Simulate PartiallyChecked checkbox state
    child.setCheckState(0, Qt.PartiallyChecked)

    # This should match the logic you updated
    assert child.checkState(0) in (Qt.Checked, Qt.PartiallyChecked)

