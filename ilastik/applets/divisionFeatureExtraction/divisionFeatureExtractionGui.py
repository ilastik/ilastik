from PyQt4.QtGui import QProgressDialog
from PyQt4.QtCore import Qt, QString

import logging
from ilastik.applets.objectExtraction.objectExtractionGui import ObjectExtractionGui
from lazyflow.rtype import SubRegion
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)


class DivisionFeatureExtractionGui( ObjectExtractionGui ):
        
    def _calculateFeaturesButtonPressed(self):
        maxt = self.mainOperator.LabelImage.meta.shape[0]
        progress = QProgressDialog("Calculating features...", "Stop", 0, 2*maxt)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButtonText(QString())

        reqs = []
        self.mainOperator._opRegFeats.fixed = False
        for t in range(maxt):
            reqs.append(self.mainOperator.RegionFeaturesVigra([t]))
            reqs[-1].submit()

        for i, req in enumerate(reqs):
            progress.setValue(i)
            if progress.wasCanceled():
                req.cancel()
            else:
                req.wait()

        self.mainOperator._opRegFeats.fixed = True        
        progress.setValue(maxt)
        print 'Vigra Region Feature Extraction: done.'
        
        
        
        reqs = []
        self.mainOperator._opDivFeats.fixed = False
        for t in range(maxt):
            reqs.append(self.mainOperator.RegionFeatures([t]))
            reqs[-1].submit()

        for i, req in enumerate(reqs):
            progress.setValue(i+maxt)
            if progress.wasCanceled():
                req.cancel()
            else:
                req.wait()

        self.mainOperator._opDivFeats.fixed = True
        progress.setValue(2*maxt)
        print 'Division Feature Extraction: done.'
        
        
        
        self.mainOperator.ObjectCenterImage.setDirty(SubRegion(self.mainOperator.ObjectCenterImage))

        print 'Object Extraction: done.'
        
        
        
        
        
