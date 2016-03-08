import logging
from itertools import imap, izip

import numpy as np
import networkx as nx
import vigra

from ilastikrag.util import edge_mask_for_axis, edge_ids_for_axis, unique_edge_labels, label_vol_mapping

logger = logging.getLogger(__name__)

def edge_decisions( overseg_vol, groundtruth_vol, asdict=True ):
    """
    Given an oversegmentation and a reference segmentation,
    return a dict of {(sp1, sp2) : bool} indicating whether or
    not edge (sp1,sp2) is ON in the reference segmentation.
    
    If asdict=False, return separate ndarrays for edge_ids 
    and boolean decisions instead of combined dict. 
    """
    sp_edges_per_axis = []
    for axis in range(overseg_vol.ndim):
        edge_mask = edge_mask_for_axis(overseg_vol, axis)
        sp_edges = edge_ids_for_axis(overseg_vol, edge_mask, axis)
        del edge_mask
        sp_edges_per_axis.append( sp_edges )
    unique_sp_edges = unique_edge_labels(sp_edges_per_axis)[['sp1', 'sp2']].values

    sp_to_gt_mapping = label_vol_mapping(overseg_vol, groundtruth_vol)
    decisions = sp_to_gt_mapping[unique_sp_edges[0]] != sp_to_gt_mapping[unique_sp_edges[1]]

    if asdict:    
        return dict( izip(imap(tuple, unique_sp_edges), decisions) )
    return unique_sp_edges, decisions

def relabel_volume_from_edge_decisions( supervoxels, edge_ids, edge_decisions, out=None ):
    """
    Given a supervoxel volume, and a set of edge_ids and corresponding ON/OFF labels
    for the edges, compute a new label volume in which all supervoxels with at least
    one inactive edge between them are merged together.
    
    Parameters
    ----------
    supervoxels: label array, labels do not need to be consecutive,
                 but excessively high label values may lead to poor performance
                 (see xrange call below)

    edge_ids: array of shape (N,2).  Must include all INactive edges.
              Active edges can be omitted (they'll be removed anyway).

    edge_decisions: 1D bool array of shape (N,).
                    1 means "active", i.e. the two superpixels are separated across that edge, at least
                    0 means "inactive", i.e. the two superpixels will be joined in the final result.

    out: Optional. Must be same shape as supervoxels, but may have different dtype.
    """
    assert hasattr(supervoxels, 'axistags'), \
        "Must provide accurate axistags, otherwise performance suffers by 10x"
    assert out is None or hasattr(out, 'axistags'), \
        "Must provide accurate axistags, otherwise performance suffers by 10x"

    inactive_edge_ids = edge_ids[np.nonzero( np.logical_not(edge_decisions) )]

    logger.debug("Finding connected components in node graph...")
    g = nx.Graph( list(inactive_edge_ids) ) 
    
    # If any supervoxels are completely independent (not merged with any neighbors),
    # they haven't been added to the graph yet.
    # Add them now.
    g.add_nodes_from(xrange(np.max(supervoxels)+1), dtype=edge_ids.dtype)
    
    sp_mapping = {}
    for i, sp_ids in enumerate(nx.connected_components(g), start=1):
        for sp_id in sp_ids:
            sp_mapping[int(sp_id)] = i
    del g

    logger.debug("Relabeling supervoxels with connected components...")
    segmentation_img = vigra.analysis.applyMapping( supervoxels, sp_mapping, out=out )
    return segmentation_img

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
