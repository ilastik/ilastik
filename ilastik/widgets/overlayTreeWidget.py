###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################
from builtins import range
from qtpy.QtWidgets import QTreeWidgetItem, QTreeWidget, QTreeWidgetItemIterator
from qtpy.QtCore import Signal, Qt, QEvent


class OverlayTreeWidgetIter(QTreeWidgetItemIterator):
    def __init__(self, *args):
        QTreeWidgetItemIterator.__init__(self, *args)

    def __next__(self):
        self.__iadd__(1)
        value = self.value()
        if value:
            return self.value()
        else:
            return False


class OverlayTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, item, overlayPathName):
        """
        item:            OverlayTreeWidgetItem
        overlayPathName: string
                         full name of the overlay, for example 'File Overlays/My Data'
        """
        self.overlayPathName = overlayPathName
        QTreeWidgetItem.__init__(self, [item.name])
        self.item = item


class OverlayTreeWidget(QTreeWidget):
    spacePressed = Signal()

    def __init__(self, parent=None):
        QTreeWidget.__init__(self, parent)

        self.singleOverlaySelection = True

        self.header().close()
        self.setSortingEnabled(True)
        self.installEventFilter(self)
        self.spacePressed.connect(self.spacePressedTreewidget)
        self.itemChanged.connect(self.treeItemChanged)

    def addOverlaysToTreeWidget(self, overlayDict, forbiddenOverlays, preSelectedOverlays, singleOverlaySelection):
        self.singleOverlaySelection = singleOverlaySelection
        testItem = QTreeWidgetItem("a")
        for keys in list(overlayDict.keys()):
            if overlayDict[keys] in forbiddenOverlays:
                continue
            else:
                boolStat = False
                split = keys.split("/")
            for i in range(len(split)):
                if len(split) == 1:
                    newItemsChild = OverlayTreeWidgetItem(overlayDict[keys], keys)
                    self.addTopLevelItem(newItemsChild)
                    boolStat = False
                    if overlayDict[keys] in preSelectedOverlays:
                        newItemsChild.setCheckState(0, Qt.Checked)
                    else:
                        newItemsChild.setCheckState(0, Qt.Unchecked)

                elif i + 1 == len(split) and len(split) > 1:
                    newItemsChild = OverlayTreeWidgetItem(overlayDict[keys], keys)
                    testItem.addChild(newItemsChild)
                    if overlayDict[keys] in preSelectedOverlays:
                        newItemsChild.setCheckState(0, Qt.Checked)
                    else:
                        newItemsChild.setCheckState(0, Qt.Unchecked)

                elif self.topLevelItemCount() == 0 and i + 1 < len(split):
                    newItem = QTreeWidgetItem([split[i]])
                    self.addTopLevelItem(newItem)
                    testItem = newItem
                    boolStat = True

                elif self.topLevelItemCount() != 0 and i + 1 < len(split):
                    if boolStat == False:
                        for n in range(self.topLevelItemCount()):
                            if self.topLevelItem(n).text(0) == split[i]:
                                testItem = self.topLevelItem(n)
                                boolStat = True
                                break
                            elif n + 1 == self.topLevelItemCount():
                                newItem = QTreeWidgetItem([split[i]])
                                self.addTopLevelItem(newItem)
                                testItem = newItem
                                boolStat = True

                    elif testItem.childCount() == 0:
                        newItem = QTreeWidgetItem([split[i]])
                        testItem.addChild(newItem)
                        testItem = newItem
                        boolStat = True
                    else:
                        for x in range(testItem.childCount()):
                            if testItem.child(x).text(0) == split[i]:
                                testItem = testItem.child(x)
                                boolStat = True
                                break
                            elif x + 1 == testItem.childCount():
                                newItem = QTreeWidgetItem([split[i]])
                                testItem.addChild(newItem)
                                testItem = newItem
                                boolStat = True

    def treeItemChanged(self, item, column):
        currentItem = item
        it = OverlayTreeWidgetIter(self, QTreeWidgetItemIterator.Checked)
        while it.value():
            if self.singleOverlaySelection == True and currentItem.checkState(column) == Qt.Checked:
                if it.value() != currentItem:
                    it.value().setCheckState(0, Qt.Unchecked)
            next(it)

    def createSelectedItemList(self):
        selectedItemList = []
        it = OverlayTreeWidgetIter(self, QTreeWidgetItemIterator.Checked)
        while it.value():
            selectedItemList.append(it.value().item)
            next(it)
        return selectedItemList

    def spacePressedTreewidget(self):
        for item in self.selectedItems():
            if item.childCount() == 0:
                if item.checkState(0) == Qt.Unchecked:
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)

    def event(self, event):
        if (event.type() == QEvent.KeyPress) and (event.key() == Qt.Key_Space):
            self.spacePressed.emit()
            return True
        return QTreeWidget.event(self, event)


class OverlayEntry(object):
    def __init__(self, name):
        self.name = name


if __name__ == "__main__":
    import sys

    # make the program quit on Ctrl+C
    import signal

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from qtpy.QtWidgets import *

    app = QApplication(sys.argv)

    ex1 = OverlayTreeWidget()
    a = OverlayEntry("Labels")
    b = OverlayEntry("Raw Data")
    ex1.addOverlaysToTreeWidget({"Classification/Labels": a, "Raw Data": b}, [], [], True)
    ex1.show()
    ex1.raise_()

    app.exec_()
