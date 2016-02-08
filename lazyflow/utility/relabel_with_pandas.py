import numpy as np

def relabel_with_pandas(labels, mapping, out=None):
    """
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
    # Late import
    # For now, pandas is not an official dependency of lazyflow
    import pandas as pd
    
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
        flat_view = out.reshape(-1, order='A')
        assert flat_view.flags.owndata is False
        pd.Series(flat_view).replace(mapping, inplace=True)
    else:
        # Slower path: Must work with an intermediate table, and copy it into the final result
        copy_dtype = labels.dtype
        if labels.dtype.itemsize < out.dtype.itemsize:
            copy_dtype = out.dtype
        copied_labels = np.array( labels, dtype=copy_dtype, copy=True, order='A' ) # allocate + copy
        flat_view = copied_labels.reshape(-1, order='A')
        assert flat_view.flags.owndata is False
        series = pd.Series(flat_view)
        relabeled_series = series.replace(mapping, inplace=True)
        out[:] = copied_labels # copy
    return out
