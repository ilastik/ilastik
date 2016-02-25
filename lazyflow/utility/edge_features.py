import collections
import numpy as np
import pandas as pd
import vigra

import logging
logger = logging.getLogger(__name__)

from lazyflow.utility.helpers import nonzero_coord_array

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


class Rag(object):
    
    # axis: int
    # mask: Either of the following:
    #       - ndarray of bool (same shape as labels) OR
    #       - index array tuple (see comments below about save_ram flag)
    # ids: ndarray of edge_id pairs, same order as mask.nonzero()
    # label_lookup: DataFrame with columns 'id1', 'id2', 'edge_label' (no duplicate rows)
    AxisEdgeData = collections.namedtuple('AxisEdgeData', 'axis mask ids label_lookup')
    
    def __init__( self, label_img, save_ram=True ):
        """
        Constructor.  See comments below about save_ram.
        """
        assert hasattr(label_img, 'axistags'), \
            "For optimal performance, make sure label_img is a VigraArray with accurate axistags"
        self.label_img = label_img

        self.axis_edge_datas = []
        for axis in range(label_img.ndim):
            edge_mask, edge_ids = edge_id_mask(label_img, axis)
            label_lookup = unique_edge_labels( [edge_ids] )
            
            if save_ram:
                # Experimental option.
                # It turns out that any line below that uses edge_mask as a bool array
                # can also accept an index-array-tuple instead.
                # As long as our supervoxels aren't tiny, we can save a lot of RAM by storing 
                # the index-array instead of the dense bool mask.
                # For my 512**3 test case, this saves 360 MB RAM 
                # (indexes just needs 40 MB instead of 400MB for masks), but costs ~2 seconds.
                # The reduced RAM saves time when extracting the values from a value_img.
                # For my 512**3 test case, the index array saves 0.5 seconds.
                # Obviously, for larger volumes (say, 1 GB) the RAM savings is bigger (~3 GB).
                edge_mask_nonzero = nonzero_coord_array(edge_mask).transpose()
                if (np.array(label_img.shape) < 2**16).all():
                    edge_mask_nonzero = edge_mask_nonzero.astype(np.uint16)
                else:
                    edge_mask_nonzero = edge_mask_nonzero.astype(np.uint32)
                edge_mask = tuple(edge_mask_nonzero)
                
            self.axis_edge_datas.append( Rag.AxisEdgeData(axis, edge_mask, edge_ids, label_lookup) )
        
        # Columns: id1, id2, edge_label
        final_edge_label_lookup_df = unique_edge_labels( map(lambda t: t.ids, self.axis_edge_datas) )

        # Tiny optimization:
        # We will be accessing edge_ids over and over, so let's extract them now
        self._edge_ids = final_edge_label_lookup_df[['id1', 'id2']].values

        # Now, to avoid having multiple copies of edge_ids in RAM,
        # re-create final_edge_label_lookup_df using the cached edge_ids array
        self.final_edge_label_lookup_df = pd.DataFrame( {'id1': self._edge_ids[:,0],
                                                         'id2': self._edge_ids[:,1],
                                                         'edge_label': final_edge_label_lookup_df['edge_label'] } )

        # Compute the number of superpixels.
        # We don't assume that SP ids are consecutive, so it's not the same as label_img.max()        
        unique_left = self.final_edge_label_lookup_df['id1'].unique()
        unique_right = self.final_edge_label_lookup_df['id2'].unique()
        self._num_sp = len( pd.Series( np.concatenate((unique_left, unique_right))).unique() )

    def num_edges(self):
        return len(self.final_edge_label_lookup_df)

    def num_sp(self):
        return self._num_sp

    def edge_ids(self):
        return self._edge_ids

    def edge_decisions_from_groundtruth(self, groundtruth_vol, asdict=False):
        sp_to_gt_mapping = label_vol_mapping(self.label_img, groundtruth_vol)

        unique_sp_edges = self.edge_ids()
        decisions = sp_to_gt_mapping[unique_sp_edges[:, 0]] != sp_to_gt_mapping[unique_sp_edges[:, 1]]
    
        if asdict:
            return dict( izip(imap(tuple, unique_sp_edges), decisions) )
        return decisions

    def compute_edge_vigra_features(self, value_img, feature_names=['Count', 'Mean', 'Variance', 'Quantiles']):
        assert hasattr(value_img, 'axistags'), \
            "For optimal performance, make sure value_img is a VigraArray with accurate axistags"
        logger.debug("Computing per-axis features...")
        axis_accumulators = []
        histogram_range = None
        for axis, edge_mask, edge_ids, edge_label_lookup in self.axis_edge_datas:
            acc, histogram_range = compute_edge_vigra_features_along_axis( axis, edge_mask, edge_ids, edge_label_lookup, value_img, feature_names, histogram_range )
            axis_accumulators.append(acc)

        edge_label_lookups = map( lambda t: t.label_lookup, self.axis_edge_datas )
        final_acc, final_edge_ids = merge_edge_vigra_features( edge_label_lookups, self.final_edge_label_lookup_df, axis_accumulators )
        return final_acc, final_edge_ids

    def compute_highlevel_edge_features(self, value_img, highlevel_features):
        """
        Computes features for edges, including superpixel features.
        Returns a pandas dataframe.  The first two columns are 'id1' and 'id2', and the other columns are the computed features.
        
        Supported feature names:
        (edge_|sp_) + ( count|sum|mean|variance|kurtosis|skewness
                        |quantiles_10|quantiles_25|quantiles_50|quantiles_75|quantiles_90 )
        For example: highlevel_features = ['edge_count', 'edge_mean', 'sp_quantiles_75']
        
        All 'sp' feature names result in two columns, for the sum and difference between the two superpixels adjacent to the edge.
        Additionally, the 'count' sp feature is reduced via cube-root (as in the multicut paper).
        Same for the 'sum' feature.
        """
        assert hasattr(value_img, 'axistags'), \
            "For optimal performance, make sure value_img is a VigraArray with accurate axistags"
        
        highlevel_features = map(str.lower, highlevel_features)
        edge_highlevel_features = filter(lambda name: name.startswith('edge_'), highlevel_features)
        edge_highlevel_features = map(lambda name: name[len('edge_'):], edge_highlevel_features) # drop 'edge_' prefix
        edge_vigra_features = map(lambda name: name.split('_')[0], edge_highlevel_features ) # drop quantile suffixes like '_25'
        edge_vigra_features = list(set(edge_vigra_features)) # drop duplicates (from multiple quantile selections)
    
        final_edge_acc, final_edge_ids = self.compute_edge_vigra_features( value_img, edge_vigra_features )
    
        # Create a dataframe to store the result
        edge_df = pd.DataFrame(final_edge_ids, columns=['id1', 'id2'])
        
        # Adding columns for edge features is easy, just add them verbatim
        for edge_feature in edge_highlevel_features:
            if edge_feature.startswith('quantiles'):
                quantile_suffix = edge_feature.split('_')[1]
                q_index = ['0', '10', '25', '50', '75', '90', '100'].index(quantile_suffix)
                edge_df['edge_' + edge_feature] = final_edge_acc['quantiles'][:, q_index]
            else:
                edge_df['edge_' + edge_feature] = final_edge_acc[edge_feature]
    
        return edge_df, edge_highlevel_features

    def compute_highlevel_sp_features(self, value_img, highlevel_features):
        """
        highlevel_features
        """
        assert hasattr(value_img, 'axistags'), \
            "For optimal performance, make sure value_img is a VigraArray with accurate axistags"
        
        highlevel_features = map(str.lower, highlevel_features)
        sp_highlevel_features = filter(lambda name: name.startswith('sp_'), highlevel_features)
        sp_highlevel_features = map(lambda name: name[len('sp_'):], sp_highlevel_features) # drop 'sp_' prefix
        sp_vigra_features = map(lambda name: name.split('_')[0], sp_highlevel_features ) # drop quantile suffixes like '_25'
        sp_vigra_features = list(set(sp_vigra_features)) # drop duplicates (from multiple quantile selections)
        if not sp_vigra_features:
            # No superpixel features.  We're done.
            return None, sp_highlevel_features
        
        logger.debug("Computing SP features...")
        sp_acc = compute_sp_vigra_features( self.label_img, value_img, sp_vigra_features )
    
        logger.debug("Saving SP features to DataFrame...")
        # Create an almost-empty dataframe to store the sp features
        sp_df = pd.DataFrame({ 'sp_id' : np.arange(sp_acc.maxRegionLabel()+1, dtype=np.uint32) })
        
        # Add a column for each sp feature we'll need
        for sp_feature in sp_highlevel_features:
            if sp_feature.startswith('quantiles'):
                quantile_suffix = sp_feature.split('_')[1]
                q_index = ['0', '10', '25', '50', '75', '90', '100'].index(quantile_suffix)
                sp_df['sp_' + sp_feature] = sp_acc['quantiles'][:, q_index]
            else:
                sp_df['sp_' + sp_feature] = sp_acc[sp_feature]
    
        return sp_df, sp_highlevel_features

    def compute_highlevel_features(self, value_img, highlevel_features):
        assert hasattr(value_img, 'axistags'), \
            "For optimal performance, make sure value_img is a VigraArray with accurate axistags"

        highlevel_features = list(set(highlevel_features))
        edge_df, edge_features = self.compute_highlevel_edge_features(value_img, highlevel_features)
        sp_df, sp_highlevel_features = self.compute_highlevel_sp_features(value_img, highlevel_features)
        if sp_df is not None:
            edge_df = append_sp_features_onto_edge_features( edge_df, sp_df, sp_highlevel_features )
        return edge_df

def edge_id_mask( label_img, axis ):
    """
    Find all supervoxel edges along the given axis and return the following:

    - A 'left-hand' mask indicating where the edges are located
      (i.e. a boolean array indicating voxels that are just to the left of an edge)
      Note that this mask is less wide (by 1 pixel) than label_img along the chosen axis.
      
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
    Given a *list* of edge_id arrays (each of which has shape (N,2))
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

    # TODO: Instead of adding a new column here, we might save some RAM 
    #       if we re-index and then add the index as a column
    combined_df['edge_label'] = np.arange(0, len(combined_df), dtype=np.uint32)
    return combined_df

def extract_edge_values_for_axis( axis, edge_mask, value_img ):
    """
    Returns 1D ndarray, in the same order as edge_mask.nonzero()
    """
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
    # then merge the two, but that seems like overkill, and only some features would be slightly different (e.g. histogram features)
    edge_values = edge_values_left
    edge_values += edge_values_right
    edge_values /= 2
    return edge_values

def compute_edge_vigra_features_along_axis( axis, edge_mask, edge_ids, edge_label_lookup, value_img, feature_names, histogram_range=None ):
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
    feature_names = map(str.lower, feature_names)
    for feature_name in feature_names:
        for nonsupported_name in ('coord', 'region'):
            # This could be fixed by the following:
            # - Combine the mask and edge_labels into a label volume (same shape as mask)
            # - Compute coordinate-based features separately
            # - If *weighted* coordinate-based features are also needed, then need to combine 
            #   mask and edge_values into a edge_value volume (same shape as mask)
            # But the performance implications could be severe...
            assert nonsupported_name not in feature_name, \
                "Coordinate-based edge features are not currently supported!"

    edge_values = extract_edge_values_for_axis(axis, edge_mask, value_img)

    index_u32 = pd.Index(np.arange(len(edge_ids)), dtype=np.uint32)
    df_edges = pd.DataFrame(edge_ids, columns=['id1', 'id2'], index=index_u32)
    df_edges_with_labels = pd.merge(df_edges, edge_label_lookup, on=['id1', 'id2'], how='left')
    edge_labels = df_edges_with_labels['edge_label'].values

    # Sanity check
    assert edge_values.shape == edge_labels.shape

    if not histogram_range and set(['quantiles', 'histogram']) & set(feature_names):
        histogram_range = [float(edge_values.min()), float(edge_values.max())]

    if not histogram_range:
        # Not using a histogram, but vigra needs a default value.
        histogram_range = "globalminmax"
    
    logger.debug("Axis {}: Computing region features...".format( axis ))
    # Must add singleton y-axis here because vigra doesn't support 1D data
    acc = vigra.analysis.extractRegionFeatures( edge_values.reshape((1,-1), order='A'),
                                                edge_labels.reshape((1,-1), order='A'),
                                                #ignoreLabel=0, # Would be necessary if we were working with the full image.
                                                features=feature_names,
                                                histogramRange=histogram_range )
    
    
    return acc, histogram_range

def compute_edge_vigra_features( label_img, value_img, feature_names=['Count', 'Mean', 'Variance', 'Quantiles'] ):
    """
    For the given supervoxels (label_img) and underlying singleband data (value_img),
    compute the given features using the vigra RegionFeatureAccumulator framework.
    
    Returns:
        - A RegionFeatureAccumulator with the statistics for all edges in the volume
        - The array edge ids [shape=(N,2)], in the same order as the accumulator results
    
    Caveats:
        - The edges and features along each axis are computed separately, and merged as a final step.
        - For histogram features, the histogram min/max values are initialized from the min/max edge
          values along axis 0, and re-used for axes 1..N
    """
    feature_names = map(str.lower, feature_names)
    assert label_img.shape == value_img.shape
    
    logger.debug("Computing per-axis features...")
    axis_accumulators = []
    edge_label_lookups = []
    histogram_range = None
    for axis in range(label_img.ndim):
        logger.debug("Axis {}: Computing edge mask...".format( axis ))
        edge_mask, edge_ids = edge_id_mask( label_img, axis )
        lookup = unique_edge_labels( [edge_ids] )
        acc, histogram_range = compute_edge_vigra_features_along_axis( axis, edge_mask, edge_ids, lookup, value_img, feature_names, histogram_range )
        
        axis_accumulators.append(acc)
        edge_label_lookups.append(lookup)

    # Get final lookup table from (u,v) -> final_edge_label
    logger.debug("Generating final lookup...")    
    all_edge_ids = []
    for lookup in edge_label_lookups:
        all_edge_ids.append(lookup[['id1', 'id2']].values)
    final_edge_label_lookup_df = unique_edge_labels( all_edge_ids )

    final_acc, final_edge_ids = merge_edge_vigra_features( edge_label_lookups, final_edge_label_lookup_df, axis_accumulators )
    return final_acc, final_edge_ids

def merge_edge_vigra_features( edge_label_lookups, final_edge_label_lookup_df, axis_accumulators ):

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
    
    # return the final accumulator, and the edge ids
    return final_acc, final_edge_label_lookup_df[['id1', 'id2']].values

def compute_sp_vigra_features( label_img, value_img, feature_names=['Count', 'Mean', 'Variance', 'Quantiles'] ):
    """
    Note: Here we flatten the arrays before passing them to vigra,
          so coordinate-based features won't work.
    """
    feature_names = map(str.lower, feature_names)
    for feature_name in feature_names:
        for nonsupported_name in ('coord', 'region'):
            # This could be fixed easily (just don't flatten the data)
            # but we should check the performance implications.
            assert nonsupported_name not in feature_name, \
                "Coordinate-based SP features are not currently supported!"
    
    value_img = value_img.astype(np.float32, copy=False)
    acc = vigra.analysis.extractRegionFeatures( value_img.reshape((1,-1), order='A'),
                                                label_img.reshape((1,-1), order='A'),
                                                features=feature_names )
    return acc

def append_sp_features_onto_edge_features( edge_df, sp_df, sp_highlevel_features ):
    """
    edge_df: The dataframe with edge features. First columns must be 'id1', 'id2'
    sp_df: The dataframe with raw superpixel features
    sp_highlevel_features: Feature names without 'sp' prefix or '_sp1' suffix
    """
    sp_highlevel_features = map(str.lower, sp_highlevel_features)
    # Add two columns to the edge_df for every sp_df column (for id1 and id2)
    edge_df = pd.merge( edge_df, sp_df, left_on=['id1'], right_on=['sp_id'], how='left', copy=False)
    edge_df = pd.merge( edge_df, sp_df, left_on=['id2'], right_on=['sp_id'], how='left', copy=False, suffixes=('_sp1', '_sp2'))
    del edge_df['sp_id_sp1']
    del edge_df['sp_id_sp2']

    # Now create sum/difference columns
    for sp_feature in sp_highlevel_features:
        sp_feature_sum = edge_df['sp_' + sp_feature + '_sp1'].values + edge_df['sp_' + sp_feature + '_sp2'].values
        if sp_feature in ('count', 'sum'):
            # Special case for count
            sp_feature_sum = np.power(sp_feature_sum, np.float32(1./3), out=sp_feature_sum)
        edge_df['sp_' + sp_feature + '_sum'] = sp_feature_sum

        sp_feature_difference = edge_df['sp_' + sp_feature + '_sp1'].values - edge_df['sp_' + sp_feature + '_sp2'].values
        if sp_feature in ('count', 'sum'):
            sp_feature_difference = np.abs(sp_feature_difference, out=sp_feature_difference)
            sp_feature_difference = np.power(sp_feature_difference, np.float32(1./3), out=sp_feature_difference)
        edge_df['sp_' + sp_feature + '_difference'] = sp_feature_difference

        # Don't need these any more
        del edge_df['sp_' + sp_feature + '_sp1']
        del edge_df['sp_' + sp_feature + '_sp2']
    
    return edge_df

##
## Everything below is not used above, but merely alternative functions
## that work directly from a label_img, not a pre-processed Rag object.
##
def compute_highlevel_edge_features( label_img, value_img, highlevel_features ):
    """
    Computes features for edges, including superpixel features.
    Returns a pandas dataframe.  The first two columns are 'id1' and 'id2', and the other columns are the computed features.
    
    Supported feature names:
    (edge_|sp_) + ( count|sum|mean|variance|kurtosis|skewness
                    |quantiles_10|quantiles_25|quantiles_50|quantiles_75|quantiles_90 )
    For example: highlevel_features = ['edge_count', 'edge_mean', 'sp_quantiles_75']
    
    All 'sp' feature names result in two columns, for the sum and difference between the two superpixels adjacent to the edge.
    Additionally, the 'count' sp feature is reduced via cube-root (as in the multicut paper).
    Same for the 'sum' feature.
    """
    highlevel_features = map(str.lower, highlevel_features)
    edge_highlevel_features = filter(lambda name: name.startswith('edge_'), highlevel_features)
    edge_highlevel_features = map(lambda name: name[len('edge_'):], edge_highlevel_features) # drop 'edge_' prefix
    edge_vigra_features = map(lambda name: name.split('_')[0], edge_highlevel_features ) # drop quantile suffixes like '_25'
    edge_vigra_features = list(set(edge_vigra_features)) # drop duplicates (from multiple quantile selections)

    edge_acc, edge_ids = compute_edge_vigra_features( label_img, value_img, edge_vigra_features )

    # Create a dataframe to store the result    
    edge_df = pd.DataFrame(edge_ids, columns=['id1', 'id2'])
    
    # Adding columns for edge features is easy, just add them verbatim
    for edge_feature in edge_highlevel_features:
        if edge_feature.startswith('quantiles'):
            quantile_suffix = edge_feature.split('_')[1]
            q_index = ['0', '10', '25', '50', '75', '90', '100'].index(quantile_suffix)
            edge_df['edge_' + edge_feature] = edge_acc['quantiles'][:, q_index]
        else:
            edge_df['edge_' + edge_feature] = edge_acc[edge_feature]

    return edge_df, edge_highlevel_features

def compute_highlevel_sp_features( label_img, value_img, highlevel_features ):
    """
    highlevel_features
    """
    highlevel_features = map(str.lower, highlevel_features)
    sp_highlevel_features = filter(lambda name: name.startswith('sp_'), highlevel_features)
    sp_highlevel_features = map(lambda name: name[len('sp_'):], sp_highlevel_features) # drop 'sp_' prefix
    sp_vigra_features = map(lambda name: name.split('_')[0], sp_highlevel_features ) # drop quantile suffixes like '_25'
    sp_vigra_features = list(set(sp_vigra_features)) # drop duplicates (from multiple quantile selections)
    if not sp_vigra_features:
        # No superpixel features.  We're done.
        return None, sp_highlevel_features
    
    logger.debug("Computing SP features...")
    sp_acc = compute_sp_vigra_features( label_img, value_img, sp_vigra_features )

    logger.debug("Converting SP features to edge features...")

    # Create an almost-empty dataframe to store the sp features
    sp_df = pd.DataFrame({ 'sp_id' : np.arange(sp_acc.maxRegionLabel()+1, dtype=np.uint32) })
    
    # Add a column for each sp feature we'll need
    for sp_feature in sp_highlevel_features:
        if sp_feature.startswith('quantiles'):
            quantile_suffix = sp_feature.split('_')[1]
            q_index = ['0', '10', '25', '50', '75', '90', '100'].index(quantile_suffix)
            sp_df['sp_' + sp_feature] = sp_acc['quantiles'][:, q_index]
        else:
            sp_df['sp_' + sp_feature] = sp_acc[sp_feature]

    return sp_df, sp_highlevel_features

def compute_highlevel_features( label_img, value_img, highlevel_features ):
    highlevel_features = list(set(highlevel_features))
    edge_df, edge_features = compute_highlevel_edge_features( label_img, value_img, highlevel_features )
    sp_df, sp_highlevel_features = compute_highlevel_sp_features(  label_img, value_img, highlevel_features  )
    if sp_df is not None:
        edge_df = append_sp_features_onto_edge_features( edge_df, sp_df, sp_highlevel_features )
    return edge_df

def get_edge_ids( label_img ):
    """
    Convenience function. Not used above (yet).
    Returns a DataFrame with columns ['id1', 'id2', 'edge_label'], sorted by ('id1', 'id2')
    """
    all_edge_ids = []
    for axis in range(label_img.ndim):
        edge_mask, edge_ids = edge_id_mask( label_img, axis )
        lookup = unique_edge_labels( [edge_ids] )
        all_edge_ids.append(lookup[['id1', 'id2']].values)
    final_edge_label_lookup_df = unique_edge_labels( all_edge_ids )
    return final_edge_label_lookup_df

if __name__ == "__main__":
    import sys
    logger.addHandler( logging.StreamHandler(sys.stdout) )
    logger.setLevel(logging.DEBUG)
    
    import h5py
    #watershed_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/256/watershed-256.h5'
    watershed_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/512/watershed-512.h5'

    #grayscale_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/256/grayscale-256.h5'
    grayscale_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/512/grayscale-512.h5'
    
    logger.info("Loading watershed...")
    with h5py.File(watershed_path, 'r') as f:
        watershed = f['watershed'][:]
    if watershed.shape[-1] == 1:
        watershed = watershed[...,0]
    watershed = vigra.taggedView( watershed, 'zyx' )

    logger.info("Loading grayscale...")
    with h5py.File(grayscale_path, 'r') as f:
        grayscale = f['grayscale'][:]
    if grayscale.shape[-1] == 1:
        grayscale = grayscale[...,0]
    grayscale = vigra.taggedView( grayscale, 'zyx' )

    feature_names = []
    feature_names += ['edge_count', 'edge_sum', 'edge_mean', 'edge_variance',
                      'edge_quantiles_10', 'edge_quantiles_25', 'edge_quantiles_50', 'edge_quantiles_75', 'edge_quantiles_90',
                       ]
    #feature_names += ['sp_count', 'sp_sum', 'sp_mean', 'sp_variance', 'sp_kurtosis', 'sp_skewness']
    feature_names += ['sp_count']

    from lazyflow.utility import Timer

    with Timer() as timer:
        logger.info("Creating python Rag...")
        rag = Rag( watershed )
        logger.info("Rag took {} seconds".format( timer.seconds() ))
        #rag.compute_edge_vigra_features(grayscale)
        #rag.compute_highlevel_edge_features(grayscale, feature_names)
        logger.info("Starting computation...")
        edge_features_df = rag.compute_highlevel_features(grayscale, feature_names)
        print edge_features_df[0:10]
    print "Computing features with python Rag took: {}".format( timer.seconds() )
    
    print ""
    print ""
    
    with Timer() as timer:
        #ec = edge_coords_nd(watershed)
        #ids = edge_ids(watershed)
        features_df = compute_highlevel_features(watershed, grayscale, feature_names)
        print features_df.columns.values
    print "time was: {}".format( timer.seconds() )

    assert (features_df.values == edge_features_df.values).all()

#     with Timer() as timer:
#         get_edge_ids(watershed)
#     print "Just computing edge ids took {}".format( timer.seconds() )

#     import vigra
#     with Timer() as timer:
#         gridGraph = vigra.graphs.gridGraph(watershed.shape)
#         rag = vigra.graphs.regionAdjacencyGraph(gridGraph, watershed)
#         #ids = rag.uvIds()
#     print "vigra time was: {}".format( timer.seconds() )





