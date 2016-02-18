import numpy as np
from volumina.utility.edge_coords import edge_ids

def contingency_table(vol1, vol2, maxlabels=None):
    """
    Return a 2D array 'table' such that table[i,j] represents
    the count of overlapping pixels with value i in vol1 and value j in vol2. 
    """
    maxlabels = maxlabels or (vol1.max(), vol2.max())
    table = np.zeros( (maxlabels[0]+1, maxlabels[1]+1), dtype=np.uint32 )
    
    # np.add.at() will accumulate counts at the given array coordinates
    np.add.at(table, [vol1.reshape(-1), vol2.reshape(-1)], 1 )
    return table

def label_vol_mapping(vol_from, vol_to):
    """
    Determine how remap voxel IDs in vol_from into corresponding
    IDs in vol_to, according to maxiumum overlap.
    (Note that this is not a commutative operation.)
    
    Returns: A 1D index array such that mapping[i] = j, where i
             is a voxel ID in vol_from, and j is the corresponding ID in vol_to.
    """
    table = contingency_table(vol_from, vol_to)
    mapping = np.argmax(table, axis=1)
    return mapping

def edge_decisions( overseg_vol, groundtruth_vol ):
    """
    Given an oversegmentation and a reference segmentation,
    return a dict of {(id1, id2) : bool} indicating whether or
    not edge (id1,id2) is ON in the reference segmentation.
    """
    sp_to_gt_mapping = label_vol_mapping(overseg_vol, groundtruth_vol)
    sp_edges = edge_ids(overseg_vol)
    decisions = {}
    for (id1, id2) in sp_edges:
        # Edge is ON if these two superpixels map to different segment IDs in the groundtruth
        decisions[(id1, id2)] = (sp_to_gt_mapping[id1] != sp_to_gt_mapping[id2])
    return decisions

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
    print "DONE"
