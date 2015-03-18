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
#		   http://ilastik.org/license.html
###############################################################################
#SciPy
import numpy

#PyQt
from PyQt4.QtCore import QTimer, Qt
from PyQt4.QtGui import QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem

#lazyflow
from lazyflow.operators.arrayCacheMemoryMgr import ArrayCacheMemoryMgr
from lazyflow.operators.arrayCacheMemoryMgr import MemInfoNode

import warnings

#===------------------------------------------------------------------------===
#=== MemUsageDialog                                                         ===
#===------------------------------------------------------------------------===


class MemUsageDialog(QDialog):
    def __init__(self, parent=None, update=True):
        QDialog.__init__(self, parent=parent)
        layout = QVBoxLayout()
        self.tree = QTreeWidget()
        layout.addWidget(self.tree)
        self.setLayout(layout)

        self.memMgr = ArrayCacheMemoryMgr.instance

        self.timer = QTimer(self)
        if update:
            self.timer.timeout.connect(self._updateReport)
            self._updateReport()

        # tree setup code
        self.tree.setHeaderLabels(
            ["cache", "memory", "roi", "dtype", "type", "id"])
        self._idIndex = self.tree.columnCount() - 1
        self.tree.setColumnHidden(self._idIndex, True)
        self.tree.clear()

    def _updateReport(self):
        # we keep track of dirty reports so we just have to update the tree
        # instead of reconstructing it
        reports = []
        for c in self.memMgr.namedCaches:
            r = MemInfoNode()
            try:
                c.generateReport(r)
            except NotImplementedError:
                warnings.warn('cache operator {} does not implement generateReport()'.format(c))
            else:
                reports.append(r)
        self._updateBranch(self.tree.invisibleRootItem(), reports)

    def _updateBranch(self, branch, reports):
        # use dict for fast access
        d = dict((r.id, r) for r in reports)

        # check what can be reused
        toRemove = []
        toUpdate = set()
        for i in range(branch.childCount()):
            child = branch.child(i)
            childId = child.data(self._idIndex, Qt.DisplayRole)
            if childId not in d:
                toRemove.append(child)
            else:
                toUpdate.add(i)

        # update existent children
        for i in toUpdate:
            child = branch.child(i)
            childId = child.data(self._idIndex)
            r = d[childId]
            del d[childId]
            self._updateBranch(child, r.children)
            self._updateNode(child, r)

        # remove children if not in reports
        for child in reversed(toRemove):
            # delete from back to front to avoid index trouble
            branch.removeChild(child)

        # handle new reports (all remaining entries in d)
        for childId in d:
            self._addNode(branch, d[childId])

    def _updateNode(self, node, report):
        l = self._makeTreeWidgetItemData(report)
        for i, v in enumerate(l):
            node.setData(i, Qt.DisplayRole, v)

    def _addNode(self, branch, report):
        node = QTreeWidgetItem(branch)
        self._updateNode(node, report)
        for child in report.children:
            self._addNode(node, child)

    def _makeTreeWidgetItemData(self, report):
        l = []
        l.append("%r" % report.name)
        l.append("%1.1f MB" % (report.usedMemory/1024**2.0))
        if report.roi is not None:
            l.append("%r\n%r" % (list(report.roi[0]), list(report.roi[1])))
        else:
            l.append("")
        if report.dtype is not None:
            if report.dtype == numpy.float32:
                l.append("float32")
            elif report.dtype == numpy.uint8:
                l.append("uint8")
            elif report.dtype == numpy.uint32:
                l.append("uint32")
            elif report.dtype == numpy.float64:
                l.append("float64")
            else:
                l.append(str(report.dtype))

        else:
            l.append("")

        t = str(report.type)
        t = t[len("<type '")+1:-len("'>")]
        t = t.split(".")[-1]
        l.append(t)
        l.append(report.id)
        return l
            
    def hideEvent(self, event):
        self.timer.stop()
        
    def showEvent(self, show):
        # update once so we don't have to wait for initial report
        self._updateReport()
        self.timer.start(5*1000) #update every 5 sec.
 
#===----------------------------------------------------------------------------------------------------------------===
#=== if __name__ == "__main__"                                                                                      ===
#===----------------------------------------------------------------------------------------------------------------===
    
if __name__ == "__main__":
    from PyQt4.QtGui import QApplication
    import pickle
    
    app = QApplication([])
    
    f = open("/tmp/reports.pickle", 'r')
    reports = pickle.load(f)
    
    dlg = MemUsageDialog(update=False)
    
    print reports
    
    dlg._showReports(reports)
    dlg.show()
    app.exec_()
