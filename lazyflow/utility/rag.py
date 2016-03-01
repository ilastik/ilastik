from itertools import izip, imap
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
    
    TODO: - Should SP features like 'mean' be weighted by SP size 
            before averaged across the edge?
          - Support for anisotropic features will be easy.
            Need to add 'axes' parameter to compute_highlevel_features()
    
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
                          (No duplicate rows.)

    axial_edge_dfs: (Mostly for internal use.)
                    A list of pandas DataFrames (one per axis).
                    Each DataFrame stores the list of all pixel edge pairs
                    in the volume along a particular axis.
                    Columns: ['sp1', 'sp2', 'forwardness', 'edge_label', 'mask_coord']
                        'forwardness': True if sp1 < sp2, otherwise False.
                        'edge_label': A uint32 that uniquely identifies this (sp1,sp2) pair, regardless of axis.
                        'mask_coord': N columns (e.g. 'z', 'y', 'x') using a multi-level index.
                                      Stores coordinates of pixel just to the 'left' of
                                      each pixel edge (or 'before', 'above', etc. depending on the axis).
    """

    def __init__( self, label_img ):
        """
        Constructor.
        
        Parameters
        ----------
        label_img: ND label volume.
                   Label values do not need to be consecutive, but *excessively* high label values
                   will require extra RAM when computing features, due to zeros in the RegionFeatureAccumulators.
        """
        if isinstance(label_img, str) and label_img == '__will_deserialize__':
            return

        assert hasattr(label_img, 'axistags'), \
            "For optimal performance, make sure label_img is a VigraArray with accurate axistags"
        assert set(label_img.axistags.keys()).issubset('zyx'), \
            "Only axes z,y,x are permitted, not {}".format( label_img.axistags.keys() )
        
        self._label_img = label_img

        edge_datas = []
        for axis in range(label_img.ndim):
            edge_mask = edge_mask_for_axis(label_img, axis)
            edge_ids = edge_ids_for_axis(label_img, edge_mask, axis)
            edge_forwardness = edge_ids[:,0] < edge_ids[:,1]
            edge_ids.sort()

            edge_mask_coords = nonzero_coord_array(edge_mask).transpose()
            
            # Save RAM: Convert to the smallest dtype we can get away with.
            if (np.array(label_img.shape) < 2**16).all():
                edge_mask_coords = edge_mask_coords.astype(np.uint16)
            else:
                edge_mask_coords = edge_mask_coords.astype(np.uint32)
                
            edge_datas.append( (edge_mask_coords, edge_ids, edge_forwardness) )

        self._init_final_edge_label_lookup_df(edge_datas)
        self._init_final_edge_ids()
        self._init_axial_edge_dfs(edge_datas)
        self._init_sp_attributes()
    
    def _init_final_edge_label_lookup_df(self, edge_datas):
        """
        Initialize the edge_label_lookup_df attribute.
        """
        all_edge_ids = map(lambda t: t[1], edge_datas)
        self._final_edge_label_lookup_df = unique_edge_labels( all_edge_ids )

    def _init_final_edge_ids(self):
        """
        Initialize the edge_ids, and as a little optimization, RE-initialize the 
        final_edge_lookup, so its columns can be a view of the edge_ids
        """
        # Tiny optimization:
        # Users will be accessing edge_ids over and over, so let's extract them now
        self._edge_ids = self._final_edge_label_lookup_df[['sp1', 'sp2']].values

        # Now, to avoid having multiple copies of _edge_ids in RAM,
        # re-create final_edge_label_lookup_df using the cached edge_ids array
        index_u32 = pd.Index(np.arange(len(self._edge_ids)), dtype=np.uint32)
        self._final_edge_label_lookup_df = pd.DataFrame( index=index_u32,
                                                         data={'sp1': self._edge_ids[:,0],
                                                               'sp2': self._edge_ids[:,1],
                                                               'edge_label': self._final_edge_label_lookup_df['edge_label'].values } )

    def _init_axial_edge_dfs(self, edge_datas):
        """
        Construct the N axial_edge_df DataFrames (for each axis)
        """
        # Now create an axial_edge_df for each axis
        self.axial_edge_dfs = []
        for edge_data in edge_datas:
            edge_mask, edge_ids, edge_forwardness = edge_data

            # Use uint32 index instead of deafult int64 to save ram            
            index_u32 = pd.Index(np.arange(len(edge_ids)), dtype=np.uint32)

            # Initialize with edge sp ids and directionality
            axial_edge_df = pd.DataFrame( columns=['sp1', 'sp2', 'is_forward'],
                                          index=index_u32,
                                          data={ 'sp1': edge_ids[:, 0],
                                                 'sp2': edge_ids[:, 1],
                                                 'is_forward': edge_forwardness } )

            # Add 'edge_label' column. Note: pd.merge() is like a SQL 'join'
            axial_edge_df = pd.merge(axial_edge_df, self._final_edge_label_lookup_df, on=['sp1', 'sp2'], how='left', copy=False)
            
            # Append columns for coordinates
            for key, coords, in zip(self._label_img.axistags.keys(), edge_mask):
                axial_edge_df[key] = coords

            # For easier manipulation of the 'mask_coord' columns, set multi-level index for column names.
            combined_columns = [['sp1', 'sp2', 'forwardness', 'edge_label'] + len(self._label_img.axistags)*['mask_coord'],
                                [  '',     '',            '',           ''] + self._label_img.axistags.keys() ]
            axial_edge_df.columns = pd.MultiIndex.from_tuples(list(zip(*combined_columns)))

            self.axial_edge_dfs.append( axial_edge_df )

    def _init_sp_attributes(self):
        # Cache the unique sp ids to expose as an attribute
        unique_left = self._final_edge_label_lookup_df['sp1'].unique()
        unique_right = self._final_edge_label_lookup_df['sp2'].unique()
        self._sp_ids = pd.Series( np.concatenate((unique_left, unique_right)) ).unique()
        self._sp_ids.sort()
        
        # We don't assume that SP ids are consecutive,
        # so num_sp is not the same as label_img.max()        
        self._num_sp = len(self._sp_ids)
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

    def compute_highlevel_features(self, value_img, highlevel_feature_names):
        """
        The primary API function for computing features.
        Returns a pandas DataFrame with columns ['sp1', 'sp2', ...output feature names...]
        
        Parameters
        ----------
        value_img: ND array, same shape as self.label_img.
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
                                
                                As a special case, the 'sp_count' feature is reduced via cube-root (or square-root)
                                (as done in the multicut paper). Same goes for the 'sp_sum' feature.
        """
        assert hasattr(value_img, 'axistags'), \
            "For optimal performance, make sure value_img is a VigraArray with accurate axistags"
        assert self._label_img.axistags.keys() == value_img.axistags.keys(), \
            "value_img must have same axistags as label_img (in the same order)"
        
        # Get generic names for each category (edge/sp)
        _, edge_generic_vigra_feature_names, _ = Rag._process_highlevel_feature_names(highlevel_feature_names, 'edge_')
        _, sp_generic_vigra_feature_names, _ = Rag._process_highlevel_feature_names(highlevel_feature_names, 'sp_')

        # Compute
        edge_df = self._compute_highlevel_edge_features(value_img, edge_generic_vigra_feature_names)        
        sp_df = self._compute_highlevel_sp_features(value_img, sp_generic_vigra_feature_names)

        # Merge
        if sp_df is not None:
            edge_df = Rag._append_sp_features_onto_edge_features( edge_df, sp_df, sp_generic_vigra_feature_names, self._label_img.ndim )
        return edge_df

    def edge_decisions_from_groundtruth(self, groundtruth_vol, asdict=False):
        """
        Given a reference segmentation, return a boolean array of "decisions"
        indicating whether each edge in this RAG should be ON or OFF for best
        consistency with the groundtruth.
        
        The result is returned in the same order as self.edge_ids.
        An OFF edge means that the two superpixels are merged in the reference volume.
        
        If asdict=True, return the result as a dict of {(sp1, sp2) : bool}
        """
        sp_to_gt_mapping = label_vol_mapping(self._label_img, groundtruth_vol)

        unique_sp_edges = self.edge_ids
        decisions = sp_to_gt_mapping[unique_sp_edges[:, 0]] != sp_to_gt_mapping[unique_sp_edges[:, 1]]
    
        if asdict:
            return dict( izip(imap(tuple, unique_sp_edges), decisions) )
        return decisions

    def naive_segmentation_from_edge_decisions(self, edge_decisions, out=None ):
        """
        Given a list of ON/OFF labels for the Rag edges, compute a new label volume in which
        all supervoxels with at least one inactive edge between them are merged together.
        
        Requires networkx.
        
        Parameters
        ----------
        edge_decisions: 1D bool array of shape (N,), in the same order as self.edge_ids
                        1 means "active", i.e. the two superpixels are separated across that edge, at least
                        0 means "inactive", i.e. the two superpixels will be joined in the final result.
    
        out: Optional. Must be same shape as self.dtype, but may have different dtype.
        """
        import networkx as nx
        assert out is None or hasattr(out, 'axistags'), \
            "Must provide accurate axistags, otherwise performance suffers by 10x"
        assert edge_decisions.shape == (self._edge_ids.shape[0],)
    
        inactive_edge_ids = self.edge_ids[np.nonzero( np.logical_not(edge_decisions) )]
    
        logger.debug("Finding connected components in node graph...")
        g = nx.Graph( list(inactive_edge_ids) ) 
        
        # If any supervoxels are completely independent (not merged with any neighbors),
        # they haven't been added to the graph yet.
        # Add them now.
        g.add_nodes_from(self.sp_ids)
        
        sp_mapping = {}
        for i, sp_ids in enumerate(nx.connected_components(g), start=1):
            for sp_id in sp_ids:
                sp_mapping[int(sp_id)] = i
        del g
    
        return vigra.analysis.applyMapping( self._label_img, sp_mapping, out=out )

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

        index_u32 = pd.Index(np.arange(self.num_edges), dtype=np.uint32)
        edge_df = pd.DataFrame(self.edge_ids, columns=['sp1', 'sp2'], index=index_u32)

        if vigra_feature_names:
            final_edge_acc = self._accumulate_edge_vigra_features( value_img, vigra_feature_names )
            Rag._add_features_to_dataframe(generic_vigra_feature_names, final_edge_acc, edge_df, 'edge_')
        
        return edge_df

    def _accumulate_edge_vigra_features(self, value_img, vigra_feature_names):
        """
        Return a vigra RegionFeaturesAccumulator with the results of all features,
        computed over the edge pixels of the given value_img.
        The accumulator's 'region' indexes will correspond to self.edge_label_lookup_df['edge_label']
        
        Parameters
        ----------
        value_img: ND array, same shape as self.label_img.
                   Pixel values are converted to float32 internally.
        
        vigra_feature_names: Feature names exactly as passed to vigra.analysis.extractRegionFeatures()
        """
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

        # Must extract all edge values first,
        # so we can compute a global histogram_range
        all_edge_values = []
        for axis, axial_edge_df in enumerate(self.axial_edge_dfs):
            logger.debug("Axis {}: Extracting values...".format( axis ))
            mask_coords = tuple(series.values for k,series in axial_edge_df['mask_coord'].iteritems())
            all_edge_values.append( extract_edge_values_for_axis(axis, mask_coords, value_img) )

        # Now pre-compute histogram_range
        histogram_range = "globalminmax"
        if set(['quantiles', 'histogram']) & set(vigra_feature_names):
            logger.debug("Computing global histogram range...")
            histogram_range = [min(map(lambda values: values.min(), all_edge_values)),
                               max(map(lambda values: values.max(), all_edge_values))]
        
        axial_accumulators = []
        for axis, (axial_edge_df, edge_values) in enumerate( zip(self.axial_edge_dfs, all_edge_values) ):
            edge_labels = axial_edge_df['edge_label'].values
            assert edge_values.shape == edge_labels.shape
        
            logger.debug("Axis {}: Computing region features...".format( axis ))
            # Must add singleton y-axis here because vigra doesn't support 1D data
            acc = vigra.analysis.extractRegionFeatures( edge_values.reshape((1,-1), order='A'),
                                                        edge_labels.reshape((1,-1), order='A'),
                                                        #ignoreLabel=0, # Would be necessary if we were working with the dense edge mask image instead of extracted labels.
                                                        features=vigra_feature_names,
                                                        histogramRange=histogram_range )
            axial_accumulators.append(acc)

        final_acc = axial_accumulators[0].createAccumulator()
        for acc in axial_accumulators:
            # This is an identity lookup, but it's necessary since vigra will complain 
            # about different maxIds if we call merge() without a lookup 
            axis_to_final_index_array = np.arange( acc.maxRegionLabel()+1, dtype=np.uint32 )
            final_acc.merge( acc, axis_to_final_index_array )
        return final_acc

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
        index_u32 = pd.Index(np.arange(sp_acc.maxRegionLabel()+1), dtype=np.uint32)
        sp_df = pd.DataFrame({ 'sp_id' : np.arange(sp_acc.maxRegionLabel()+1, dtype=np.uint32) }, index=index_u32)
        Rag._add_features_to_dataframe(generic_vigra_feature_names, sp_acc, sp_df, 'sp_')            
        return sp_df

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
                                                    self._label_img.reshape((1,-1), order='A'),
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
    def _append_sp_features_onto_edge_features(cls, edge_df, sp_df, generic_vigra_features, ndim):
        """
        Given a DataFrame with edge features and another DataFrame with superpixel features,
        add columns to the edge_df for each of the specified (superpixel) feature names.
        
        For each sp feature, two columns are added to the output, for the sum and (absolute) difference
        between the feature values for the two superpixels adjacent to the edge.
        (See 'output' feature naming convention notes above for column names.)

        As a special case, the 'count' and 'sum' sp features are normalized first by taking
        their cube roots (or square roots), as indicated in the Multicut paper.
        
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
        
        ndim: The dimensionality of the original label volume (an integer).
              Used to normalize the 'count' and 'sum' features.
        """
        # Add two columns to the edge_df for every sp_df column (for sp1 and sp2)
        # note: pd.merge() is like a SQL 'join' operation.
        edge_df = pd.merge( edge_df, sp_df, left_on=['sp1'], right_on=['sp_id'], how='left', copy=False)
        edge_df = pd.merge( edge_df, sp_df, left_on=['sp2'], right_on=['sp_id'], how='left', copy=False, suffixes=('_sp1', '_sp2'))
        del edge_df['sp_id_sp1']
        del edge_df['sp_id_sp2']
    
        # Now create sum/difference columns
        for sp_feature in generic_vigra_features:
            sp_feature_sum = ( edge_df['sp_' + sp_feature + '_sp1'].values
                             + edge_df['sp_' + sp_feature + '_sp2'].values )
            if sp_feature in ('count', 'sum'):
                # Special case for count
                sp_feature_sum = np.power(sp_feature_sum,
                                          np.float32(1./ndim),
                                          out=sp_feature_sum)
            edge_df['sp_' + sp_feature + '_sum'] = sp_feature_sum
    
            sp_feature_difference = ( edge_df['sp_' + sp_feature + '_sp1'].values
                                    - edge_df['sp_' + sp_feature + '_sp2'].values )
            sp_feature_difference = np.abs(sp_feature_difference, out=sp_feature_difference)
            if sp_feature in ('count', 'sum'):
                sp_feature_difference = np.power(sp_feature_difference,
                                                 np.float32(1./ndim),
                                                 out=sp_feature_difference)
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

    def serialize_hdf5(self, h5py_group, store_labels=False, compression='lzf', compression_opts=None):
        """
        Serialize the Rag to the given hdf5 group.

        store_labels: If True, the labels will be stored as a (compressed) h5py Dataset.
                      If False, the labels are *not* stored, but you are responsible 
                      for loading them separately when calling dataframe_to_hdf5(),
                      unless you don't plan to use superpixel features.
        """
        # Edge DFs
        axial_df_parent_group = h5py_group.create_group('axial_edge_dfs')
        for axis, axial_edge_df in enumerate(self.axial_edge_dfs):
            df_group = axial_df_parent_group.create_group('{}'.format(axis))
            Rag.dataframe_to_hdf5(df_group, axial_edge_df)

        # Final lookup DF
        lookup_df_group = h5py_group.create_group('final_edge_label_lookup_df')
        Rag.dataframe_to_hdf5(lookup_df_group, self._final_edge_label_lookup_df)

        # label_img metadata
        labels_dset = h5py_group.create_dataset('label_img',
                                                shape=self._label_img.shape,
                                                dtype=self._label_img.dtype,
                                                compression=compression,
                                                compression_opts=compression_opts)
        labels_dset.attrs['axistags'] = self.label_img.axistags.toJSON()
        labels_dset.attrs['valid_data'] = False

        # label_img contents        
        if store_labels:
            # Copy and compress.
            labels_dset[:] = self._label_img
            labels_dset.attrs['valid_data'] = True

    @classmethod
    def deserialize_hdf5(cls, h5py_group, label_img=None):
        """
        Classmethod.
        
        Deserialize the Rag from the given h5py group,
        which was written via Rag.serialize_to_hdf5.

        label_img: If not None, don't load labels from hdf5, use this volume instead.
                   Useful for when serialize_hdf5() was called with store_labels=False. 
        """
        rag = Rag('__will_deserialize__')
        
        # Edge DFs
        rag.axial_edge_dfs =[]
        axial_df_parent_group = h5py_group['axial_edge_dfs']
        for groupname, df_group in sorted(axial_df_parent_group.items()):
            rag.axial_edge_dfs.append( Rag.dataframe_from_hdf5(df_group) )

        # Final lookup DF
        rag._final_edge_label_lookup_df = Rag.dataframe_from_hdf5( h5py_group['final_edge_label_lookup_df'] )
        
        # label_img
        label_dset = h5py_group['label_img']
        axistags = vigra.AxisTags.fromJSON(label_dset.attrs['axistags'])
        if label_dset.attrs['valid_data']:
            assert not label_img, \
                "The labels were already stored to hdf5. Why are you also providing them externally?"
            label_img = label_dset[:]
            rag._label_img = vigra.taggedView( label_img, axistags )
        elif label_img is not None:
            assert hasattr(label_img, 'axistags'), \
                "For optimal performance, make sure label_img is a VigraArray with accurate axistags"
            assert set(label_img.axistags.keys()).issubset('zyx'), \
                "Only axes z,y,x are permitted, not {}".format( label_img.axistags.keys() )
            rag._label_img = label_img
        else:
            rag._label_img = Rag._EmptyLabels(label_dset.shape, label_dset.dtype, axistags)

        # Other attributes
        rag._init_final_edge_ids()
        rag._init_sp_attributes()

        return rag

    @classmethod
    def dataframe_to_hdf5(cls, h5py_group, df):
        """
        Helper function to serialize a pandas.DataFrame to an h5py.Group.

        Known to work for the DataFrames used in this file,
        including the MultiIndex columns in the axial_edge_dfs.
        Not tested with more complicated DataFrame structures. 
        """
        h5py_group['row_index'] = df.index.values
        h5py_group['column_index'] = repr(df.columns.values)
        columns_group = h5py_group.create_group('columns')
        for col_index, col_name in enumerate(df.columns.values):
            columns_group['{:03}'.format(col_index)] = df[col_name].values

    @classmethod
    def dataframe_from_hdf5(cls, h5py_group):
        """
        Helper function to deserialize a pandas.DataFrame from an h5py.Group,
        as written by Rag.dataframe_to_hdf5().

        Known to work for the DataFrames used in this file,
        including the MultiIndex columns in the axial_edge_dfs.
        Not tested with more complicated DataFrame structures. 
        """
        from numpy import array # We use eval() for the column index, which uses 'array'
        row_index_values = h5py_group['row_index'][:]
        column_index_names = list(eval(h5py_group['column_index'][()]))
        if isinstance(column_index_names[0], np.ndarray):
            column_index_names = map(tuple, column_index_names)
            column_index = pd.MultiIndex.from_tuples(column_index_names)
        elif isinstance(column_index_names[0], str):
            column_index = column_index_names
        else:
            raise NotImplementedError("I don't know how to handle that type of column index.: {}"
                                      .format(h5py_group['column_index'][()]))

        columns_group = h5py_group['columns']
        col_values = []
        for _, col_values_dset in sorted(columns_group.items()):
            col_values.append( col_values_dset[:] )
        
        return pd.DataFrame( index=row_index_values,
                             columns=column_index,
                             data={ name: values for name,values in zip(column_index_names, col_values) } )

    class _EmptyLabels(object):
        """
        A little stand-in for a labels object, in case the user wants
        to deserialize the Rag without a copy of the original labels.
        All functions in Rag can work with this object, except for
        SP computation, which needs the original label image.
        """
        def __init__(self, shape, dtype, axistags):
            object.__setattr__(self, 'shape', shape)
            object.__setattr__(self, 'dtype', dtype)
            object.__setattr__(self, 'axistags', axistags)
            object.__setattr__(self, 'ndim', len(shape))

        def _raise_NotImplemented(self, *args, **kwargs):
            raise NotImplementedError("Labels were not deserialized from hdf5.")
        
        # Accessing any function or attr other than those defined in __init__ will fail.
        __add__ = __radd__ = __mul__ = __rmul__ = __div__ = __rdiv__ = \
        __truediv__ = __rtruediv__ = __floordiv__ = __rfloordiv__ = \
        __mod__ = __rmod__ = __pos__ = __neg__ = __call__ = \
        __getitem__ = __lt__ = __le__ = __gt__ = __ge__ = \
        __complex__ = __pow__ = __rpow__ = \
        __str__ = __repr__ = __int__ = __float__ = \
        __setattr__ = \
            _raise_NotImplemented
        
        def __getattr__(self, k):
            try:
                return object.__getattr__(self, k)
            except AttributeError:
                self._raise_NotImplemented()

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
        rag = Rag( watershed )
    logger.info("Creating rag ({} superpixels, {} edges) took {} seconds"
                .format( rag.num_sp, rag.num_edges, timer.seconds() ))
    print "unique edge labels per axis: {}".format( [len(df['edge_label'].unique()) for df in rag.axial_edge_dfs] )
    print "Total pixel edges: {}".format( sum(len(df) for df in rag.axial_edge_dfs ) )

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
