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
    seed_labels = label_with_background(binary_seeds)

    # Invert image for the watershed
    # (Must add img_max here because StopAtThreshold method can't handle negative values.)
    logger.debug("Inverting image")
    img_max = img.max()
    inverted_img = -img + img_max
    inverted_low_threshold = -1*img.dtype.type(low_threshold) + img_max

    # The 'low threshold' is actually a watersehd operation.    
    logger.debug("First watershed")
    
    # Make sure arrays have matching axes
    inverted_img = inverted_img.withAxes(list(seed_labels.axistags.keys()))
    if out is not None:
        out = out.withAxes(list(seed_labels.axistags.keys()))
    
    watershed_labels, max_label = vigra.analysis.watershedsNew( inverted_img,
                                                                seeds=seed_labels,
                                                                terminate=vigra.analysis.SRGType.StopAtThreshold,
                                                                max_cost=inverted_low_threshold,
                                                                out=out )

    # Toss out the tiny objects
    logger.debug("Filtering labels")
    filter_labels(watershed_labels, min_size, max_size)
    
    if watershed_labels.max() == 0:
        # Everything got filtered out.
        return watershed_labels
      
    # Run watershed a second time to make sure the larger labels
    #  eat up the tiny stuff we removed, if it was adjacent.
    logger.debug("Second watershed")
    vigra.analysis.watershedsNew( inverted_img,
                                  seeds=watershed_labels,
                                  terminate=vigra.analysis.SRGType.StopAtThreshold,
                                  max_cost=inverted_low_threshold,
                                  out=watershed_labels )
    logger.debug("Complete")
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
