import numpy as np
import pandas as pd
import vigra

import logging
logger = logging.getLogger(__name__)

def edge_id_mask( label_img, axis ):
    """
    Find all supervoxel edges along the given axis and return the following:

    - A 'left-hand' mask indicating where the edges are located
      (i.e. a boolean array indicating voxels that are just to the left of an edge)
      Note that this mask be less wide (by 1 pixel) than label_img along the chosen axis.
      
    - An array of of edge ids (u,v) corresonding to the voxel ids of every voxel in the mask,
      in the same order as mask.nonzero() would return.
      The edge ids are sorted such that u < v. 
    """
    if axis < 0:
        axis += label_img.ndim
    assert label_img.ndim > axis
    
    if label_img.shape[axis] == 1:
        edge_mask = np.zeros_like(label_img)
        edge_ids = np.ndarray( (0, 2), dtype=label_img.dtype )
        return edge_mask, edge_ids

    left_slicing = ((slice(None),) * axis) + (np.s_[:-1],)
    right_slicing = ((slice(None),) * axis) + (np.s_[1:],)

    edge_mask = (label_img[left_slicing] != label_img[right_slicing])

    num_edges = np.count_nonzero(edge_mask)
    edge_ids = np.ndarray(shape=(num_edges, 2), dtype=np.uint32 )
    edge_ids[:, 0] = label_img[left_slicing][edge_mask]
    edge_ids[:, 1] = label_img[right_slicing][edge_mask]
    edge_ids.sort(axis=1)

    return edge_mask, edge_ids

def unique_edge_labels( all_edge_ids ):
    """
    Given a *list* of edge_id arrays (each of which has shape (N,2)
    Merge all edge_id arrays into a single pandas.DataFrame with
    columns ['id1', 'id2', and 'edge_label], where `edge_label`
    is a unique ID number for each edge_id pair.
    (The DataFrame will have no duplicate entries.)
    """
    all_dfs = []
    for edge_ids in all_edge_ids:
        assert edge_ids.shape[1] == 2
        num_edges = len(edge_ids)
        index_u32 = pd.Index(np.arange(num_edges), dtype=np.uint32)
        df = pd.DataFrame(edge_ids, columns=['id1', 'id2'], index=index_u32)
        df.drop_duplicates(inplace=True)
        all_dfs.append( df )

    if len(all_dfs) == 1:
        combined_df = all_dfs[0]
    else:
        combined_df = pd.concat(all_dfs)
        combined_df.drop_duplicates(inplace=True)

    # This sort isn't necessary, but it's convenient for debugging.
    combined_df.sort(columns=['id1', 'id2'], inplace=True)

    # TODO: Instead of adding a new column here, we might save some RAM if we re-index and then add the index as a column
    combined_df['edge_label'] = np.arange(1, 1+len(combined_df), dtype=np.uint32)
    return combined_df

def compute_edge_features_along_axis( label_img, value_img, feature_names, histogram_range=None, axis=0):
    """
    Find the edges in the direction of the given axis and
    compute region features for the pixels adjacent to the edge.
    
    Returns:
     - A vigra RegionFeaturesAccumulator containing the edge statistics.
       Each edge will be assigned a unique label id (an integer).
     - A pandas DataFrame that can be used to map from edge_label to edge_id pairs (u,v).
       The columns of the DataFrame are: ['id1', 'id2', 'edge_label'], where 'id1' and 'id2' are supervoxel ids.
     - The histogram range used for any histogram features.
    """
    logger.debug("Axis {}: Computing edge mask...".format( axis ))
    edge_mask, edge_ids = edge_id_mask( label_img, axis )

    logger.debug("Axis {}: Generating edge label IDs...".format( axis ))    
    edge_label_lookup = unique_edge_labels( [edge_ids] )
    
    index_u32 = pd.Index(np.arange(len(edge_ids)), dtype=np.uint32)
    df_edges = pd.DataFrame(edge_ids, columns=['id1', 'id2'], index=index_u32)
    df_edges_with_labels = pd.merge(df_edges, edge_label_lookup, on=['id1', 'id2'], how='left')
    edge_labels = df_edges_with_labels['edge_label'].values

    left_slicing = ((slice(None),) * axis) + (np.s_[:-1],)
    right_slicing = ((slice(None),) * axis) + (np.s_[1:],)

    # Here, we extract the voxel values *first* and then compute features on the 1D list of values (with associated labels)
    # This saves RAM (and should therefore be fast), but can't be used with coordinate-based features or shape features.
    # We could, instead, change the lines below to not extract the mask values, and pass the full image into vigra...
    logger.debug("Axis {}: Extracting edge values...".format( axis ))    
    edge_values_left = value_img[left_slicing][edge_mask]
    edge_values_right = value_img[right_slicing][edge_mask]

    # Vigra region features require float32    
    edge_values_left = edge_values_left.astype(np.float32, copy=False)
    edge_values_right = edge_values_right.astype(np.float32, copy=False)

    # We average the left and right-hand voxel values 'manually' here and just compute features on the average
    # In theory, we could compute the full set of features separately for left and right-hand voxel sets and 
    # then merge the two, but that seems like overkill.
    edge_values = (edge_values_left + edge_values_right) / 2
    assert edge_values.shape == edge_labels.shape

    if not histogram_range and set(['Quantiles', 'Histogram']) & set(feature_names):
        histogram_range = [float(edge_values.min()), float(edge_values.max())]

    if not histogram_range:
        # Not using a histogram, but vigra needs a default value.
        histogram_range = "globalminmax"
    
    logger.debug("Axis {}: Computing region features...".format( axis ))    
    # Must add singleton y-axis here because vigra doesn't support 1D data
    acc = vigra.analysis.extractRegionFeatures( edge_values.reshape(1,-1),
                                                edge_labels.reshape(1,-1),
                                                #ignoreLabel=0, # Would be necessary if we were working with the full image.
                                                features=feature_names,
                                                histogramRange=histogram_range )
    
    
    return acc, edge_label_lookup, histogram_range

def compute_edge_features( label_img, value_img, feature_names=['Count', 'Mean', 'Variance', 'Quantiles'] ):
    """
    For the given supervoxels (label_img) and underlying singleband data (value_img),
    compute the given features using the vigra RegionFeatureAccumulator framework.
    
    Returns:
        - A RegionFeatureAccumulator with the statistics for all edges in the volume
        - A pandas.DataFrame that can be used to map from region labels to edge_ids (i.e. u,v pairs)
          The columns of the DataFrame are: ['id1','id2','edge_label']
    
    Caveats:
        - The edges and features along each axis are computed separately, and merged as a final step.
        - For histogram features, the histogram min/max values are initialized from the min/max edge
          values along axis 0, and re-used for axes 1..N
    """
    assert label_img.shape == value_img.shape
    
    logger.debug("Computing per-axis features...")    
    axis_accumulators = []
    edge_label_lookups = []
    histogram_range = None
    for axis in range(label_img.ndim):
        acc, lookup, histogram_range = compute_edge_features_along_axis( label_img, value_img, feature_names, histogram_range, axis )
        axis_accumulators.append(acc)
        edge_label_lookups.append(lookup)    

    # Get final lookup table from (u,v) -> final_edge_label
    logger.debug("Generating final lookup...")    
    all_edge_ids = []
    for lookup in edge_label_lookups:
        all_edge_ids.append(lookup[['id1', 'id2']].values)
    final_edge_label_lookup_df = unique_edge_labels( all_edge_ids )

    # Then for each axis-specific lookup: translate edge_label -> (u,v) -> final_edge_label
    # And merge into the final accumulator
    logger.debug("Merging per-axis features into final accumulator...")    
    final_acc = axis_accumulators[0].createAccumulator()
    for acc, this_axis_lookup_df in zip(axis_accumulators, edge_label_lookups):
        # Columns of this combined_lookup_df will be:
        # ['id1', 'id2', 'edge_label_this_axis', 'edge_label_final']
        combined_lookup_df = pd.merge( this_axis_lookup_df,
                                       final_edge_label_lookup_df,
                                       on=['id1', 'id2'],
                                       how='left',
                                       suffixes=('_this_axis', '_final'))
        
        # Create an index array for converting between 'this_axis' labels and 'final' labels.
        max_edge_label_this_axis = this_axis_lookup_df['edge_label'].max()
        axis_to_final_index_array = np.zeros( shape=(max_edge_label_this_axis+1,), dtype=np.uint32 )
        axis_to_final_index_array[ combined_lookup_df['edge_label_this_axis'].values ] = combined_lookup_df['edge_label_final'].values

        final_acc.merge( acc, axis_to_final_index_array )
    
    # return the final accumulator, and the final_edge_label lookup
    return final_acc, final_edge_label_lookup_df

if __name__ == "__main__":
    import sys
    logger.addHandler( logging.StreamHandler(sys.stdout) )
    logger.setLevel(logging.DEBUG)
    
    import h5py
    watershed_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/256/watershed-256.h5'
    #watershed_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/512/watershed-512.h5'

    grayscale_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/256/grayscale-256.h5'
    
    logger.info("Loading watershed...")
    with h5py.File(watershed_path, 'r') as f:
        watershed = f['watershed'][:256, :256, :256, 0]

    logger.info("Loading grayscale...")
    with h5py.File(grayscale_path, 'r') as f:
        grayscale = f['grayscale'][:256, :256, :256, 0]

    from lazyflow.utility import Timer
    with Timer() as timer:
        #ec = edge_coords_nd(watershed)
        #ids = edge_ids(watershed)
        acc, lookup_df = compute_edge_features(watershed, grayscale)
    print "time was: {}".format( timer.seconds() )






