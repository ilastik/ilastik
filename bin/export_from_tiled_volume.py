import os
import numpy
import h5py
from lazyflow.utility import Timer
from lazyflow.utility.io import TiledVolume

import logging
logger = logging.getLogger(__name__)

def export_from_tiled_volume(tiles_description_json_path, roi, output_hdf5_path, output_dataset_name):
    """
    Export a cutout volume from a TiledVolume into an hdf5 dataset.

    Args:
        tiles_description_json_path: path to the TiledVolume's json description file.
        roi: The (start, stop) corners of the cutout region to export. (Must be tuple-of-tuples.)
        output_hdf5_path: The HDF5 file to export to.
        output_dataset_name: The name of the HDF5 dataset to write.  Will be deleted first if necessary.
    """
    if not os.path.exists(tiles_description_json_path):
        raise Exception("Description file does not exist: " + tiles_description_json_path)

    start, stop = numpy.array(roi)
    shape = tuple(stop - start)

    tiled_volume = TiledVolume( tiles_description_json_path )

    with Timer() as timer:
        result_array = numpy.ndarray(shape, tiled_volume.description.dtype)    

        logger.info("Reading cutout volume of shape: {}".format(shape))            
        tiled_volume.read( (start, stop), result_out=result_array )

        logger.info("Writing data to: {}/{}".format( output_hdf5_path, output_dataset_name ))
        with h5py.File( output_hdf5_path, 'a' ) as output_h5_file:
            if output_dataset_name in output_h5_file:
                del output_h5_file[output_dataset_name]
            dset = output_h5_file.create_dataset( output_dataset_name, 
                                                  shape, 
                                                  result_array.dtype, 
                                                  chunks=True,
                                                  data=result_array )            
            try:
                import vigra
            except ImportError:
                pass
            else:
                # Attach axistags to the exported dataset, so ilastik 
                #  automatically interprets the volume correctly.
                output_axes = tiled_volume.description.output_axes
                dset.attrs['axistags'] = vigra.defaultAxistags(output_axes).toJSON()    

        logger.info("Exported {:.1e} pixels in {:.1f} seconds.".format( numpy.prod(shape), timer.seconds() ))


# EXAMPLE USAGE:
# python lazyflow/bin/export_from_tiled_volume.py fib-19-description.json "(10000,4000,8000)" "(10100,4100,8100)" /tmp/exported.h5 cutout_data
if __name__ == "__main__":
    import sys
    import argparse

    # Make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser()
    parser.add_argument("tiles_description_json_path")
    parser.add_argument("cutout_start", help="A Python tuple in Z-Y-X order, provided as a string, e.g. '(0,0,0)'")
    parser.add_argument("cutout_stop", help="A Python tuple in Z-Y-X order, provided as a string, e.g. '(1000,1000,1000)'")
    parser.add_argument("output_hdf5_path")
    parser.add_argument("output_dataset_name")
    parsed_args = parser.parse_args()
    
    # Parse ROI start
    try:
        start = eval(parsed_args.cutout_start)
        assert isinstance(start, (list, tuple))
    except:
        sys.stderr.write("cutout_start not understood: " + parsed_args.cutout_start + "\n")
        sys.exit(1)
    
    # Parse ROI stop
    try:
        stop = eval(parsed_args.cutout_stop)
        assert isinstance(stop, (list, tuple))
    except:
        sys.stderr.write("cutout_stop not understood: " + parsed_args.cutout_stop + "\n")
        sys.exit(1)

    # More validation.
    assert all([isinstance(x, int) for x in start]), "cutout_start must contain integers only."
    assert all([isinstance(x, int) for x in stop]), "cutout_stop must contain integers only."

    # Enable logging.
    handler = logging.StreamHandler( sys.stdout )
    logger.addHandler( handler )
    logger.setLevel(logging.INFO)

    # Export.
    sys.exit( export_from_tiled_volume( parsed_args.tiles_description_json_path,
                                        (start, stop),
                                        parsed_args.output_hdf5_path,
                                        parsed_args.output_dataset_name ) )
    