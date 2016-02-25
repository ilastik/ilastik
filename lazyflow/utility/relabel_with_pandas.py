import numpy as np

def relabel_with_pandas(labels, mapping, out=None):
    """
    Deprecated!  This function isn't as fast as I thought it was.
                 Use vigra.analysis.applyMapping() instead!
    
    Map all the elements of `labels` to new values, based on a mapping dict.
    To relabel in-place, set `out=labels`.
    Requires the 'pandas' python library.

    Parameters
    ----------
    labels: ndarray
    mapping: dict of `{old_label : new_label}`
             Array values not present in `mapping`
             will be not be changed.
    out: ndarray to hold the data. If None, it will be allocated for you.
         The dtype of `out` is allowed to be smaller (or bigger) than the dtype of
         `labels`, but not of a different type.
         For example, you can map from uint64 to uint32, but not from uint64 to float32.
    """
    if out is not None:
        assert out.shape == labels.shape, \
            "'out' parameter does not match input shape: {} != {}"\
            .format(out.shape, labels.shape)

        assert labels.dtype.kind == out.dtype.kind, \
            "input/output dtypes are not compatible: Can't map floats to ints, signed to unsigned or vice-versa"

    if out is None:
        out = np.empty_like(labels, order='A') # allocate

    # If possible, take the fast path: copy labels to 'out' and relabel in-place.
    # Requires contiguous output array and large enough dtype to handle both sides of the mapping. 
    if out.flags.contiguous and out.dtype.itemsize >= labels.dtype.itemsize:
        if labels is not out:
            out[:] = labels # copy
        _relabel_inplace(out, mapping)
    else:
        # Slower path: Must work with an intermediate series, and copy it into the final result
        if labels.dtype.itemsize < out.dtype.itemsize:
            copy_dtype = out.dtype
        else:
            copy_dtype = labels.dtype
        copied_labels = np.array( labels, dtype=copy_dtype, copy=True, order='A' ) # allocate + copy
        _relabel_inplace(copied_labels, mapping)
        out[:] = copied_labels.reshape( out.shape ) # copy
    return out

def _relabel_inplace(labels, mapping):
    """
    Relabel the given *contiguous* array in-place according to the given mapping dict.

    FIXME: Ugh. This function doesn't really do its work in-place.
           Need a better implementation.
    
    For an input uint32 array with N pixels, this function will need 8*N bytes for the
    'index' column and 4*N bytes for the intermediate result.
    That is, twice the size of the input.
    """
    # Late import
    # For now, pandas is not an official dependency of lazyflow
    import pandas as pd

    assert labels.flags.contiguous
    flat_view = labels.reshape(-1, order='A')
    assert flat_view.flags.owndata is False

    original_series = pd.Series(flat_view)
    new_series = original_series.map(mapping)
    flat_view[:] = new_series.values
    return

    df_labels = pd.DataFrame({'labels':flat_view}, index=index_u32)
    df_mapping = pd.DataFrame(mapping.items(), columns=['labels', 'newlabels'])
    df_newlabels = df_labels.merge(df_mapping, how='left', on='labels', copy=False)
    flat_view[:] = df_newlabels['newlabels'].values

if __name__ == "__main__":
    import sys
    import logging
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)

    from ilastik.applets.edgeTraining.util import label_vol_mapping
    
    import h5py
    watershed_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/256/watershed-256.h5'
    #watershed_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/512/watershed-512.h5'

    logger.info("Loading watershed...")
    with h5py.File(watershed_path, 'r') as f:
        watershed = f['watershed'][:]
        if watershed.shape[-1] == 1:
            watershed = watershed[...,0]
    
    groundtruth_path = '/magnetic/data/flyem/chris-two-stage-ilps/volumes/subvol/256/segmentation-256.h5'

    logger.info("Loading groundtruth...")
    with h5py.File(groundtruth_path, 'r') as f:
        groundtruth = f['segmentation'][:]
        if groundtruth.shape[-1] == 1:
            groundtruth = groundtruth[...,0]

    index_mapping = label_vol_mapping(watershed, groundtruth)
    mapping = dict( enumerate( index_mapping ) )

    #relabeled = relabel_via_vectorize(watershed, mapping)
    relabeled = relabel_with_pandas(watershed, mapping)
    
    print groundtruth[0]
    print relabeled[0]

    assert (relabeled == groundtruth).all()
    print "Done."
