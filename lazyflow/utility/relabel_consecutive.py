import pandas as pd
import vigra

def relabel_consecutive(label_img, start_label=0, out=None):
    """
    Relabel the given label_img to have consectuive label values.
    start_label: The lowest label value in the returned array.
    """
    # pandas.Series.unique() is 2x faster than numpy.unique(), even after manual sort
    unique_labels = pd.Series(label_img.reshape((-1), order='A')).unique()
    unique_labels.sort()

    num_labels = len(unique_labels)
    min_label = unique_labels[0]
    max_label = unique_labels[-1]

    # Are the labels already consecutive?
    if start_label == min_label and max_label == num_labels-1+start_label:
        # No need to remap, just return the original array.
        if out is None:
            return label_img.copy()
        elif out is label_img:
            return label_img
        else:
            out[:] = label_img
            return out
    else:
        # Remap to consecutive labels
        mapping = { old:new for new, old in enumerate(unique_labels, start=start_label) }
        return vigra.analysis.applyMapping(label_img, mapping, out=out)

