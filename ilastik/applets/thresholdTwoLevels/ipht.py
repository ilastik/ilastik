import numpy
import vigra
import logging
logger = logging.getLogger(__name__)

from lazyflow.utility import vigra_bincount

def identity_preserving_hysteresis_thresholding( img,
                                                 high_threshold, low_threshold,
                                                 min_size, max_size=None, out=None ):
    """
    Threshold the given image at two levels (hysteresis thresholding), 
    but don't allow two 'high' thresholded regions bleed into each other 
    when the low threshold is applied. A labeled image is returned, and 
    no connected component will be too small or too large according to 
    the given min/max sizes.
    
    Ideas for improvement: Allow separate images for the high and low thresholding steps.
    """
    logger.debug("Computing high threshold")
    binary_seeds = (img >= high_threshold).view(numpy.uint8) # bool is 8-bit in numpy

    logger.debug("Labeling")
    core_labels = label_with_background(binary_seeds)

    # Toss out the tiny objects
    logger.debug("Filtering core labels")
    filter_labels(core_labels, min_size, max_size)
    if core_labels.max() == 0:
        # Everything got filtered out.
        return 

    watershed_labels = threshold_from_cores(img, core_labels, low_threshold, out)
    return watershed_labels


def threshold_from_cores(img, core_labels, final_threshold, out=None):
    """
    Given a grayscale image and a label image of object 'cores', use core_labels
    as the seeds for a (upside-down) watershed operation.  The watershed will be restricted to
    those pixels within the bounds defined by the given final_threshold value.
    
    img:
        The single-channel input data.  (It will be inverted before the watershed is performed.)
    
    core_labels:
        A label image indicating high-valued pixel regions from which to seed the watershed.
    
    low_threshold:
        The watershed will proceed until reaching this threshold value.
    
    out:
        (Optional.) Where to write the results, a label image filling the around
        core_labels that are greater than final_threshold.
    """
    assert hasattr(img, 'axistags')

    # Invert image for the watershed
    # (Must add img_max here because StopAtThreshold method can't handle negative values.)
    logger.debug("Inverting image")
    img_max = img.max()
    inverted_img = -img + img_max
    inverted_threshold = -1*img.dtype.type(final_threshold) + img_max

    # Make sure arrays have matching axes
    inverted_img = inverted_img.withAxes(core_labels.axistags.keys())
    if out is not None:
        out = out.withAxes(core_labels.axistags.keys())
    
    # The 'low threshold' is actually a watershed operation.    
    watershed_labels, max_label = vigra.analysis.watershedsNew( inverted_img,
                                                                seeds=core_labels,
                                                                terminate=vigra.analysis.SRGType.StopAtThreshold,
                                                                max_cost=inverted_threshold,
                                                                out=out )
    return watershed_labels
    

def label_with_background(img):
    img = img.squeeze()
    if img.ndim == 2:
        return vigra.analysis.labelImageWithBackground(img)
    if img.ndim == 3:
        return vigra.analysis.labelVolumeWithBackground(img)
    assert False

def filter_labels(a, min_size, max_size=None):
    """
    Remove (set to 0) labeled connected components that are too small or too large.
    Note: Operates in-place.
    """
    if min_size == 0 and (max_size is None or max_size > numpy.prod(a.shape)): # shortcut for efficiency
        return a

    component_sizes = vigra_bincount(a)
    bad_sizes = component_sizes < min_size
    if max_size is not None:
        numpy.logical_or( bad_sizes, component_sizes > max_size, out=bad_sizes )
    
    bad_locations = bad_sizes[a]
    a[bad_locations] = 0
    return a
