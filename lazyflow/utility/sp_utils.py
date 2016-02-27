import numpy as np
import pandas as pd

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

def edge_mask_for_axis( label_img, axis ):
    """
    Find all supervoxel edges along the given axis and return
    a 'left-hand' mask indicating where the edges are located
    (i.e. a boolean array indicating voxels that are just to the left of an edge).
    Note that this mask is less wide (by 1 pixel) than label_img along the chosen axis.
    """
    if axis < 0:
        axis += label_img.ndim
    assert label_img.ndim > axis
    
    if label_img.shape[axis] == 1:
        return np.zeros_like(label_img)

    left_slicing = ((slice(None),) * axis) + (np.s_[:-1],)
    right_slicing = ((slice(None),) * axis) + (np.s_[1:],)

    edge_mask = (label_img[left_slicing] != label_img[right_slicing])
    return edge_mask

def edge_ids_for_axis(label_img, edge_mask, axis):
    """
    Given an 'left-hand' edge_mask indicating where edges are located along the given axis,
    return an array of of edge ids (u,v) corresonding to the voxel ids of every voxel under the mask,
    in the same order as mask.nonzero().
    The edge ids are sorted such that u < v. 
    """
    if axis < 0:
        axis += label_img.ndim
    assert label_img.ndim > axis

    if label_img.shape[axis] == 1:
        return np.ndarray( (0, 2), dtype=label_img.dtype )

    left_slicing = ((slice(None),) * axis) + (np.s_[:-1],)
    right_slicing = ((slice(None),) * axis) + (np.s_[1:],)

    num_edges = np.count_nonzero(edge_mask)
    edge_ids = np.ndarray(shape=(num_edges, 2), dtype=np.uint32 )
    edge_ids[:, 0] = label_img[left_slicing][edge_mask]
    edge_ids[:, 1] = label_img[right_slicing][edge_mask]
    edge_ids.sort(axis=1)

    return edge_ids

def unique_edge_labels( all_edge_ids ):
    """
    Given a *list* of edge_id arrays (each of which has shape (N,2))
    Merge all edge_id arrays into a single pandas.DataFrame with
    columns ['sp1', 'sp2', and 'edge_label], where `edge_label`
    is a unique ID number for each edge_id pair.
    (The DataFrame will have no duplicate entries.)
    """
    all_dfs = []
    for edge_ids in all_edge_ids:
        assert edge_ids.shape[1] == 2
        num_edges = len(edge_ids)
        index_u32 = pd.Index(np.arange(num_edges), dtype=np.uint32)
        df = pd.DataFrame(edge_ids, columns=['sp1', 'sp2'], index=index_u32)
        df.drop_duplicates(inplace=True)
        all_dfs.append( df )

    if len(all_dfs) == 1:
        combined_df = all_dfs[0]
    else:
        combined_df = pd.concat(all_dfs)
        combined_df.drop_duplicates(inplace=True)

    # This sort isn't necessary, but it's convenient for debugging.
    combined_df.sort(columns=['sp1', 'sp2'], inplace=True)

    # TODO: Instead of adding a new column here, we might save some RAM 
    #       if we re-index and then add the index as a column
    combined_df['edge_label'] = np.arange(0, len(combined_df), dtype=np.uint32)
    return combined_df

def extract_edge_values_for_axis( axis, edge_mask, value_img ):
    """
    Returns 1D ndarray, in the same order as edge_mask.nonzero().
    Result is float32, regardless of value_img.dtype
    """
    left_slicing = ((slice(None),) * axis) + (np.s_[:-1],)
    right_slicing = ((slice(None),) * axis) + (np.s_[1:],)

    # Here, we extract the voxel values *first* and then compute features on the 1D list of values (with associated labels)
    # This saves RAM (and should therefore be fast), but can't be used with coordinate-based features or shape features.
    # We could, instead, change the lines below to not extract the mask values, and pass the full image into vigra...
    edge_values_left = value_img[left_slicing][edge_mask]
    edge_values_right = value_img[right_slicing][edge_mask]

    # Vigra region features require float32    
    edge_values_left = edge_values_left.astype(np.float32, copy=False)
    edge_values_right = edge_values_right.astype(np.float32, copy=False)

    # We average the left and right-hand voxel values 'manually' here and just compute features on the average
    # In theory, we could compute the full set of features separately for left and right-hand voxel sets and 
    # then merge the two, but that seems like overkill, and only some features would be slightly different (e.g. histogram features)
    edge_values = edge_values_left
    edge_values += edge_values_right
    edge_values /= 2
    return edge_values

def get_edge_ids( label_img ):
    """
    Convenience function.
    Returns a DataFrame with columns ['sp1', 'sp2', 'edge_label'], sorted by ('sp1', 'sp2')
    """
    all_edge_ids = []
    for axis in range(label_img.ndim):
        edge_mask = edge_mask_for_axis(label_img, axis)
        edge_ids = edge_ids_for_axis(label_img, edge_mask, axis)
        lookup = unique_edge_labels( [edge_ids] )
        all_edge_ids.append(lookup[['sp1', 'sp2']].values)
    final_edge_label_lookup_df = unique_edge_labels( all_edge_ids )
    return final_edge_label_lookup_df

def nonzero_coord_array(a):
    """
    Equivalent to np.transpose(a.nonzero()), but much
    faster for large arrays, thanks to a little trick:
    The elements of the tuple returned by a.nonzero() share a common base,
    so we can avoid the copy that would normally be incurred when
    calling transpose() on the tuple.
    """
    base_array = a.nonzero()[0].base
    
    # This is necessary because VigraArrays have their own version
    # of nonzero(), which adds an extra base in the view chain.
    while base_array.base is not None:
        base_array = base_array.base
    return base_array
    
