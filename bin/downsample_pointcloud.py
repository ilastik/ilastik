from __future__ import division
from past.utils import old_div
import sys
import os
import csv

import numpy

from ilastik.utility.commandLineProcessing import ParseListFromString

import logging
logger = logging.getLogger(__name__)

# NOTE: This file depends on numpy.add.at(), which requires numpy v1.8.0

def downsample_pointcloud( pointcloud_csv_filepath, 
                       output_filepath, 
                       scale_xyz=None, 
                       offset_xyz=None, 
                       volume_shape_xyz=None, 
                       method='by_count',
                       smoothing_sigma_xyz=None,
                       normalize_with_max=None,
                       output_dtype=None ):
    """
    Generate an intensity image volume from the given pointcloud 
    file as described in density_volume_from_pointcloud(), below.
    
    Write the resulting volume to either hdf5 or tiff.
    Optionally, perform gaussian smoothing on the downsampled 
    volume before it is saved to disk.
    
    pointcloud_csv_filepath: The input pointcloud csv file.
    output_filepath: The path to store the output image volume.  Either .h5 or .tif
    
    smoothing_sigma_xyz: A float or tuple to use with vigra.filters.gaussianSmoothing, in XYZ order.    
    normalize_with_max: If provided, renormalize the intensities with the given max value
    output_dtype: If provided, convert the image to the given dtype before export
    
    other parameters: See density_volume_from_pointcloud(), below.
    """
    density_volume_zyx = density_volume_from_pointcloud( pointcloud_csv_filepath, 
                                                     scale_xyz,
                                                     offset_xyz, 
                                                     volume_shape_xyz, 
                                                     method )
    
    if smoothing_sigma_xyz:
        logger.debug("Smoothing with sigma: {}".format( smoothing_sigma_xyz ))
        import vigra
        smoothing_sigma_zyx = smoothing_sigma_xyz[::-1]
        density_volume_zyx = numpy.asarray( density_volume_zyx, numpy.float32 )
        density_volume_zyx = vigra.taggedView(density_volume_zyx, 'zyx')
        vigra.filters.gaussianSmoothing( density_volume_zyx, 
                                         smoothing_sigma_zyx,
                                         out=density_volume_zyx )

    if normalize_with_max:
        logger.debug("Normalizing with max: {}".format( normalize_with_max ))
        max_px = density_volume_zyx.max()
        if max_px > 0:
            density_volume_zyx[:] *= old_div(normalize_with_max, max_px)
    
    if output_dtype:
        logger.debug("Converting to dtype: {}".format( str(output_dtype().dtype) ))
        density_volume_zyx = numpy.asarray( density_volume_zyx, dtype=output_dtype )        

    # Now write the volume to the output file
    output_ext = os.path.splitext(output_filepath)[1]
    if output_ext == '.h5':
        export_hdf5( density_volume_zyx, output_filepath, 'downsampled_density' )
    elif output_ext == '.tif' or output_ext == '.tiff':
        export_tiff( density_volume_zyx, output_filepath )
    logger.debug("FINISHED downsampling pointcloud.")


def density_volume_from_pointcloud( pointcloud_csv_filepath, 
                                    scale_xyz=None, 
                                    offset_xyz=None,
                                    volume_shape_xyz=None,
                                    method='by_count' ): 
    """
    Read the given pointcloud file and generate a downsampled intensity volume 
    according to how many points fall within each downsampled pixel.
    
    Optionally, also weight the intensity of each downsampled pixel according to the size of each point.
    
    NOTE: This function depends on numpy.add.at(), which requires numpy v1.8.0
    
    pointcloud_csv_filepath: The input pointcloud file.  Must include
    scale_xyz: (optional) The downsampling factor, specified as a tuple in XYZ order, e.g. (10,10,1).
                If not provided, (1,1,1) is assumed.
    offset_xyz: (optional) Will be subtracted from all coordinates before downsampling.
                If not provided, the output will be shifted according to the bounding box of the pointcloud data.
    volume_shape_xyz: (optional) Sets the size of the output volume.
                If not provided, the output shape will be set according to the bounding box of the pointcloud data.
    method: One of the following:
               - 'binary': Produce a binary image.  No scaling for downsampled voxels containing more than one detection.
               - 'by_count': Each downsampled voxel represents the count of points contained within it.
               - 'by_size': Weight the intensity of each downsampled voxel according to the size of each point (via the size_px column).    
    """
    # Load csv data
    pointcloud_data = array_from_csv( pointcloud_csv_filepath, 
                                      DEFAULT_CSV_FORMAT, 
                                      numpy.uint32 )

    POINTCLOUD_COLUMNS = ["x_px", "y_px", "z_px",
                          "size_px", 
                          "min_x_px", "min_y_px", "min_z_px", 
                          "max_x_px", "max_y_px", "max_z_px"]

    expected_columns = set(POINTCLOUD_COLUMNS)
    data_columns = set(pointcloud_data.dtype.fields.keys())
    assert expected_columns.issubset( data_columns ), \
        "Your pointcloud data file does not contain all expected columns.\n"\
        "Expected columns: {},\n"\
        "Your file's columns: {}"\
        .format( POINTCLOUD_COLUMNS, list(pointcloud_data.dtype.fields.keys()) )

    # Determine offset if not provided.
    if not offset_xyz:
        offset_xyz = ( pointcloud_data['x_px'].min(),
                       pointcloud_data['y_px'].min(),
                       pointcloud_data['z_px'].min() )

    # Apply offset
    logger.debug("Subtracting offset: {}".format( offset_xyz ))
    for axis, axis_offset in zip('xyz', offset_xyz):
        fields = [ '{}_px'.format(axis),
                   'min_{}_px'.format(axis), 
                   'max_{}_px'.format(axis) ]
        for field in fields:
            pointcloud_data[field] -= axis_offset

    # Determine volume shape if not provided.
    if not volume_shape_xyz:
        volume_shape_xyz = ( pointcloud_data['x_px'].max(),
                             pointcloud_data['y_px'].max(),
                             pointcloud_data['z_px'].max() )
        volume_shape_xyz = 1 + numpy.array(volume_shape_xyz)
        volume_shape_xyz = tuple(volume_shape_xyz)

    logger.debug("Assuming original volume shape: {}".format(volume_shape_xyz))

    # Apply scale
    if not scale_xyz:
        logger.debug("No scale provided. Rendering at full scale.")
        scaled_volume_shape_xyz = volume_shape_xyz
    else:
        logger.debug("Dividing by scale: {}".format( scale_xyz ))
        scaled_volume_shape_xyz = old_div((numpy.array(volume_shape_xyz) + scale_xyz-1), scale_xyz)
        
        # Scale coordinates, too.
        for axis, axis_scale in zip('xyz', scale_xyz):
            fields = [ '{}_px'.format(axis),
                       'min_{}_px'.format(axis), 
                       'max_{}_px'.format(axis) ]
            for field in fields:
                pointcloud_data[field] /= axis_scale

    # All coords
    coordinates_zyx = ( pointcloud_data['z_px'],
                        pointcloud_data['y_px'],
                        pointcloud_data['x_px'] )

    if method == 'binary':
        scaled_volume_shape_zyx = tuple(scaled_volume_shape_xyz[::-1])
        logger.debug("Initializing binary volume of zyx shape: {}".format( scaled_volume_shape_zyx ))
        density_volume_zyx = numpy.zeros( scaled_volume_shape_zyx, dtype=numpy.uint8 )
        density_volume_zyx[coordinates_zyx] = 1
    else:
        # Prepare weights
        if method == 'by_size':
            weights = pointcloud_data['size_px']
        elif method == 'by_count':
            weights = 1
        else:
            assert False, "Unknown method: {}".format( method )
    
        # Initialize volume
        scaled_volume_shape_zyx = tuple(scaled_volume_shape_xyz[::-1])
        logger.debug("Initializing volume of zyx shape: {}".format( scaled_volume_shape_zyx ))
        density_volume_zyx = numpy.zeros( scaled_volume_shape_zyx, dtype=numpy.float32 )

        # We can't just use the following:
        # density_volume_zyx[coordinates_zyx] = weights
        # Because that wouldn't correctly handle multiple rows with identical coordinates
        # (the multiple rows wouldn't both be counted).
        # Instead, we must use an "unbuffered" (accumulated) operation:
        logger.debug("Accumulating densities...")
        numpy.add.at( density_volume_zyx, coordinates_zyx, weights )

    return density_volume_zyx


DEFAULT_CSV_FORMAT = { 'delimiter' : '\t', 'lineterminator' : '\n' }
def array_from_csv( pointcloud_csv_filepath, 
                    csv_format=DEFAULT_CSV_FORMAT, 
                    column_dtypes=None, 
                    weight_by_size=False,
                    use_cache=True):
    """
    Read the given csv file and return a corresponding 
    numpy structured array of all its values.  
    The CSV file must include a header row.
    
    pointcloud_csv_filepath: The input file
    csv_format: A dict of formatting parameters for the csv module
    column_dtypes: Either: 
                   - a dtype object to use for all columns, or 
                   - a dict of {column_name : dtype} to use for each column
    weight_by_size: If True, weight the intensity of each downsampled pixel 
                    according to the size_px of the objects that it represents.
    use_cache: If True, attempt to use a cached copy of the imported csv data, already in .npy format.
               Provide a string instead of a bool to specify the location of the cache file.
               If the cache file can't be found, it will be created after csv import is complete.
    """
    cache_path = pointcloud_csv_filepath + ".cache.npy"
    if use_cache:
        if isinstance(use_cache, (str, unicode)):
            cache_path = use_cache
        if os.path.exists(cache_path):
            if os.path.getmtime(cache_path) > os.path.getmtime(pointcloud_csv_filepath):
                logger.info("Loading data from cache file: {}".format( cache_path ))
                return numpy.load(cache_path)
    
    # Quick first pass to get the number of points
    # (-1 for header)
    num_points = countlines(pointcloud_csv_filepath) - 1

    logger.debug("Loading data from csv file: {}".format( pointcloud_csv_filepath ))
    with open(pointcloud_csv_filepath, 'r') as f_in:
        csv_reader = csv.reader(f_in, **csv_format)
        column_names = next(csv_reader)

        # If user provided only a single dtype, it is the default type.
        if isinstance(column_dtypes, dict):
            default_column_dtype = numpy.float32
        else:
            if column_dtypes is not None:
                default_column_dtype = column_dtypes
            column_dtypes = {}

        if not column_dtypes:
            column_dtypes = {}
        for column_name in column_names:
            if column_name not in column_dtypes:
                column_dtypes[column_name] = default_column_dtype

        dtype_list = [column_dtypes[column_name] for column_name in column_names]
        row_dtype = list(zip( column_names, dtype_list ))
        csv_array_data = numpy.ndarray( shape=(num_points,), dtype=row_dtype )
    
        for row_index, row_data in enumerate(csv_reader):
            csv_array_data[row_index] = tuple(int(x) for x in row_data)

    if use_cache:
        logger.info("Saving data to cache file: {}".format( cache_path ))
        numpy.save(cache_path, csv_array_data)
    
    return csv_array_data


def countlines(file_path):
    """
    Return the number of lines in the given file.
    """
    line_count = 0
    with open(file_path, 'r') as f:
        for _ in f:
            line_count += 1
    return line_count


def export_hdf5( density_volume_zyx, output_filepath, dset_name ):
    """
    Export the given 3D zyx volume to HDF5.

    density_volume_zyx: The volume to export.  Must be in ZYX order.
    output_filepath: The file to (over)write.
    dset_name: The HDF5 dataset name to use.
    """
    import h5py
    logger.debug("Writing output to: {}/{}".format( output_filepath, dset_name ))
    with h5py.File(output_filepath, 'w') as f_out:
        dset = f_out.create_dataset( dset_name,
                                     density_volume_zyx.shape,
                                     density_volume_zyx.dtype,
                                     chunks=True )
        dset[:] = density_volume_zyx

        # Try to provide axistags on the volume if possible.
        try:
            import vigra
            dset.attrs["axistags"] = vigra.defaultAxistags( "zyx" ).toJSON()
        except ImportError:
            pass


def export_tiff( density_volume_zyx, output_filepath ):
    """
    Export the given 3D zyx volume as a multipage TIFF.
    
    density_volume_zyx: The volume to export.  Must be in ZYX order.
    output_filepath: The name of the .tiff file to write.
    """
    assert os.path.splitext(output_filepath)[1] in ['.tif', '.tiff'], \
        "Wrong extension for TIFF export: {}".format( output_filepath )
    import vigra
    density_volume_zyx = vigra.taggedView(density_volume_zyx, "zyx")
    logger.debug( "Writing output to multipage tiff: {}".format(output_filepath) )
    if os.path.exists( output_filepath ):
        os.remove( output_filepath )
    for z_slice in density_volume_zyx:
        vigra.impex.writeImage( z_slice, output_filepath, dtype='', compression='', mode='a' )


if __name__ == "__main__":
    # When executing from cmdline, print all logging output
    logger.addHandler( logging.StreamHandler(sys.stdout) )
    logger.setLevel(logging.DEBUG)    

    # Define cmd-line API    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=['binary', 'by_count', 'by_size'], default='by_count', 
                        help="The method by which points will be accumulated into the downsampled volume.")
    parser.add_argument("--smooth_with_sigma_xyz", required=False)
    parser.add_argument("--normalize_with_max", type=float, required=False)
    parser.add_argument("--output_dtype", required=False)
    parser.add_argument("pointcloud_csv_filepath")
    parser.add_argument("output_filepath", help="Path to .h5 or .tiff file to (over)write.")
    parser.add_argument("scale_xyz", required=False,
                        help="Scale to divide all coordinates by (after offset), [100, 100, 1.1]",
                        action=ParseListFromString)

    # These parameters aren't usually needed...
    parser.add_argument("offset_xyz", required=False,
                        help="Offset to remove from all point coordinates before processing, [7.1, 8, 0]",
                        action=ParseListFromString)
    parser.add_argument("volume_shape_xyz", required=False,
                        help="Full shape of the original volume. If not provided, use bounding box of the pointcloud.",
                        action=ParseListFromString)

    # Here's some default cmd-line args for debugging...
    DEBUG = False
    if DEBUG:
        sys.argv += ["--method=binary",
                     #"--smooth_with_sigma_xyz=(3.0, 3.0, 3.0)",
                     "--normalize_with_max=255",
                     "--output_dtype=uint8",
                     "../pointclouds/bock-863-pointcloud-20141203.csv", 
                     "../pointclouds/bock-863-pointcloud-20141203.tif", 
                     "(100, 100, 10)"]

    # Parse!
    parsed_args = parser.parse_args()

    volume_shape_xyz = parsed_args.volume_shape_xyz
    offset_xyz = parsed_args.offset_xyz
    scale_xyz = parsed_args.scale_xyz
    smoothing_sigma_xyz = parsed_args.smooth_with_sigma_xyz
    
    # Evaluate other optional args
    output_dtype = None
    if parsed_args.output_dtype:
        assert parsed_args.output_dtype in \
            [ 'uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64', 'int64', 'float32', 'float64' ], \
            "Unknown dtype: {}".format( parsed_args.output_dtype )
        output_dtype = numpy.dtype(parsed_args.output_dtype).type
    
    normalize_with_max = parsed_args.normalize_with_max

    # Main func.
    sys.exit( downsample_pointcloud( parsed_args.pointcloud_csv_filepath,
                                     parsed_args.output_filepath,
                                     scale_xyz,
                                     offset_xyz,
                                     volume_shape_xyz, 
                                     parsed_args.method,
                                     smoothing_sigma_xyz,
                                     normalize_with_max,
                                     output_dtype ) )
