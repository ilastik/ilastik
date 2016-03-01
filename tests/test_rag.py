import os
import tempfile
from collections import OrderedDict
import numpy as np
import vigra
import nose

try:
    import pandas as pd
    _has_pandas = True
except ImportError:
    # For now, pandas is optional, but Rag doesn't work without it.
    _has_pandas = False
else:
    from lazyflow.utility.rag import Rag

class TestRag(object):
    
    @classmethod
    def setupClass(cls):
        if not _has_pandas:
            raise nose.SkipTest
    
    def generate_superpixels(self, shape, num_sp):
        """
        Generate a superpixel image for testing.
        A set of N seed points (N=num_sp) will be chosen randomly, and the superpixels
        will simply be a voronoi diagram for those seeds.
        Note: The first superpixel ID is 1.
        """
        seed_coords = []
        for dim in shape:
            # Generate more than we need, so we can toss duplicates
            seed_coords.append( np.random.randint( dim, size=(2*num_sp,) ) )

        seed_coords = np.transpose(seed_coords)
        seed_coords = list(set(map(tuple, seed_coords)))
        seed_coords = seed_coords[:num_sp]
        seed_coords = tuple(np.transpose(seed_coords))

        superpixels = np.zeros( shape, dtype=np.uint32 )
        superpixels[seed_coords] = np.arange( num_sp )+1
        
        vigra.analysis.watersheds( np.zeros(shape, dtype=np.float32),
                                   seeds=superpixels,
                                   out=superpixels )
        superpixels = vigra.taggedView(superpixels, 'zyx'[3-len(shape):])        
        return superpixels

    def test_construction(self):
        superpixels = self.generate_superpixels((100,200), 200)
        
        rag = Rag( superpixels )
        assert rag.num_sp == 200, "num_sp was: {}".format(rag.num_sp)
        assert rag.max_sp == 200
        assert (rag.sp_ids == np.arange(1,201)).all()

        # Just check some basic invariants of the edge_ids
        assert rag.edge_ids.shape == (rag.num_edges, 2)

        # For all edges (u,v): u < v
        edge_ids_copy = rag.edge_ids.copy()
        edge_ids_copy.sort(axis=1)
        assert (rag.edge_ids == edge_ids_copy).all()

        # edge_ids should be sorted by u, then v.
        edge_df = pd.DataFrame(edge_ids_copy, columns=['sp1', 'sp2'])
        edge_df.sort(columns=['sp1', 'sp2'], inplace=True)
        assert (rag.edge_ids == edge_df.values).all()

    def test_sp_features(self):
        superpixels = self.generate_superpixels((100,200), 200)
        rag = Rag( superpixels )

        # For simplicity, just make values identical to superpixels
        values = superpixels.astype(np.float32)

        # Manually compute the sp counts
        sp_counts = np.bincount(superpixels.flat[:])

        # COUNT
        features_df = rag.compute_highlevel_features(values, ['sp_count'])
        assert len(features_df) == len(rag.edge_ids)
        assert (features_df.columns.values == ['sp1', 'sp2', 'sp_count_sum', 'sp_count_difference']).all()
        assert (features_df[['sp1', 'sp2']].values == rag.edge_ids).all()

        # sp count features are normalized, consistent with the multicut paper.
        for index, sp1, sp2, sp_count_sum, sp_count_difference in features_df.itertuples():
            assert sp_count_sum == np.power(sp_counts[sp1] + sp_counts[sp2], 1./superpixels.ndim)
            assert sp_count_difference == np.power(np.abs(sp_counts[sp1] - sp_counts[sp2]), 1./superpixels.ndim)

        # SUM
        features_df = rag.compute_highlevel_features(values, ['sp_sum'])
        assert len(features_df) == len(rag.edge_ids)
        assert (features_df.columns.values == ['sp1', 'sp2', 'sp_sum_sum', 'sp_sum_difference']).all()
        assert (features_df[['sp1', 'sp2']].values == rag.edge_ids).all()

        # sp sum features ought to be normalized, too...
        for index, sp1, sp2, sp_sum_sum, sp_sum_difference in features_df.itertuples():
            assert sp_sum_sum == np.power(sp1*sp_counts[sp1] + sp2*sp_counts[sp2], 1./superpixels.ndim)
            assert sp_sum_difference == np.power(np.abs(sp1*sp_counts[sp1] - sp2*sp_counts[sp2]), 1./superpixels.ndim)

        # MEAN
        features_df = rag.compute_highlevel_features(values, ['sp_mean'])
        assert len(features_df) == len(rag.edge_ids)
        assert (features_df.columns.values == ['sp1', 'sp2', 'sp_mean_sum', 'sp_mean_difference']).all()
        assert (features_df[['sp1', 'sp2']].values == rag.edge_ids).all()

        # No normalization for other features...
        # Should there be?
        for index, sp1, sp2, sp_mean_sum, sp_mean_difference in features_df.itertuples():
            assert sp_mean_sum == sp1 + sp2
            assert sp_mean_difference == np.abs(np.float32(sp1) - sp2)

    def test_edge_features(self):
        superpixels = self.generate_superpixels((100,200), 200)
        rag = Rag( superpixels )

        # For simplicity, just make values identical to superpixels
        values = superpixels.astype(np.float32)

        feature_names = ['edge_mean', 'edge_minimum', 'edge_maximum', 'edge_variance',
                         'edge_quantiles_25', 'edge_quantiles_50', 'edge_quantiles_75',
                         'edge_count', 'edge_sum']

        features_df = rag.compute_highlevel_features(values, feature_names)
        assert len(features_df) == len(rag.edge_ids)
        assert list(features_df.columns.values) == ['sp1', 'sp2'] + list(feature_names), \
            "Wrong output feature names: {}".format( features_df.columns.values )

        assert (features_df[['sp1', 'sp2']].values == rag.edge_ids).all()

        for row_tuple in features_df.itertuples():
            row = OrderedDict( zip(['index', 'sp1', 'sp2'] + list(feature_names),
                                   row_tuple) )
            sp1 = row['sp1']
            sp2 = row['sp2']
            # Values were identical to the superpixels, so this is boring...
            assert np.isclose(row['edge_mean'],  (sp1+sp2)/2.)
            assert np.isclose(row['edge_minimum'], (sp1+sp2)/2.)
            assert np.isclose(row['edge_maximum'], (sp1+sp2)/2.)
            assert np.isclose(row['edge_variance'], 0.0)
            assert np.isclose(row['edge_quantiles_25'], (sp1+sp2)/2.)
            assert np.isclose(row['edge_quantiles_75'], (sp1+sp2)/2.)
            assert row['edge_count'] > 0
            assert np.isclose(row['edge_sum'], row['edge_count'] * (sp1+sp2)/2.)

    def test_edge_decisions_from_groundtruth(self):
        # 1 2
        # 3 4
        vol1 = np.zeros((20,20), dtype=np.uint8)
        vol1[ 0:10,  0:10] = 1
        vol1[ 0:10, 10:20] = 2
        vol1[10:20,  0:10] = 3
        vol1[10:20, 10:20] = 4
        
        vol1 = vigra.taggedView(vol1, 'yx')
        rag = Rag(vol1)
    
        # 2 3
        # 4 5
        vol2 = vol1.copy() + 1

        decisions = rag.edge_decisions_from_groundtruth(vol2)
        assert decisions.all()

        # 7 7
        # 4 5
        vol2[( vol2 == 2 ).nonzero()] = 7
        vol2[( vol2 == 3 ).nonzero()] = 7
        
        decision_dict = rag.edge_decisions_from_groundtruth(vol2, asdict=True)
        assert decision_dict[(1,2)] == False
        assert decision_dict[(1,3)] == True
        assert decision_dict[(2,4)] == True
        assert decision_dict[(3,4)] == True

    def test_naive_segmentation_from_edge_decisions(self):
        superpixels = self.generate_superpixels((100,200), 200)
        rag = Rag( superpixels )
        
        # The 'groundtruth' is just divided into quadrants
        groundtruth = np.zeros_like(superpixels)
        groundtruth[0:50,   0:100] = 1
        groundtruth[50:100, 0:100] = 2
        groundtruth[0:50,   100:200] = 3
        groundtruth[50:100, 100:200] = 4

        decisions = rag.edge_decisions_from_groundtruth(groundtruth)
        segmentation = rag.naive_segmentation_from_edge_decisions(decisions)
        
        # We don't know where the exact boundary is, but pixels 
        # near the corners should definitely be homogenous
        assert (segmentation[:20,   :20] == segmentation[0,  0]).all()
        assert (segmentation[:20,  -20:] == segmentation[0, -1]).all()
        assert (segmentation[-20:,  :20] == segmentation[-1, 0]).all()
        assert (segmentation[-20:, -20:] == segmentation[-1,-1]).all()

    def test_serialization_with_labels(self):
        """
        Serialize the rag and labels to hdf5,
        then deserialize it and make sure nothing was lost.
        """
        import h5py

        superpixels = self.generate_superpixels((100,200), 200)
        original_rag = Rag( superpixels )

        tmp_dir = tempfile.mkdtemp()
        filepath = os.path.join(tmp_dir, 'test_rag.h5')
        rag_groupname = 'saved_rag'

        # Serialize with labels       
        with h5py.File(filepath, 'w') as f:
            rag_group = f.create_group(rag_groupname)
            original_rag.serialize_hdf5(rag_group, store_labels=True)

        # Deserialize
        with h5py.File(filepath, 'r') as f:
            rag_group = f[rag_groupname]
            deserialized_rag = Rag.deserialize_hdf5(rag_group)

        assert deserialized_rag.label_img.dtype == original_rag.label_img.dtype
        assert deserialized_rag.label_img.shape == original_rag.label_img.shape
        assert deserialized_rag.label_img.axistags == original_rag.label_img.axistags
        assert (deserialized_rag.label_img == original_rag.label_img).all()        

        assert (deserialized_rag.sp_ids == original_rag.sp_ids).all()
        assert deserialized_rag.max_sp == original_rag.max_sp
        assert deserialized_rag.num_sp == original_rag.num_sp
        assert deserialized_rag.num_edges == original_rag.num_edges
        assert (deserialized_rag.edge_ids == original_rag.edge_ids).all()

        # Check some features
        # For simplicity, just make values identical to superpixels
        values = superpixels.astype(np.float32)
        feature_names = ['edge_mean', 'sp_count']
        features_df_original = original_rag.compute_highlevel_features(values, feature_names)
        features_df_deserialized = deserialized_rag.compute_highlevel_features(values, feature_names)
        assert (features_df_original.values == features_df_deserialized.values).all()

    def test_serialization_without_labels(self):
        """
        Users can opt to serialize the Rag without serializing the labels,
        but then they can't use superpixel features on the deserialized Rag.
        """
        import h5py

        superpixels = self.generate_superpixels((100,200), 200)
        original_rag = Rag( superpixels )

        tmp_dir = tempfile.mkdtemp()
        filepath = os.path.join(tmp_dir, 'test_rag.h5')
        rag_groupname = 'saved_rag'

        # Serialize with labels       
        with h5py.File(filepath, 'w') as f:
            rag_group = f.create_group(rag_groupname)
            original_rag.serialize_hdf5(rag_group, store_labels=False) # Don't store

        # Deserialize
        with h5py.File(filepath, 'r') as f:
            rag_group = f[rag_groupname]
            deserialized_rag = Rag.deserialize_hdf5(rag_group)

        assert deserialized_rag.label_img.dtype == original_rag.label_img.dtype
        assert deserialized_rag.label_img.shape == original_rag.label_img.shape
        assert deserialized_rag.label_img.axistags == original_rag.label_img.axistags
        #assert (deserialized_rag.label_img == original_rag.label_img).all() # not stored

        assert (deserialized_rag.sp_ids == original_rag.sp_ids).all()
        assert deserialized_rag.max_sp == original_rag.max_sp
        assert deserialized_rag.num_sp == original_rag.num_sp
        assert deserialized_rag.num_edges == original_rag.num_edges
        assert (deserialized_rag.edge_ids == original_rag.edge_ids).all()

        # Check some features
        # For simplicity, just make values identical to superpixels
        values = superpixels.astype(np.float32)
        feature_names = ['edge_mean', 'edge_count']
        features_df_original = original_rag.compute_highlevel_features(values, feature_names)
        features_df_deserialized = deserialized_rag.compute_highlevel_features(values, feature_names)
        assert (features_df_original.values == features_df_deserialized.values).all()

        try:
            deserialized_rag.compute_highlevel_features(values, ['sp_count'])
        except NotImplementedError:
            pass
        else:
            assert False, "Shouldn't be able to use superpixels if labels weren't serialized/deserialized!"

    def test_serialization_with_external_labels(self):
        """
        Users can opt to serialize the Rag without serializing the labels,
        but then they can't use superpixel features on the deserialized Rag.
        
        When deserializing, they can provide the labels from an external source,
        as tested here.
        """
        import h5py

        superpixels = self.generate_superpixels((100,200), 200)
        original_rag = Rag( superpixels )

        tmp_dir = tempfile.mkdtemp()
        filepath = os.path.join(tmp_dir, 'test_rag.h5')
        rag_groupname = 'saved_rag'

        # Serialize with labels       
        with h5py.File(filepath, 'w') as f:
            rag_group = f.create_group(rag_groupname)
            original_rag.serialize_hdf5(rag_group, store_labels=False)

        # Deserialize
        with h5py.File(filepath, 'r') as f:
            rag_group = f[rag_groupname]
            deserialized_rag = Rag.deserialize_hdf5(rag_group, label_img=superpixels) # Provide labels explicitly

        assert deserialized_rag.label_img.dtype == original_rag.label_img.dtype
        assert deserialized_rag.label_img.shape == original_rag.label_img.shape
        assert deserialized_rag.label_img.axistags == original_rag.label_img.axistags
        assert (deserialized_rag.label_img == original_rag.label_img).all()

        assert (deserialized_rag.sp_ids == original_rag.sp_ids).all()
        assert deserialized_rag.max_sp == original_rag.max_sp
        assert deserialized_rag.num_sp == original_rag.num_sp
        assert deserialized_rag.num_edges == original_rag.num_edges
        assert (deserialized_rag.edge_ids == original_rag.edge_ids).all()

        # Check some features
        # For simplicity, just make values identical to superpixels
        values = superpixels.astype(np.float32)
        feature_names = ['edge_mean', 'sp_count']
        features_df_original = original_rag.compute_highlevel_features(values, feature_names)
        features_df_deserialized = deserialized_rag.compute_highlevel_features(values, feature_names)
        assert (features_df_original.values == features_df_deserialized.values).all()

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
