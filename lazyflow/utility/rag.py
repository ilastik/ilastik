import collections
import numpy as np
import pandas as pd
import vigra

import logging
logger = logging.getLogger(__name__)

from sp_utils import label_vol_mapping, edge_mask_for_axis, edge_ids_for_axis, \
                     unique_edge_labels, extract_edge_values_for_axis, nonzero_coord_array

class Rag(object):
    """
    Region Adjacency Graph
    
    Initialized with an ND label image of superpixels, and stores
    the edges between superpixels.
    
    Internally, the edges along each axis are found and stored separately.
    (See the Rag.AxisEdgeData type.)
    
    Attributes
    ----------
    label_img: The label volume
    
    sp_ids: 1D ndarray of (possibly non-consecutive) superpixel ID values, sorted.

    max_sp: The maximum superpixel ID in the label volume

    num_sp: The number of superpixels in the volume.
            Not necessarily the same as max_sp.
    
    num_edges: The number of edges in the label volume.

    edge_ids: ndarray of adjacent superpixel IDs, shape=(num_edges, 2). Sorted.
              Guarantee: For all edge_ids (u,v), u < v.
    
    edge_label_lookup_df: A pandas DataFrame listing pairs of adjacent superpixels 
                          and a column of uint32 values to uniquely identify each edge.
                          Columns: 'sp1', 'sp2', 'edge_label'
    """

    # AxisEdgeData objects store all information for edges along a particular axis.
    # The Rag stores one for each dimension of the label volume.
    #
    # Fields:
    #     axis: int
    #     mask: Either of the following:
    #           - ndarray of bool (same shape as labels) OR
    #           - index array tuple (see comments below about save_ram flag)
    #     ids: ndarray of edge_id pairs for all edge pixels along the axis, same order as mask.nonzero()
    #     label_lookup: DataFrame with columns 'sp1', 'sp2', 'edge_label' (no duplicate rows)
    AxisEdgeData = collections.namedtuple('AxisEdgeData', 'axis mask ids label_lookup')
    
    def __init__( self, label_img, save_ram=True ):
        """
        Constructor.
        
        Parameters
        ----------
        label_img: ND label volume.
                   Label values do not need to be consecutive, but *excessively* high label values
                   will require extra RAM when computing features, due to zeros in the RegionFeatureAccumulators.

        save_ram: Save RAM by storing edge locations as coordinate arrays instead of boolean masks.
                  (See source code comments for more details.)
        """
        assert hasattr(label_img, 'axistags'), \
            "For optimal performance, make sure label_img is a VigraArray with accurate axistags"
        self._label_img = label_img

        self.axis_edge_datas = []
        for axis in range(label_img.ndim):
            edge_mask = edge_mask_for_axis(label_img, axis)
            edge_ids = edge_ids_for_axis(label_img, edge_mask, axis)
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
        
        # Columns: sp1, sp2, edge_label
        final_edge_label_lookup_df = unique_edge_labels( map(lambda t: t.ids, self.axis_edge_datas) )

        # Tiny optimization:
        # We will be accessing edge_ids over and over, so let's extract them now
        self._edge_ids = final_edge_label_lookup_df[['sp1', 'sp2']].values

        # Now, to avoid having multiple copies of edge_ids in RAM,
        # re-create final_edge_label_lookup_df using the cached edge_ids array
        self._final_edge_label_lookup_df = pd.DataFrame( {'sp1': self._edge_ids[:,0],
                                                          'sp2': self._edge_ids[:,1],
                                                          'edge_label': final_edge_label_lookup_df['edge_label'].values } )

        # Compute the number of superpixels.
        # We don't assume that SP ids are consecutive, so it's not the same as label_img.max()        
        unique_left = self._final_edge_label_lookup_df['sp1'].unique()
        unique_right = self._final_edge_label_lookup_df['sp2'].unique()
        self._sp_ids = pd.Series( np.concatenate((unique_left, unique_right))).unique()
        self._sp_ids.sort()
        self._num_sp = len( self._sp_ids )
        self._max_sp = self._sp_ids.max()

    @property
    def label_img(self):
        return self._label_img

    @property
    def sp_ids(self):
        return self._sp_ids

    @property
    def num_sp(self):
        return self._num_sp
    
    @property
    def max_sp(self):
        return self._max_sp

    @property
    def num_edges(self):
        return len(self._final_edge_label_lookup_df)

    @property
    def edge_ids(self):
        return self._edge_ids

    @property
    def edge_label_lookup_df(self):
        return self._final_edge_label_lookup_df

    def serialize_hdf5(self, h5py_group):
        raise NotImplementedError # FIXME

    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        raise NotImplementedError # FIXME

    def edge_decisions_from_groundtruth(self, groundtruth_vol, asdict=False):
        """
        Given a reference segmentation, return a boolean array of "decisions"
        indicating whether each edge in this RAG should be ON or OFF for best
        consistency with the groundtruth.
        
        The result is returned in the same order as self.edge_ids.
        An OFF edge means that the two superpixels are merged in the reference volume.
        
        If asdict=True, return the result as a dict of {(sp1, sp2) : bool}
        """
        sp_to_gt_mapping = label_vol_mapping(self.label_img, groundtruth_vol)

        unique_sp_edges = self.edge_ids()
        decisions = sp_to_gt_mapping[unique_sp_edges[:, 0]] != sp_to_gt_mapping[unique_sp_edges[:, 1]]
    
        if asdict:
            return dict( izip(imap(tuple, unique_sp_edges), decisions) )
        return decisions

    def compute_highlevel_features(self, value_img, highlevel_feature_names):
        """
        The primary API function for computing features.
        Returns a pandas DataFrame with columns ['sp1', 'sp2', ...output feature names...]
        
        Parameters
        ----------
        value_img: ND array, same shape as Rag.label_img.
                   Pixel values are converted to float32 internally.
        
        highlevel_feature_names: A list of feaature names to compute.
                                 All features are computed with the vigra RegionFeatureAccumulators library.
                                 
                                 Names must begin with a prefix of either 'edge_' or 'sp_' indicating whether
                                 the feature is to be computed on the edge-adjacent pixels themselves, or over
                                 the entire superpixels adjacent to the edges.
                                 
                                 Additionally, quantile features must have a suffix to indicate which quantile
                                 value to extract, e.g. '_25'.
                                 
                                 Coordinate-based features (such as RegionAxes) are not supported.
                                 With minor changes, we could support them for superpixels.
                                 Supporting them for edge features would require significant changes,
                                 but would be possible (at a cost).

                                SUPPORTED FEATURE NAMES:
                                
                                (edge_|sp_) + ( count|sum|minimum|maximum|mean|variance|kurtosis|skewness
                                                |quantiles_10|quantiles_25|quantiles_50|quantiles_75|quantiles_90 )
                                For example: highlevel_features = ['edge_count', 'edge_mean', 'sp_quantiles_75']
                                
                                All 'sp' feature names result in *two* output columns, for the sum and difference
                                between the two superpixels adjacent to the edge.
                                
                                As a special case, the 'sp_count' feature is reduced via cube-root
                                (as done in the multicut paper). Same goes for the 'sp_sum' feature.
        """
        assert hasattr(value_img, 'axistags'), \
            "For optimal performance, make sure value_img is a VigraArray with accurate axistags"
        
        # Get generic names for each category (edge/sp)
        _, edge_generic_vigra_feature_names, _ = Rag._process_highlevel_feature_names(highlevel_feature_names, 'edge_')
        _, sp_generic_vigra_feature_names, _ = Rag._process_highlevel_feature_names(highlevel_feature_names, 'sp_')

        # Compute
        edge_df = self._compute_highlevel_edge_features(value_img, edge_generic_vigra_feature_names)        
        sp_df = self._compute_highlevel_sp_features(value_img, sp_generic_vigra_feature_names)

        # Merge
        if sp_df is not None:
            edge_df = Rag._append_sp_features_onto_edge_features( edge_df, sp_df, sp_generic_vigra_feature_names )

        return edge_df

    ##
    ## FEATURE NAMING CONVENTIONS:
    ##
    ##    The user passes in 'highlevel' feature names, but internal functions 
    ##    require slightly different variations of the names, as described here.
    ##
    ##    So-called 'highlevel' feature names include a prefix ('edge_' or 'sp_'),
    ##    and possibly a suffix (e.g. '_25'), while internal functions deal with 
    ##    lower-level variations referred to as:
    ##      - 'generic_feature_names', i.e. no prefix, but might have a quantile suffix such as '_25'
    ##      - 'vigra_feature_names', i.e. no prefix or suffix. These names are directly passed to extractRegionFeatures()
    ## 
    ##    So, the transformations go from 'highlevel' -> 'generic' -> 'vigra'.
    ##
    ##    Example highlevel_feature_names:
    ##        ['sp_count', 'edge_count', 'edge_mean', 'edge_quantiles_25']
    ##    Example generic_vigra_feature_names:
    ##        ['count', 'mean', 'quantiles_25']
    ##    Example vigra_feature_names: 
    ##        ['count', mean', 'quantiles']
    ##
    ##    The final results are returned in a pandas.DataFrame, with columns named with 'output' feature names.
    ##    For edge-based features, the output names are identical to the 'highlevel' names.
    ##    For superpixel-based features, the output names have an additional suffix for 'sum' and 'difference'.
    ##
    ##    Example output_feature_names:
    ##        ['edge_count', 'edge_quantiles_25',
    ##         'sp_count_sum', 'sp_count_difference', 'sp_quantiles_25_sum', 'sp_quantiles_25_difference' ]

    def _compute_highlevel_edge_features(self, value_img, generic_vigra_feature_names):
        """
        Computes features over the edge pixels.
        Returns a pandas dataframe with length == self.num_edges
        The first two columns are 'sp1' and 'sp2', and the other columns are the computed features.
        
        Parameters
        ----------
        value_img: ND array, same shape as self.label_img.
                   Pixel values are converted to float32 internally.
        
        generic_vigra_feature_names: See feature naming convention notes in source comments above.
        """
        vigra_feature_names = Rag._process_generic_vigra_feature_names(generic_vigra_feature_names)

        edge_df = pd.DataFrame(self.edge_ids, columns=['sp1', 'sp2'])

        if vigra_feature_names:
            final_edge_acc = self._accumulate_edge_vigra_features( value_img, vigra_feature_names )
            Rag._add_features_to_dataframe(generic_vigra_feature_names, final_edge_acc, edge_df, 'edge_')
        
        return edge_df

    def _accumulate_edge_vigra_features(self, value_img, vigra_feature_names):
        """
        Return a vigra RegionFeaturesAccumulator with the results of all features.
        computed over the edge pixels of the given value_img.
        The accumulator's 'region' indexes will correspond to self.edge_label_lookup_df['edge_label']
        
        Parameters
        ----------
        value_img: ND array, same shape as self.label_img.
                   Pixel values are converted to float32 internally.
        
        vigra_feature_names: Feature names exactly as passed to vigra.analysis.extractRegionFeatures()
        """
        logger.debug("Computing per-axis features...")

        axis_accumulators = []
        histogram_range = None
        for axis in range(self.label_img.ndim):
            # The histogram_range is computed from the first axis edges,
            # and re-used for subsequent axes.
            # (The histogram_range for any given axis will be close enough to the global 
            # histogram_range, except for pathological cases, such as rectangular superpixels.)
            acc, histogram_range = self._compute_edge_vigra_features_along_axis( axis,
                                                                                value_img,
                                                                                vigra_feature_names,
                                                                                histogram_range )
            axis_accumulators.append(acc)

        final_acc = self._merge_edge_vigra_features( axis_accumulators )
        return final_acc

    def _compute_edge_vigra_features_along_axis(self, axis, value_img, vigra_feature_names, histogram_range=None):
        """
        Find the edges in the direction of the given axis and
        compute region features for the pixels adjacent to the edges.
        
        Returns a tuple:

         - A vigra RegionFeaturesAccumulator containing the edge statistics.
           Each edge will be assigned a unique label id (an integer).

         - The histogram range that was used for any histogram features.
           (See parameter explanation below.)

        Parameters
        ----------
        axis: The axis to compute features along.
        
        value_img: ND array, same shape as self.label_img.
                   Pixel values are converted to float32 internally.
        
        vigra_feature_names: Feature names exactly as passed to vigra.analysis.extractRegionFeatures()
        
        histogram_range: If None, histogram_range will be determined automatically as needed (and returned).
                         Otherwise, must be a range [min,max] to use for all histogram features (e.g. 'quantiles').
                         In that case, the returned histogram_range will simply be identical to the one you gave.
        """
        _axis, edge_mask, edge_ids, edge_label_lookup = self.axis_edge_datas[axis]
        assert _axis == axis
    
        for feature_name in vigra_feature_names:
            for nonsupported_name in ('coord', 'region'):
                # This could be fixed by the following:
                # - Combine the mask and edge_labels into a label volume (same shape as mask)
                # - Compute coordinate-based features separately
                # - Edges with multiple 'faces' will have strange or undefined coordinate features.
                # - If *weighted* coordinate-based features are also needed, then need to combine 
                #   mask and edge_values into a edge_value volume (same shape as mask)
                # But the performance implications could be severe...
                assert nonsupported_name not in feature_name.lower(), \
                    "Coordinate-based edge features are not currently supported!"
    
        edge_values = extract_edge_values_for_axis(axis, edge_mask, value_img)
    
        # We could use the default pandas index, but that's int64
        # Forcing uint32 for the index should save RAM.
        index_u32 = pd.Index(np.arange(len(edge_ids)), dtype=np.uint32)
        df_edges = pd.DataFrame(edge_ids, columns=['sp1', 'sp2'], index=index_u32)
        df_edges_with_labels = pd.merge(df_edges, edge_label_lookup, on=['sp1', 'sp2'], how='left')
        edge_labels = df_edges_with_labels['edge_label'].values
    
        # Sanity check
        assert edge_values.shape == edge_labels.shape
    
        if not histogram_range and set(['quantiles', 'histogram']) & set(vigra_feature_names):
            histogram_range = [float(edge_values.min()), float(edge_values.max())]
    
        if not histogram_range:
            # Not using a histogram, but vigra needs a default value.
            histogram_range = "globalminmax"
        
        logger.debug("Axis {}: Computing region features...".format( axis ))
        # Must add singleton y-axis here because vigra doesn't support 1D data
        acc = vigra.analysis.extractRegionFeatures( edge_values.reshape((1,-1), order='A'),
                                                    edge_labels.reshape((1,-1), order='A'),
                                                    #ignoreLabel=0, # Would be necessary if we were working with the full image.
                                                    features=vigra_feature_names,
                                                    histogramRange=histogram_range )
        
        
        return acc, histogram_range

    def _compute_highlevel_sp_features(self, value_img, generic_vigra_feature_names):
        """
        Computes features over all voxels in each superpixel.
        Returns a pandas dataframe with length == self.num_sp
        The first two columns is 'sp_id', and the other columns are the computed features.
        
        Parameters
        ----------
        value_img: ND array, same shape as self.label_img.
                   Pixel values are converted to float32 internally.
        
        generic_vigra_feature_names: See feature naming convention notes in source comments above.
        """
        if not generic_vigra_feature_names:
            # No superpixel features requested. We're done.
            return None

        vigra_feature_names = Rag._process_generic_vigra_feature_names(generic_vigra_feature_names)
        
        logger.debug("Computing SP features...")
        sp_acc = self._accumulate_sp_vigra_features( value_img, vigra_feature_names )
    
        # Create an almost-empty dataframe to store the sp features
        logger.debug("Saving SP features to DataFrame...")
        sp_df = pd.DataFrame({ 'sp_id' : np.arange(sp_acc.maxRegionLabel()+1, dtype=np.uint32) })
        Rag._add_features_to_dataframe(generic_vigra_feature_names, sp_acc, sp_df, 'sp_')            
        return sp_df

    def _merge_edge_vigra_features(self, axis_accumulators):
        """
        Merge the given list of RegionFeatureAccumulators (one per axis) into a single accumulator.
        The given accumulators are each indexed according to the `label_lookup` for the corresponding axis.
        Pandas will be used to convert edge_label indices from each accumulator into a final edge label,
        and then merged into one final RegionFeatureAccumulator, which is returned.
        
        Parameters
        ----------
        axis_accumulators: A list of RegionFeatureAccumulators (one for each dimension of our label_img)
        """
        assert len(axis_accumulators) == len(self.axis_edge_datas) == self.label_img.ndim
        edge_label_lookups = map(lambda t: t.label_lookup, self.axis_edge_datas)
    
        # For each axis-specific lookup: translate edge_label -> (u,v) -> final_edge_label
        # And merge into the final accumulator
        logger.debug("Merging per-axis features into final accumulator...")
        final_acc = axis_accumulators[0].createAccumulator()
        for acc, this_axis_lookup_df in zip(axis_accumulators, edge_label_lookups):
            # Columns of this combined_lookup_df will be:
            # ['sp1', 'sp2', 'edge_label_this_axis', 'edge_label_final']
            combined_lookup_df = pd.merge( this_axis_lookup_df,
                                           self._final_edge_label_lookup_df,
                                           on=['sp1', 'sp2'],
                                           how='left',
                                           suffixes=('_this_axis', '_final'))
            
            # Create an index array for converting between 'this_axis' labels and 'final' labels.
            max_edge_label_this_axis = this_axis_lookup_df['edge_label'].max()
            axis_to_final_index_array = np.zeros( shape=(max_edge_label_this_axis+1,), dtype=np.uint32 )
            axis_to_final_index_array[ combined_lookup_df['edge_label_this_axis'].values ] = combined_lookup_df['edge_label_final'].values
    
            final_acc.merge( acc, axis_to_final_index_array )
        
        # return the final accumulator
        return final_acc

    def _accumulate_sp_vigra_features(self, value_img, vigra_feature_names):
        """
        Note: Here we flatten the arrays before passing them to vigra,
              so coordinate-based features won't work.
              This could be easiliy fixed by simply not flattening the arrays,
              but you'll also need to define new suffixes for multi=value features
              (e.g. 'region_axes', etc.), and modify _add_features_to_dataframe() accordingly.
        """
        for feature_name in vigra_feature_names:
            for nonsupported_name in ('coord', 'region'):
                # This could be fixed easily (just don't flatten the data)
                # but we should check the performance implications.
                assert nonsupported_name not in feature_name, \
                    "Coordinate-based SP features are not currently supported!"
        
        value_img = value_img.astype(np.float32, copy=False)
        acc = vigra.analysis.extractRegionFeatures( value_img.reshape((1,-1), order='A'),
                                                    self.label_img.reshape((1,-1), order='A'),
                                                    features=vigra_feature_names )
        return acc

    @classmethod
    def _add_features_to_dataframe(cls, generic_vigra_feature_names, acc, df, output_prefix):
        """
        Extract the specified features from the given RegionFeaturesAccumulator
        and append them as columns to the given DataFrame.
        Here we implement the logic for handling feature names that have 
        a suffix (e.g. 'quantiles_25').
        
        Parameters
        ----------
        generic_vigra_feature_names: See feature naming convention notes in source comments above.

        acc: A RegionFeatureAccumulator from which to extract the specified features.

        df: A pandas.DataFrame to append the features to

        output_prefix: Prefix column names with the given string.  Must be either 'edge_' or 'sp_'.
        """
        assert output_prefix in ('edge_', 'sp_')
        # Add a column for each feature we'll need
        for generic_name in generic_vigra_feature_names:
            output_name = output_prefix + generic_name
            if generic_name.startswith('quantiles'):
                quantile_suffix = generic_name.split('_')[1]
                q_index = ['0', '10', '25', '50', '75', '90', '100'].index(quantile_suffix)
                df[output_name] = acc['quantiles'][:, q_index]
            else:
                df[output_name] = acc[generic_name]

    @classmethod
    def _append_sp_features_onto_edge_features(cls, edge_df, sp_df, generic_vigra_features):
        """
        Given a DataFrame with edge features and another DataFrame with superpixel features,
        add columns to the edge_df for each of the specified (superpixel) feature names.
        
        For each sp feature, two columns are added to the output, for the sum and difference
        between the feature values for the two superpixels adjacent to the edge.
        (See 'output' feature naming convention notes above for column names.)

        As a special case, the 'count' and 'sum' sp features are normalized first by taking
        their cube roots, as indicated in the Multicut paper.
        
        Returns the augmented edge_df.

        Parameters
        ----------
        edge_df: The dataframe with edge features.
                 First columns must be 'sp1', 'sp2'.
                 len(edge_df) == self.num_edges
                 
        sp_df: The dataframe with raw superpixel features.
               First column must be 'sp_id'.
               len(sp_df) == self.num_sp

        generic_vigra_features: Superpixel feature names without 'sp_' prefix or '_sp1' suffix,
                                 but possibly with quantile suffix, e.g. '_25'.
                                 See feature naming convention notes above for details.
        """
        # Add two columns to the edge_df for every sp_df column (for sp1 and sp2)
        edge_df = pd.merge( edge_df, sp_df, left_on=['sp1'], right_on=['sp_id'], how='left', copy=False)
        edge_df = pd.merge( edge_df, sp_df, left_on=['sp2'], right_on=['sp_id'], how='left', copy=False, suffixes=('_sp1', '_sp2'))
        del edge_df['sp_id_sp1']
        del edge_df['sp_id_sp2']
    
        # Now create sum/difference columns
        for sp_feature in generic_vigra_features:
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

    @classmethod
    def _process_highlevel_feature_names(cls, highlevel_feature_names, prefix):
        """
        A little utility function for converting so-called 'highlevel'
        feature names into their 'low-level' counterparts.
        See feature naming convention explanation above for more details.
        """
        highlevel_feature_names = map(str.lower, highlevel_feature_names)
        assert prefix in ('edge_', 'sp_')

        # Get only the edge|sp features
        highlevel_feature_names = filter(lambda name: name.startswith(prefix), highlevel_feature_names)
        
        # drop 'edge_' prefix
        generic_vigra_feature_names = map(lambda name: name[len(prefix):], highlevel_feature_names)

        vigra_feature_names = cls._process_generic_vigra_feature_names(generic_vigra_feature_names)
        
        return highlevel_feature_names, generic_vigra_feature_names, vigra_feature_names

    @classmethod
    def _process_generic_vigra_feature_names(cls, generic_vigra_feature_names):
        """
        A little utility function for converting so-called 'generic' vigra feature names
        into the `low-level` name required by vigra's extractRegionFeatures().
        See feature naming convention explanation above for more details.
        """
        generic_vigra_feature_names = map(str.lower, generic_vigra_feature_names)

        # drop quantile suffixes like '_25'
        vigra_feature_names = map(lambda name: name.split('_')[0], generic_vigra_feature_names )
        
        # drop duplicates (from multiple quantile selections)
        return list(set(vigra_feature_names))



if __name__ == "__main__":
    import sys
    logger.addHandler( logging.StreamHandler(sys.stdout) )
    logger.setLevel(logging.DEBUG)

    from lazyflow.utility import Timer
    
    import h5py
    watershed_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/256/watershed-256.h5'
    grayscale_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/256/grayscale-256.h5'

    #watershed_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/512/watershed-512.h5'
    #grayscale_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/512/grayscale-512.h5'
    
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
    # typical features will be float32, not uint8, so let's not cheat
    grayscale = grayscale.astype(np.float32, copy=False)

    feature_names = []
    #feature_names = ['edge_mean']
    feature_names += ['edge_count', 'edge_sum', 'edge_mean', 'edge_variance',
                      'edge_minimum', 'edge_maximum', 'edge_quantiles_25', 'edge_quantiles_50', 'edge_quantiles_75', 'edge_quantiles_100']
    feature_names += ['sp_count']
    #feature_names += ['sp_count', 'sp_sum', 'sp_mean', 'sp_variance', 'sp_kurtosis', 'sp_skewness']
    #feature_names += ['sp_count', 'sp_variance', 'sp_quantiles_25', ]

    with Timer() as timer:
        logger.info("Creating python Rag...")
        rag = Rag( watershed, save_ram=True )
    logger.info("Creating rag took {} seconds".format( timer.seconds() ))

    with Timer() as timer:
        edge_features_df = rag.compute_highlevel_features(grayscale, feature_names)
    print "Computing features with python Rag took: {}".format( timer.seconds() )
    #print edge_features_df[0:10]
    
    print ""
    print ""

#     # For comparison with vigra.graphs.vigra.graphs.regionAdjacencyGraph
#     import vigra
#     with Timer() as timer:
#         gridGraph = vigra.graphs.gridGraph(watershed.shape)
#         rag = vigra.graphs.regionAdjacencyGraph(gridGraph, watershed)
#         #ids = rag.uvIds()
#     print "Creating vigra Rag took: {}".format( timer.seconds() )
#  
#     from relabel_consecutive import relabel_consecutive
#     watershed = relabel_consecutive(watershed, out=watershed)
#     assert watershed.axistags is not None
#  
#     grayscale_f = grayscale.astype(np.float32, copy=False)
#     with Timer() as timer:
#         gridGraphEdgeIndicator = vigra.graphs.edgeFeaturesFromImage(gridGraph,grayscale_f)
#         p0 = rag.accumulateEdgeFeatures(gridGraphEdgeIndicator)/255.0
#     print "Computing 1 vigra feature took: {}".format( timer.seconds() )
 

#     # For comparison with scikit-image Rag performance. (It's bad.)
#     from skimage.future.graph import RAG
#     with Timer() as timer:
#         logger.info("Creating skimage Rag...")
#         rag = RAG( watershed )
#     logger.info("Creating skimage rag took {} seconds".format( timer.seconds() ))
