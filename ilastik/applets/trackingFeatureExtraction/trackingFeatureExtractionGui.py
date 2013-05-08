from PyQt4.QtGui import QProgressDialog
from PyQt4.QtCore import Qt, QString

import logging
from ilastik.applets.objectExtraction.objectExtractionGui import ObjectExtractionGui,\
    ObjectExtractionGuiNonInteractive
from lazyflow.rtype import SubRegion
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)


#class TrackingFeatureExtractionGui( ObjectExtractionGuiNonInteractive ):
class TrackingFeatureExtractionGui( ObjectExtractionGui ):
        
    def _calculateFeatures(self):
        maxt = self.topLevelOperatorView.LabelImage.meta.shape[0]
        progress = QProgressDialog("Calculating features...", "Stop", 0, 2*maxt)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButtonText(QString())

        reqs = []
        self.topLevelOperatorView._opRegFeats.fixed = False
        for t in range(maxt):
            troi = SubRegion(self.topLevelOperatorView.RegionFeaturesVigra, [t], [t+1])
            reqs.append(self.topLevelOperatorView.RegionFeaturesVigra.get(troi))
            reqs[-1].submit()

        for i, req in enumerate(reqs):
            progress.setValue(i)
            if progress.wasCanceled():
                req.cancel()
            else:
                req.wait()

        self.topLevelOperatorView._opRegFeats.fixed = True        
        progress.setValue(maxt)
        print 'Vigra Region Feature Extraction: done.'
        
        
        
        reqs = []
        self.topLevelOperatorView._opCellFeats.fixed = False
        for t in range(maxt):
            troi = SubRegion(self.topLevelOperatorView._opCellFeats.RegionFeaturesExtended, [t], [t+1])
#            reqs.append(self.topLevelOperatorView.BlockwiseRegionFeatures.get(troi))
            reqs.append(self.topLevelOperatorView._opCellFeats.RegionFeaturesExtended.get(troi))
#            reqs.append(self.topLevelOperatorView.BlockwiseRegionFeatures([t]))
            reqs[-1].submit()

        for i, req in enumerate(reqs):
            progress.setValue(i+maxt)
            if progress.wasCanceled():
                req.cancel()
            else:
                req.wait()

        self.topLevelOperatorView._opCellFeats.fixed = True
        progress.setValue(2*maxt)
        print 'Division Feature Extraction: done.'
        
        
        
        self.topLevelOperatorView.ObjectCenterImage.setDirty(SubRegion(self.topLevelOperatorView.ObjectCenterImage))

        print 'Object Extraction: done.'
        
        
        
        
        
