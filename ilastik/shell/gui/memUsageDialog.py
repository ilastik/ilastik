#SciPy
import numpy

#PyQt
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem

#lazyflow
from lazyflow.operators.arrayCacheMemoryMgr import ArrayCacheMemoryMgr, MemInfoNode

import warnings

#===----------------------------------------------------------------------------------------------------------------===
#=== MemUsageDialog                                                                                                 ===
#===----------------------------------------------------------------------------------------------------------------===

class MemUsageDialog(QDialog):
    def __init__(self, parent=None, update=True):
        QDialog.__init__(self, parent=parent)
        layout = QVBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["cache", "memory", "roi", "dtype", "type"])
        layout.addWidget(self.tree)
        self.setLayout(layout)
        
        self.memMgr = ArrayCacheMemoryMgr.instance
        
        self.timer = QTimer(self)
        if update:
            self.timer.timeout.connect(self._updateReport)
            self._updateReport()
       
    def _updateReport(self):
        reports = []
        for c in self.memMgr.namedCaches:
            r = MemInfoNode()
            try:
                c.generateReport(r)
                reports.append(r)
            except NotImplementedError:
                warnings.warn('cache operator {} does not implement generateReport()'.format(c))
        self._showReports(reports)
        
        '''
        import pickle
        f = open("/tmp/reports.pickle",'w')
        pickle.dump(reports, f)
        f.close()
        print "... saved MEM reports to file ..."
        '''
        
    def _showReports(self, reports):
        self.tree.clear()
        root = self.tree.invisibleRootItem()
        for r in reports:
            self._showReportsImpl(r, root, 0)
       
    def _makeTreeWidgetItem(self, node):
        l = []
        l.append("%r" % node.name)
        l.append("%1.1f MB" % (node.usedMemory/1024**2.0))
        if node.roi is not None:
            l.append("%r\n%r" % (list(node.roi[0]), list(node.roi[1])))
        else:
            l.append("")
        if node.dtype is not None:
            if node.dtype == numpy.float32:
                l.append("float32")
            elif node.dtype == numpy.uint8:
                l.append("uint8")
            elif node.dtype == numpy.uint32:
                l.append("uint32")
            elif node.dtype == numpy.float64:
                l.append("float64")
            else:
                l.append(str(node.dtype))
                
        else:
            l.append("")
        
        t = str(node.type)
        t = t[len("<type '")+1:-len("'>")]
        t = t.split(".")[-1]
        l.append(t)
        return QTreeWidgetItem(l)
    
    def _showReportsImpl(self, node, itm, level):
        #print "  "*level,
        #print "node", node.name
        
        root = self._makeTreeWidgetItem(node)
        itm.addChild(root)
        root.setExpanded(True)
        
        for c in node.children:
            self._showReportsImpl(c, root, level+1)
            
    def hideEvent(self, event):
        self.timer.stop()
        
    def showEvent(self, show):
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
