# -*- coding: utf-8 -*-
from PyQt4.QtGui import QTreeWidgetItem, QTreeWidget, QTreeWidgetItemIterator
from PyQt4.QtCore import pyqtSignal, Qt, QEvent, SIGNAL


class OverlayTreeWidgetIter(QTreeWidgetItemIterator):
    def __init__(self, *args):
        QTreeWidgetItemIterator.__init__(self, *args)
    def next(self):
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
    spacePressed = pyqtSignal()
    
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
        for keys in overlayDict.keys():
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
                    
                elif i+1 == len(split) and len(split) > 1:
                    newItemsChild = OverlayTreeWidgetItem(overlayDict[keys], keys)
                    testItem.addChild(newItemsChild)
                    if overlayDict[keys] in preSelectedOverlays:
                        newItemsChild.setCheckState(0, Qt.Checked)
                    else:
                        newItemsChild.setCheckState(0, Qt.Unchecked)
                    
                elif self.topLevelItemCount() == 0 and i+1 < len(split):
                    newItem = QTreeWidgetItem([split[i]])
                    self.addTopLevelItem(newItem)
                    testItem = newItem
                    boolStat = True
                    
                elif self.topLevelItemCount() != 0 and i+1 < len(split):
                    if boolStat == False:
                        for n in range(self.topLevelItemCount()):
                            if self.topLevelItem(n).text(0) == split[i]:
                                testItem = self.topLevelItem(n)
                                boolStat = True
                                break
                            elif n+1 == self.topLevelItemCount():
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
                            elif x+1 == testItem.childCount():
                                newItem = QTreeWidgetItem([split[i]])
                                testItem.addChild(newItem)
                                testItem = newItem
                                boolStat = True
                                
    def treeItemChanged(self, item, column):
        currentItem = item
        it = OverlayTreeWidgetIter(self, QTreeWidgetItemIterator.Checked)
        while (it.value()):
            if self.singleOverlaySelection == True and currentItem.checkState(column) == Qt.Checked:
                if it.value() != currentItem:
                    it.value().setCheckState(0, Qt.Unchecked)
            it.next()

                                
    def createSelectedItemList(self):
        selectedItemList = []
        it = OverlayTreeWidgetIter(self, QTreeWidgetItemIterator.Checked)
        while (it.value()):
            selectedItemList.append(it.value().item)
            it.next()
        return selectedItemList


    def spacePressedTreewidget(self):
        for item in self.selectedItems():
            if item.childCount() == 0:
                if item.checkState(0) == Qt.Unchecked:
                    item.setCheckState(0, Qt.Checked)
                else: 
                    item.setCheckState(0, Qt.Unchecked)
                    
    def event(self, event):
        if (event.type()==QEvent.KeyPress) and (event.key()==Qt.Key_Space):
            self.emit(SIGNAL("spacePressed"))
            return True
        return QTreeWidget.event(self, event)
    

class OverlayEntry:
    def __init__(self, name):
        self.name = name

if __name__ == "__main__":
    import sys
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import *
        
    app = QApplication(sys.argv)
    
    ex1 = OverlayTreeWidget()
    a = OverlayEntry("Labels")
    b = OverlayEntry("Raw Data")
    ex1.addOverlaysToTreeWidget({"Classification/Labels": a, "Raw Data": b}, [], [], True)
    ex1.show()
    ex1.raise_()        
    
    app.exec_() 
