import numpy as np
import vigra

from lazyflow.graph import Graph
from ilastik.applets.thresholdTwoLevels.opThresholdTwoLevels import OpLabeledThreshold, ThresholdMethod, _has_graphcut

class TestOpLabeledThreshold(object):

    _ = 0
    data = [[_,_,_,_,_,_,_,_,_,_], # 0
            [_,2,2,2,2,_,1,1,1,_], # 1
            [_,2,5,5,2,_,1,1,1,_], # 2
            [_,2,5,5,2,_,_,_,_,_], # 3
            [_,2,2,2,2,_,_,_,_,_], # 4
            [_,2,2,2,2,_,_,_,_,_], # 5
            [_,1,1,1,1,_,_,_,_,_], # 6 (dividing line for IPHT mode)
            [_,2,2,2,2,_,1,1,1,_], # 7
            [_,2,2,2,2,_,1,_,1,_], # 8
            [_,2,5,5,2,_,1,1,1,_], # 9
            [_,2,5,5,2,_,_,_,_,_], # 10
            [_,2,2,2,2,_,_,_,_,_], # 11
            [_,_,_,_,_,_,_,_,_,_]] # 12
        
    data = np.asarray(data, dtype=np.float32)[None, :, :, None, None]
    data = vigra.taggedView(data, 'tzyxc')
    
    def test_simple(self):
        data = self.data
        core_labels = np.zeros_like(data) # core_labels aren't used by 'simple' method
        
        op = OpLabeledThreshold(graph=Graph())
        op.Method.setValue(ThresholdMethod.SIMPLE)
        op.FinalThreshold.setValue(0.5)
        op.Input.setValue(data.copy())
        op.CoreLabels.setValue(core_labels)
        
        result = op.Output[:].wait()
        assert result.max() == 3
        assert (result.astype(bool) == data.astype(bool)).all()

    def test_hysteresis(self):
        data = self.data
        core_binary = (data == 5)
        core_labels = np.empty_like(data, dtype=np.uint32)
        core_labels[0,...,0] = vigra.analysis.labelMultiArrayWithBackground(core_binary[0,...,0].astype(np.uint8))

        op = OpLabeledThreshold(graph=Graph())
        op.Method.setValue(ThresholdMethod.HYSTERESIS)
        op.FinalThreshold.setValue(0.5)
        op.Input.setValue(data.copy())
        op.CoreLabels.setValue(core_labels)
        
        result = op.Output[:].wait()
        
        label_values = np.unique(result)[1:]
        assert len(label_values) == 1

        expected_result = np.where(data, label_values[0], 0)
        expected_result[0,:,5:,0,0] = 0 # Right half won't survive
        
        #print expected_result[0,:,:,0,0]
        #print result[0,:,:,0,0]
        assert (result == expected_result).all()

    def test_ipht(self):
        data = self.data
        core_binary = (data == 5)
        core_labels = np.empty_like(data, dtype=np.uint32)
        core_labels[0,...,0] = vigra.analysis.labelMultiArrayWithBackground(core_binary[0,...,0].astype(np.uint8))

        op = OpLabeledThreshold(graph=Graph())
        op.Method.setValue(ThresholdMethod.IPHT)
        op.FinalThreshold.setValue(0.5)
        op.Input.setValue(data.copy())
        op.CoreLabels.setValue(core_labels)
        
        result = op.Output[:].wait()
        result_yx = result[0,:,:,0,0]
        #print result_yx
        
        label_values = np.unique(result)[1:]
        assert len(label_values) == 2
        assert len(np.unique(result_yx[1:6, 1:5])) == 1
        assert len(np.unique(result_yx[7:12, 1:5])) == 1

    def test_graphcut(self):
        if _has_graphcut:
            data = self.data
            
            # Core labels don't matter in this graphcut test
            #core_binary = (data == 5)
            core_labels = np.empty_like(data, dtype=np.uint32)
            #core_labels[0,...,0] = vigra.analysis.labelMultiArrayWithBackground(core_binary[0,...,0].astype(np.uint8))

            op = OpLabeledThreshold(graph=Graph())
            op.Method.setValue(ThresholdMethod.GRAPHCUT)
            op.FinalThreshold.setValue(0.5)
            op.Input.setValue(data.copy())
            op.CoreLabels.setValue(core_labels)
            op.GraphcutBeta.setValue(0.5) # High enough to fill the hole in the third segment
            
            result = op.Output[:].wait()
            result_yx = result[0,:,:,0,0]
            #print result_yx
            
            label_values = np.unique(result)[1:]
            assert len(label_values) == 3        
            assert len(np.unique(result_yx[1:12, 1:5])) == 1 # Same as 'simple'
            assert len(np.unique(result_yx[7:10, 6:9])) == 1 # Almost same as simple, but with the hole filled in.
