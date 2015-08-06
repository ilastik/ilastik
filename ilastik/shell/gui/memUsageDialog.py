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
from lazyflow.operators.cacheMemoryManager import CacheMemoryManager
from lazyflow.operators.opCache import MemInfoNode

#volumina
from volumina.utility.qstring_codec import encode_from_qstring

import warnings

#===------------------------------------------------------------------------===
#=== MemUsageDialog                                                         ===
#===------------------------------------------------------------------------===


class TreeNode(QTreeWidgetItem):
    _updated = False
    _children = {}
    _id = None
    _size_index = 1

    def handleChildrenReports(self, reports, root=None):
        if root is None:
            root = self
        for report in reports:
            child = self._childFromReport(report, root)
            child._setData(report)
            child.handleChildrenReports(report.children)
            child._updated = True
        for child in [self.child(i) for i in range(self.childCount())]:
            if not child._updated:
                root.removeChild(child)
            child._updated = False

    def _childFromReport(self, report, root):
        if report.id in self._children:
            return self._children[report.id]
        else:
            child = TreeNode()
            root.addChild(child)
            child._id = report.id
            self._children[report.id] = child
            return child

    def _setData(self, report):
        l = self._makeTreeWidgetItemData(report)
        for i, v in enumerate(l):
            self.setData(i, Qt.DisplayRole, v)

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
        l.append(report.info)
        l.append(report.id)
        return l

    def __lt__(self, other):
        col = self.treeWidget().sortColumn()
        if col == self._size_index:
            a = self.data(col, Qt.DisplayRole)
            a = TreeNode.extract_numeric_size(a)
            b = other.data(col, Qt.DisplayRole)
            b = TreeNode.extract_numeric_size(b)
            return a < b
        else:
            return super(TreeNode, self).__lt__(other)

    @staticmethod
    def constructFrom(other):
        node = TreeNode()
        node.__dict__.update(other.__dict__)
        return node

    @staticmethod
    def extract_numeric_size(txt):
        split = encode_from_qstring(txt.toString()).split()
        if len(split) == 0:
            return 0.0
        else:
            return float(split[0])


class MemUsageDialog(QDialog):
    def __init__(self, parent=None, update=True):
        QDialog.__init__(self, parent=parent)
        layout = QVBoxLayout()
        self.tree = QTreeWidget()
        layout.addWidget(self.tree)
        self.setLayout(layout)

        self._mgr = CacheMemoryManager()

        self._tracked_caches = {}

        # tree setup code
        self.tree.setHeaderLabels(
            ["cache", "memory", "roi", "dtype", "type", "info", "id"])
        self._idIndex = self.tree.columnCount() - 1
        self.tree.setColumnHidden(self._idIndex, True)
        self.tree.setSortingEnabled(True)
        self.tree.clear()

        self._root = TreeNode()

        # refresh every x seconds (see showEvent())
        self.timer = QTimer(self)
        if update:
            self.timer.timeout.connect(self._updateReport)

    def _updateReport(self):
        # we keep track of dirty reports so we just have to update the tree
        # instead of reconstructing it
        reports = []
        for c in self._mgr.getFirstClassCaches():
            r = MemInfoNode()
            c.generateReport(r)
            reports.append(r)
        self._root.handleChildrenReports(
            reports, root=self.tree.invisibleRootItem())

    def hideEvent(self, event):
        self.timer.stop()

    def showEvent(self, show):
        # update once so we don't have to wait for initial report
        self._updateReport()
        # update every 5 sec.
        self.timer.start(5*1000)


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
