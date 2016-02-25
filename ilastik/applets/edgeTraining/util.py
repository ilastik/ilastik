import logging
from itertools import imap, izip

import numpy as np
import vigra

from lazyflow.utility.edge_features import edge_id_mask, unique_edge_labels, label_vol_mapping

logger = logging.getLogger(__name__)

def edge_decisions( overseg_vol, groundtruth_vol, asdict=True ):
    """
    Given an oversegmentation and a reference segmentation,
    return a dict of {(id1, id2) : bool} indicating whether or
    not edge (id1,id2) is ON in the reference segmentation.
    
    If asdict=False, return separate ndarrays for edge_ids 
    and boolean decisions instead of combined dict. 
    """
    sp_edges_per_axis = []
    for axis in range(overseg_vol.ndim):
        mask, sp_edges = edge_id_mask(overseg_vol, axis)
        del mask
        sp_edges_per_axis.append( sp_edges )
    unique_sp_edges = unique_edge_labels(sp_edges_per_axis)[['id1', 'id2']].values

    sp_to_gt_mapping = label_vol_mapping(overseg_vol, groundtruth_vol)
    decisions = sp_to_gt_mapping[unique_sp_edges[0]] != sp_to_gt_mapping[unique_sp_edges[1]]

    if asdict:    
        return dict( izip(imap(tuple, unique_sp_edges), decisions) )
    return unique_sp_edges, decisions


if __name__ == "__main__":
    # 1 2
    # 3 4    
    vol1 = np.zeros((20,20), dtype=np.uint8)
    vol1[ 0:10,  0:10] = 1
    vol1[ 0:10, 10:20] = 2
    vol1[10:20,  0:10] = 3
    vol1[10:20, 10:20] = 4

    # 2 3
    # 4 5
    vol2 = vol1.copy() + 1
    
    assert (label_vol_mapping(vol1, vol2) == [0,2,3,4,5]).all()
    assert (label_vol_mapping(vol1[3:], vol2[:-3]) == [0,2,3,4,5]).all()
    assert (label_vol_mapping(vol1[6:], vol2[:-6]) == [0,2,3,2,3]).all()
    
    # 7 7
    # 4 5
    vol2[( vol2 == 2 ).nonzero()] = 7
    vol2[( vol2 == 3 ).nonzero()] = 7

    assert (label_vol_mapping(vol1, vol2) == [0,7,7,4,5]).all()
    
    decision_dict = edge_decisions(vol1, vol2, asdict=True)
    
    edge_ids, decisions = edge_decisions(vol1, vol2, asdict=False)
    relabel_volume_from_edge_decisions( vol1, edge_ids, decisions )
    print "DONE"
