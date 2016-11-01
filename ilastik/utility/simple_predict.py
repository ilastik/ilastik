import sys
import json
import logging
import argparse
import collections
from itertools import starmap
from functools import partial, wraps

import numpy as np
import h5py
import vigra

from lazyflow.request import Request, RequestPool

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('grayscale', help='example: my-grayscale.h5/volume')
    parser.add_argument('classifier', help='example: my-file.h5/forest')
    parser.add_argument('filter_specs', help='json file containing filter list')
    parser.add_argument('output_path', help='example: my-predictions.h5/volume')
    parser.add_argument('--compute-blockwise', help='Compute blockwise instead of as a whole', action='store_true')
    parser.add_argument('--thread-count', help='The threadpool size', default=0, type=int)
    args = parser.parse_args()

    # Show log messages on the console.
    logger.setLevel(logging.INFO)
    logger.addHandler( logging.StreamHandler(sys.stdout) )

    Request.reset_thread_pool(args.thread_count)
    
    load_and_predict( args.grayscale, args.classifier, args.filter_specs, args.output_path, args.compute_blockwise )
    logger.info("DONE.")

def load_and_predict( input_data_or_path, classifier_filepath, feature_list_json_path, output_path=None, compute_blockwise=False ):
    assert output_path is None or isinstance( output_path, basestring )

    # Load
    input_data = load_data( input_data_or_path )
    filter_specs = load_filter_specs( feature_list_json_path )
    rf = load_classifier( classifier_filepath )

    # Predict
    if compute_blockwise:
        predictions = blockwise_predict( input_data, rf, filter_specs )
    else:
        predictions = simple_predict( input_data, rf, filter_specs )
    
    # Save
    if output_path:
        save_predictions( predictions, output_path )

    return predictions

def simple_predict( input_grayscale, random_forest, filter_spec_list ):
    assert isinstance(random_forest, vigra.learning.RandomForest)
    assert isinstance( input_grayscale, vigra.VigraArray )
    input_grayscale = input_grayscale.dropChannelAxis()
    
    num_channels = get_filter_channel_ranges(filter_spec_list, input_grayscale.ndim)[-1][1]
    assert num_channels == random_forest.featureCount(), \
        "Mismatch between feature list and RF expected features count.\n" \
        "RF expects {} features, but filter specs will provide {}" \
        .format( random_forest.featureCount(), num_channels )

    # Determine filter output locations
    logger.info( "Computing {} filters ({} channels)" .format( len(filter_spec_list), num_channels ) )

    # Compute features
    feature_volume = compute_features( input_grayscale, filter_spec_list )

    # Predict
    logger.info("Predicting...")
    prediction_volume = predict_from_features( feature_volume, random_forest )
    return prediction_volume

def blockwise_predict( input_grayscale, random_forest, filter_spec_list, block_shape=None ):
    assert isinstance(random_forest, vigra.learning.RandomForest)
    assert isinstance( input_grayscale, vigra.VigraArray )
    input_grayscale = input_grayscale.dropChannelAxis()
    
    num_channels = get_filter_channel_ranges(filter_spec_list, input_grayscale.ndim)[-1][1]
    assert num_channels == random_forest.featureCount(), \
        "Mismatch between feature list and RF expected features count.\n" \
        "RF expects {} features, but filter specs will provide {}" \
        .format( random_forest.featureCount(), num_channels )

    # Determine filter output locations
    logger.info( "Computing {} filters ({} channels)" .format( len(filter_spec_list), num_channels ) )
    
    if block_shape is None:
        # Arbitrary: Choose input_shape / 4
        block_shape = np.array(input_grayscale.shape) // 4
    else:
        block_shape = np.array( block_shape )

    num_classes = random_forest.labelCount()
    prediction_volume = np.ndarray( shape=input_grayscale.shape + (num_classes,), dtype=np.float32)

    # How many blocks in each dimension?
    # This is the input shape, measured in units of blocks (rounded up)
    nd_block_counts = (input_grayscale.shape + np.array(block_shape)-1) // block_shape

    # Iterate over blocks
    for i, block_ndindex in enumerate( np.ndindex( *nd_block_counts ) ):
        block_ndindex = np.array(block_ndindex)
        block_roi = np.array([ block_shape*block_ndindex,
                               block_shape*(block_ndindex+1) ])

        # Clip to image boundaries
        block_roi[0] = np.maximum( block_roi[0], (0,)*input_grayscale.ndim )
        block_roi[1] = np.minimum( block_roi[1], input_grayscale.shape )

        logger.info("Computing Features for block {}: {}".format( i, block_roi.tolist() ))
        block_feature_volume = compute_features(input_grayscale, filter_spec_list, roi=block_roi)

        logger.info("Computing Predictions for block {}: {}".format( i, block_roi.tolist() ))
        prediction_volume[bb_to_slicing(*block_roi)] = predict_from_features( block_feature_volume, random_forest )
    
    return prediction_volume

def bb_to_slicing(start, stop):
    """
    For the given bounding box (start, stop),
    return the corresponding slicing tuple.

    Example:
    
        >>> assert bb_to_slicing([1,2,3], [4,5,6]) == np.s_[1:4, 2:5, 3:6]
    """
    return tuple( starmap( slice, zip(start, stop) ) )

# In vigra, 0.0 means 'automatically determined' (Toufiq uses 0.0)
# In ilastik, we use 2.0 for all filters (except the pre-smoothing step)
WINDOW_SIZE = 0.0

def define_filter(is_vector_valued=False):
    def decorator( filter_func ):
        """
        Decorator for filter functions.
        Performs basic checks on the inputs (for shape, dtype, etc.).

        Also, convert the roi to an np.array.

        Lastly, attach an attribute to the function object 'is_vector_valued',
        for clients to read if they want.
        """
        @wraps(filter_func)
        def wrapper(input_data, scale, out, roi):
            # Check input data format
            assert input_data.dtype == np.float32
            assert hasattr(input_data, 'axistags'), "Input must have axistags"
            assert 't' not in input_data.axistags, "Time axis not allowed in input_data"
            if 'c' in input_data.axistags:
                assert input_data.shape[input_data.channelIndex] == 1, \
                    "Multi-channel data not supported.  Drop channel axis before calling this function."

            # check roi
            assert len(roi) == 2
            roi = np.array(roi)

            # Check output data format            
            assert 't' not in out.axistags, "Time axis not allowed in output array"
            assert out.dtype == np.float32
            assert hasattr(out, 'axistags'), "Output must have axistags"

            if is_vector_valued:
                assert 'c' in out.axistags, "Output array for this vector-valued filter has no channel dimensions"
                assert out.ndim == roi.shape[1]+1
                assert out.shape[:-1] == tuple(roi[1] - roi[0])
                num_output_channels = out.shape[out.axistags.index('c')]
                spatial_dims = input_data.axistags.axisTypeCount(vigra.AxisType.Space)
                assert num_output_channels == spatial_dims, \
                    "Output array has the wrong number of channels.  It has {}, expected {}." \
                    .format(num_output_channels, spatial_dims)
            elif 'c' in out.axistags:
                assert out.channelIndex == out.ndim-1, "Channel must be last axis."
                assert out.shape[out.channelIndex] == 1, \
                    "Output array has the wrong number of channels.  Should have exactly 1 channel."
                assert out.ndim == roi.shape[1]+1
                assert out.shape[:-1] == tuple(roi[1] - roi[0])
            else:
                assert out.ndim == roi.shape[1]
                assert out.shape == tuple(roi[1] - roi[0])
            
            # Call the filter
            ret = filter_func( input_data, scale, out, roi )
            assert ret is None, "Filter should work in-place, not return a value"
    
        wrapper.__wrapped__ = filter_func # Emulate python 3 behavior of @functools.wraps
        wrapper.is_vector_valued = is_vector_valued # Tag the function with this bool.
        return wrapper
    return decorator

@define_filter()
def gaussian_smoothing(input_data, scale, out, roi):
    vigra.filters.gaussianSmoothing(input_data, sigma=scale, out=out, window_size=WINDOW_SIZE, roi=roi)

@define_filter()
def laplacian_of_gaussian(input_data, scale, out, roi):
    vigra.filters.laplacianOfGaussian(input_data, scale=scale, out=out, window_size=WINDOW_SIZE, roi=roi)

@define_filter()
def gaussian_gradient_magnitude(input_data, scale, out, roi):
    vigra.filters.gaussianGradientMagnitude(input_data, sigma=scale, out=out, window_size=WINDOW_SIZE, roi=roi)

@define_filter()
def difference_of_gaussians(input_data, scale, out, roi):
    sigma_1 = scale
    sigma_2 = 0.66*scale

    # Save RAM: Use the 'out' array as a temporary variable for smoothed_1.
    smoothed_1 = out
    smoothed_2 = np.empty_like( out )

    vigra.filters.gaussianSmoothing(input_data, sigma=sigma_1, out=smoothed_1, window_size=WINDOW_SIZE, roi=roi)
    vigra.filters.gaussianSmoothing(input_data, sigma=sigma_2, out=smoothed_2, window_size=WINDOW_SIZE, roi=roi)
    
    # In-place subtraction ('smoothed_1' is same as 'out')
    np.subtract( smoothed_1, smoothed_2, out=out )

@define_filter(is_vector_valued=True)
def structure_tensor_eigenvalues(input_data, scale, out, roi):
    inner_scale = scale
    outer_scale = scale / 2.0

    # FIXME: vigra seems to have a problem with non-contiguous arrays (in the channel dimension)
    #        For now, we must provide a our own output array, which is always contiguous.
    tempout = np.empty_like( out )
    vigra.filters.structureTensorEigenvalues(input_data, innerScale=inner_scale, outerScale=outer_scale, out=tempout, window_size=WINDOW_SIZE, roi=roi)
    out[:] = tempout

@define_filter(is_vector_valued=True)
def hessian_of_gaussian_eigenvalues(input_data, scale, out, roi):
    # FIXME: vigra seems to have a problem with non-contiguous arrays (in the channel dimension)
    #        For now, we must provide a our own output array, which is always contiguous.
    tempout = np.empty_like( out )
    vigra.filters.hessianOfGaussianEigenvalues(input_data, scale=scale, out=tempout, window_size=WINDOW_SIZE, roi=roi)
    out[:] = tempout


FilterFunctions = { 'GaussianSmoothing'            : gaussian_smoothing,
                    'LaplacianOfGaussian'          : laplacian_of_gaussian,
                    'GaussianGradientMagnitude'    : gaussian_gradient_magnitude,
                    'DifferenceOfGaussians'        : difference_of_gaussians,
                    'StructureTensorEigenvalues'   : structure_tensor_eigenvalues,
                    'HessianOfGaussianEigenvalues' : hessian_of_gaussian_eigenvalues }

FilterSpec = collections.namedtuple( 'FilterSpec', 'name scale' )



def compute_features( input_grayscale, filter_spec_list, out=None, roi=None ):
    """
    Given a grayscale volume and a list of FilterSpecs, compute the filters and store them to a single multi-channel array.
    
    input_grayscale:
        A VigraArray, with axistags

    filter_spec_list:
        List of FilterSpec objects (tuples)

    out:
        Optional pre-allocated return value.

    roi:
        Optional (start, stop) tuple indicating which region to process,
        where len(roi[0]) == input_grayscale.ndim
        By default, the whole input volume is processed.
    """
    # Convert args as needed
    assert isinstance( input_grayscale, vigra.VigraArray )
    input_grayscale = input_grayscale.dropChannelAxis()
    if roi is None:
        roi = ( (0,)*input_grayscale.ndim,
                input_grayscale.shape )
    assert len(roi[0]) == len(roi[1]) == input_grayscale.ndim, \
        "roi doesn't match input dimensionality."

    # Determine filter output locations
    filter_channel_ranges = get_filter_channel_ranges( filter_spec_list, input_grayscale.ndim )
    total_output_channels = filter_channel_ranges[-1][1]
    
    if out is None:
        # Allocate space for the results
        roi_shape = tuple(np.array(roi[1]) - roi[0])
        output_shape = roi_shape + (total_output_channels,)
        out = np.ndarray( shape=output_shape, dtype=np.float32 )
        out = vigra.taggedView( out, 'zyxc'[-out.ndim:] )
    else:
        assert isinstance( out, vigra.VigraArray )
        assert out.shape[:-1] == roi_shape
        assert out.shape[-1] == output_shape, \
            "output array has the wrong shape. Expected {}, got {}" \
            .format( output_shape, out.shape )

    # Prepare a list of tasks to execute.
    tasks = []
    for (filter_name, scale), (start_channel, stop_channel) in zip(filter_spec_list, filter_channel_ranges):
        filter = FilterFunctions[filter_name]
        filter_out = out[..., start_channel:stop_channel]
        task = partial( filter, input_grayscale, scale, filter_out, roi )
        tasks.append( task )

    # Actually do the work
    execute_tasks(tasks)
    return out

def execute_tasks( tasks ):
    """
    Executes the given list of tasks (functions) in the lazyflow threadpool.
    """
    pool = RequestPool()
    for task in tasks:
        pool.add( Request(task) )
    pool.wait()


def get_filter_channel_ranges( filter_spec_list, ndim ):
    """
    Determine how many channels we need, and in which channels of
    the whole output to store each filter output.
    """
    # For N filters, output_channel_steps will contain N+1 integers,
    # starting with 0 and ending with the total channel count.
    output_channel_steps = [0]
    for (filter_name, scale) in filter_spec_list:
        filter = FilterFunctions[filter_name]
        if filter.is_vector_valued:
            num_output_channels = ndim
        else:
            num_output_channels = 1
        output_channel_steps.append( output_channel_steps[-1] + num_output_channels )

    filter_channel_ranges = zip( output_channel_steps[:-1], output_channel_steps[1:] )
    return filter_channel_ranges
    

def predict_from_features( feature_volume, random_forest ):
    assert isinstance(random_forest, vigra.learning.RandomForest)

    feature_matrix = feature_volume.view( np.ndarray ).reshape( (-1, feature_volume.shape[-1]) )
    
    prediction_matrix = random_forest.predictProbabilities(feature_matrix)

    prediction_volume = prediction_matrix.reshape( feature_volume.shape[:-1] + (prediction_matrix.shape[1],) )
    prediction_volume = vigra.taggedView( prediction_volume, feature_volume.axistags )
    return prediction_volume


def load_data( input_data ):
    """
    Read from .h5 or .npy, drop channel axis (if any), and convert to float32.
    """
    # Load input data
    if isinstance(input_data, basestring):
        logger.info( "Loading {}".format(input_data) )
        input_path = input_data
        if '.h5' in input_path:
            assert not input_path.endswith('.h5'), \
                "Please append the dataset name to the filepath, e.g. my-file.h5/mydata"
            input_path, dataset = input_path.split('.h5')
            input_path += '.h5'
            with h5py.File(input_path, 'r') as f:
                input_data = f[dataset][:]
        elif '.npy' in input_data:
            input_data = np.load(input_data)
        else:
            raise RuntimeError("Unknown input file type: {}".format(input_data))

    assert isinstance(input_data, np.ndarray), "Input data is not an ndarray"

    if input_data.shape[-1] == 1:
        input_data = input_data[...,0]

    # Must be float32
    input_data = np.asarray( input_data, dtype=np.float32 )
    
    axes = 'zyx'[-input_data.ndim:]
    return vigra.taggedView( input_data, axes )

def load_filter_specs( feature_list_json_path ):
    logger.info( "Reading filter specs from {}".format( feature_list_json_path ) )
    # Read filter specs
    with open( feature_list_json_path, 'r' ) as f:
        filter_spec_list = json.load(f)
        assert isinstance( filter_spec_list, list )
        filter_spec_list = list( starmap( FilterSpec, filter_spec_list ) )
    return filter_spec_list

def load_classifier( classifier_filepath ):
    logger.info( "Loading classifier from {}".format( classifier_filepath ) )
    if '.h5' in classifier_filepath:
        ext = '.h5'
    elif '.ilp' in classifier_filepath:
        ext = '.ilp'
    else:
        raise RuntimeError("Classifier file must have .h5 or .ilp extension")
        
    assert not classifier_filepath.endswith(ext), \
        "Please append the classifier group name to the filepath, e.g. my-classifier.h5/forest01"

    classifier_filepath, classifier_groupname = classifier_filepath.split(ext)
    classifier_filepath += ext

    classifier_filepath = str(classifier_filepath)
    classifier_groupname = str(classifier_groupname)

    # Load classifier from hdf5
    rf = vigra.learning.RandomForest(classifier_filepath, classifier_groupname)
    return rf

def save_predictions( predictions, output_path, compression=False ):
    logger.info("Saving predictions to {}".format( output_path ))
    if '.h5' in output_path:
        output_path, dataset = output_path.split('.h5')
        output_path += '.h5'
        with h5py.File(output_path, 'w') as f:
            if compression:
                f.create_dataset(dataset, data=predictions, chunks=True, compression='gzip', compression_opts=4)
            else:
                f.create_dataset(dataset, data=predictions, chunks=True)
                
    elif '.npy' in output_path:
        assert not compression, "Compression not available in .npy format."
        np.save(output_path, predictions)
    else:
        raise RuntimeError("Unknown output file format: {}".format( output_path ))
        

def __debug_setup():
    filter_specs = [ FilterSpec('GaussianSmoothing', 0.3),
                     FilterSpec('GaussianSmoothing', 0.7),
 
                     FilterSpec('LaplacianOfGaussian', 0.7),
                     FilterSpec('LaplacianOfGaussian', 1.6),
                     FilterSpec('LaplacianOfGaussian', 3.5),
  
                     FilterSpec('GaussianGradientMagnitude', 0.7),
                     FilterSpec('GaussianGradientMagnitude', 1.6),
                     FilterSpec('GaussianGradientMagnitude', 3.5),
  
                     FilterSpec('DifferenceOfGaussians', 0.7),
                     FilterSpec('DifferenceOfGaussians', 1.6),
                     FilterSpec('DifferenceOfGaussians', 3.5),
  
                     FilterSpec('StructureTensorEigenvalues', 0.7),
                     FilterSpec('StructureTensorEigenvalues', 1.6),
                     FilterSpec('StructureTensorEigenvalues', 3.5),
    
                     FilterSpec('HessianOfGaussianEigenvalues', 0.7),
                     FilterSpec('HessianOfGaussianEigenvalues', 1.6),
                     FilterSpec('HessianOfGaussianEigenvalues', 3.5), ]

    filter_specs_path = '/tmp/filter-specs.json'
    with open(filter_specs_path, 'w') as f:
        json.dump( filter_specs, f, indent=4, separators=(',', ': ') )

    sys.argv.append( '--compute-blockwise' )
    sys.argv.append( '/magnetic/data/flyem/pb-june2016/teeny-grayscale.h5/grayscale' )
    sys.argv.append( '/magnetic/data/flyem/pb-june2016/pixel_classifier_4class_2.5_1000000_10_800_1000_1.0_1.h5/PixelClassification/ClassifierForests/Forest0000' )
    sys.argv.append( filter_specs_path )
    sys.argv.append( '/tmp/simple-prediction.h5/predictions' )

if __name__ == "__main__":
    #__debug_setup()

    # vigra convolutions produce an annoying FutureWarning about comparing arrays to None
    import warnings
    warnings.simplefilter("ignore", FutureWarning)

    main()
